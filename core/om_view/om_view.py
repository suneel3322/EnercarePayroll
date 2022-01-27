import csv
import datetime
from datetime import date, time, timedelta
from http.client import HTTPResponse
from itertools import chain

from django.db import connection

from core.models import Dispute, DowntimeTracker, Employee, Payroll, Roster
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import *
from django.db.models.functions import *
from django.http import HttpResponse
from django.shortcuts import redirect, render
# Create your views here.
from django.views import View

from core.utils.common import dictfetchall


class OperationsManagerView(View):
    '''Displays the Dashboard of Operations Manager along with other metrics'''
    template_name = 'dashboard.html'

    def get(self,req):
        '''It Display agent count, supervisor count, dipsute raised, approved dispute, declined dipsute metrics in a card layout'''
        if req.user.role !='OPER_MAN':
            messages.warning(req,'You are not authorized to login')
            return redirect('core:logout')

        agt = [it.loginId for it in req.user.get_all_children if it.loginId!=req.user.loginId]
        res = Dispute.objects.filter(oper_man_approve_date__isnull=True,employee__in=agt).all()
        # agents = Employee.objects.all()
        supervisors = Employee.objects.filter(supervisor=req.user.pk)
        agents = Employee.objects.filter(supervisor__in=supervisors)

        ctx = {
            'res':res,
            'agents_count':agents.count(),
            'supervisor_count':supervisors.count(),
            'dispute_raised_count':res.count(),
        'dispute_resolved_count':res.filter(Q(status='YES') | Q(approved_by_sup__isnull=False) | Q(
            approved_by_oper_man__isnull=False) | Q(approved_by_finan__isnull=False)).count(),
        }
        return render(req,self.template_name,ctx)

    def post(self,req):
        dispute_id = req.POST['dispute_id']
        action = req.POST['action']
        reasonArea = req.POST.get('reasonArea',None)

        if reasonArea is None:
            reasonArea = ''

        if action == 'YES':
            oper_man = req.user.loginId.replace("."," ").title()
            print(oper_man)
            dis = Dispute.objects.get(pk=dispute_id)
            dis.comment = f'''{dis.comment}
            Approved by {oper_man}
            (Operations Manager)'''
            dis.approved_by_oper_man=True
            dis.oper_man_approve_date = date.today()

            # checking conditions
            if dis.approved_by_sup:
                pass
            else:
                payroll_id = dis.payroll.pk
                disputed_time = dis.dispute_time
                pay = Payroll.objects.get(pk=payroll_id)
                pay.status = 'YES'
                pay.is_approved = True
                if dis.approve_time is None or dis.approve_time==0:
                    pay.payroll = str(int(pay.payroll) + int(disputed_time))
                else:
                    pay.payroll = str(int(pay.payroll) + int(dis.approve_time))
                pay.save()
            dis.save()

            messages.success(req,'Dispute approved sucess')
            return redirect('core:operations')
        if action == 'NO':
            dis = Dispute.objects.get(pk=dispute_id)
            dis.status = 'NO'
            dis.comment = f'''{dis.comment} ,
            Declined by {req.user.loginId.replace('.',' ').title()} 
            (Operations Manager)
            Due to {reasonArea}'''
            dis.approved_by_oper_man=False
            dis.oper_man_approve_date=date.today()
            payroll_id = dis.payroll.pk
            disputed_time = dis.dispute_time
            if dis.approved_by_sup:
                pay = Payroll.objects.get(pk=payroll_id)
                pay.status = 'NO'
                pay.is_approved = True
                if dis.approve_time is None or dis.approve_time==0:
                    pay.payroll = str(int(pay.payroll) - int(disputed_time))
                else:
                    pay.payroll = str(int(pay.payroll) - int(dis.approve_time))
                pay.save()
            else:
                pass
            dis.save()


            messages.warning(req, 'Dispute declined sucess')
            return redirect('core:operations')


class OperationsDisputeView(LoginRequiredMixin,View):
    '''Displays the disputes processed by the supervisors end. It shows agent name, disputed hours, comment by agent and supervisor on the page.'''
    template_name = 'om_agent_disputes.html'
    title = 'Operations|Payroll Logs'

    def get(self,req):
        '''It redirects the user if role is not operations manager. Contains date filter in the page
        along with a table for dipsutes actioned by supervisors. Whole page is paginated.'''
        if req.user.role !='OPER_MAN':
            messages.warning(req,'You are not authorized to login')
            return redirect('core:logout')
        
        from_date = req.GET.get('fdate')
        to_date = req.GET.get('tdate')

        agt = [it.loginId for it in req.user.get_all_children if it.loginId!=req.user.loginId]
        sup_agt = [it.loginId for it in req.user.get_all_children if it.role=='TEAM_SUP']
        cond = Q(approved_by_sup__isnull=False,approved_by_oper_man__isnull=True,employee__in=agt,approved_by_sup=True) | Q(employee__in=sup_agt,approved_by_oper_man__isnull=True)
        dispute_list = Dispute.objects.filter(cond,dispute_date__gte='2021-12-01').all().order_by('-dispute_date')

        if from_date is not None and to_date is not None:
            lookups = Q(dispute_date__gte=from_date) & Q(dispute_date__lte=to_date)
            dispute_list = dispute_list.filter(lookups).all().order_by('-dispute_date')
        elif from_date is not None and to_date is None:
            lookups = Q(dispute_date__gte=from_date) & Q(dispute_date__lte = (datetime.datetime.fromisoformat(from_date)-timedelta(days=30)).strftime("%Y-%m-%d"))
            dispute_list = dispute_list.filter(lookups).all().order_by('-dispute_date')
        elif from_date is None and to_date is not None:
            lookups = Q(dispute_date__gte = (datetime.datetime.fromisoformat(from_date)+timedelta(days=30)).strftime("%Y-%m-%d")) & Q(dispute_date__lte=to_date)
            dispute_list = dispute_list.filter(lookups).all().order_by('-dispute_date')
        # using pagination with the page
        page = req.GET.get('page',1)
        paginator = Paginator(dispute_list,10)
        try:
            disputes = paginator.page(page)
        except PageNotAnInteger:
            disputes = paginator.page(1)
        except EmptyPage:
            disputes = paginator.page(paginator.num_pages)
        ctx = {
            'res':disputes,
            'title': self.title,
        }

        return render(req,self.template_name,ctx)

    def post(self,req):
        '''It processed the post request and save the actions done by OM on the supervisors action.
        If Yes then dispute is approved else it is rejected and redirected with a message on the screen.'''
        dispute_id = req.POST['dispute_id']
        action = req.POST['action']
        reasonArea = req.POST.get('reasonArea',None)
        dispute_time = req.POST.get('approve_time',None)

        if reasonArea is None:
            reasonArea = ''

        if action == 'YES':
            oper_man = req.user.getName
            dis = Dispute.objects.get(pk=dispute_id)
            dis.comment = f'''{dis.comment}
            Approved By {oper_man}
            (Operations manager)'''
            dis.approved_by_oper_man = True
            dis.oper_man_approve_date = date.today()
            if dispute_time is not None or dispute_time!='':
                dis.dispute_time = dispute_time
            dis.save()

            messages.success(req,'Dispute approved !')
            return redirect('core:om-disputes')
        if action == 'NO':
            oper_man = req.user.getName
            dis = Dispute.objects.get(pk=dispute_id)
            dis.comment = f'''{dis.comment}
            Declined By {oper_man}
            (Operations manager)
            Due to {reasonArea}'''
            dis.approved_by_oper_man = False
            dis.oper_man_approve_date = date.today()
            dis.save()

            messages.warning(req, 'Dispute declined sucess')
            return redirect('core:om-disputes')

class PasswordResetView(LoginRequiredMixin,View):
    '''Helps to reset the password for agents or employees in the current operations manager only.'''
    template_name = 'rest_password.html'

    def get(self,req):
        '''Displays a list of all the active employees under a manager, with action buttons on the right of it.'''
        if req.user.role !='OPER_MAN':
            messages.warning(req,'You are not authorized to login')
            return redirect('core:logout')

        agt = [it.pk for it in req.user.get_all_children if it.loginId!=req.user.loginId]
        emp_lists = Employee.objects.filter(pk__in=agt).order_by('loginId')
        res = Roster.objects.all()

        ctx = {
            'groups':res.values('lob').distinct(),
            'supervisors':Employee.objects.filter(Q(role='TEAM_SUP')|Q(role='FIN')|Q(role='OPER_MAN')).values('loginId').distinct(),
            'resp':emp_lists,
        }
        return render(req, self.template_name, ctx)

    def post(self,req):
        '''It checks for the password authenticity if they are same then the new password is saved for the employee.
        Page is then redirected to reset password again with a message.'''
        pk = req.POST['pk']
        password = req.POST['password']
        password_reset = req.POST['password_reset']

        if password!=password_reset:
            messages.error(req,'New Password and Re-type New Password must match')
            return  redirect('core:reset_password')
        if len(password)<6 or len(password_reset)<6 :
            messages.info(req,'Password must contain atleast 6 characters')
            return  redirect('core:reset_password')

        # in future change this to deluxe code instead of loginId
        emp = Employee.objects.get(pk=pk)
        if emp:
            emp.password = make_password(password)
            emp.save()
            messages.success(req,f'Password reset success for {emp.loginId} .')
            return  redirect('core:reset_password')

        messages.info(req,'No such agent exists')
        return redirect('core:reset_password')

class OmAddAgentView(LoginRequiredMixin,View):
    '''Displays a form by which an operations manager can add the new employee.'''
    template_name = 'register.html'

    def get(self,req):
        '''It returns register page by which operations manager can add an employee.'''
        if req.user.role != 'OPER_MAN':
            messages.warning(req,'You are not authorized to login')
            return redirect('core:logout')

        res = Roster.objects.all()
        ctx = {
            'groups':res.values('lob').distinct(),
            'clients':res.values('client').distinct(),
            'supervisors':Employee.objects.filter(Q(role='TEAM_SUP')|Q(role='FIN')|Q(role='OPER_MAN')).all()
        }
        return render(req,self.template_name,ctx)

    def post(self,req):
        '''It saves the employee data entered from the form, like first, last name, clinet, joining date, zipwire, lob, password,
        password repeat, supervisor, deluxe code. if passwords would not match user is redirected to the register.html page. else 
        saved to the employee and roster table.'''
        firstname = req.POST['firstname']
        lastname = req.POST['lastname']
        client = req.POST['client']
        joining_date = req.POST['joining_date']
        zipwire = req.POST['zipwire']
        lob = req.POST['lob']
        password = req.POST['password']
        password_repeat = req.POST['password_repeat']
        supervisor = req.POST['supervisor']
        deluxe_code = req.POST['deluxe_code']

        if (len(password)<6 and len(password_repeat)<6):
            messages.warning(req,'Password must should be greater than 6 characters')
            return redirect('core:add_agent')
        if password!=password_repeat:
            messages.warning(req,'Password and Repeat password not matched!')
            return redirect('core:add_agent')

        emp, created = Employee.objects.get_or_create(
            deluxCode=deluxe_code,
            defaults={
                'first_name':firstname.strip(),
                'last_name':lastname.strip(),
                'loginId': zipwire.strip().lower(),
                'password': make_password(password.strip()),
                'zipwire_name': firstname.replace(' ','').lower().strip()+' '+lastname.replace(' ','').lower().strip(),
                'supervisor': Employee.objects.get(pk=supervisor),
            }
        )

        if created:
            messages.success(req,'Agent is created..')

        ros, created = Roster.objects.get_or_create(
            deluxcode = deluxe_code,
            defaults = {
                'zipwire':zipwire.strip(),
                'yearMonth':joining_date,
                'lob':lob.strip(),
                'supervisor':Employee.objects.get(pk=supervisor).loginId.replace('.',' ').title(),
                'client':client.strip(),
            }
        )

        return redirect('core:add_agent')

class DowntimeApprovalView(LoginRequiredMixin,View):
    '''Displays the manual downtime added by supervisors for approvals.'''
    template_name = 'downtime_approve.html'

    def get(self,req):
        '''Fetches data from downtime tracker table and displays it in a tabular format with accept and decline buttons.'''
        if req.user.role !='OPER_MAN':
            messages.warning(req,'You are not authorized to login')
            return redirect('core:logout')

        dt_tracker = DowntimeTracker.objects.filter(approved_by__isnull=True)
        emp = Employee.objects.filter(supervisor=req.user)
        res = dt_tracker.filter(zipwire__in=emp.values_list('loginId',flat=True))

        ctx = {
            'res':res
        }

        return render(req,self.template_name,ctx)

    def post(self,req):
        '''As per the action say YES or NO the downtime request is either accepted or declined with remarks and approved by.'''
        tracker_id = req.POST['tracker_id']
        action = req.POST['action']
        print(tracker_id)
        if action == 'YES':
            dt = DowntimeTracker.objects.get(pk=tracker_id)
            dt.approved_by = req.user.loginId
            dt.save()
            messages.success(req,'Request for approved success!')
            return redirect('core:downtime-approve')

        if action == 'NO':
            reason = req.POST['reasonArea']
            dt = DowntimeTracker.objects.get(pk=tracker_id)
            dt.time_min = 0
            dt.approved_by = req.user.loginId
            dt.remarks = f'''{dt.remarks}
            {reason}
            '''
            dt.save()
            messages.success(req, 'Request for declined success!')
            return redirect('core:downtime-approve')

class ProcessAutoDowntimeView(LoginRequiredMixin, View):
    '''This displays all the downtimes automatically which were there in the payroll list of the employee.'''
    template_name = 'downtime_index.html'

    def get(self,req):
        '''Fetches downtime from SP and populates the table.'''
        with connection.cursor() as cursor:
            cursor.execute(f'''EXEC dbo.get_downtime '{req.user.pk}', '{req.user.role}' ''')
            payroll_list = dictfetchall(cursor)
            
        page = req.GET.get('page',1)
        paginator = Paginator(payroll_list,10)
        try:
            payrolls = paginator.page(page)
        except PageNotAnInteger:
            payrolls = paginator.page(1)
        except EmptyPage:
            payrolls = paginator.page(paginator.num_pages)

        ctx = {
            'res':payrolls
        }
        return render(req,self.template_name,ctx)
    
    def post(self,req):
        '''It either approves or declines the downtime and saves it to the payroll table.'''
        action = req.POST.get('action',None)
        tracker_id = req.POST.get('trackerId',None)

        if action == 'YES':
            payroll = Payroll.objects.get(pk=tracker_id)
            payroll.is_om_approve_downtime = True
            payroll.save()
            messages.success(req,'Downtime Approved Success!')
        
        if action == 'NO':
            payroll = Payroll.objects.get(pk=tracker_id)
            payroll.is_om_approve_downtime = False
            payroll.save()
            messages.error(req,'Downtime Declined!')

        return redirect('core:ops-process-downtime')

def change_supervisor_lob(req):
    '''This function is used to change the supervisor for employees when required.'''
    if req.method =='POST':
        zipwire = req.POST['zipwire']
        lob = req.POST['lob']
        supervisor = req.POST['supervisor']

        emp, emp_created = Employee.objects.update_or_create(
            loginId=zipwire,
            defaults = {
                'supervisor':Employee.objects.filter(loginId=supervisor.strip().replace(' ','.').lower()).first(),
            }
        )

        ros = Roster(
            startdate = date.today().strftime('%Y-%m-%d'),
            yearMonth = date.today().strftime('%Y-%m-%d'),
            deluxcode = Roster.objects.filter(zipwire=zipwire).first().deluxcode,
            zipwire = zipwire.strip(),
            lob = lob.strip(),
            supervisor = supervisor.strip(),
        )

        ros.save()
        messages.info(req,'Supervisor and LOB changed..')
        return redirect('core:reset_password')

def gen_report(req):
    '''returns a csv file with ['Date','Agent Name','Deluxe Code','To be paid','Location','LOB','Break','Lunch','Not Ready','Coaching','Training'] columns'''
    resp = HttpResponse(
        content_type='text/csv',
    )
    # resp = HTTPResponse(content_type='text/csv')
    resp['Content-Disposition'] = date.today().strftime('attachment;filename="Export-%Y-%m-%d-Payroll.csv"')
    from_date = req.GET.get('fdate',None)
    to_date = req.GET.get('tdate',None)
    client = req.GET.get('client',None)
    lob =  req.GET.get('lob',None)

    payroll = None
    if from_date is not None and to_date is not None and client is not None and lob is not None:
        with connection.cursor() as cursor:
            cursor.execute(f'''EXEC get_payroll_export_data '{from_date}','{to_date}','{client}','{lob}'  ''')
            payroll = dictfetchall(cursor)
    else:
        with connection.cursor() as cursor:
            cursor.execute(f'''EXEC dbo.get_payroll_export_data '{(date.today()-timedelta(days=30)).strftime('%Y-%m-%d')}','{date.today().strftime('%Y-%m-%d')}','{client}'  ''')
            payroll = dictfetchall(cursor)

    writer = csv.writer(resp)
    writer.writerow(['Date','Agent Name','Deluxe Code','To be paid','Location','LOB','Project','Break','Lunch','Not Ready',
                     'Coaching','Training','ACW','Downtime Tracker','Disputed Hrs','Approved Disputed Hrs'])
    for it in payroll:
        writer.writerow(
            [it.get('startdate'),it.get('Agent Name'),it.get('deluxcode'),it.get('To be paid'),it.get('Location'),
             it.get('LOB'),it.get('Project'),
             it.get('Break'),
             it.get('Lunch'),it.get('Not Ready'),it.get('Coaching'),it.get('Training'),
             it.get('ACW (For AW Only)'),
             it.get('DowntimeTracker'),
             it.get('Disputed Hour'),
             it.get('Approved Disputes')]
            )

    return resp

class UnattenedDisputeView(LoginRequiredMixin,View):

    template_name = 'unattended_disputes_by_sup.html'
    template_name2 = 'unattened_dispute_logs.html'

    def get(self,req):
        employee_name = req.GET.get('q',None)
        if employee_name:
            unattended_disputes_list = Dispute.objects.filter(
                supervisor=employee_name,
                dispute_date__lte=(date.today()-timedelta(days=3)),
                sup_approve_date__isnull=True
                ).values('supervisor','dispute_date','employee','created_at').order_by('-dispute_date')
            

            ctx = {
                'disputes_lst':unattended_disputes_list
            }
            return render(req,self.template_name2,ctx)

        supervisor_name_list = Employee.objects.filter(supervisor=req.user).values_list('loginId',flat=True).distinct()
        unattended_dispute_list = Dispute.objects.filter(supervisor__in=supervisor_name_list,dispute_date__lte=(date.today()-timedelta(days=3)),sup_approve_date__isnull=True).values('supervisor').annotate(dispute_count = Count('dispute_date'))

        ctx = {
            'unattended_dispute_lst':unattended_dispute_list
        }

        return render(req,self.template_name,ctx)

class UnattenedPayrollView(LoginRequiredMixin,View):
    template_name = 'om_unattended_payroll_logs.html'

    def get(self,request):
        supervisors = Employee.objects.filter(supervisor=request.user)
        agents = Employee.objects.filter(supervisor__in=supervisors).values_list('loginId',flat=True)
        all_payroll = Payroll.objects.filter(
            client=request.user.getClient,
            startdate__lte=(date.today()-timedelta(days=3)).strftime('%Y-%m-%d'),
            startdate__gte = (date.today()-timedelta(days=15)).strftime('%Y-%m-%d')
            ).annotate(
                email = Subquery(
                    Employee.objects.filter(
                        loginId=OuterRef('login_id')
                        ).values('email')[:1]
                )
            ).values('startdate','login_id','email')
        excludable_data = Dispute.objects.filter(
            dispute_date__in = all_payroll.values('startdate'),
            employee__in = all_payroll.values('login_id')
        ).values('dispute_date','employee')    

        unattended_payrolls = all_payroll.exclude(
            startdate__in=excludable_data.values('dispute_date'),
            login_id__in=excludable_data.values('employee')).values('startdate','login_id','email').order_by('-startdate')

        page = request.GET.get('page',1)
        paginator = Paginator(unattended_payrolls,10)
        try:
            unattended_payroll = paginator.page(page)
        except PageNotAnInteger:
            unattended_payroll = paginator.page(1)
        except EmptyPage:
            unattended_payroll = paginator.page(paginator.num_pages)

        ctx = {
            'unattended_payrolls':unattended_payroll
        }

        return render(request,self.template_name,ctx)

class OmAcwView(LoginRequiredMixin,View):

    template_name = 'om_acw.html'

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute(f'''EXEC dbo.get_acw_time '{request.user.pk}', '{request.user.role}' ''')
            acw_list = dictfetchall(cursor)

        page = request.GET.get('page',1)
        paginator = Paginator(acw_list,10)
        try:
            acws_list = paginator.page(page)
        except PageNotAnInteger:
            acws_list = paginator.page(1)
        except EmptyPage:
            acws_list = paginator.page(paginator.num_pages)

        ctx = {
            'res':acws_list
        }
        return render(request,self.template_name,ctx)

    def post(self,request):
        action = request.POST['action']
        acw_id = request.POST['acw_id']

        if action=='YES':
            current_payroll = Payroll.objects.get(pk=acw_id)
            current_payroll.is_acw_approved_by_om = True
            current_payroll.save()
            messages.success(request,'ACW Hours approved!')
            return redirect(request.META.get('HTTP_REFERER'))

        if action=='NO':
            current_payroll = Payroll.objects.get(pk=acw_id)
            current_payroll.is_acw_approved_by_om = False
            current_payroll.save()
            messages.info(request,'ACW Hours declined success!')
            return redirect(request.META.get('HTTP_REFERER'))

        
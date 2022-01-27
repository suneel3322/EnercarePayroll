from datetime import date, timedelta

from django.db import connection
from django.contrib.auth.hashers import make_password
from core.models import Dispute, DowntimeTracker, Employee, Payroll, Roster
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import *
from django.db.models.functions import *
from django.shortcuts import redirect, render
from django.views import View

from core.utils.common import declined_disputes, dictfetchall


class SupervisorView(LoginRequiredMixin,View):
    '''
    This basically display all the metrics like total agents, approved disputes, raised dispute, declined disputes in a card on the 
    html page.'''
    # template_name = 'core/supervisor/SupervisorDashboard.html'
    template_name = 'dashboard_v3.html'

    def get(self, req):
        if req.user.role !='TEAM_SUP':
            messages.warning(req,'You are not authorized to login')
            return redirect('core:logout')
        
        agents = Employee.objects.filter(supervisor=req.user.pk)


        context = {
            'agent_count':agents.count(),
        }
        return render(req, self.template_name, context)
    
class SupervisorDisputeView(LoginRequiredMixin,View):
    template_name = 'payroll-super.html'
    title = 'Supervisor|Payroll Logs'

    def get(self,req):
        '''
        This displays all the disputes raised by agents in a tabular form along with
        filters which can use used to filter out the dipsutes as per the date. It only works for
        the employee's whose role is TEAM_SUP, other than that everyone is redirected to login page.
        '''
        if req.user.role !='TEAM_SUP':
            messages.warning(req,'You are not authorized to login')
            return redirect('core:logout')

        
        from_date = req.GET.get('fdate')
        to_date = req.GET.get('tdate')
        # dispute_list = Dispute.objects.filter(supervisor__iexact=req.user.loginId,status='DISPUTE',approved_by_oper_man__isnull=True,approved_by_finan__isnull=True).all()

        '''
        This will check for all the disputes where sup_approve_date=NULL
        in the column
        '''
        dispute_list = Dispute.objects.filter(status='DISPUTE',supervisor__iexact=req.user.loginId,dispute_date__gte='2021-12-01',sup_approve_date__isnull=True).order_by('-dispute_date').all()
        cond = Q(approved_by_finan__isnull=False) | Q(approved_by_oper_man__isnull=False) 
        dispute_list = dispute_list.exclude(cond)
        # using pagination with the page
        if from_date is not None and to_date is not None:
            lookups = Q(dispute_date__gte=from_date) & Q(dispute_date__lte=to_date)
            dispute_list = dispute_list.filter(lookups).all().order_by('-dispute_date')
        elif from_date is not None and to_date is None:
            lookups = Q(dispute_date__gte=from_date) & Q(dispute_date__lte = (datetime.datetime.fromisoformat(from_date)-timedelta(days=30)).strftime("%Y-%m-%d"))
            dispute_list = dispute_list.filter(lookups).all().order_by('-dispute_date')
        elif from_date is None and to_date is not None:
            lookups = Q(dispute_date__gte = (datetime.datetime.fromisoformat(from_date)+timedelta(days=30)).strftime("%Y-%m-%d")) & Q(dispute_date__lte=to_date)
            dispute_list = dispute_list.filter(lookups).all().order_by('-dispute_date')
        else:
            # lookups = Q(dispute_date__gte=(date.today()-timedelta(days=45)).strftime("%Y-%m-%d")) & Q(dispute_date__lte=date.today().strftime("%Y-%m-%d"))
            # dispute_list = dispute_list.filter(lookups).all().order_by('-dispute_date')
            pass
            
        page = req.GET.get('page',1)
        paginator = Paginator(dispute_list,3)
        try:
            disputes = paginator.page(page)
        except PageNotAnInteger:
            disputes = paginator.page(1)
        except EmptyPage:
            disputes = paginator.page(paginator.num_pages)
        context = {
            'res':disputes,
            'title':self.title,
        }
        return render(req, self.template_name, context)


    def post(self,req):
        '''
        This method takes care of the events related to approve a dispute or decline it.
        If action is YES, the dipsute id which we fetch from the view is used and that 
        dispute record is updated accordingly. Else if NO is there, dispute status is updated 
        and NO is added to it. After this the page is redirected to dipsute view again.
        '''
        id = req.POST['pk']
        comment = req.POST['comment']
        action = req.POST['action']
        approve_time = req.POST['approve_time']
        
        if approve_time=='':
            approve_time=None

        if action=='YES':
            Dispute.objects.select_related()\
                .filter(pk=id)\
                .update(
                comment = comment,
                updated_at = date.today(),
                approve_time = approve_time,
                approved_by_sup = True,
                sup_approve_date = date.today().strftime('%Y-%m-%d'),
            )

            messages.info(req,'Dispute Approval success!')
            return redirect('core:super-disputes')
        if action == 'NO':
            Dispute.objects.filter(pk=id).update(
                comment=comment,
                updated_at=date.today(),
                status=action,
                approve_time = approve_time,
                approved_by_sup = False,
                sup_approve_date = date.today().strftime('%Y-%m-%d'),
            )

            messages.info(req, 'Dispute Denied success!')
            return redirect('core:super-disputes')

class DowntimeTrackerView(LoginRequiredMixin,View):
    '''
    It is responsible for adding the downtime time for agents
    when they were engaged in other activities by supervisors. 
    Here a form is presented in which agents can be selected from a 
    list, date can be selected, and reason is given by the supervisor.
    '''
    title = 'Supervisor|D-Tracker'
    template_name = 'form-standard.html'

    def get(self,req):
        '''
        This method is responsible to show the downtime tracker form.
        It renders the form-standard.html file in templates dir.
        '''
        if req.user.role !='TEAM_SUP':
            messages.warning(req,'You are not authorized to login')
            return redirect('core:logout')

        emp = Employee.objects.filter(
            supervisor = req.user.pk
        )

        # if emp:
        ctx = {
                'res':emp,
                'title':self.title,
            }
        return render(req,self.template_name,ctx)

    def post(self,req):
        '''
        This method takes date, agents name list and time, aux code and remarks from 
        supervisors end and saves it to the database, then redirects the user to 
        downtime tracker view again.
        '''
        today = req.POST['date']
        agent_list = req.POST.getlist('agent_name')
        time_min = req.POST['time']
        aux_code = req.POST['aux_code']
        remarks = req.POST['remarks']


        for it in agent_list:
            dt = DowntimeTracker(
                created_at = today,
                agent_name = it,
                time_min = time_min,
                aux_code = aux_code,
                remarks = remarks,
                zipwire = req.user.loginId,
            )
            dt.save()

        messages.success(req,'Downtime has been sent to the Operations Manager for approval!')
        return  redirect('core:downtime-tracker')

class AddAgentView(LoginRequiredMixin,View):
    '''
    AddAgentView is responsible for adding agents to the employee and roster table.
    Here a supervisor can add the agent as an employee to the payroll tool.
    '''
    template_name = 'register.html'

    def get(self,req):
        '''
        This method displays a form which can be used to create the user.
        '''
        if req.user.role != 'TEAM_SUP':
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
        '''
        This method saves the user information send from the above get method. It fetches firstname, 
        last name, client, joining_date, zipwire, lob, password, password_repeat, supervisor and deluxe_code
        from the form and creates an instance of Roster and Employee type to save the data.
        if passwords don't match a message is sent back to the page else Agent created is shown.
        '''
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
            return redirect('core:super_add_agent')
        if password!=password_repeat:
            messages.warning(req,'Password and Repeat password not matched!')
            return redirect('core:super_add_agent')

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

        return redirect('core:super_add_agent')


class PayrollApprovedView(LoginRequiredMixin,View):
    template_name = "agent_payroll_approve.html"

    def get(self,req):
        approved_disputes_by_agents = Dispute.objects.filter(
            status='YES',
            supervisor = req.user.loginId,
            created_at__lte=(date.today()-timedelta(days=3)),
            sup_approve_date__gte = (date.today()-timedelta(days=3)),
            oper_man_approve_date__gte = (date.today()-timedelta(days=3)),
            finan_approve_date__gte = (date.today()-timedelta(days=3)),
        ).values('employee','dispute_date','created_at').annotate(approved_dispute_date_count = Count('dispute_date')).order_by('-created_at')


        page = req.GET.get('page',1)
        paginator = Paginator(approved_disputes_by_agents,10)
        try:
            approved_pay_list = paginator.page(page)
        except PageNotAnInteger:
            approved_pay_list = paginator.page(1)
        except EmptyPage:
            approved_pay_list = paginator.page(paginator.num_pages)

        ctx = {
            'approved_disputes_by_agents':approved_pay_list
        }
        return render(req,self.template_name,ctx)

class PayrollNotApprovedView(LoginRequiredMixin,View):
    '''
    This is responsible for showing all the agents who have not approved the payroll
    in last 3 days from the current date. It shows the payroll created date along with name of agent
    in a tabular format.
    '''
    template_name = 'agent_payroll_not_approved.html'

    def get(self,req):
        agents_loginId_list = [emp.loginId for emp in Employee.objects.filter(supervisor=req.user.pk)]
        payroll_list = Payroll.objects.filter(
            startdate__lte = (date.today()-timedelta(days=3)),
            login_id__in = agents_loginId_list,
        )
        dipsute_list = Dispute.objects.filter(
            supervisor = req.user.loginId,
            employee__in = payroll_list.values_list('login_id',flat=True),
            dispute_date__in=payroll_list.values_list('startdate',flat=True)
        ).values_list('dispute_date',flat=True)
        not_approved_payroll_list = payroll_list.exclude(
            startdate__in = dipsute_list,
        ).values('login_id','startdate').order_by('-startdate')

        # values('login_id','startdate').annotate(approved_dispute_date_count = Count('startdate')).order_by('-startdate')

        if len(not_approved_payroll_list) == 0:
            messages.warning(req,'No one reacted to the payroll in past 3 days!')

        page = req.GET.get('page',1)
        paginator = Paginator(not_approved_payroll_list,10)
        try:
            not_approved_pay_list = paginator.page(page)
        except PageNotAnInteger:
            not_approved_pay_list = paginator.page(1)
        except EmptyPage:
            not_approved_pay_list = paginator.page(paginator.num_pages)

        ctx = {
            'not_approved_payroll_list':not_approved_pay_list
        }
        return render(req,self.template_name,ctx)

class DowntimeProcessView(LoginRequiredMixin,View):
    '''
    This is responsible for showing the downtime values from the payroll table 
    and here supervisor can approve the downtime for auxes like lunch break, not ready etc.
    This data is auto fetched from the payroll table so no manual requests were shown.
    '''
    temaplate_name = 'downtime_index.html'
    title = ''

    def get(self,req):
        '''
        This method calls a SP in the database end which gets all the downtime values from the table and shows
        it in a tabular format which can be used to approve or decline by the supervisors or TL's in the org.
        '''
        
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
        return render(req,self.temaplate_name,ctx)

    def post(self,req):
        '''
        This method basically fetches the action and tracker id for downtime.
        If action is YES it approves the downtime and if NO then the downtime is declined.
        '''
        action = req.POST.get('action',None)
        tracker_id = req.POST.get('trackerId',None)

        if action == 'YES':
            payroll = Payroll.objects.get(pk=tracker_id)
            payroll.is_downtime_approved = True
            payroll.save()
            messages.success(req,'Downtime Approved Success!')
        
        if action == 'NO':
            payroll = Payroll.objects.get(pk=tracker_id)
            payroll.is_downtime_approved = False
            payroll.save()
            messages.error(req,'Downtime Declined!')

        return redirect('core:process-downtime')


class SupAcwView(LoginRequiredMixin,View):

    template_name = 'supervisor_acw.html'

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
            current_payroll.is_acw_approved_by_sup = True
            current_payroll.save()
            messages.success(request,'ACW Hours approved!')
            return redirect(request.META.get('HTTP_REFERER'))

        if action=='NO':
            current_payroll = Payroll.objects.get(pk=acw_id)
            current_payroll.is_acw_approved_by_sup = False
            current_payroll.save()
            messages.info(request,'ACW Hours declined success!')
            return redirect(request.META.get('HTTP_REFERER'))

        
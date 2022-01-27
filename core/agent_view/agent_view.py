from datetime import date

from django.db import connection

from core.models import Dispute, DowntimeTracker, Employee, Payroll, Roster
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import *
from django.db.models.functions import *
from django.shortcuts import redirect, render
from django.views import View

from core.utils.common import dictfetchall


class PayrollView(LoginRequiredMixin,View):
    '''Renders a payroll view for employee with role as agent.'''
    title = 'Payroll'
    template_name = 'table-datatable.html'

    def get(self,req):
        '''Calls a SP which is reponsible for fetching payroll data for the employee.'''
        with connection.cursor() as cursor:
            cursor.execute(f'''EXEC dbo.get_payroll_login '{req.user.loginId}' , '{req.user.getClient}' ''')
            payroll_list = dictfetchall(cursor)
        # using pagination with the page
        page = req.GET.get('page',1)
        paginator = Paginator(payroll_list,10)
        try:
            payrolls = paginator.page(page)
        except PageNotAnInteger:
            payrolls = paginator.page(1)
        except EmptyPage:
            payrolls = paginator.page(paginator.num_pages)

        ctx = {
            'title':req.user.getName+' | '+self.title,
            'res':payrolls,
        }
            
        return render(req,self.template_name,ctx)


class AgentHomeView(LoginRequiredMixin,View):
    '''Displays agent dashboard'''
    title = 'Dashboard'
    template_name = 'dashboard_v2.html'

    def get(self, req):
        '''Renders a page with metrics like total working time, break time etc.'''
        # for this month total working time, total login time, total lunch break not ready
        # for this month total coaching training, payroll time in minutes
        month_wise_data = Payroll.objects.annotate(
            dt = Cast('startdate',DateField())
        ).filter(
            login_id=req.user.loginId, dt__month = date.today().month, dt__year = date.today().year
        ).aggregate(total_working_time_sum = Sum('working_time'),total_login_time_sum = Sum('total_login_time'),total_lunch_break_not_ready_sum = Sum(F('lunch_time')+F('break_time')+F('not_ready_time')),total_coaching_training_sum = Sum(F('coaching_time')+F('training_time')),total_payroll_sum = Sum('payroll'))

        nomr_time = Payroll.objects.annotate(
            dt = Cast('startdate',DateField()),
            working_time_min = Cast('working_time',FloatField()),
            payroll_time_min = Cast('payroll',FloatField()),
        ).filter(login_id=req.user.loginId, dt__month = date.today().month, dt__year = date.today().year)\
            .annotate(norm_working = F('working_time_min')/1440,
            norm_payroll = F('payroll_time_min')/1440,)

        res = Payroll.objects.order_by('-startdate')\
            .prefetch_related('dispute_set')\
            .filter(login_id__exact=req.user.loginId)\
            .all()
        context = {
            'title':req.user.getName+' | '+self.title,
            'res': res,
            'norm_time':nomr_time,
            'disputes_approved_count':nomr_time.filter(status='YES',is_approved=True).count(),
            'raised_disputes_count':nomr_time.filter(status='YES',is_approved=False).count(),

        }
        context = dict(context,**month_wise_data)
        return render(req, self.template_name, context)


def ApproveDispute(req):
    '''To approve the dispute from agent page'''
    if req.method == 'POST':
        status = req.POST.get('approveStatus', None)
        id = req.POST.get('approveId', None)

        payObj = Payroll.objects.get(pk=id)
        start_date = payObj.startdate
        RosObj = Roster.objects.filter(zipwire__exact=req.user.loginId, yearMonth__lte=start_date,deluxcode=req.user.deluxCode).order_by(
            '-yearMonth').first()
        supervisor = RosObj.supervisor.strip().lower().replace(' ','.')

        Dispute.objects.create(
            status = status,
            supervisor = supervisor,
            employee = req.user.loginId,
            updated_at = date.today(),
            dispute_date = start_date,
            approved_by_sup = True,
            approved_by_oper_man = True,
            approved_by_finan = True,
            sup_approve_date = date.today(),
            oper_man_approve_date = date.today(),
            finan_approve_date = date.today(),
        )
        messages.info(req, 'Your payroll is approved..')
        return redirect('core:agent-payroll')


def RaiseDispute(req):
    '''Used to raise a dispute by agent'''
    if req.method == 'POST':
        dispute_status = req.POST.get('disputeStatus', None)
        emp_comment = req.POST.get('emp_comment',None)
        dispute_id = req.POST.get('disputeId', None)
        payroll_id = req.POST.get('payrollId', None)
        disputeType = req.POST.get('disputeType', None)
        dispute_time = req.POST.get('dispute_time', None)

        payObj = Payroll.objects.get(pk=payroll_id)
        start_date = payObj.startdate

        RosObj = Roster.objects.filter(zipwire__exact=req.user.loginId, yearMonth__lte=start_date,deluxcode=req.user.deluxCode).order_by(
            '-yearMonth').first()
        supervisor = RosObj.supervisor.strip().lower().replace(' ','.')

        if dispute_time == '':
            dispute_time = 0

        if dispute_id == '':
            Dispute.objects.create(
                type = disputeType,
                status = dispute_status,
                dispute_time = dispute_time,
                supervisor = supervisor,
                employee = req.user.loginId,
                updated_at = date.today(),
                dispute_date = start_date,
                emp_comment = emp_comment,
            )
            messages.info(req, 'Dispute is sent to your supervisor')
            return redirect('core:agent-payroll')
        else:
            dis_obj , created = Dispute.objects.update_or_create(
                pk=dispute_id,
                defaults = {
                    'type':disputeType,
                    'status':dispute_status,
                    'dispute_time':dispute_time,
                    'supervisor':supervisor,
                    'employee':req.user.loginId,
                    'updated_at':date.today(),
                    'dispute_date':start_date,
                    'emp_comment' : emp_comment,
                }
            )

            if not created:
                messages.info(req, 'Updated dispute is sent to your supervisor')
                return redirect('core:agent-payroll')


from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import redirect, render
from django.db.models import Q
from django.contrib import messages
from django.views import View
from datetime import date

from core.models import Dispute, Payroll, Roster
from core.models.Employee import Employee



class FinanceDashboardView(View):
    '''Displays the Finanace Dashboard with all the metrics on it.'''
    template_name = 'dashboard_v3.html'

    def get(self,req):
        qs = req.GET.get('q')
        name = ''
        if qs is not None:
            if qs.isnumeric():
                emp = Employee.objects.filter(deluxCode=qs.strip()).first()
                if emp:
                    qs = emp.loginId
                    name = emp.getName
                qs = 'None'
            lookups = Q(login_id__icontains=qs)
            qs = Payroll.objects.filter(lookups).all().order_by('-startdate')
            if qs:
                name = qs[0].login_id.strip().replace('.', ' ').title()

        res = Dispute.objects.filter(
            approved_by_finan__isnull=True,
            finan_approve_date__isnull= True
        ).order_by('-dispute_date').all()
        ctx = {
            'qs':qs,
            'name':name,
            'res':res
        }
        return render(req, self.template_name,ctx)

    def post(self, req):
        dispute_id = req.POST['dispute_id']
        action = req.POST['action']
        reasonArea = req.POST.get('reasonArea', None)

        if reasonArea is None:
            reasonArea = ''

        if action == 'YES':
            finanace_obj = req.user.loginId.replace(".", " ").title()
            print(finanace_obj)
            dis = Dispute.objects.get(pk=dispute_id)
            dis.comment = f'''{dis.comment}
                    Approved by {finanace_obj}
                    (Finance)'''

            # condition checking
            if dis.approved_by_sup and not dis.approved_by_oper_man:
                payroll_id = dis.payroll.pk
                disputed_time = dis.dispute_time
                pay = Payroll.objects.get(pk=payroll_id)
                pay.status = 'YES'
                pay.is_approved = True
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    pay.payroll = str(float(pay.payroll) - float(dis.approve_time))
                pay.save()
            elif not dis.approved_by_sup and not dis.approved_by_oper_man:
                payroll_id = dis.payroll.pk
                disputed_time = dis.dispute_time
                pay = Payroll.objects.get(pk=payroll_id)
                pay.status = 'YES'
                pay.is_approved = True
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    pay.payroll = str(float(pay.payroll) - float(dis.approve_time))
                pay.save()

            dis.approved_by_finan = True
            dis.finan_approve_date = date.today()
            dis.save()



            messages.success(req, 'Dispute approved sucess')
            return redirect('core:finance-index')
        if action == 'NO':
            dis = Dispute.objects.get(pk=dispute_id)
            dis.status = 'NO'
            dis.comment = f'''{dis.comment} ,
                    Declined by {req.user.loginId.replace('.', ' ').title()} 
                    (Finance)
                    Due to {reasonArea}'''
            # condition checking
            if dis.approved_by_sup and dis.approved_by_oper_man:
                payroll_id = dis.payroll.pk
                disputed_time = dis.dispute_time
                pay = Payroll.objects.get(pk=payroll_id)
                pay.status = 'NO'
                pay.is_approved = True
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    pay.payroll = str(float(pay.payroll) - float(dis.approve_time))
                pay.save()
            elif not dis.approved_by_sup and dis.approved_by_oper_man:
                payroll_id = dis.payroll.pk
                disputed_time = dis.dispute_time
                pay = Payroll.objects.get(pk=payroll_id)
                pay.status = 'NO'
                pay.is_approved = True
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    pay.payroll = str(float(pay.payroll) - float(dis.approve_time))
                pay.save()
            elif dis.approved_by_sup or not dis.approved_by_oper_man:
                payroll_id = dis.payroll.pk
                disputed_time = dis.dispute_time
                pay = Payroll.objects.get(pk=payroll_id)
                pay.status = 'NO'
                pay.is_approved = True
                if dis.approve_time is None or dis.approve_time == 0:
                    pay.payroll = str(float(pay.payroll) - float(disputed_time))
                else:
                    pay.payroll = str(float(pay.payroll) - float(dis.approve_time))
                pay.save()

            dis.approved_by_oper_man = True
            dis.finan_approve_date = date.today()

            dis.save()

            messages.warning(req, 'Dispute declined sucess')
            return redirect('core:finance-index')


class FinanceDisputeView(LoginRequiredMixin,View):
    '''Displays all the disputes actioned by operations manager.'''
    template_name = 'finn_agent_disputes.html'
    title = 'Finance | Open Disputes'

    def get(self,req):
        '''Returns dipsute page where all the disputes along with date filter is presented.
        User can download the dipsutes in a csv file.'''
        from_date = req.GET.get('fdate')
        to_date = req.GET.get('tdate')
        qs = req.GET.get('q')
        name = ''

        if qs is not None:
            if qs.isnumeric():
                emp = Employee.objects.filter(deluxCode=qs.strip()).first()
                if emp:
                    qs = emp.loginId
                    name = emp.getName
                qs = 'None'
            lookups = Q(login_id__icontains=qs)
            qs = Payroll.objects.filter(lookups).all().order_by('-startdate')
            if qs:
                name = qs[0].login_id.strip().replace('.', ' ').title()

                if from_date is not None and to_date is not None:
                    lookups = Q(startdate__gte=from_date) & Q(startdate__lte=to_date)
                    qs = qs.filter(lookups).all().order_by('-startdate')
                elif from_date is not None and to_date is None:
                    lookups = Q(startdate__gte=from_date)
                    qs = qs.filter(lookups).all().order_by('-startdate')
                elif from_date is None and to_date is not None:
                    lookups = Q(startdate__lte=to_date)
                    qs = qs.filter(lookups).all().order_by('-startdate')

        dispute_lists = Dispute.objects.filter(
            dispute_date__gte='2021-12-01',
            approved_by_sup__isnull=False,
            approved_by_oper_man__isnull=False,
            approved_by_oper_man=True,
            approved_by_finan__isnull=True,
            finan_approve_date__isnull= True
        ).order_by('-dispute_date').all()

        # using pagination with the page
        page = req.GET.get('page',1)
        paginator = Paginator(dispute_lists,10)
        try:
            disputes = paginator.page(page)
        except PageNotAnInteger:
            disputes = paginator.page(1)
        except EmptyPage:
            disputes = paginator.page(paginator.num_pages)
        ctx = {
            'qs':qs,
            'name':name,
            'res':disputes,
            'title':self.title,
        }
        return render(req, self.template_name,ctx)

    def post(self, req):
        '''It helps to do some action by the finance on the disputes listed, if action is YES,
        then the employee dispute is accepted else rejected, and redirected to the dipsutes page again.'''
        dispute_id = req.POST['dispute_id']
        action = req.POST['action']
        reasonArea = req.POST.get('reasonArea', None)

        if reasonArea is None:
            reasonArea = ''

        if action == 'YES':
            finanace_obj = req.user.getName
            dis = Dispute.objects.get(pk=dispute_id)
            dis.status = 'YES'
            dis.comment = f'''{dis.comment}
                    Approved by {finanace_obj}
                    (Finance)'''
            # condition checking
            client = Roster.objects.filter(zipwire=dis.employee.strip().lower(),supervisor__icontains=dis.supervisor,startdate__lte=dis.dispute_date)[0].client
            pay = Payroll.objects.filter(startdate=dis.dispute_date,login_id = dis.employee, client=client).first()
            pay.is_approved = True
            if dis.approved_by_sup and dis.approved_by_oper_man:
                pass
            elif not dis.approved_by_sup and dis.approved_by_oper_man:
                pass
            elif dis.approved_by_sup and not dis.approved_by_oper_man:
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    dis.dispute_time = dis.approve_time
                pay.save()
            elif not dis.approved_by_sup and not dis.approved_by_oper_man:
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    dis.dispute_time = dis.approve_time
                pay.save()

            dis.approved_by_finan = True
            dis.finan_approve_date = date.today()
            dis.save()



            messages.success(req, 'Dispute approved sucess')
            return redirect(req.META.get('HTTP_REFERER'))
            return redirect('core:finn-disputes')
        if action == 'NO':
            dis = Dispute.objects.get(pk=dispute_id)
            dis.status = 'NO'
            dis.comment = f'''{dis.comment} ,
                    Declined by {req.user.loginId.replace('.', ' ').title()} 
                    (Finance)
                    Due to {reasonArea}'''
            # condition checking
            client = Roster.objects.filter(zipwire=dis.employee.strip().lower(),supervisor__icontains=dis.supervisor,startdate__lte=dis.dispute_date)[0].client
            pay = Payroll.objects.filter(startdate=dis.dispute_date,login_id = dis.employee, client=client).first()
            pay.status = 'NO'
            pay.is_approved = True
            if dis.approved_by_sup and dis.approved_by_oper_man:
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    dis.dispute_time = dis.approve_time
                pay.save()
            elif not dis.approved_by_sup and dis.approved_by_oper_man:
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    dis.dispute_time = dis.approve_time
                pay.save()
            elif dis.approved_by_sup or not dis.approved_by_oper_man:
                if dis.approve_time is None or dis.approve_time == 0:
                    dis.approve_time = dis.dispute_time
                else:
                    dis.dispute_time = dis.approve_time
                pay.save()

            dis.approved_by_finan = False
            dis.finan_approve_date = date.today()

            dis.save()

            messages.warning(req, 'Dispute declined sucess')
            return redirect(req.META.get('HTTP_REFERER'))

class FinanaceAddressedDisputeView(LoginRequiredMixin,View):
    
    template_name = 'finn_addressed_disputes.html'

    def get(self,request):
        dispute_lists = Dispute.objects.filter(
            dispute_date__gte='2021-12-01',
            comment__isnull=False,
            approved_by_finan__isnull=False,
            finan_approve_date__isnull= False
        ).order_by('-dispute_date').all()

        # using pagination with the page
        page = request.GET.get('page',1)
        paginator = Paginator(dispute_lists,10)
        try:
            disputes = paginator.page(page)
        except PageNotAnInteger:
            disputes = paginator.page(1)
        except EmptyPage:
            disputes = paginator.page(paginator.num_pages)
        ctx = {
            'res':disputes
        }
        return render(request,self.template_name,ctx)
        
    
from django.db.models import Q
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views import View
from datetime import date

from core.models import Dispute, Payroll, Employee


class FinanceDashboardView(View):
    template_name = 'core/finance/index.html'

    def get(self,req):

        from_date = req.GET.get('fdate')
        to_date = req.GET.get('tdate')
        qs = req.GET.get('q')
        name = ''
        dt = None
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
            dt = Payroll.objects.filter(lookups).all().order_by('-startdate')
        elif from_date is not None and to_date is None:
            lookups = Q(startdate__gte=from_date)
            dt = Payroll.objects.filter(lookups).all().order_by('-startdate')
        elif from_date is None and to_date is not None:
            lookups = Q(startdate__lte=to_date)
            dt = Payroll.objects.filter(lookups).all().order_by('-startdate')
        if dt:
            name = 'All Agents'

        res = Dispute.objects.filter(
            approved_by_finan__isnull=True,
            finan_approve_date__isnull= True
        ).order_by('-dispute_date').all()
        ctx = {
            'qs':qs,
            'dt':dt,
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
            if dis.approved_by_sup and dis.approved_by_oper_man:
                pass
            elif not dis.approved_by_sup and dis.approved_by_oper_man:
                pass
            elif dis.approved_by_sup and not dis.approved_by_oper_man:
                payroll_id = dis.payroll.pk
                disputed_time = dis.dispute_time
                pay = Payroll.objects.get(pk=payroll_id)
                pay.status = 'YES'
                pay.is_approved = True
                if dis.approve_time is None or dis.approve_time == 0:
                    pay.payroll = str(float(pay.payroll) - float(disputed_time))
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
                    pay.payroll = str(float(pay.payroll) - float(disputed_time))
                else:
                    pay.payroll = str(float(pay.payroll) - float(dis.approve_time))
                pay.save()

            # payroll_id = dis.payroll.pk
            # disputed_time = dis.dispute_time
            # pay = Payroll.objects.get(pk=payroll_id)
            # pay.status = 'YES'
            # pay.is_approved = True
            # pay.payroll = str(float(pay.payroll) + float(disputed_time))
            # pay.save()

            dis.approved_by_sup = True
            dis.approved_by_oper_man = True
            dis.approved_by_finan = True
            dis.oper_man_approve_date = date.today()
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
                    pay.payroll = str(float(pay.payroll) - float(disputed_time))
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
                    pay.payroll = str(float(pay.payroll) - float(disputed_time))
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
            elif not dis.approved_by_sup and not dis.approved_by_oper_man:
                pass



            dis.approved_by_sup = True
            dis.approved_by_finan = True
            dis.approved_by_oper_man = True
            dis.oper_man_approve_date = date.today()
            dis.finan_approve_date = date.today()

            dis.save()

            messages.warning(req, 'Dispute declined sucess')
            return redirect('core:finance-index')

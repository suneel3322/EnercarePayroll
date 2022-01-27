import csv
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import connection
from core.models import Dispute,Payroll
from django.shortcuts import redirect, render
from datetime import date, timedelta
from django.http import HttpResponse
from django.db.models import *
from django.db.models.functions import *

from core.models.Employee import Employee
from core.models.Dispute import Roster

def dictfetchall(cursor):
    '''Return all rows from a cursor as a dict'''
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

@login_required
def agent_payroll_view(req,pk):
    '''Returns the page where all payroll logs is present for a specific user.'''
    zipwire_id = Dispute.objects.get(pk=pk).employee
    with connection.cursor() as cursor:
            cursor.execute(f'''EXEC dbo.get_payroll_login '{zipwire_id}', '{req.user.getClient}' ''')
            payroll_lists = dictfetchall(cursor)
    # using pagination with the page
    page = req.GET.get('page',1)
    paginator = Paginator(payroll_lists,7)
    try:
        payrolls = paginator.page(page)
    except PageNotAnInteger:
        payrolls = paginator.page(1)
    except EmptyPage:
        payrolls = paginator.page(paginator.num_pages)
    context = {
        'res': payrolls,
        'user': zipwire_id.replace('.',' ').title(),
    }
    return render(req,'common_payroll.html',context)

@login_required
def approved_disputes(req):
    if req.method == 'GET':
        template_name = 'approved_dispute_logs.html'
        if req.user.role == 'TEAM_SUP' :
            res = Dispute.objects.filter(supervisor__icontains=req.user.loginId,sup_approve_date__isnull=False).order_by('-sup_approve_date').all()
            ctx = {
                'res':res
            }
            return render(req,template_name,ctx)
        if req.user.role == 'OPER_MAN' :
            res = Dispute.objects.filter(supervisor__icontains=req.user.loginId,oper_man_approve_date__isnull=False).all()
            ctx = {
                'res':res
            }
            return render(req,template_name,ctx)
        if req.user.role == 'FIN' :
            res = Dispute.objects.filter(supervisor__icontains=req.user.loginId,finan_approve_date__isnull=False).all()
            ctx = {
                'res':res
            }
            return render(req,template_name,ctx)

@login_required
def declined_disputes(req):
    if req.method == 'GET':
        pass
    pass

@login_required
def ajax_get_client(request):
    if request.method == 'GET':
        # get the lob from the client side
        client = request.GET.get('client',None)
        resp = Roster.objects.values('lob','client').distinct()
        if client is None or client == 'None':
            return JsonResponse({'lob':list(resp.values_list('lob',flat=True))}, status=200)
        # check for the lob in the database
        if resp.exists():
            out = []
            for result in resp:
                if result.get('client')==client:
                    out.append(result['lob'])
            return JsonResponse({'lob':out}, status = 200)
        else:
            return JsonResponse({}, status=400)
    pass

@login_required
def sup_om_gen_report(req):
    '''Returns a csv for supervisors and operations manager when they want to download the disputes log.'''
    resp = HttpResponse(
        content_type='text/csv',
    )
    resp['Content-Disposition'] = date.today().strftime('attachment;filename="Export-%Y-%m-%d-Disputes.csv"')
    
    from_date = req.GET.get('fdate',None)
    to_date = req.GET.get('tdate',None)
    dispute_type = req.GET.get('dispute_type',None)
    dispute_status = req.GET.get('dispute_status',None)

    if from_date=='':
        from_date = None
    if to_date == '':
        to_date = None
    if dispute_type == '':
        dispute_type = None
    if dispute_status == '':
        dispute_status = None

    dispute_queryset = None

    if from_date is not None and to_date is not None:
        lookups = (Q(dispute_date__gte=from_date) & Q(dispute_date__lte=to_date))

        if req.user.role == 'OPER_MAN':
            agt = [it.loginId for it in req.user.get_all_children if it.loginId!=req.user.loginId]
            dispute_queryset = Dispute.objects.filter(lookups,employee__in=agt).all()
            dispute_queryset = dispute_queryset.exclude(dispute_time__isnull=True)
        
        if req.user.role == 'FINN':
            # agt = [it.loginId for it in req.user.get_all_children if it.loginId!=req.user.loginId]
            dispute_queryset = Dispute.objects.filter(lookups).all()
            dispute_queryset = dispute_queryset.exclude(dispute_time__isnull=True)

    elif from_date is None and to_date is not None:
        pass
    elif from_date is not None and to_date is None:
        pass
    else:
        from_date = (date.today()-timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = date.today().strftime("%Y-%m-%d")

        lookups = (Q(dispute_date__gte=from_date) & Q(dispute_date__lte=to_date))

        if req.user.role == 'OPER_MAN':
            agt = [it.loginId for it in req.user.get_all_children if it.loginId!=req.user.loginId]
            dispute_queryset = Dispute.objects.filter(lookups,employee__in=agt).all()
            dispute_queryset = dispute_queryset.exclude(dispute_time__isnull=True)

        if req.user.role == 'FINN':
            # agt = [it.loginId for it in req.user.get_all_children if it.loginId!=req.user.loginId]
            dispute_queryset = Dispute.objects.filter(lookups).all()
            dispute_queryset = dispute_queryset.exclude(dispute_time__isnull=True)

    writer = csv.writer(resp)

    if req.user.role == 'OPER_MAN':
        writer.writerow(['Date','Raised By','Disputed Time (min)','Approved Time (By Supervisor)','Dispute Status','Dispute Type','Agent Comment','Supervisor comment'])

        for it in dispute_queryset:
            writer.writerow(
                [
                    it.dispute_date,
                    it.employee,
                    it.dispute_time,
                    it.approve_time,
                    it.status,
                    it.type,
                    it.emp_comment,
                    it.comment
                ]
            )

    if req.user.role == 'FINN':
        writer.writerow(['Date','Raised By','Disputed Time (min)','Approved Time By Supervisor','Dispute status','Dispute Type','Agent Comment','Supervisor Comment'])

        for it in dispute_queryset:
            writer.writerow(
                [
                    it.dispute_date,
                    it.employee,
                    it.dispute_time,
                    it.approve_time,
                    it.status,
                    it.type,
                    it.emp_comment,
                    it.comment
                ]
            )
    return resp

@login_required
def save_email(req):
    email = req.GET.get('work_mail')

    if email is None:
        messages.info(req,'Email cannot be empty')
        return redirect(req.META.get('HTTP_REFERER'))

    if email == ' ':
        messages.info(req,'Email cannot be empty')
        return redirect(req.META.get('HTTP_REFERER'))
    elif email == '':
        messages.info(req,'Email cannot be empty')
        return redirect(req.META.get('HTTP_REFERER'))

    e = Employee.objects.get(deluxCode=req.user.deluxCode)
    e.email = email.lower()
    e.save()
    messages.success(req,'Thank you for providing email!')
    return redirect(req.META.get('HTTP_REFERER'))
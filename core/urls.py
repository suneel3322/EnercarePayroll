from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls import path

from core.models import DowntimeTracker
from core.agent_view.agent_view import (AgentHomeView, ApproveDispute,RaiseDispute,PayrollView)
from core.finance_view.finnace_view import FinanceDashboardView, FinanceDisputeView, FinanaceAddressedDisputeView
from core.login_view.login_view import ChangePasswordView, LoginView, LogoutView
from core.supervisor_view.supervisor_view import (DowntimeProcessView, PayrollApprovedView, PayrollNotApprovedView, SupervisorDisputeView,DowntimeTrackerView,SupervisorView,AddAgentView,SupAcwView)

from core.om_view.om_view import OperationsDisputeView, OperationsManagerView,PasswordResetView,OmAddAgentView,DowntimeApprovalView, ProcessAutoDowntimeView,change_supervisor_lob,gen_report, UnattenedDisputeView, UnattenedPayrollView, OmAcwView
from core.utils.common import agent_payroll_view, ajax_get_client, save_email, sup_om_gen_report,approved_disputes
from core.views import maintenance

app_name = 'core'

urlpatterns = [

    # login urls
    path('',LoginView.as_view(),name='login'),
    # url(r'^',maintenance,name='login'),
    path('logout/',LogoutView,name='logout'),
    path('password/change/',ChangePasswordView.as_view(),name='change-password'),
    
    # agents urls
    path('agent/',login_required(AgentHomeView.as_view()),name='home'),
    path('agent/payroll/',PayrollView.as_view(),name='agent-payroll'),
    # dispute related agent urls
    path('agent/approve/',ApproveDispute,name='approve'),
    path('agent/dispute/',RaiseDispute,name='raise-dispute'),


    # operations manager urls
    path('operations/',login_required(OperationsManagerView.as_view()),name='operations'),
    path('operations/reset_password/',PasswordResetView.as_view(),name='reset_password'),
    path('operations/add/',OmAddAgentView.as_view(),name='add_agent'),
    path('operations/change_supervisor_lob/',login_required(change_supervisor_lob),name='change_supervisor_lob'),
    path('operations/downtime-approve/',DowntimeApprovalView.as_view(),name='downtime-approve'),
    path('operations/disputes/',OperationsDisputeView.as_view(),name='om-disputes'),
    path('operations/payroll/<pk>/',agent_payroll_view,name='agent_payroll'),
    path('operations/process/downtime/',ProcessAutoDowntimeView.as_view(),name='ops-process-downtime'),
    path('operations/unattended/disputes/',UnattenedDisputeView.as_view(),name='om-unattended-disputes'),
    path('operations/unattended/payrolls/',UnattenedPayrollView.as_view(),name='om-unattended-payrolls'),
    path('operations/acw/',OmAcwView.as_view(),name='om-acw'),
    # path('operations/approved/disputes/',approved_disputes,name='om-approved-disputes'),
    
    # supervisor urls
    path('supervisor/',login_required(SupervisorView.as_view()),name='super-home'),
    path('supervisor/add/',AddAgentView.as_view(),name='super_add_agent'),
    path('profile/',login_required(SupervisorView.as_view()),name='profile'),
    path('supervisor/downtime-tracker/',DowntimeTrackerView.as_view(),name='downtime-tracker'),
    path('supervisor/disputes/',SupervisorDisputeView.as_view(),name='super-disputes'),
    path('supervisor/payroll/<int:pk>/',agent_payroll_view,name='super_agent_payroll'),
    path('supervisor/process/downtime/',DowntimeProcessView.as_view(),name='process-downtime'),
    path('supervisor/payroll/approved/',PayrollApprovedView.as_view(),name='sup-approved-payroll'),
    path('supervisor/payroll/not/approved/',PayrollNotApprovedView.as_view(),name='sup-not-approved-payroll'),
    path('supervisor/acw/',SupAcwView.as_view(),name='super-acw'),
    # path('supervisor/approved/disputes/',approved_disputes,name='sup-approved-disputes'),

    # finacne urls
    path('finance/',FinanceDashboardView.as_view(),name='finance-index'),
    path('finance/disputes/',FinanceDisputeView.as_view(),name='finn-disputes'),
    path('finance/payroll/<pk>/',agent_payroll_view,name='finn_agent_payroll'),
    path('finance/addressed/disputes/',FinanaceAddressedDisputeView.as_view(),name='finn-addressed-dispute'),
    # path('finance/approved/disputes/',approved_disputes,name='finance-approved-disputes'),
    # report export path
    path('export/',gen_report,name='export'),
    path('export-csv/',sup_om_gen_report,name='export-csv'),

    path('save/email/',save_email,name='save-email'),
    path('get/ajax/client', ajax_get_client, name='get_ajax_client'),
]

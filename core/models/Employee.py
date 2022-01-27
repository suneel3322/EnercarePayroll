from datetime import date

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from core.models.Dispute import Dispute, Roster


class UserManager(BaseUserManager):

    def _create_user(self, loginId, password, is_superuser, **extra_fields):
        if not loginId:
            raise ValueError('Users must have a login ID')
        today = date.today()
        loginId = self.normalize_email(loginId)
        extra_fields['last_login'] = today
        user = self.model(
            loginId=loginId,
            is_active=True,
            is_superuser=is_superuser,
            date_joined=today,
            **extra_fields
        )
        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_user(self, loginId, password, **extra_fields):
        return self._create_user(loginId, password, False, **extra_fields)

    def create_superuser(self, loginId, password, **extra_fields):
        user = self._create_user(loginId, password, True, **extra_fields)
        return user


class Employee(AbstractBaseUser, PermissionsMixin):
    AGENT = 'AGT'
    OPERATIONS_MANAGER = 'OPER_MAN'
    TEAM_LEAD_OR_SUPERVISOR = 'TEAM_SUP'
    FIN = 'FIN'
    Roles = (
        ('AGT', 'Agent'),
        ('OPER_MAN', 'Operations Manager'),
        ('TEAM_SUP', 'Team Lead/Supervisor'),
        ('FIN','Finance'),
    )

    deluxCode = models.CharField(max_length=255, unique=True, null=True) # unique employee no. or id
    loginId = models.CharField(max_length=255, null=False, unique=False) # employee username
    password = models.CharField(max_length=255, null=False) # password of an emp in hashed format
    zipwire_name = models.CharField(max_length=255, null=True) # same as loginId
    first_name = models.CharField(max_length=255, null=True) # frist name of emp    
    last_name = models.CharField(max_length=255, null=True) # last name of emp
    role = models.CharField(max_length=255, choices=Roles, default='AGT') # roles an emp may have   
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='agent', null=True) # supervisor of an emp
    is_active = models.BooleanField(default=True) # defines whether an emp is active or not
    is_superuser = models.BooleanField(default=False) # defines whether an emp is supervisor or  not
    last_login = models.DateField(null=True, blank=True) # this is an auto field
    date_joined = models.DateField(auto_now_add=True) # this is an auto field
    email = models.EmailField(null=True) # this field is entered by each new emp on the joining

    USERNAME_FIELD = 'deluxCode'
    EMAIL_FIELD = 'zipwire_name'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.loginId}"

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def get_emails(employee_lst):
        return Employee.objects.filter(loginId__in=employee_lst).values_list('email',flat=True)

    @property
    def getActiveAgentCount(self):
        '''Returns active agents count'''
        if self.role == 'FIN':
            return Employee.objects.filter(role='AGT',is_active=True).count()
        return 'N/A'

    @property
    def getRaisedDispute(self):
        '''Returns raised dispute counts as per the role of employee'''
        if self.role =='TEAM_SUP':
            disputes = Dispute.objects.filter(
                supervisor__iexact=self.loginId,
                approved_by_sup__isnull=True,
                sup_approve_date__isnull=True).count()
            return disputes

        if self.role =='OPER_MAN':
            agts = Employee.objects.filter(supervisor=self.pk).values_list('loginId',flat=True).all()
            disputes = Dispute.objects.filter(
                supervisor__in=agts,
                approved_by_oper_man__isnull=True,
                oper_man_approve_date__isnull=True).count()
            return disputes

        disputes = Dispute.objects.filter(
                approved_by_finan__isnull=True,
                finan_approve_date__isnull= True).count()
        return disputes

    @property
    def getApprovedDispute(self):
        '''Returns approved dispute counts as per role of employee'''
        if self.role =='TEAM_SUP':
            disputes = Dispute.objects.filter(
                supervisor__iexact=self.loginId,
                sup_approve_date__isnull=False).count()
            return disputes

        if self.role =='OPER_MAN':
            agts = Employee.objects.filter(supervisor=self.pk).values_list('loginId',flat=True).all()
            disputes = Dispute.objects.filter(
                supervisor__in=agts,
                oper_man_approve_date__isnull=False).count()
            return disputes

        disputes = Dispute.objects.filter(
                finan_approve_date__isnull=False,
                status='YES').count()
        return disputes

    @property
    def getDeclinedDispute(self):
        '''Returns declined disputes count as per the role of employee'''
        if self.role =='TEAM_SUP':
            disputes = Dispute.objects.filter(
                supervisor__iexact=self.loginId,
                # status='NO',
                approved_by_sup=False,
                sup_approve_date__isnull=False).count()
            return disputes

        if self.role =='OPER_MAN':
            agts = Employee.objects.filter(supervisor=self.pk).values_list('loginId',flat=True)
            disputes = Dispute.objects.filter(
                supervisor__in=agts,
                approved_by_oper_man=False,
                oper_man_approve_date__isnull=False).count()
            return disputes

        disputes = Dispute.objects.filter(
                approved_by_finan=False,
                finan_approve_date__isnull=False,
                status='NO').count()
        return disputes


    @property
    def getApproved(self):
        '''
        Returns the total approved dispute count as per the role of employee.
        '''
        if self.role =='TEAM_SUP':
            disputes = Dispute.objects.filter(
                supervisor__iexact=self.loginId,
                approved_by_sup=True,
                sup_approve_date__isnull=False).count()
            return disputes

        if self.role =='OPER_MAN':
            agts = Employee.objects.filter(supervisor=self.pk).values_list('loginId',flat=True)
            disputes = Dispute.objects.filter(
                supervisor__in=agts,
                approved_by_oper_man=True,
                oper_man_approve_date__isnull=False).count()
            return disputes

        disputes = Dispute.objects.filter(
                approved_by_finan=True
                ).count()
        return disputes

    @property
    def getName(self):
        '''
        Returns the name of the employee
            If name is not null then first name with last name is returned
            else parsed login id is returned.
        '''
        return self.loginId.replace('.',' ').title().strip()

    @property
    def getLob(self):
        '''Returns the LOB of the employee'''
        ros = Roster.objects.filter(zipwire__iexact = self.loginId).order_by('-yearMonth').first()
        if ros:
            return ros.lob
        return 'N/A'

    @property
    def getSupervisorName(self):
        '''Returns the supervisor name of employee if exists else NA'''
        ros = Roster.objects.filter(zipwire__iexact = self.loginId).order_by('-yearMonth').first()
        if ros:
            return ros.supervisor.replace('.' , ' ').title().strip()
        return 'N/A'

    @property
    def getSupervisor(self):
        '''Returns the supervisor of employee'''
        ros = Roster.objects.filter(zipwire__iexact = self.loginId).order_by('-yearMonth').first()
        if ros:
            return ros.supervisor.strip()
        return 'N/A'

    @property
    def get_all_children(self):
        '''Returns all the employees under the current employee.
        Note : The employee for which it returns includes it also'''
        children = list()
        # if include_self:
        children.append(self)
        for child in self.agent.all():
            children.extend(child.get_all_children)
        return children

    @property
    def getClient(self):
        return Roster.objects.filter(deluxcode=self.deluxCode).first().client

    @property
    def get_lob_list(self):
        return Roster.objects.values('lob').distinct()

    @property
    def get_client_list(self):
        return Roster.objects.values('client').distinct()

    @property
    def get_supervisor_list(self):
        supervisors = Employee.objects.filter(supervisor=self).values_list('loginId',flat=True)
        if supervisors.exists():
            return supervisors
        return None
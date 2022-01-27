from django.db import models

from core.models import Employee


class Dispute(models.Model):
    type = models.CharField(max_length=255,default='None')
    status = models.CharField(max_length=25,null=False,default='HOLD')
    comment = models.TextField(null=True)
    emp_comment = models.TextField(null=True)
    dispute_time = models.PositiveIntegerField(null=True)
    approve_time = models.PositiveIntegerField(null=True)
    supervisor = models.CharField(max_length=255,null=True)
    employee = models.CharField(max_length=255,null=True)
    dispute_date = models.CharField(max_length=255,null=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now_add=False, null=True)
    payroll = models.ForeignKey('Payroll',on_delete=models.SET_NULL,null=True)
    approved_by_sup = models.BooleanField(null=True)
    approved_by_oper_man = models.BooleanField(null=True)
    approved_by_finan = models.BooleanField(null=True)

    sup_approve_date = models.DateField(auto_now_add=False,null=True)
    oper_man_approve_date = models.DateField(auto_now_add=False, null=True)
    finan_approve_date = models.DateField(auto_now_add=False, null=True)

class Roster(models.Model):
    startdate = models.CharField(max_length=255,null=True) # this field is no longer in use
    yearMonth = models.CharField(max_length=255,null=True) # hiredate of an emp
    deluxcode = models.CharField(max_length=255,null=False) # unique employee no. or id
    zipwire = models.CharField(max_length=255,null=False) # same as loginId field in Employee model
    lob = models.CharField(max_length=255,null=False) # group in which an emp may reside
    supervisor = models.CharField(max_length=255,null=False) # sueprvisor name of emp
    client = models.CharField(max_length=255,null=True) # Project Initials for each client

    def __str__(self):
        return f'{self.zipwire} {self.supervisor}'

    @property
    def getName(self):
        return self.zipwire.replace('.',' ').title()

    @property
    def getSupervisorName(self):
        return self.supervisor.replace('.', ' ').title()

class Payroll(models.Model):
    startdate = models.CharField(max_length=255,null=False)
    login_id = models.CharField(max_length=255,null=False)
    login_time = models.CharField(max_length=255,default=0)
    logout_time = models.CharField(max_length=255,default=0)
    total_login_time = models.FloatField(default=0)
    working_time = models.FloatField(default=0)
    lunch_time = models.FloatField( default=0)
    break_time = models.FloatField( default=0)
    not_ready_time = models.FloatField( default=0)
    coaching_time = models.FloatField( default=0)
    training_time = models.FloatField( default=0)
    payroll = models.FloatField(default=0)
    status = models.CharField(max_length=255,default='NEW')
    is_downtime_approved = models.BooleanField(null=True) # this is to check whether the downtime is approved by supervisor or not
    is_om_approve_downtime = models.BooleanField(null=True) # this is to check whether the downtime is approved by om or not
    is_approved = models.BooleanField(default=False)
    client = models.CharField(max_length=255,null=True)
    acw = models.FloatField(default=0)
    is_acw_approved_by_sup = models.BooleanField(null=True) # for AWR accounts only
    is_acw_approved_by_om = models.BooleanField(null=True) # for AWR accounts only

    def __str__(self):
        return f'''{self.login_id} payroll date: {self.startdate}'''

    @property
    def convertLoginId(self):
        return self.login_id.replace('.',' ').title()

    @property
    def getLoginTimeInHours(self):
        return f'{int(self.login_time)}:{int(((self.login_time)*60)%60)}'

    @property
    def getLogoutTimeInHours(self):
        return f'{int(self.logout_time)}:{int(((self.logout_time)*60)%60)}'

    @property
    def getTotalLoginTimeInHours(self):
        h,m = divmod(float(self.total_login_time), 60)
        m = str(m).split('.')[0]
        h = str(h).split('.')[0]
        if len(m) == 1:
            m = '0'+m
        return  f"{h}:{m}"

    @property
    def getWorkingTimeInHours(self):
        h,m = divmod(self.working_time, 60)
        m = str(m).split('.')[0]
        h = str(h).split('.')[0]
        if len(m) == 1:
            m = '0'+m
        return f"{h}:{m}"

    @property
    def getLunchBreakNotReadyTimeInHours(self):
        h,m = divmod((self.lunch_time + self.break_time + self.not_ready_time),60)
        m = str(m).split('.')[0]
        h = str(h).split('.')[0]
        if len(m) == 1:
            m = '0'+m
        return f"{h}:{m}"

    @property
    def getCoachingTrainingTimeInHours(self):
        h,m = divmod((self.coaching_time+ self.training_time), 60)
        m = str(m).split('.')[0]
        h = str(h).split('.')[0]
        if len(m) == 1:
            m = '0'+m
        return f"{h}:{m}"

    @property
    def getPayrollTimeInHours(self):
        h, m = divmod((self.payroll), 60)
        m = str(m).split('.')[0]
        h = str(h).split('.')[0]
        if len(m) == 1:
            m = '0'+m
        return f"{h}:{m}"
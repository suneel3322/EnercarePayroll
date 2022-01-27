from django.db import models

from core.models import Employee


class DowntimeTracker(models.Model):
    created_at = models.DateField(auto_now_add=False,null=True) # contains date when this event is being done
    agent_name = models.CharField(max_length=255,null=True) # contains emp loginId same as of Employee Model
    time_min = models.BigIntegerField(default=0) # time entered in minutes from supervisors end
    remarks = models.TextField(null=True) # reason sent by the supevisor for the addition of downtime
    aux_code = models.CharField(max_length=255,null=True) # events for which agents were occupied in other activities
    approved_by = models.CharField(max_length=255,null=True) # contains operations manager loginId(same as Employee Model)
    zipwire = models.CharField(max_length=255,null=True) # contains supervisor loginId(Same as Employee Model)

    def __str__(self):
        return f'{self.agent_name} has {self.time_min} worked'

    @property
    def getAgentName(self):
        return self.agent_name.replace('.',' ').title()

    @property
    def getRaiserName(self):
        return self.zipwire.replace('.',' ').title()
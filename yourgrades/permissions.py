from django.db import models


class RightsSupport(models.Model):

    class Meta:
        managed = False
        permissions = (
            ('manager', 'Global manager rights'),
            ('teacher', 'Global teacher rights'),
            ('student', 'Global student rights'),
            ('parent', 'Global parent rights'),
        )

from django.db import models

# Create your models here.

class UAT(models.Model):
    prefix = models.CharField(max_length=1, default='X')
    server = models.IntegerField() 
    message = models.TextField(default='No Message')
    progress = models.IntegerField(default=0)
    taskid = models.TextField(default='None')
 #   user = models.TextField(default='None')
 #   date = models.TextField(default='None')
    

    def __str__(self):
        return str(self.prefix)+str(self.server)

class QA(models.Model):
    prefix = models.CharField(max_length=1, default='X')
    server = models.IntegerField() 
    message = models.TextField(default='No Message')
    progress = models.IntegerField(default=0)
    taskid = models.TextField(default='None')
#    user = models.TextField(default='None')
#    date = models.TextField(default='None')

    def __str__(self):
        return str(self.prefix)+str(self.server)



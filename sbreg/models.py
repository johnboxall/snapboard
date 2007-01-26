from django.db import models

from django.contrib.auth.models import User 

# Create your models here.

class UserProfile(models.Model): 
    user = models.OneToOneField(User) 
    activation_key = models.CharField(maxlength=40) 
    key_expires = models.DateTimeField()

    class Admin:
        pass

"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} Profile"

from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('core', 'Core User'),
        ('admin', 'Admin User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='core')

    def is_admin_user(self):
        return self.role == 'admin'

    def is_core_user(self):
        return self.role == 'core'
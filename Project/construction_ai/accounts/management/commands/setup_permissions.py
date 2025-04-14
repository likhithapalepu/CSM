from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Setup user groups and permissions'

    def handle(self, *args, **kwargs):
        # Core User
        core_group, created = Group.objects.get_or_create(name='core_user')
        # Add specific view-only permissions if needed

        # Admin User
        admin_group, created = Group.objects.get_or_create(name='admin_user')
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)

        self.stdout.write(self.style.SUCCESS("User groups and permissions created."))

from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(m2m_changed, sender=User.groups.through)
def assign_admin_permissions(sender, instance, action, pk_set, **kwargs):
    """
    Automatically set is_staff=True when a user is added to the Admin group.
    """
    if action == "post_add":
        admin_group = Group.objects.filter(name="Admin").first()
        if admin_group and admin_group.id in pk_set:
            instance.is_staff = True
            instance.save()

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.utils.translation import gettext_lazy as _
from authentication.manager import AccountManagement
from django.contrib.auth.hashers import make_password

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fullname = models.CharField(max_length=100)  # Increased max_length for flexibility
    password = models.CharField(max_length=250)  # Store hashed passwords
    email = models.EmailField(max_length=254, unique=True)
    wallet_pin = models.CharField(max_length=128, blank=True, null=True)  # Increased max_length for hashed PIN
    pin_created_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']

    objects = AccountManagement()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Ensure password is hashed before saving
        if not self.password.startswith('pbkdf2_') and not self._state.adding:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

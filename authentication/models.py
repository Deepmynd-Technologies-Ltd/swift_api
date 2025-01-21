import uuid
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from authentication.manager import AccountManagement

# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user_id = models.CharField(max_length=100, unique=True)
  fullname = models.CharField(max_length=20)
  password = models.CharField(max_length=250)
  email = models.EmailField(max_length=254, unique=True)
  is_active = models.BooleanField(default=True)
  is_verified = models.BooleanField(default=False)
  is_staff = models.BooleanField(default=False)

  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS= ['fullname']

  objects = AccountManagement()

  class Meta:
      verbose_name = _("User")
      verbose_name_plural = _("Users")

  def __str__(self):
      return self.user_id

  # def get_absolute_url(self):
  #     return reverse("user_detail", kwargs={"pk": self.pk})

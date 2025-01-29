import uuid
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

from provider.libs import decrypt_data, encrypt_data

class ProviderType(models.TextChoices):
    BUY = "buy", "BUY"
    SELL = "sell", "SELL"
    BOTH = "both", "BOTH"

# Create your models here.
class Provider(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  provider_name = models.CharField(max_length=100, unique=True)
  provider_subtitle = models.CharField(max_length=100)
  provider_link = models.CharField(max_length=500)
  provider_type = models.CharField(max_length=10,choices=ProviderType.choices,default=ProviderType.BOTH,)


  class Meta:
      verbose_name = _("Provider")
      verbose_name_plural = _("Providers")

  def set_sensitive_data(self, data):
        self.provider_link = encrypt_data(data)

  def get_sensitive_data(self):
        return decrypt_data(self.provider_link)

  def __str__(self):
      return self.provider_name

  def get_absolute_url(self):
      return reverse("Provider_detail", kwargs={"pk": self.pk})

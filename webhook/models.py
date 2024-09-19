from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
# Create your models here.

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.CharField(max_length=50)
    message = models.CharField(max_length=255)
    fee = models.DecimalField(max_digits=18, decimal_places=8)
    owner = models.ForeignKey("User", on_delete=models.CASCADE, verbose_name="notification")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")

    def __str__(self):
        return self.id

    # def get_absolute_url(self):
    #     return reverse("notification_detail", kwargs={"pk": self.pk})
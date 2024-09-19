from django.db import models
from uuid import uuid4
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from authentication.models import User

# Create your models here.
class Wallets(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid4)
  address = models.CharField(max_length=255, unique=True)
  private_key = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)
  amount = models.DecimalField(default=0.0, max_digits=19, decimal_places=10)
  owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallets')

  class Meta:
    verbose_name = _("Wallet")
    verbose_name_plural = _("Wallet Addresses")

  def __str__(self):
      return self.address

class Transaction(models.Model):
    wallet = models.ForeignKey(Wallets, on_delete=models.CASCADE, related_name='transactions')
    id = models.UUIDField(primary_key=True, default=uuid4)
    tx_hash = models.CharField(max_length=255)
    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42)
    amount = models.DecimalField(max_digits=18, decimal_places=8)  # Ether value
    token = models.CharField(max_length=20, default='ETH')  # Token type (ETH, USDT, etc.)
    timestamp = models.DateTimeField(auto_now_add=True)  # When the transaction was made
    status = models.CharField(max_length=10, default='pending')  # Can be pending, success, failed
    gas_fee = models.DecimalField(max_digits=18, decimal_places=8, default=0)  # Gas fee for the transaction


    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    def __str__(self):
        return f'{self.token} Transaction {self.tx_hash}'

    def get_absolute_url(self):
        return reverse("transaction_detail", kwargs={"pk": self.pk})

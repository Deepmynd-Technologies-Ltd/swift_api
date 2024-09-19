from django.contrib import admin
from .models import Wallets, Transaction

# Register your models here.
admin.site.register(Wallets)
admin.site.register(Transaction)
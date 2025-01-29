from django.contrib import admin

from provider.libs import encrypt_data
from .models import Provider

class ProviderModelAdmin(admin.ModelAdmin):
    list_display = ('provider_name', 'provider_subtitle')

    def save_model(self, request, obj, form, change):
        # Encrypt the string before saving
        if 'provider_link' in form.cleaned_data:
            obj.provider_link = encrypt_data(form.cleaned_data['provider_link'])
        super().save_model(request, obj, form, change)

admin.site.register(Provider, ProviderModelAdmin)
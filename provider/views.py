from typing import List, Optional
from django.shortcuts import render
from ninja import Router

from provider.schemas import ProviderSchemas
from .models import Provider, ProviderType

# Create your views here.

provider_system = Router(tags=["Provider Services"])

@provider_system.get('/', response=List[ProviderSchemas])
def get_all_provider(request, provider_options: ProviderType = ProviderType.BOTH):
  provider = Provider.objects.all()
  if provider_options is not ProviderType.BOTH:
    provider = provider.filter(provider_type=provider_options)
  return provider
from enum import Enum
from ninja import Schema
import uuid

class ProviderTypeEnum(str, Enum):
    BUY = "buy"
    SELL = "sell"
    BOTH = "both"

class ProviderSchemas(Schema):
    id: uuid.UUID
    provider_name: str
    provider_subtitle: str
    provider_link: str
    provider_type: ProviderTypeEnum

from typing import Any, List, Optional

from ninja.schema import BaseModel


class AmountTo(BaseModel):
    amount: str
    currency: str


class AmountFrom(BaseModel):
    amount: str
    currency: str


class AmountReceived(BaseModel):
    amount: str
    currency: str


class Fees(BaseModel):
    currency: str
    network_fee: str
    service_fee: str
    partner_fee: str
    total_fee: str


class FeesInUsd(BaseModel):
    network_fee: str
    service_fee: str
    partner_fee: str
    total_fee: str


class Quote(BaseModel):
    quoteId: str
    amountTo: AmountTo
    amountFrom: AmountFrom
    amountReceived: AmountReceived
    currencyCodeTo: str
    currencyCodeFrom: str
    fees: Fees
    feesInUsd: FeesInUsd
    directionChange: str
    expiresAt: str


class Transaction(BaseModel):
    status: str
    rejectReason: Any
    invoice: str
    flow: str
    createdAt: str
    statusUpdatedAt: str


class Country(BaseModel):
    name: str
    code: str


class BillingAddress(BaseModel):
    country: Country
    state: Any
    zip: str
    city: str
    address: str


class Card(BaseModel):
    source: str
    cardholderName: str
    maskedCardNumber: str
    expirationDate: str
    billingAddress: BillingAddress


class Payment(BaseModel):
    id: str
    name: str
    card: Card
    errorCode: Any


class Payout(BaseModel):
    id: str
    name: str
    transaction_hash: str
    explorer_link: str
    destinationWalletAddress: str


class AmountFrom1(BaseModel):
    amount: str
    currency: str


class AmountTo1(BaseModel):
    amount: str
    currency: str


class Data(BaseModel):
    requestId: str
    partnerUserId: str
    userEmail: str
    userIp: str
    quote: Quote
    transaction: Transaction
    payment: Payment
    payout: Payout
    amountFrom: AmountFrom1
    amountTo: AmountTo1
    promoCode: Any


class Asset(BaseModel):
    currency: str
    currencyCode: str
    displayName: str
    blockchain: str
    network: str
    decimals: int
    tokenContract: Any
    hasDestinationTag: bool


class Meta(BaseModel):
    assets: List[Asset]


class WebhookPayload(BaseModel):
    timestamp: Optional[int] = None
    event: Optional[str] = None
    data: Optional[Data] = None
    meta: Optional[Meta] = None
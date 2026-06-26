from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    order_id: str
    status: str
    purchase_date: datetime
    total_amount: float
    currency: str
    items_count: int
    platform: str
    account: str


@dataclass
class InventoryItem:
    sku: str
    asin: str | None
    condition: str
    fulfillable_qty: int
    inbound_qty: int
    reserved_qty: int
    platform: str
    account: str


@dataclass
class AccountHealth:
    account: str
    platform: str
    order_defect_rate: str
    late_shipment_rate: str
    valid_tracking_rate: str
    status: str


@dataclass
class Listing:
    sku: str
    asin: str | None
    title: str
    price: float
    currency: str
    status: str        # Active / Inactive / Incomplete
    quantity: int
    platform: str
    account: str


@dataclass
class ReportMeta:
    report_id: str
    report_type: str
    created_time: datetime
    status: str                    # IN_QUEUE / IN_PROGRESS / DONE / FATAL
    report_document_id: str | None
    platform: str
    account: str


class PlatformAdapter(ABC):
    @abstractmethod
    def get_orders(self, days: int = 7, status: str | None = None) -> list[Order]: ...

    @abstractmethod
    def get_inventory(self, sku: str | None = None) -> list[InventoryItem]: ...

    @abstractmethod
    def get_account_health(self) -> AccountHealth: ...

    @abstractmethod
    def get_listings(self, sku: str | None = None) -> list[Listing]: ...

    @abstractmethod
    def update_price(self, sku: str, price: float, currency: str = "USD") -> None: ...

    @abstractmethod
    def request_report(self, report_type: str, start_date: datetime, end_date: datetime) -> str: ...

    @abstractmethod
    def get_report_status(self, report_id: str) -> ReportMeta: ...

    @abstractmethod
    def download_report(self, report_document_id: str) -> str: ...

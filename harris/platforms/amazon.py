import gzip
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from sp_api.api import Orders, Inventories, Sellers
from sp_api.base import Marketplaces, SellingApiException

from .base import PlatformAdapter, Order, InventoryItem, AccountHealth, Listing, ReportMeta

MARKETPLACE_MAP = {
    "US": Marketplaces.US,
    "CA": Marketplaces.CA,
    "MX": Marketplaces.MX,
    "UK": Marketplaces.UK,
    "DE": Marketplaces.DE,
    "FR": Marketplaces.FR,
    "JP": Marketplaces.JP,
    "AU": Marketplaces.AU,
    "SG": Marketplaces.SG,
    "AE": Marketplaces.AE,
}

ORDER_STATUS_MAP = {
    "pending": "Pending",
    "unshipped": "Unshipped",
    "shipped": "Shipped",
    "canceled": "Canceled",
    "invoice_unconfirmed": "InvoiceUnconfirmed",
}


def _retry(fn, *args, **kwargs):
    for attempt in range(3):
        try:
            return fn(*args, **kwargs)
        except SellingApiException as e:
            if e.code == 429 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise


class AmazonAdapter(PlatformAdapter):
    def __init__(self, account_name: str, account_config: dict):
        self.account_name = account_name
        marketplace_code = account_config.get("marketplace", "US").upper()
        self.marketplace = MARKETPLACE_MAP.get(marketplace_code, Marketplaces.US)
        self.credentials = {
            "lwa_app_id": account_config["client_id"],
            "lwa_client_secret": account_config["client_secret"],
            "refresh_token": account_config["refresh_token"],
            "aws_access_key": account_config["aws_access_key"],
            "aws_secret_key": account_config["aws_secret_key"],
        }
        if role_arn := account_config.get("role_arn"):
            self.credentials["role_arn"] = role_arn
        self._seller_id: str | None = None

    def _get_seller_id(self) -> str:
        if self._seller_id is not None:
            return self._seller_id
        client = Sellers(credentials=self.credentials, marketplace=self.marketplace)
        response = _retry(client.get_marketplace_participation)
        participations = response.payload
        # participations is a list; grab the first sellerId available
        for entry in participations:
            seller_id = entry.get("seller", {}).get("sellerId")
            if seller_id:
                self._seller_id = seller_id
                return self._seller_id
        raise RuntimeError("Unable to determine seller ID from marketplace participations")

    def get_orders(self, days: int = 7, status: str | None = None) -> list[Order]:
        created_after = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).isoformat()

        kwargs: dict = {"CreatedAfter": created_after}
        if status:
            api_status = ORDER_STATUS_MAP.get(status.lower(), status)
            kwargs["OrderStatuses"] = [api_status]

        client = Orders(credentials=self.credentials, marketplace=self.marketplace)
        response = _retry(client.get_orders, **kwargs)

        all_orders = []
        all_orders.extend(response.payload.get("Orders", []))
        next_token = response.payload.get("NextToken")
        while next_token:
            response = _retry(client.get_orders, NextToken=next_token)
            all_orders.extend(response.payload.get("Orders", []))
            next_token = response.payload.get("NextToken")

        orders = []
        for o in all_orders:
            order_total = o.get("OrderTotal", {})
            orders.append(
                Order(
                    order_id=o["AmazonOrderId"],
                    status=o["OrderStatus"],
                    purchase_date=datetime.fromisoformat(
                        o["PurchaseDate"].replace("Z", "+00:00")
                    ),
                    total_amount=float(order_total.get("Amount", 0)),
                    currency=order_total.get("CurrencyCode", "USD"),
                    items_count=o.get("NumberOfItemsShipped", 0)
                    + o.get("NumberOfItemsUnshipped", 0),
                    platform="amazon",
                    account=self.account_name,
                )
            )
        return orders

    def get_inventory(self, sku: str | None = None) -> list[InventoryItem]:
        client = Inventories(credentials=self.credentials, marketplace=self.marketplace)
        kwargs: dict = {"details": True}
        if sku:
            kwargs["sellerSkus"] = [sku]

        response = _retry(client.get_inventory_summary_marketplace, **kwargs)

        all_summaries = []
        all_summaries.extend(response.payload.get("inventorySummaries", []))
        next_token = response.payload.get("nextToken")
        while next_token:
            page_kwargs = dict(kwargs)
            page_kwargs["nextToken"] = next_token
            response = _retry(client.get_inventory_summary_marketplace, **page_kwargs)
            all_summaries.extend(response.payload.get("inventorySummaries", []))
            next_token = response.payload.get("nextToken")

        items = []
        for item in all_summaries:
            details = item.get("inventoryDetails", {})
            items.append(
                InventoryItem(
                    sku=item["sellerSku"],
                    asin=item.get("asin"),
                    condition=item.get("condition", "NewItem"),
                    fulfillable_qty=details.get("fulfillableQuantity", 0),
                    inbound_qty=details.get("inboundReceivingQuantity", {}).get(
                        "totalQuantity", 0
                    ),
                    reserved_qty=details.get("reservedQuantity", {}).get(
                        "totalReservedQuantity", 0
                    ),
                    platform="amazon",
                    account=self.account_name,
                )
            )
        return items

    def get_account_health(self) -> AccountHealth:
        # Seller metrics via Reports API (simplified — real impl needs Reports API)
        client = Sellers(credentials=self.credentials, marketplace=self.marketplace)
        _retry(client.get_marketplace_participation)
        return AccountHealth(
            account=self.account_name,
            platform="amazon",
            order_defect_rate="N/A",
            late_shipment_rate="N/A",
            valid_tracking_rate="N/A",
            status="active",
        )

    def get_listings(self, sku: str | None = None) -> list[Listing]:
        from sp_api.api import ListingsItems
        client = ListingsItems(credentials=self.credentials, marketplace=self.marketplace)
        inv_items = self.get_inventory(sku=sku)
        listings = []
        for item in inv_items:
            try:
                resp = _retry(
                    client.get_listings_item,
                    sellerId=self._get_seller_id(),
                    sku=item.sku,
                    marketplaceIds=[self.marketplace.marketplace_id],
                    includedData=["summaries", "offers"],
                )
                payload = resp.payload
                summaries = payload.get("summaries", [{}])[0]
                offers = payload.get("offers", [{}])
                price = offers[0].get("regularPrice", {}).get("amount", 0.0) if offers else 0.0
                currency = offers[0].get("regularPrice", {}).get("currencyCode", "USD") if offers else "USD"
                listings.append(Listing(
                    sku=item.sku,
                    asin=item.asin,
                    title=summaries.get("itemName", ""),
                    price=float(price),
                    currency=currency,
                    status=summaries.get("status", "Unknown"),
                    quantity=item.fulfillable_qty,
                    platform="amazon",
                    account=self.account_name,
                ))
            except Exception:
                continue
        return listings

    def update_price(self, sku: str, price: float, currency: str = "USD") -> None:
        from sp_api.api import ListingsItems
        client = ListingsItems(credentials=self.credentials, marketplace=self.marketplace)
        body = {
            "productType": "PRODUCT",
            "patches": [
                {
                    "op": "replace",
                    "path": "/attributes/purchasable_offer",
                    "value": [{
                        "marketplace_id": self.marketplace.marketplace_id,
                        "currency": currency,
                        "our_price": [{"schedule": [{"value_with_tax": price}]}],
                    }],
                }
            ],
        }
        _retry(
            client.patch_listings_item,
            sellerId=self._get_seller_id(),
            sku=sku,
            marketplaceIds=[self.marketplace.marketplace_id],
            body=body,
        )

    def request_report(self, report_type: str, start_date: datetime, end_date: datetime) -> str:
        from sp_api.api import Reports
        client = Reports(credentials=self.credentials, marketplace=self.marketplace)
        body = {
            "reportType": report_type,
            "dataStartTime": start_date.isoformat(),
            "dataEndTime": end_date.isoformat(),
            "marketplaceIds": [self.marketplace.marketplace_id],
        }
        response = _retry(client.create_report, body=body)
        return response.payload["reportId"]

    def get_report_status(self, report_id: str) -> ReportMeta:
        from sp_api.api import Reports
        client = Reports(credentials=self.credentials, marketplace=self.marketplace)
        response = _retry(client.get_report, report_id)
        p = response.payload
        return ReportMeta(
            report_id=p["reportId"],
            report_type=p["reportType"],
            created_time=datetime.fromisoformat(p["createdTime"].replace("Z", "+00:00")),
            status=p["processingStatus"],
            report_document_id=p.get("reportDocumentId"),
            platform="amazon",
            account=self.account_name,
        )

    def download_report(self, report_document_id: str) -> str:
        from sp_api.api import Reports
        client = Reports(credentials=self.credentials, marketplace=self.marketplace)
        response = _retry(client.get_report_document, report_document_id)
        doc = response.payload
        url = doc["url"]
        compression = doc.get("compressionAlgorithm", "")
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
        if compression == "GZIP":
            data = gzip.decompress(data)
        return data.decode("utf-8")

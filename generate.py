import base64
import datetime
import requests
import os

API_KEY = os.environ["SS_API_KEY"]
API_SECRET = os.environ["SS_API_SECRET"]
STORE_ID = os.environ.get("SS_STORE_ID", None)


def make_authorization_header(key, secret):
    encoded = base64.urlsafe_b64encode(f"{key}:{secret}".encode("utf-8"))
    return f"Basic {encoded.decode('ascii')}"


class Shipstation:
    BASE_URL = "https://ssapi.shipstation.com"

    def __init__(self, api_key, api_secret):
        self.http = requests.Session()
        self.http.headers["Authorization"] = make_authorization_header(api_key, api_secret)

    def list_orders(self, store_id=None, order_status=None, page_size=None, page=None):
        response = self.http.get(f"{self.BASE_URL}/orders", params={
            "storeId": store_id,
            "orderStatus": order_status,
            "pageSize": page_size,
            "page": page,
        })

        response.raise_for_status()

        return response.json()

    def list_shipments(self, store_id=None, ship_date_start=None, page_size=None, page=None):
        response = self.http.get(f"{self.BASE_URL}/shipments", params={
            "storeId": store_id,
            "pageSize": page_size,
            "page": page,
            "shipDateStart": ship_date_start
        })

        response.raise_for_status()

        return response.json()

    def list_stores(self):
        response = self.http.get(f"{self.BASE_URL}/stores")
        response.raise_for_status()
        return response.json()


def list_stores(ss):
    print("No store specified, please set SS_STORE_ID to one of the following:")
    stores = ss.list_stores()

    for store in stores:
        print(f"* {store['storeName']}: {store['storeId']}")


def count_shipped_orders_over_last_month(ss):
    start_date = (datetime.date.today() - datetime.timedelta(days=31)).strftime("%Y-%m-%d")
    shipments = ss.list_shipments(store_id=STORE_ID, page_size=500, ship_date_start=start_date)

    last_ship_date = shipments["shipments"][-1]["shipDate"]
    last_ship_date = datetime.datetime.strptime(last_ship_date, "%Y-%m-%d")
    last_ship_date = f"{last_ship_date:%B} {last_ship_date.day}"

    return len(shipments["shipments"]), last_ship_date

def generate_order_list(ss):
    shipped_in_last_month, last_shipped = count_shipped_orders_over_last_month(ss)
    orders = ss.list_orders(order_status="awaiting_shipment", store_id=STORE_ID, page_size=500)

    with open("docs/queue.md", "w") as fh:
        print(f"We have shipped **{shipped_in_last_month}** orders over the last month, and the last order we shipped went out on {last_shipped}.\n\n", file=fh)
        print("| position in queue | order number | order date |", file=fh)
        print("| - | - | - |", file=fh)

        for n, order in enumerate(orders["orders"], 1):
            order_date = datetime.datetime.fromisoformat(order["orderDate"].rsplit(".", 1)[0]).date()
            combined = "<sup title='This order was combined with another'>*</sup>" if order["advancedOptions"]["mergedOrSplit"] else ""

            print(f"| {n} | #{order['orderNumber']} {combined} | {order_date} |", file=fh)


def generate_preorder_list(ss):
    orders = ss.list_orders(order_status="on_hold", store_id=STORE_ID, page_size=500)

    with open("docs/preorder-queue.md", "w") as fh:
        print("| position in queue | order number | order date |", file=fh)
        print("| - | - | - |", file=fh)

        for n, order in enumerate(orders["orders"], 1):
            order_date = datetime.datetime.fromisoformat(order["orderDate"].rsplit(".", 1)[0]).date()
            hold_date = datetime.datetime.fromisoformat(order["holdUntilDate"].rsplit(".", 1)[0]).date()
            combined = "<sup title='This order was combined with another'>*</sup>" if order["advancedOptions"]["mergedOrSplit"] else ""

            print(f"| {n} | #{order['orderNumber']} {combined} | {order_date} |", file=fh)

def main():
    ss = Shipstation(API_KEY, API_SECRET)

    if STORE_ID is None:
        list_stores(ss)
    else:
        generate_order_list(ss)
        generate_preorder_list(ss)


if __name__ == "__main__":
    main()

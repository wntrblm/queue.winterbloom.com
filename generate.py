import base64
import datetime
import requests
import os

API_KEY = os.environ["SS_API_KEY"]
API_SECRET = os.environ["SS_API_SECRET"]
STORE_ID = os.environ["SS_STORE_ID"]


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


ss = Shipstation(API_KEY, API_SECRET)

orders = ss.list_orders(order_status="awaiting_shipment", store_id=STORE_ID, page_size=500)


with open("site/queue.md", "w") as fh:
    print("| position in queue | order number | order date |", file=fh)
    print("| - | - | - |", file=fh)

    for n, order in enumerate(orders["orders"], 1):
        order_date = datetime.datetime.fromisoformat(order["orderDate"].rsplit(".", 1)[0]).date()
        print(f"| {n} | #{order['orderNumber']} | {order_date} |", file=fh)

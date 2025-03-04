import requests
from django.conf import settings
import uuid

class SquadcoAPI:
    def __init__(self):
        self.base_url = "https://api-d.squadco.com"
        self.secret_key = settings.SQUADCO_SECRET_KEY

    def buy_airtime(self, phone, amount):
        endpoint = f"{self.base_url}/vending/purchase/airtime"
        payload = {
            "phone_number": phone,
            "amount": amount,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.secret_key}"
        }
        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"API call failed: {str(e)}"}
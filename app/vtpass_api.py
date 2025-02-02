import requests
from django.conf import settings
from datetime import datetime
import pytz
import uuid
import logging

logger = logging.getLogger(__name__)

class VTPassAPI:
    BASE_URL = 'https://sandbox.vtpass.com/api'
    
    def __init__(self):
        self.api_key = settings.VTPASS_API_KEY
        self.secret_key = settings.VTPASS_SECRET_KEY

    def generate_request_id(self):
        wat_timezone = pytz.timezone('Africa/Lagos')
        current_time = datetime.now(wat_timezone)
        date_time_part = current_time.strftime('%Y%m%d%H%M%S')
        unique_part = uuid.uuid4().hex[:8]
        return f"{date_time_part}{unique_part}"

    def make_request(self, method, endpoint, payload=None):
        headers = {
            'api-key': self.api_key,
            'secret-key': self.secret_key,
            'Content-Type': 'application/json',
        }
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=payload, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            logger.debug(f"Raw API response: {response.text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"error": str(e)}

    def get_data_variation_codes(self):
        return self.make_request('GET', 'service-variations?serviceID=mtn-data')

    def buy_data(self, phone, network, variation_code):
        payload = {
            "request_id": self.generate_request_id(),
            "serviceID": f"{network}-data",
            "billersCode": phone,
            "variation_code": variation_code,
            "phone": phone
        }
        return self.make_request('POST', 'pay', payload)

    def buy_airtime(self, phone, amount, network):
        payload = {
            "request_id": self.generate_request_id(),
            "serviceID": network,
            "amount": amount,
            "phone": phone
        }
        return self.make_request('POST', 'pay', payload)

    def query_transaction_status(self, request_id):
        return self.make_request('GET', f'requery?request_id={request_id}')
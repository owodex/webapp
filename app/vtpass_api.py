import requests
from django.conf import settings
from datetime import datetime
import pytz
import base64
import uuid
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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

    def get_data_variation_codes(self, network):
        serviceID = f"{network}-data"
        endpoint = f"service-variations?serviceID={serviceID}"
        return self.make_request('GET', endpoint)

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

    def buy_electricity(self, meter_number, operator, plan, amount, phone):
        payload = {
            "request_id": self.generate_request_id(),
            "serviceID": operator,
            "billersCode": meter_number,
            "variation_code": plan,
            "amount": str(amount),
            "phone": phone
        }
        return self.make_request('POST', 'pay', payload)
    
    def verify_smartcard(self, billersCode, serviceID):
        payload = {
            "billersCode": billersCode,
            "serviceID": serviceID,
        }
        logger.debug(f"Verifying smart card: {payload}")
        response = self.make_request('POST', 'merchant-verify', payload)
        logger.debug(f"Smart card verification response: {response}")
        return response
    
    def verify_meter(self, operator, meter_number, meter_type):
        payload = {
            "request_id": self.generate_request_id(),
            "serviceID": operator,
            "billersCode": meter_number,
            "type": meter_type
        }
        return self.make_request('POST', 'merchant-verify', payload)

    def query_transaction_status(self, request_id):
        return self.make_request('GET', f'requery?request_id={request_id}')

class VTPassCableAPI:
    def __init__(self):
        self.base_url = "https://sandbox.vtpass.com/api"
        self.api_key = settings.VTPASS_API_KEY
        self.secret_key = settings.VTPASS_SECRET_KEY
        self.session = self._get_session()

    def generate_request_id(self):
        wat_timezone = pytz.timezone('Africa/Lagos')
        current_time = datetime.now(wat_timezone)
        date_time_part = current_time.strftime('%Y%m%d%H%M%S')
        unique_part = uuid.uuid4().hex[:8]
        return f"{date_time_part}{unique_part}"
    
    def _get_session(self):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def make_request(self, method, endpoint, payload=None):
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "api-key": self.api_key,
            "secret-key": self.secret_key,
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Headers: {headers}")
        if payload:
            logger.debug(f"Payload: {payload}")

        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, params=payload, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, headers=headers, json=payload, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            logger.debug(f"Raw API response: {response.text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            logger.error(f"Response content: {e.response.content if hasattr(e, 'response') else 'No response content'}")
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 401:
                    return {"error": "Authentication failed. Please check your API credentials."}
            return {"error": str(e)}

    # ... (keep the rest of the methods unchanged)

    def get_variation_codes(self, service_id):
        url = f"{self.base_url}/service-variations"
        params = {"serviceID": service_id}
        response = requests.get(url, headers=self.auth_header, params=params)
        return response.json()

    def verify_smartcard(self, billers_code, service_id):
        url = f"{self.base_url}/merchant-verify"
        data = {
            "billersCode": billers_code,
            "serviceID": service_id
        }
        response = requests.post(url, headers=self.auth_header, json=data)
        return response.json()

    def purchase_product(self, service_id, request_id, billers_code, variation_code, amount, phone, subscription_type):
        endpoint = 'pay'
        payload = {
            'request_id': self.generate_request_id(),
            'serviceID': service_id,
            'billersCode': billers_code,
            'variation_code': variation_code,
            'amount': amount,
            'phone': phone,
            'subscription_type': subscription_type,
        }
        return self.make_request('POST', endpoint, payload)

    def renew_bouquet(self, service_id, request_id, billers_code, amount, phone):
        endpoint = 'pay'
        payload = {
            'request_id': self.generate_request_id(),
            'serviceID': service_id,
            'billersCode': billers_code,
            'amount': amount,
            'phone': phone,
            'subscription_type': 'renew',
        }
        return self.make_request('POST', endpoint, payload)

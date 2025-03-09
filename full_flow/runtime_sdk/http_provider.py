import requests
import json

class HTTPPostRequest:
    def __init__(self, url):
        self.url = url

    def post(self, params):
        try:
            encoded_params = json.dumps(params)
            response = requests.post(self.url, data=encoded_params)
            response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
            return response.text
        except requests.exceptions.RequestException as e:
            print("Error:", e)
            return None
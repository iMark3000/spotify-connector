import os
from time import sleep

import requests

class DjangoRestApi:

    BASE_URL = os.getenv('API_BASEPATH')

    def __init__(self):
        pass

    def _call_endpoint(self, url, data=None):
        headers = {
            "Content-Type": "application/json"
            }
        if data:
            response = requests.post(url, headers=headers, data=data)
        else:
            response = requests.get(url, headers=headers)

        sleep(0.25)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            data = response.json()["errors"][0]
            raise Exception(f"API Error: {data['message']}\n"
                                     f"Status Code{response.status_code}\n"
                                     f"URL: {url}")
        

    def get_recent_logs(self):
        url = f"{self.BASE_URL}listen-logs/"
        return self._call_endpoint(url)

    def create_new_log(self, data):
        url = f"{self.BASE_URL}listen-log/create"
        return self._call_endpoint(url, data=data)

    def get_track(self, track_id):
        url = f"{self.BASE_URL}track/{track_id}"
        return self._call_endpoint(url)

    def create_track(self, data):
        url = f"{self.BASE_URL}track/create"
        return self._call_endpoint(url, data=data)

    def get_album(self, album_id):
        url = f"{self.BASE_URL}album/{album_id}"
        return self._call_endpoint(url)

    def create_album(self, data):
        url = f"{self.BASE_URL}album/create/"
        return self._call_endpoint(url, data=data)

    def get_artist(self, artist_id):
        url = f"{self.BASE_URL}artist/{artist_id}"
        return self._call_endpoint(url)

    def create_artist(self, data):
        url = f"{self.BASE_URL}artist/create/"
        return self._call_endpoint(url, data=data)
    
    def get_listen_log(self, log_id):
        url = f"{self.BASE_URL}listen-log/{log_id}"
        return self._call_endpoint(url)
    
    def create_listen_log(self, data):
        url = f"{self.BASE_URL}listen-log/create"
        return self._call_endpoint(url, data=data)

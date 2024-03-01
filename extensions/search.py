import requests, os
from bs4 import BeautifulSoup

class GoogleSearch:
    def __init__(self):
        self.api_key = os.environ["CSAPIKEY"]
        self.cse_id = os.environ["CSEAPIKEY"]
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def search(self, query):
        params = {
            'q': query,
            'key': self.api_key,
            'cx': self.cse_id,
            'num':  10
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT  10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(self.base_url, params=params, headers=headers)
        results = response.json().get('items', [])
        formatted_results = []
        for result in results:
            title = result.get('title')
            #snippet = result.get('snippet')
            link = result.get('link')
            formatted_results.append((title, link))
        return formatted_results

    def get_html(self, url):
        response = requests.get(url)
        return response.text
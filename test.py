import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

CRCON_TOKEN = os.getenv('CRCON_TOKEN')
SERVER_URL = os.getenv('CRCON_URL_SERVER1') + '/api/'  # Nimm Server 1 als Beispiel, passe an

headers = {'Authorization': f'Bearer {CRCON_TOKEN}'}

def get_api_docs():
    try:
        full_url = SERVER_URL + 'get_api_documentation'
        print(f"Versuche GET: {full_url}")
        resp = requests.get(full_url, headers=headers, timeout=30, verify=False)
        resp.raise_for_status()
        data = resp.json()
        print("API-Docs erhalten!")
        with open('api_docs.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("Gespeichert als api_docs.json – öffne es, um Endpoints zu suchen (z. B. 'stats', 'kills', 'logs')")
    except Exception as e:
        print(f"Fehler: {e}")

get_api_docs()
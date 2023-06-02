import requests
import os

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def api_auth():
    access_token = requests.post("https://accounts.spotify.com/api/token",
                             headers={"Content-Type": "application/x-www-form-urlencoded"},
                             data={"grant_type": "client_credentials", "client_id": f"{CLIENT_ID}", "client_secret": f"{CLIENT_SECRET}"}).json()
    access_token = access_token['access_token']
    return {"Authorization": f"Bearer {access_token}"}
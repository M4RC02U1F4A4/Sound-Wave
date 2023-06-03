import os
import requests
import schedule
import pymongo
import time
from datetime import datetime
from auth import api_auth

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_HOST = os.getenv('MONGODB_HOST')
MONGODB_PORT = os.getenv('MONGODB_PORT')

mongo_client = pymongo.MongoClient(f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}")
db = mongo_client.soundwave
artistsDB = db['artists']
albumsDB = db['albums']
randomDB = db['random']

def update_album():
    auth = api_auth()
    for ar in artistsDB.find():

        if not albumsDB.find_one({"artist":ar['_id']}):
            first_time = 1
        else:
            first_time = 0

        album = requests.get(f"https://api.spotify.com/v1/artists/{ar['_id']}/albums?include_groups=album%2Csingle&limit=1", headers=auth).json()
        
        albums = []
        link = f"https://api.spotify.com/v1/artists/{ar['_id']}/albums?include_groups=album%2Csingle&limit=1&offset=0"
        while True:
            album = requests.get(link, headers=auth).json()
            if album['items']:
                albums.append(album['items'][0]['id'])
            if album['next']:
                link = album['next']
            else:
                break
        print(f"{ar['_id']} -> {len(albums)}")

        for aid in albums:
            mydict = albumsDB.find_one({"_id":f"{aid}"})
            if not mydict:
                print(aid)
                album = requests.get(f"https://api.spotify.com/v1/albums/{aid}", headers=auth).json()

                if album['release_date_precision'] == 'day':
                    date = datetime.strptime(album['release_date'], '%Y-%m-%d')
                if album['release_date_precision'] == 'month':
                    date = datetime.strptime(album['release_date'], '%Y-%m')
                if album['release_date_precision'] == 'year':
                    date = datetime.strptime(album['release_date'], '%Y')
                if first_time == 1:
                    viewed = 1
                else:
                    viewed = 0

                try:
                    albumsDB.insert_one({
                        "_id": f"{album['id']}",
                        "artist": f"{ar['_id']}",
                        "total_tracks": album['total_tracks'],
                        "album_type": f"{album['album_type']}",
                        "image": f"{album['images'][0]['url']}",
                        "name": f"{album['name']}",
                        "release_date": date,
                        "label": f"{album['label']}",
                        "viewed": viewed
                    })
                except:
                    pass
    try:
        randomDB.insert_one({"_id":"last_update", "time":f"{datetime.now().strftime('%d/%m/%y %H:%M')}"})
    except:
        randomDB.update_one({"_id":"last_update"},{"$set":{"time":f"{datetime.now().strftime('%d/%m/%y %H:%M')}"}})




schedule.every().day.at("00:00").do(update_album)

update_album()

while True:
    schedule.run_pending()
    time.sleep(1)
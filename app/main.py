from flask import Flask, render_template, redirect, request
import os
import pymongo
import requests
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


app = Flask(__name__)

def last_update():
    try:
        return randomDB.find_one({"_id":"last_update"})['time']
    except:
        return 'NA'

def calc_n():
    n_albums = albumsDB.count_documents({"viewed":0})
    all_n_albums = albumsDB.count_documents({})
    n_artists = artistsDB.count_documents({})
    return n_albums, all_n_albums, n_artists

@app.template_filter('beautify_time')
def beautify_time(t):
    return t.strftime("%d %b %Y")

@app.route('/')
def home():
    albums = albumsDB.find({"viewed":0}).sort('release_date', -1)
    artists = artistsDB.find({})
    n_albums, all_n_albums, n_artists = calc_n()
    return render_template('home.html',
                           n_albums=n_albums,
                           all_n_albums=all_n_albums,
                           n_artists=n_artists,
                           albums=albums,
                           artists={a["_id"]: a["name"] for a in artists},
                           active='home',
                           last_update=last_update())

@app.route('/artists')
def artists():
    artists = artistsDB.find({}).sort('name', 1)
    n_albums, all_n_albums, n_artists = calc_n()
    return render_template('artists.html',
                           n_albums=n_albums,
                           all_n_albums=all_n_albums,
                           n_artists=n_artists,
                           artists=artists,
                           active='artists',
                           last_update=last_update())

@app.route('/albums')
def albums():
    albums = albumsDB.find({}).sort('release_date', -1)
    artists = artistsDB.find({})
    n_albums, all_n_albums, n_artists = calc_n()
    return render_template('albums.html',
                           n_albums=n_albums,
                           all_n_albums=all_n_albums,
                           n_artists=n_artists,
                           albums=albums,
                           artists={a["_id"]: a["name"] for a in artists},
                           active='albums',
                           last_update=last_update())

@app.route('/manage')
def manage():
    n_albums, all_n_albums, n_artists = calc_n()
    return render_template('manage.html',
                           n_albums=n_albums,
                           all_n_albums=all_n_albums,
                           n_artists=n_artists,
                           active='manage',
                           last_update=last_update())

@app.route('/add', methods = ['POST'])
def add():
    artist = request.form['search']
    result = requests.get(f"https://api.spotify.com/v1/search?q=artist:{artist}&type=artist", headers=api_auth()).json()
    n_albums, all_n_albums, n_artists = calc_n()
    return render_template('manage.html',
                           n_albums=n_albums,
                           all_n_albums=all_n_albums,
                           n_artists=n_artists,
                           result=result,
                           active='manage',
                           last_update=last_update())

@app.route('/add/<id>', methods = ['GET'])
def add_id(id):
    result = requests.get(f"https://api.spotify.com/v1/artists/{id}", headers=api_auth()).json()
    data = {
        "_id":f"{result['id']}",
        "name":f"{result['name']}",
        "genres": result['genres'],
        "image":f"{result['images'][0]['url']}"
    }
    try:
        artistsDB.insert_one(data)
    except:
        pass

    return redirect("/")

@app.route('/read/<id>')
def read(id):
    albumsDB.update_one({"_id":f"{id}"}, {"$set": {"viewed":1}})
    return "OK", 200

@app.route('/remove', methods = ['POST'])
def remove():
    id = request.form['id']

    artistsDB.delete_one({"_id":id})
    albumsDB.delete_many({"artist":id})

    return redirect('/manage')


# app.run(debug=True, port=5001, host='0.0.0.0')
import spotipy
import requests
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
import datetime
import os

from sqlalchemy import all_

#Client Authorization using Environment Variables
client_id = os.environ.get('SPOTIPY_CLIENT_ID')
client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')

#defining scope, read-access only
scope = "user-top-read"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id = client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope = scope
    )
)

top_tracks_short = sp.current_user_top_tracks(limit = 50, offset=0, time_range="short_term")

#extracting track id's
def extract_track_ids(tracklist):
    id_list = []
    for tr in tracklist['items']:
        id_list.append(tr['id'])
    return id_list

track_ids = extract_track_ids(top_tracks_short)

#extracting track url's
    #potential program idea: have user insert url of track for a given output (waveform image)
def extract_track_urls(tracks):
    ids = []
    for t in range(len(tracks['items'])):
        ids.append(tracks['items'][t]['external_urls']['spotify'])
    return ids

track_urls = extract_track_urls(top_tracks_short)


top_ids_short = extract_track_ids(top_tracks_short)
top_urls_short = extract_track_urls(top_tracks_short)

#extracting features of track id (metadata)
def extract_track_feats(id):

    #song information
    feats = sp.track(id)
    track_name = feats['name']
    track_id = feats['id']
    track_album = feats['album']['name']
    track_artist = feats['album']['artists'][0]['name'] #only pulling the first artist listed (primary artist)
    track_popularity = feats['popularity']

    #finding related artists to the primary artist
    related_artists = sp.artist_related_artists(feats['album']['artists'][0]['id'])
    related_artists = related_artists['artists']
    related_artists_list = list()
    for i in range(len(related_artists)):
        related_artists_list.append(related_artists[i]['name'])
    
    related_artists=related_artists_list

    #finding genres
    genres = sp.artist(feats['album']['artists'][0]['id']) #genres for the primary artist of the track
    genre_list = genres['genres']

    #track url and artwork url
    spotify_url = feats['external_urls']['spotify']
    album_cover = feats['album']['images'][0]['url'] #pulls the url for the album cover

    #combining all features
    track_meta = [track_name,track_id,track_album,track_artist,track_popularity,genre_list,related_artists,spotify_url,album_cover]
    return track_meta


extract_track_feats(top_ids_short[1])
top_ids_df = pd.DataFrame(columns=['TITLE', 'TRACK_ID','ALBUM','ARTIST','POPULARITY_SCALE','GENRE','RELATED_ARTISTS','SPOTIFY_URL','ARTWORK_URL'])
for i in range(len(top_ids_short)):
    short_ids_info = extract_track_feats(top_ids_short[i])
    top_ids_df.loc[i]=short_ids_info
print(top_ids_df)






#extracting features of track url (metadata)
def extract_track_feats_url(url):
    feats = sp.track(url)
    track_id = feats['id']    
    track_name = feats['name']
    track_album = feats['album']['name']
    track_artist = feats['album']['artists'][0]['name'] #only pulling the first artist listed (primary artist)
    album_cover = feats['album']['images'][0]['url'] #pulls the url for the album cover
    track_meta_url = [track_id,track_name,track_album,track_artist,album_cover]
    return track_meta_url

for i in range(len(top_urls_short)):
    print(extract_track_feats_url(top_urls_short[i]))

extract_track_feats()
#function to loop over all track_ids from the original dictionary
all_tracks = []
for a in range(len(track_ids)):
    time.sleep(1) #sleep for 15 seconds
    full_track = extract_track_feats(track_ids[a])
    all_tracks.append(full_track)
all_tracks


#function to loop over all track_urls from the original dictionary
all_tracks_url = []
for a in range(len(track_urls)):
    time.sleep(1) #sleep for 15 seconds
    full_track_url = extract_track_feats(track_urls[a])
    all_tracks_url.append(full_track_url)
all_tracks_url

#sending to csv
df = pd.DataFrame(all_tracks).transpose()
df.head()
df = df.rename(index = {0:'title',1:'album', 2:'artist_name', 3:'spotify_url',4:'album_artwork'})
df.head()
df.to_csv('top20.csv')
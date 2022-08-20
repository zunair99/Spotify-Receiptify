from email.mime import audio
import re
from venv import create
from scipy import rand
import spotipy
import requests
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
import datetime
import os
import random

def auth():
    #Client Authorization using Environment Variables
    client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')
    #defining scope, read-access only
    scope = "user-top-read,playlist-read-collaborative,playlist-modify-public,playlist-modify-private"
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id = client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope = scope
        )
    )
    return sp

#Allow user to define the timeframe by which top tracks will be searched
def timeframe():
    print("Please type short, medium, or long to define the timeframe of your top tracks search.")
    user_range=input()
    if user_range.lower() == 'medium':
        return 'medium_term'
    if user_range.lower() == 'short':
        return 'short_term'
    if user_range.lower() == 'long':
        return 'long_term'
    else:
        print("You did not type properly. Please try again.")
        timeframe()

#extracting track id's
def extract_track_ids(tracklist):
    id_list = []
    for tr in tracklist['items']:
        id_list.append(tr['id'])
    return id_list

#extracting features of tracks
def extract_track_feats(id):
    sp = auth()
    #song information
    feats = sp.track(id)
    track_name = feats['name']
    track_id = feats['id']
    track_album = feats['album']['name']
    primary_artist = feats['album']['artists'][0]['name'] #only pulling the first artist listed (primary artist)
    primary_artist_id = feats['album']['artists'][0]['id']
    #extract list of all artists on a track, not just the primary artist
    track_artists_list = list()
    for i in range(len(feats['artists'])):
        track_artists_list.append(feats['artists'][i]['name'])
    track_artists = track_artists_list
    
    track_popularity = feats['popularity']

    #audio analysis
    audio_analysis = sp.audio_analysis(id)
    tempo = audio_analysis['track']['tempo']
    loudness = audio_analysis['track']['loudness']

    audio_features = sp.audio_features(id)
    duration = audio_features[0]['duration_ms']
    acousticness = audio_features[0]['acousticness']
    danceability = audio_features[0]['danceability']
    energy = audio_features[0]['energy']
    instrumentalness = audio_features[0]['instrumentalness']
    if instrumentalness > 0.5:
        instrumental_predict = 'Instrumental'
    else:
        instrumental_predict = 'Vocal'
    liveness = audio_features[0]['liveness']
    valence = audio_features[0]['valence']
    if valence > 0.5:
        valence_predict = 'Positive'
    else:
        valence_predict = 'Negative'
    
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

    #recs
    

    #combining all features
    track_meta = [
        track_name,
        track_id,
        track_album,
        primary_artist,
        primary_artist_id,
        track_artists,
        tempo,
        loudness,
        duration,
        acousticness,
        danceability,
        energy,
        instrumentalness,
        instrumental_predict,
        liveness,
        valence,
        valence_predict,
        track_popularity,
        genre_list,
        related_artists,
        spotify_url,
        album_cover]
    return track_meta

def track_df(track_ids):
    print("Creating dataframe based on your Spotify history...")
    top_ids_df = pd.DataFrame(columns=['TITLE', 'TRACK_ID','ALBUM','PRIMARY_ARTIST','PRIMARY_ARTIST_ID','ALL_ARTISTS','TEMPO_(BPM)','LOUDNESS_(db)','DURATION_(ms)','ACOUSTICNESS','DANCEABILITY','ENERGY','INSTRUMENTALNESS','INSTRUMENTAL_PREDICT','LIVENESS','VALENCE','VALENCE_PREDICT','POPULARITY_SCALE','GENRE','RELATED_ARTISTS','SPOTIFY_URL','ARTWORK_URL'])
    for i in range(len(track_ids)):
        short_ids_info = extract_track_feats(track_ids[i])
        top_ids_df.loc[i]=short_ids_info
    return top_ids_df



def recs_df(track_ids):
    sp = auth()
    rec_df = pd.DataFrame(columns = ['TRACK_NAME','TRACK_ID'])
    for i in range(0,len(track_ids),5):
        recs = sp.recommendations(seed_tracks=track_ids[i:i+5], limit = 20)
        rec_tracks = recs['tracks']
        for j in range(len(rec_tracks)):
            rec_track_name = rec_tracks[j]['name']
            rec_track_id = rec_tracks[j]['id']
            rec_track_info = [rec_track_name,rec_track_id]
            rec_df = rec_df.append(pd.DataFrame([rec_track_info], columns = ['TRACK_NAME','TRACK_ID']),ignore_index=True)
        rec_df = rec_df.append(rec_df,ignore_index=True)
    rec_df = rec_df.drop_duplicates().reset_index(drop=True)
    return rec_df



def rec_playlist_creator(track_ids,user_range):
    sp = auth()
    user_id = sp.me()['id']
    create_playlist = sp.user_playlist_create(
        user=user_id,
        name ="Recs Playlist Based on Top {} Songs".format(user_range),
        public=False,
        collaborative=False,
        description="""
        This playlist uses your top 50 songs from the chosen timeframe to generate a list of recommendations and inserts them into a playlist. 
        Recommendations are based on the top songs themselves, not just the artists, to encapsulate all metadata.
        """
        )
    sp.user_playlist_add_tracks(user=user_id,playlist_id=create_playlist['id'], tracks=track_ids[0:100])

def main():
    sp = auth()
    user_range = timeframe()
    top_tracks = sp.current_user_top_tracks(limit = 50, offset=0, time_range=user_range)
    track_ids = extract_track_ids(top_tracks)
    df = track_df(track_ids)
    df = df.sort_values(by=['POPULARITY_SCALE'], ascending=False)
    recom_df = recs_df(track_ids)
    print("Creating CSV with Top Songs Information...")
    df.to_csv('{}_top_songs.csv'.format(user_range))
    print("CSV Created.")
    print("Creating CSV with Song Recommendations...")
    recom_df.to_csv('{}_song_recoms.csv'.format(user_range))
    print("CSV Created.")
    print("Generating Playlist Based On Song Recommendations...")
    rec_playlist_creator(track_ids=recom_df['TRACK_ID'], user_range=user_range)
    print("Playlist with Recommended Songs Added to Your Profile.")

if __name__ == "__main__":
    main()
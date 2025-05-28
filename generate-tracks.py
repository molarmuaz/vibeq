# Gathering the tracks in my saved songs and selected playlists
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pandas import DataFrame
from time import time, sleep
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = 'http://localhost:3000/callback'

PLAYLIST_IDS = [
    '7ibppCk3o4zE9GCcCItfAV',
    '4KkUzf6D8n1uiCGk9Dffoc',
    '24nrq7z86mohBIiBESIYpm',
    '4XBWhD61NFCNZV2YS5oBv1',
    '6ax76kPK2ma5FC9FB9FWLP'
]

SCOPE = "user-library-read playlist-read-private playlist-read-collaborative user-read-private user-read-email"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=SCOPE,
    cache_path=".spotify_cache"
))

def extract_track_info(track):
    if not track or track.get('is_local', False):
        return None

    return {
        'id': track['id'],
        'name': track['name'],
        'artist': ', '.join([artist['name'] for artist in track['artists']]),
        'album': track['album']['name'],
        'release_date': track['album']['release_date'],
        'duration_ms': track['duration_ms'],
        'popularity': track['popularity'],
        'explicit': track['explicit'],
        'artist_ids': [artist['id'] for artist in track['artists']]
    }

all_tracks = {}

# Fetch saved tracks
offset = 0
while True:
    try:
        paged_tracks = sp.current_user_saved_tracks(offset=offset, limit=50)
        for item in paged_tracks['items']:
            track_info = extract_track_info(item['track'])
            if track_info and track_info['id']:
                all_tracks[track_info['id']] = track_info

        offset += 50
        if paged_tracks['next'] is None:
            break
        sleep(0.1)
    except:
        break

# Fetch playlist tracks
for playlist_id in PLAYLIST_IDS:
    try:
        offset = 0
        while True:
            try:
                paged_tracks = sp.playlist_tracks(playlist_id, offset=offset, limit=100)
                for item in paged_tracks['items']:
                    if item['track']:
                        track_info = extract_track_info(item['track'])
                        if track_info and track_info['id']:
                            all_tracks[track_info['id']] = track_info
                offset += 100
                if paged_tracks['next'] is None:
                    break
                sleep(0.1)
            except:
                break
    except:
        continue

# Get genres for all tracks
artist_cache = {}
for track in all_tracks.values():
    track_genres = set()
    for artist_id in track.get('artist_ids', []):
        if artist_id not in artist_cache:
            try:
                artist_info = sp.artist(artist_id)
                artist_cache[artist_id] = artist_info['genres']
                sleep(0.05)
            except:
                artist_cache[artist_id] = []
        track_genres.update(artist_cache[artist_id])

    track['genres'] = ', '.join(sorted(track_genres))
    del track['artist_ids']  # Remove helper field

# Create final dataset
final_tracks = list(all_tracks.values())
df = DataFrame(final_tracks)

# Reorder columns to match requested order
df = df[['id', 'name', 'artist', 'album', 'release_date', 'duration_ms', 'genres', 'popularity', 'explicit']]

filename = f'spotify_tracks_{int(time())}.csv'
df.to_csv(filename, index=False)
print(f'Saved {len(df)} tracks to {filename}')
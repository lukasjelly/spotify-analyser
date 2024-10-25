import requests
import json
import pandas as pd
import os
import tqdm

def authenticate():
    auth_url = 'https://accounts.spotify.com/api/token'
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    auth_header = requests.auth.HTTPBasicAuth(client_id, client_secret)
    payload = {
        'grant_type': 'client_credentials',
    }
    response = requests.post(auth_url, auth=auth_header, data=payload)
    response.raise_for_status()
    return response.json()['access_token']

def get_playlist_items(token, playlist_id):
    get_playlist_items_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items(track(name,href,artists(name,href)))'
    playlist_items = requests.get(get_playlist_items_url, headers={'Authorization': f'Bearer {token}'})
    playlist_items_json = playlist_items.json()
    with open('output/playlist_items.json', 'w') as f:
        f.write(json.dumps(playlist_items_json, indent=4))
    return playlist_items_json

def get_artist_genre(token, artist_href):
    artist = requests.get(artist_href, headers={'Authorization': f'Bearer {token}'})
    artist_json = artist.json()
    return artist_json['genres']

def get_track_audio_features(token, track_href):
    track_id = track_href.split('/')[-1]
    track_audio_features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
    track_audio_features = requests.get(track_audio_features_url, headers={'Authorization': f'Bearer {token}'})
    track_audio_features_json = track_audio_features.json()
    return track_audio_features_json

def process_spotify_data(playlist_id):
    token = authenticate()
    playlist_items_json = get_playlist_items(token, playlist_id)

    # Get the genres of the artists and the audio features of the tracks
    for item in tqdm.tqdm(playlist_items_json['items']):
        genres = []
        for artist in item['track']['artists']:
            artist_genre = get_artist_genre(token, artist['href'])
            genres.extend(artist_genre)
        item['track']['genres'] = genres
        track_audio_features = get_track_audio_features(token, item['track']['href'])
        item['track']['audio_features'] = track_audio_features
    with open('output/playlist_items_with_extra_info.json', 'w') as f:
        f.write(json.dumps(playlist_items_json, indent=4))

    # create dataframe for each track
    track_data = []
    for item in tqdm.tqdm(playlist_items_json['items']):
        track = item['track']
        track_data.append({
            'name': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'genres': ', '.join(track['genres']),
            'danceability': track['audio_features']['danceability'],
            'energy': track['audio_features']['energy'],
            'key': track['audio_features']['key'],
            'loudness': track['audio_features']['loudness'],
            'mode': track['audio_features']['mode'],
            'speechiness': track['audio_features']['speechiness'],
            'acousticness': track['audio_features']['acousticness'],
            'instrumentalness': track['audio_features']['instrumentalness'],
            'liveness': track['audio_features']['liveness'],
            'valence': track['audio_features']['valence'],
            'tempo': track['audio_features']['tempo'],
            'duration_ms': track['audio_features']['duration_ms'],
            'time_signature': track['audio_features']['time_signature'],
        })
    df = pd.DataFrame(track_data)
    df.to_excel('output/playlist_tracks.xlsx', index=False)
    with open('output/playlist_tracks.json', 'w') as f:
        f.write(json.dumps(playlist_items_json, indent=4))

if __name__ == '__main__':
    playlist_ids = ['4e2Mmg89uWPQbNK6JG3v41','25io3HnI7g9NfkEbI80zSj']
    playlist_id = playlist_ids[0]

    process_spotify_data(playlist_id)
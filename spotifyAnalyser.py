import requests
import json
import pandas as pd
import os
import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def authenticate_client_credentials():
    scope = 'playlist-read-private'
    auth_url = 'https://accounts.spotify.com/api/token'
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    auth_header = requests.auth.HTTPBasicAuth(client_id, client_secret)
    payload = {
        'grant_type': 'client_credentials',
        'scope': scope
    }
    response = requests.post(auth_url, auth=auth_header, data=payload)
    response.raise_for_status()
    return response.json()['access_token']

def get_playlist_items(token, playlist_id):
    offset=0
    limit=100
    playlist_items = []
    while True:
        get_playlist_items_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items(track(external_urls,name,href,artists(name,href)))&offset={offset}&limit={limit}'
        current_playlist_items = requests.get(get_playlist_items_url, headers={'Authorization': f'Bearer {token}'})
        current_playlist_items_json = current_playlist_items.json()
        if len(current_playlist_items_json['items']) == 0:
            break
        playlist_items.extend(current_playlist_items_json['items'])
        offset += limit
    playlist_items_json = {'items': playlist_items}
    with open('output/playlist_items.json', 'w') as f:
        f.write(json.dumps(playlist_items_json, indent=4))
    logging.info(f'found {len(playlist_items_json["items"])} tracks in playlist id {playlist_id}')
    
    #return {'items': playlist_items[:2]}
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

def get_track_data(playlist_id):
    token = authenticate_client_credentials()
    playlist_items_json = get_playlist_items(token, playlist_id)

    # Get the genres of the artists and the audio features of the tracks
    for item in tqdm.tqdm(playlist_items_json['items'], desc='Getting artist genres and track audio features'):
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
    for item in tqdm.tqdm(playlist_items_json['items'], desc='Creating dataframe'):
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
            'link': track['external_urls']['spotify'],
        })
    df = pd.DataFrame(track_data)
    df.to_excel('output/playlist_tracks.xlsx', index=False, engine='xlsxwriter')
    with open('output/playlist_tracks.json', 'w') as f:
        f.write(json.dumps(playlist_items_json, indent=4))

def add_tracks_to_playlist():
    playlist_wedding_heavy = os.getenv('PLAYLIST_WEDDING_HEAVY')
    playlist_wedding_medium = os.getenv('PLAYLIST_WEDDING_MEDIUM')
    playlist_wedding_light = os.getenv('PLAYLIST_WEDDING_LIGHT')
    token = os.getenv('SPOTIFY_ACCESS_TOKEN')

    # clear the playlists
    for playlist_id in [playlist_wedding_heavy, playlist_wedding_medium, playlist_wedding_light]:
        get_playlist_items_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        current_playlist_items = requests.get(get_playlist_items_url, headers={'Authorization': f'Bearer {token}'})
        current_playlist_items_json = current_playlist_items.json()
        for item in current_playlist_items_json['items']:
            track_id = item['track']['id']
            remove_track_from_playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?'
            remove_track_payload = {
                "tracks": [
                    {
                        "uri": f"spotify:track:{track_id}"
                    }
                ]
            }
            response = requests.delete(
                remove_track_from_playlist_url,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                data=json.dumps(remove_track_payload)
            )
            response.raise_for_status()
            
    with open('output/playlist_items_with_extra_info.json', 'r') as f:
        playlist_items_json = json.load(f)
    playlist_items = playlist_items_json['items']

    for track in tqdm.tqdm(playlist_items, desc='Adding tracks to playlists according to energy'):
        track_energy = track['track']['audio_features']['energy']
        if track_energy >= 0.666:
            playlist_id = playlist_wedding_heavy
        elif track_energy > 0.333 and track_energy < 0.666:
            playlist_id = playlist_wedding_medium
        elif track_energy <= 0.333:
            playlist_id = playlist_wedding_light
        track_id = track['track']['href'].split('/')[-1]
        add_track_to_playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?uris=spotify%3Atrack%3A{track_id}'
        response = requests.post(add_track_to_playlist_url, headers={'Authorization': f'Bearer {token}'})
        response.raise_for_status()

def get_all_genres():
    with open('output/playlist_tracks.json', 'r') as f:
        playlist_tracks = json.load(f)
    genres = set()
    for track in tqdm.tqdm(playlist_tracks['items'], desc='Getting all genres'):
        for genre in track['track']['genres']:
            genres.add(genre)
    with open('output/genres.json', 'w') as f:
        f.write(json.dumps(list(genres), indent=4))


if __name__ == '__main__':
    playlist_id = os.getenv('PLAYLIST_WEDDING_ALL')

    #get_track_data(playlist_id)
    #add_tracks_to_playlist()
    #get_all_genres()
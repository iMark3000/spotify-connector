from datetime import datetime
import json
import logging
from time import mktime
import traceback
from zoneinfo import ZoneInfo
import pprint

from django_rest_api import DjangoRestApi

from job_notifications import create_notifications
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Todo: Create Mailgun account
# Todo: Set up logging
notifications = create_notifications("Spotify Connector", "mailgun", logs='app.log')


def listen_log_exists_check(time_stmp_str: str, drf: DjangoRestApi) -> bool:
    log = drf.get_listen_log(time_stmp_str)
    if log is not None:
        print(log)
        return True
    else:
        return False


def artist_exists_check(artist_id: str, drf: DjangoRestApi) -> bool:
    artist = drf.get_artist(artist_id)
    if artist is not None:
        return True
    else:
        return False


def album_exists_check(album_id: str, drf: DjangoRestApi) -> bool:
    album = drf.get_album(album_id)
    if album is not None:
        return True
    else:
        return False


def track_exists_check(track_id: str, drf: DjangoRestApi) -> bool:
    track = drf.get_track(track_id)
    if track is not None:
        return True
    else:
        return False


def posix_times_stamp_key(date_str) -> str:
    date_obj = datetime.fromisoformat(date_str)
    local_tz = ZoneInfo("America/Los_Angeles")
    new_date_obj = date_obj.astimezone(local_tz)
    time_stamp = str(new_date_obj.timestamp())
    return time_stamp.split('.')[0]


def album_response_filter(response: dict) -> dict:
    data = {}
    data['album_id'] = response['id']
    data['name'] = response['name']
    data['year'] = response['release_date']
    data['artists'] = [artist['id'] for artist in response['artists']] 
    data['album_type'] = response['album_type']
    parse_images(response['images'], data)
    pprint.pprint(data)
    return data


def artist_response_filter(response: dict) -> dict:
    data = {}
    data['artist_id'] = response['id']
    data['name'] = response['name']
    data['genres'] = response['genres']
    parse_images(response['images'], data)
    pprint.pprint(data)
    return data


def track_response_filter(response: dict) -> dict:
    data = {}
    data['track_id'] = response['id']
    data['name'] = response['name']
    data['duration'] = response['duration_ms']
    data['artists'] = [artist['id'] for artist in response['artists']]
    data['album'] = [response['album']['id']]
    pprint.pprint(data)
    return data


def parse_images(images: list, data: dict) -> None:
    for image in images:
        if image['height'] == 64:
            data['image_small'] = image['url']
        elif image['height'] == 300:
            data['image_medium'] = image['url']
        elif image['height'] == 640:
            data['image_large'] = image['url']


def genre_conversion(genres: list, drf: DjangoRestApi) -> list:
    genre_pk = []
    for genre in genres:
        genre_data = drf.get_genre_details(genre)
        if genre_data:
            genre_pk.append(genre_data['id'])
        else:
            payload = {"name": genre}
            response = drf.create_genre(payload)
            genre_pk.append(response['id'])
    return genre_pk


def create_artists(artists: list, sp, drf):
    for artist in artists:
        if not artist_exists_check(artist, drf):
            artist_data = sp.artist(artist)
            print('Creating Artist')
            artist_data = artist_response_filter(artist_data)
            artist_data['genres'] = genre_conversion(artist_data['genres'], drf)
            drf.create_artist(artist_data)


def create_album(album: str, sp, drf):
    if not album_exists_check(album, drf):
        album_data = sp.album(album)
        print('Creating Album')
        album_data = album_response_filter(album_data)
        # create_artists(album_data['artists'], sp, drf)
        drf.create_album(album_data)


def add_a_track(track, sp, drf):
    artists = [artist['id'] for artist in track['artists']]
    create_artists(artists, sp, drf)
    album = track['album']['id']
    create_album(album, sp, drf)
    print('Creating Track')
    track_data = track_response_filter(track)
    drf.create_track(track_data)


def create_listen_log(track, drf):
    payload = {}
    payload['posix_tmstmp'] = track['posix_tmstmp']
    payload['played_at_datetime'] = track['played_at']
    payload['track_played'] = track['track']['id']
    print("Creating Listen Log")
    pprint.pprint(payload)
    drf.create_listen_log(payload)


def main():
        drf = DjangoRestApi()

        scope = ["user-library-read", "user-read-recently-played"]
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        recently_played = sp.current_user_recently_played(limit=50)
        recently_played = recently_played['items']
        for item in recently_played:
            t = item["track"]["name"]
            a = item["track"]["artists"][0]["name"]
            p = item["played_at"]
            print(f"{t} by {a} played at {p}")
            item['posix_tmstmp'] = posix_times_stamp_key(item['played_at'])
        recently_played_filtered = [track for track in recently_played if listen_log_exists_check(track['posix_tmstmp'], drf) is False]

        for track in recently_played_filtered:
            print(f'Working on {track["track"]["name"]}')
            if track_exists_check(track['track']['id'], drf) is False:
                print(f'{track["track"]["name"]} does not exist. Attempting to create')
                add_a_track(track['track'], sp, drf)
            else:
                print(f'{track["track"]["name"]} exists')
            create_listen_log(track, drf)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        stack_trace = traceback.format_exc()
        print(stack_trace)

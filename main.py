import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import fastapi
from fastapi.middleware.cors import CORSMiddleware

app = fastapi.FastAPI()

origins=['http://localhost:3000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope="playlist-modify-private",
        redirect_uri='https://example.com',
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        show_dialog=True,
        cache_path="token.txt"
    )
)


def create_playlist(year, month, day):
    response = requests.get(f'https://www.billboard.com/charts/hot-100/{year}-{month}-{day}/#')
    billboard_data = response.text
    soup = BeautifulSoup(billboard_data, "html.parser")

    songs_data = soup.select(".o-chart-results-list__item #title-of-a-story")
    artists_data = soup.select(".o-chart-results-list__item #title-of-a-story ~ span")

    songs = [song.getText().strip() for song in songs_data]
    artists = [artist.getText().split("Featuring")[0].split(' X ')[0].split("&")[0].split(' x ')[0].split(':')[0].split('Presents')[0].split('ft.')[0].split('ft')[0].split('feat')[0].strip('"').strip() for artist in artists_data]

    user_id = sp.current_user()["id"]

    song_uris = []
    aux = 0
    for song in songs:
        result = sp.search(q=f"track:{song} artist:{artists[aux]}", type="track")
        aux += 1
        try:
            uri = result["tracks"]["items"][0]["uri"]
            song_uris.append(uri)
            # print(f"{song} found")
        except IndexError:
            print(f"{song} doesn't exist in Spotify. Skipped.")


    playlist = sp.user_playlist_create(user_id, name=f"{year}.{month}.{day}", public=False, description=f"Playlist containing the Billboard Hot 100 for the week of {year}.{month}.{day}")

    sp.playlist_add_items(playlist_id=playlist["id"], items=song_uris)

    return playlist['id'].strip()


@app.get("/createPlaylist/{year:month:day}")
async def get_playlist_id(year:str, month:str, day:str):
    return create_playlist(year, month, day)

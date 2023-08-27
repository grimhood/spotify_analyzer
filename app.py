import dash
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import dash_bootstrap_components as dbc

#Load environment variables
load_dotenv()

def track_card_container(range):
    dict_range = {
        'short_term': 'Last 4 Weeks',
        'medium_term': 'Last 6 Months',
        'long_term': ''
    }

    title = html.H4(f"Top Tracks: {dict_range[range]}", className="card-title")

    container = html.Div(
        [
            dbc.Row([dbc.Col([title])]),
            dbc.Row([]),
            dbc.Row([]),
            dbc.Row([]),
        ],
    )

    return container

def track_card_item(index, item):
    image = dbc.CardImg(src=item['album']['images'][0]['url'], top=True)
    track_name = f'{index+1}: {item["name"]}'
    artist_name = item["artists"][0]["name"]
    track_id = f'Spotify ID: {item["id"]}'
    title = html.P(track_name, className="card-title")
    subtitle = html.P(artist_name, className="card-subtitle")
    #track_id = html.P(track_id, className="card-text")
    #snippet = html.Audio(src=item['preview_url'], controls=True, style={'width': '100%'})

    container_item = html.Div(
        [
            dbc.Row([dbc.Col([image])]),
            dbc.Row([dbc.Col([title])]),
            dbc.Row([dbc.Col([subtitle])]),
        ],
    )
    
    return container_item

#Top tracks
def top_tracks_card(range):
    scope = 'user-top-read'
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    dict_ranges = {
        'Last 4 Weeks' :    'short_term',
        'Last 6 Months':    'medium_term',
        'All Time':         'long_term'
    }

    results = sp.current_user_top_tracks(time_range=dict_ranges[range], limit=12)
    card_container = track_card_container(dict_ranges[range])
    list_item_cards = [track_card_item(i, item) for i, item in enumerate(results['items'])]
    row1 = [dbc.Col([list_item_cards[0]]), dbc.Col([list_item_cards[1]]), dbc.Col([list_item_cards[2]]), dbc.Col([list_item_cards[3]])]
    row2 = [dbc.Col([list_item_cards[4]]), dbc.Col([list_item_cards[5]]), dbc.Col([list_item_cards[6]]), dbc.Col([list_item_cards[7]])]
    row3 = [dbc.Col([list_item_cards[8]]), dbc.Col([list_item_cards[9]]), dbc.Col([list_item_cards[10]]), dbc.Col([list_item_cards[11]])]
    card_container.children[1].children = row1
    card_container.children[2].children = row2
    card_container.children[3].children = row3
    return card_container

#App Layout Components
header = html.H4(
    "Spotify Usage Analyzer", className="bg-primary text-white p-2 mb-2 text-center"
)
tracks_range_radio = dcc.RadioItems(['Last 4 Weeks', 'Last 6 Months','All Time'], 'Last 4 Weeks', inline=True, id='tracks-range-radio')

card_overview = html.Div([], id='top-tracks-card')
card_patterns = []
card_genres = []
card_playlists = []
card_history = []
card_mood = []
#card_pinkf = album_card(pinkf_uri)

#Initialize App
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


#Callbacks
@app.callback(
    Output('top-tracks-card', 'children'),
    Input('tracks-range-radio', 'value'),
)
def top_tracks(value):
    return top_tracks_card(value)

#App Layout
app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col([header])),
        dbc.Row(dbc.Col([tracks_range_radio], width=3)),
        dbc.Row([dbc.Col([card_overview], width=3), dbc.Col([card_patterns], width=5), dbc.Col([card_genres], width=4)]),
        dbc.Row([dbc.Col([card_playlists], width=3), dbc.Col([card_history], width=5), dbc.Col([card_mood], width=4)]),
    ],
    className="dbc",
    fluid=True,
)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
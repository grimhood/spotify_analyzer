import dash
from dash import Dash, html, dcc, Output, Input, State, callback, ClientsideFunction
from dash.exceptions import PreventUpdate
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objs as go
from flask import Flask
from flask_caching import Cache
import pathlib
import json

#Initialize App
dbc_css = 'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css'
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = 'Spotify Dashboard'

#Load environment variables
load_dotenv()

#Spotify data
spotify_df = pd.read_csv('src\spotify_data\enriched_data\streaming_history.csv')

def top_track_div(item):
    image = dbc.CardImg(src=item['album']['images'][0]['url'], top=True)
    track_name = item['name']
    artist_name = item['artists'][0]['name']
    track_id = f'Spotify ID: {item["id"]}'
    title = html.P(track_name, className='text-top-track')
    subtitle = html.P(artist_name, className='subtitle-top-track')

    container_item = html.Div(
        [
            dbc.Row([dbc.Col([image])]),
            dbc.Row([dbc.Col([title])]),
            dbc.Row([dbc.Col([subtitle])]),
        ],
        className='track-card',
    )
    
    return container_item

def recent_track_div(item):
    image = dbc.CardImg(src=item['track']['album']['images'][0]['url'], top=True)
    track_name = item['track']['name']
    artist_name = item['track']['artists'][0]['name']
    title = html.P(track_name, className='text-top-track text-recent-track')
    subtitle = html.P(artist_name, className='subtitle-top-track')

    container_item = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col([image], className='image-recent-track', width=3),
                    dbc.Col(
                        [
                            dbc.Row([dbc.Col([title])]),
                            dbc.Row([dbc.Col([subtitle])]),
                        ],
                        width=8)
                ]
            ),
        ],
        className='track-card recent-track-card',
    )

    return container_item

def top_tracks(range):
    top_scope = 'user-top-read'
    sp_auth = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=top_scope))
    dict_ranges = {
        'Last 4 Weeks' :    'short_term',
        'Last 6 Months':    'medium_term',
        'All Time':         'long_term'
    }

    results = sp_auth.current_user_top_tracks(time_range=dict_ranges[range], limit=12)
    title = html.H4(f'Top Tracks: {range}', className='section-header')

    container = html.Div(
        [
            dbc.Row([dbc.Col([title])]),
            dbc.Row([]),
            dbc.Row([]),
            dbc.Row([]),
        ],
        className='top-tracks-card-container',
    )

    items = [top_track_div(item) for item in results['items']]
    def row(items):
        return dbc.Row([dbc.Col([i]) for i in items])
    row1 = row(items[:4])
    row2 = row(items[4:8])
    row3 = row(items[8:12])
    container.children[1].children = row1
    container.children[2].children = row2
    container.children[3].children = row3
    return container

def recent_tracks():
    recent_scope = 'user-read-recently-played'
    sp_auth = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=recent_scope))
    results = sp_auth.current_user_recently_played(limit=7)
    items = [recent_track_div(item) for item in results['items']]
    title = html.H4(f'Recently played', className='section-header')
    children = [dbc.Row([dbc.Col([items[i]])]) for i in (range(len(items)))]
    children.insert(0, dbc.Row([dbc.Col([title])]))
    container = html.Div(
        children,
        className='top-tracks-card-container',
    )
    return container

def user_stats():
    df = spotify_df.copy()
    total_time = df['msPlayed'].sum()
    total_time_minutes = round(total_time / 60000)
    total_time_hours = round(total_time / 3600000)
    total_time_days = round(total_time_hours / 24)
    total_tracks = df.shape[0]
    total_artists = df['artistName'].nunique()
    df['trackLength'] = df['msPlayed'] / 60000
    avg_track_length = round(df['trackLength'].mean(), 2)


    dict_stats = {
        'Minutes listened' : total_time_minutes,
        'Days listened' : total_time_days,
        'Tracks' : total_tracks,
        'Artists' : total_artists,
        'Average track length' : f'{avg_track_length} min'
    }

    stats = dbc.Container(
        [
            dbc.Stack(
                [
                    dbc.Row(
                        [
                            html.P(k, className='title-stats'),
                            html.P(v, className='value-stats')
                        ],
                        className='stat-card',
                        justify='center'
                    )
                    for k,v in dict_stats.items()
                ],
                gap=4
            )
        ],
    )
    return stats

def df_to_heatmap(df):
    #Create the heatmap graph
    fig = px.imshow(
        df,
        labels=dict(x='Time', y='Day', color='Number of songs listened', title='Listening activity heatmap'),
        color_continuous_scale='inferno',
        height=400)
    fig.update_layout(
        yaxis = dict(
            tickmode = 'array',
            tickvals = [*range(0, 7, 1)],
            ticktext = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
            zeroline = False,
            showline = False,
            showgrid = False,
            ticksuffix="   "
        ),
        xaxis = dict(
            tickmode = 'array',
            tickvals = [*range(0, 24, 1)],
            ticktext = ['12AM','1AM','2AM','3AM','4AM','5AM','6AM','7AM','8AM','9AM',
                        '10AM','11AM','12PM','1PM','2PM','3PM','4PM','5PM','6PM','7PM',
                        '8PM','9PM','10PM','11PM'],
            zeroline = False,
            showline = False,
            showgrid = False
        ),
        font_color='white',
        title_font_color='white',
        paper_bgcolor='rgb(39,38,38)',
        plot_bgcolor='rgb(0,0,0)',
        margin=dict(t=20,b=20,l=20,r=20),
    )
    return fig

def heatmap_yearly():
    #Create a matrix dataframe with the number of tracks played per hour (rows) and day of the week (columns)
    df = spotify_df.copy()
    df['endTime'] = pd.to_datetime(df['endTime'], format='%Y-%m-%d %H:%M')
    df['hour'] = df['endTime'].dt.hour
    df['day'] = df['endTime'].dt.dayofweek
    heatmap = df.groupby(['day', 'hour']).count()
    heatmap.reset_index(inplace=True)
    heatmap = heatmap[['day', 'hour', 'trackName']]
    heatmap.rename(columns={'trackName': 'Number of songs listened'}, inplace=True)
    heatmap.sort_values(by=['day', 'hour'], inplace=True)
    heatmap.reset_index(inplace=True)
    heatmap.drop(columns='index', inplace=True)
    heatmap = heatmap.pivot(index='day', columns='hour', values='Number of songs listened')
    return heatmap

def heatmap_weekly():
    df = spotify_df.copy()
    df['endTime'] = pd.to_datetime(df['endTime'], format='%Y-%m-%d %H:%M')
    df['hour'] = df['endTime'].dt.hour
    df['day'] = df['endTime'].dt.dayofweek
    df['week'] = df['endTime'].dt.isocalendar().week
    heatmap = df.groupby(['week', 'day', 'hour']).count()
    heatmap.reset_index(inplace=True)
    heatmap = heatmap[['week', 'day', 'hour', 'trackName']]
    heatmap.rename(columns={'trackName': 'Number of songs listened'}, inplace=True)
    heatmap.sort_values(by=['week', 'day', 'hour'], inplace=True)
    heatmap.reset_index(inplace=True)
    heatmap.drop(columns='index', inplace=True)
    heatmap = heatmap.fillna(0)
    #Get a list of week values from the dataframe
    week_list = heatmap['week'].astype(str).unique().tolist()

    def pivot_df(df):
        df = df.copy()
        df = df.pivot(index='day', columns='hour', values='Number of songs listened')
        df.reset_index(inplace=True)
        return df

    #Create a list of dataframes, one for each week of the year
    heatmap_list = [pivot_df(heatmap[heatmap['week'] == week]) for week in heatmap['week'].unique()]
    #Create a list containing heatmap figures for each week of the year
    json_list = [df.to_json(date_format='iso', orient='split') for df in heatmap_list]
    return json_list


#App Layout Components
header = html.P('Spotify Dashboard', className='app-header')
tracks_range_radio = html.Div(
    [
        dcc.RadioItems(['Last 4 Weeks', 'Last 6 Months','All Time'],
        'Last 4 Weeks',
        id='tracks-range-radio',
        className='horizontal-radio')
    ],
    className='radio-container',
)

profile_image = html.Div(html.Img(src='assets/profile.jpg', className='profile-image'), className='profile-image-container')
card_top_tracks = html.Div([], id='top-tracks')
card_recent_tracks = html.Div([recent_tracks()], id='recent-tracks')
card_user_stats = html.Div(user_stats())

navbar = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink('Overview', active= 'exact', href='/overview/')),
        dbc.NavItem(dbc.NavLink('Listening Patterns', active= 'exact', href='/listening_patterns/')),
        dbc.NavItem(dbc.NavLink('Favorite Genres', active= 'exact', href='/favorite_genres/')),
        dbc.NavItem(dbc.NavLink('Top Tracks & Artists', active= 'exact', href='/top/')),
    ],
    vertical='lg',
    pills=True,
    fill=True,
)
navbar_container = dbc.Col([navbar], width=1, className='column-container')

content = dbc.Container(
    children=[
            dbc.Row(
                [
                    dbc.Col([header])
                ],
                justify='center'
            ),
            dbc.Row(
                [
                    navbar_container
                ],
                id='page-content',
                justify='center', 
            ),
    ],
    className='dbc',
    fluid=True,
)

dcc.Location(id='url'),
heatmap_buttons = html.Div(
    [
        dbc.Button('Prev', n_clicks=0, id='button-prev', className='mr-1', size='sm', ),
        dbc.Button('Next', n_clicks=0, id='button-next', className='mr-1', size='sm'),
    ],
    className='d-grid gap-2 d-md-flex justify-content-md-start',
)

#heatmaps_weekly = heatmaps_weekly()

#App Layout
app.layout = dbc.Container(
    [
        html.Div(id='dummy'),
        dcc.Location(id='url'),
        dcc.Store(id='stored-window-size'),
        dcc.Store(id='stored-heatmap-yearly'),
        dcc.Store(id='stored-heatmap-weekly'),
        dcc.Store(id='current-state-heatmap'),
        content
    ],
    className='dbc',
    fluid=True,
    id='main-container',
)

#Client-Side callbacks
#––––––––––––––––––––––––––––––––––––––––––––––––––
#Sets zoom of the layout depending on the browser window size
app.clientside_callback(
    """
    function(href) {
        var window_height = window.innerHeight;
        return [window_height]
    }
    """,
    Output('stored-window-size','data'),
    Input('url', 'href'),
)


#Callbacks
@app.callback(
    Output('stored-heatmap-yearly', 'data'),
    Input('dummy', 'children'),
)
def store_heatmap_data_yearly_callback(dummy):
    df = heatmap_yearly().to_json(date_format='iso', orient='split')
    return df

@app.callback(
    Output('stored-heatmap-weekly', 'data'),
    Input('dummy', 'children'),
)
def store_heatmap_data_weekly_callback(dummy):
    df = heatmap_weekly()
    return df

@app.callback(
    Output('top-tracks', 'children'),
    Input('tracks-range-radio', 'value'),
)
def top_tracks_callback(value):
    if value:
        return top_tracks(value)
    else:
        raise PreventUpdate
    
@app.callback(
    Output('current-state-heatmap', 'data'),
    Output('listening-patterns', 'children'),
    Input('stored-window-size', 'data'),
    Input('stored-heatmap-yearly', 'data'),
    Input('stored-heatmap-weekly', 'data'),
    Input('button-next', 'n_clicks'),
    Input('button-prev', 'n_clicks'),
    State('current-state-heatmap', 'data'),
)
def listening_patterns_callback(window_size, heatmap_yearly_json, heatmap_weekly_json, clicks_next, clicks_prev, current_state_heatmap):
    title1=html.H4('Yearly listening patterns', className='section-header section-header-heatmap')
    height = window_size[0] *0.35
    fig_yearly = pd.read_json(heatmap_yearly_json, orient='split').copy()
    fig_yearly = df_to_heatmap(fig_yearly)
    fig_yearly.update_layout(height=height)
    heatmaps_weekly = [pd.read_json(json, orient='split').copy() for json in heatmap_weekly_json]
    figs_weekly = [df_to_heatmap(df) for df in heatmaps_weekly]

    for fig in figs_weekly:
        fig.update_layout(height=height)
    if current_state_heatmap is None:
        week = 0
        clicks_next = 0
        clicks_prev = 0
    else:
        if clicks_next > current_state_heatmap['clicks_next']:
            week = current_state_heatmap['current_week'] + 1
            clicks_next = clicks_next
        
        if clicks_prev > current_state_heatmap['clicks_prev']:
            week = current_state_heatmap['current_week'] - 1
            clicks_prev = clicks_prev  

    listening_patterns_yearly = html.Div([dcc.Graph(figure=fig_yearly)], className='heatmap')
    listening_patterns_weekly = html.Div([dcc.Graph(figure=figs_weekly[week])], className='heatmap')
    title2=html.H4(f'Weekly listening patterns (Week {week})', className='section-header section-header-heatmap')

    return [
        {
            'current_week': week,
            'clicks_next': clicks_next,
            'clicks_prev': clicks_prev,
        },
        [
            title1,
            listening_patterns_yearly,
            title2,
            listening_patterns_weekly
        ]    
    ]
    
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
)
def render_page_content(pathname):
    landing_pathnames = ['/','/overview/']
    if pathname in landing_pathnames:
        return [
            navbar_container,
            dbc.Col([card_recent_tracks], width=2, className='column-container'),
            dbc.Col([card_top_tracks, tracks_range_radio], width=4, className='column-container'),
            dbc.Col([profile_image, card_user_stats], width=2, className='column-container')
        ]
    elif pathname == '/listening_patterns/':
        return [
            navbar_container,
            dbc.Col([html.Div(id='listening-patterns'), heatmap_buttons], width=8, className='column-container')
        ]
    elif pathname == '/favorite_genres/':
        return [
            navbar_container,
            dbc.Col([], width=8, className='column-container')
        ]
    elif pathname == '/top/':
        return [
            navbar_container,
            dbc.Col([], width=8, className='column-container')
        ]
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1('404: Not found', className='text-danger'),
            html.Hr(),
            html.P(f'The pathname {pathname} was not recognised...'),
        ]
    )


if __name__ == '__main__':
    app.run(debug=True)
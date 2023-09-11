import pandas as pd
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
import plotly.express as px

load_dotenv()
sp_auth = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

audio_features = [
    'danceability',
    'energy',
    'key',
    'loudness',
    'mode',
    'speechiness',
    'acousticness',
    'instrumentalness',
    'liveness',
    'valence',
    'tempo',
    'time_signature'
]

#Function to read a json file using pandas
def read_json(file_path):
    df = pd.read_json(file_path)
    return df

#Function to stack together two dataframes with the same columns
def stack_dfs(df1, df2):
    df = pd.concat([df1, df2])
    return df

#Function to stack together n number of dataframes with the same columns
def stack_n_dfs(df_list):
    df = pd.concat(df_list)
    return df

#Function to get removed duplicates from a dataframe based on two column names
def remove_duplicates(df, col1, col2):
    df.drop_duplicates(subset=[col1, col2], inplace=True)
    df.reset_index(inplace=True)
    return df

#Function to get the track ID from Spotofy API, given the track name and artist name
def get_track_id(track_name, artist_name, sp_auth):
    try:
        track_id = sp_auth.search(q=f'track:{track_name} artist:{artist_name}', type='track')['tracks']['items'][0]['id']
        return track_id
    except:
        return 'ID not found'

#Function to create a new column in a dataframe with the track ID
def add_track_id(csv_filename, sp_auth):
    df = pd.read_csv(csv_filename)
    df['trackID'] = df.apply(lambda x: get_track_id(x['trackName'], x['artistName'], sp_auth), axis=1)
    df.to_csv(csv_filename, index=False)
    return df

#Function to get the audio features of a track from Spotify API, given the track ID
def get_audio_features(track_id, sp_auth):
    try:
        audio_features = sp_auth.audio_features(track_id)[0]
        return audio_features
    except:
        return 'Audio features not found'

#Function to create new columns in a dataframe with the audio features of a track (one column for each feature)
def add_audio_features(csv_filename, sp_auth):
    df = pd.read_csv(csv_filename)
    df['audioFeatures'] = df.apply(lambda x: get_audio_features(x['trackID'], sp_auth), axis=1)
    for feature in audio_features:
        df[feature] = df.apply(lambda x: x['audioFeatures'][feature] if x['audioFeatures']not in ['Audio features not found', None] else '', axis=1)
    df.drop(columns=['audioFeatures'], inplace=True)
    df.to_csv(csv_filename, index=False)
    return df

#function to split a dataframe into smaller dataframes and save them as csv files
def split_df(df, n):
    df_list = [df[i:i+n] for i in range(0,df.shape[0],n)]
    for i in range(len(df_list)):
        df_list[i].to_csv(f'spotify_data/enriched_data/df_{i}.csv', index=False)
    return df_list

#Function to get the top 10 artists from a dataframe
def top_artists(df):
    top_artists = df.groupby('artistName').count().sort_values(by='endTime', ascending=False).head(10)
    return top_artists

#Function to get the top 10 tracks from a dataframe
def top_tracks(df):
    top_tracks = df.groupby(['artistName', 'trackName']).count().sort_values(by='endTime', ascending=False).head(10)
    top_tracks.rename(columns={'endTime': 'PlayCount'}, inplace=True)
    top_tracks.drop(columns='msPlayed', inplace=True)
    top_tracks.reset_index(inplace=True)
    return top_tracks

#Function to get the number of times a track has been played
def track_count(df, track_name):
    track_count = df.groupby('trackName').size()[track_name]
    return track_count

#Function to find duplicated rows in a dataframe
def find_duplicates(df):
    duplicates = df[df.duplicated()]
    return duplicates

#Function to find the rows that have a specific value in two columns
def find_rows(df, col1, col2, value1, value2):
    rows = df[(df[col1] == value1) & (df[col2] == value2)]
    return rows.index.tolist()

# #Create streaming_history csv file
# streaming1 = read_json('spotify_data/StreamingHistory0.json')
# streming2 = read_json('spotify_data/StreamingHistory1.json')
# streaming_df = stack_dfs(streaming1, streming2)
# streaming_df.to_csv('spotify_data/streaming_history.csv', index=False)

# #Create a file with no duplicates from streaming_history.csv
# no_duplicates_df = remove_duplicates(streaming_df, 'trackName', 'artistName')
# #Split the dataframe into smaller dataframes (104) and save them as csv files
# split_df(no_duplicates_df, 50)

# #Apply add_audio_features function to all dataframes in the enriched_data folder
# for i in range(0,105):
#     import time
#     #wait 1 minute every 5 files
#     if i % 5 == 0:
#         print('Waiting 1 minute...')
#         time.sleep(40)
#         print(f'Processing df_{i}.csv')
#         add_audio_features(f'spotify_data/enriched_data/df_{i}.csv', sp_auth)
#     else:
#         print(f'Processing df_{i}.csv')
#         time.sleep(5)
#         add_audio_features(f'spotify_data/enriched_data/df_{i}.csv', sp_auth)

# #Apply add_track_id function to all dataframes in the enriched_data folder
# for i in range(0,105):
#     import time
#     #wait 1 minute every 5 files
#     if i % 5 == 0:
#         print('Waiting 1 minute...')
#         time.sleep(40)
#         print(f'Processing df_{i}.csv')
#         add_track_id(f'spotify_data/enriched_data/df_{i}.csv', sp_auth)
#     else:
#         print(f'Processing df_{i}.csv')
#         time.sleep(5)
#         add_track_id(f'spotify_data/enriched_data/df_{i}.csv', sp_auth)

# #Create track_dictionary file by joining all files in the enriched_data folder
# list_dfs = [pd.read_csv(f'spotify_data/enriched_data/df_{i}.csv') for i in range(0,105)]
# track_dictionary = stack_n_dfs(list_dfs)
# track_dictionary.to_csv('spotify_data/enriched/data/track_dictionary.csv', index=False)


#Add empty columns to the streaming_history dataframe
# streaming_history = pd.read_csv('spotify_data/streaming_history.csv')
# streaming_history['trackID'] = ''
# for feature in audio_features:
#     streaming_history[feature] = ''
# # and save again to the same csv file
# streaming_history.to_csv('spotify_data/streaming_history.csv', index=False)

# track_dictionary = pd.read_csv('spotify_data/enriched_data/track_dictionary.csv')
# streaming_history = pd.read_csv('spotify_data/streaming_history.csv')

# #Loop through each row of a dataframe and poerform an action
# for index, row in track_dictionary.iterrows():
#     #Find the rows that have the same artist name and track name but in a different dataframe
#     rows = find_rows(streaming_history, 'artistName', 'trackName', row['artistName'], row['trackName'])
#     #If there are rows that match the artist name and track namem then update the trackID and audio features in the streaming_history dataframe
#     if len(rows) > 0:
#         for i in rows:
#             streaming_history.at[i, 'trackID'] = row['trackID']
#             for feature in audio_features:
#                 streaming_history.at[i, feature] = row[feature]

# #Save the streaming_history dataframe to a csv file
# streaming_history.to_csv('spotify_data/streaming_history.csv', index=False) 

#Create a graph with the number of tracks played per day
# streaming_df = pd.read_csv('spotify_data/enriched_data/streaming_history.csv')
# streaming_df['endTime'] = pd.to_datetime(streaming_df['endTime'])
# streaming_df['endTime'] = streaming_df['endTime'].dt.date
# tracks_per_day = streaming_df.groupby('endTime').count()
# tracks_per_day.reset_index(inplace=True)
# tracks_per_day = tracks_per_day[['endTime', 'trackName']]
# tracks_per_day.rename(columns={'trackName': 'PlayCount'}, inplace=True)
# tracks_per_day['endTime'] = pd.to_datetime(tracks_per_day['endTime'])
# tracks_per_day.sort_values(by='endTime', inplace=True)
# tracks_per_day.reset_index(inplace=True)
# tracks_per_day.drop(columns='index', inplace=True)
# tracks_per_day['endTime'] = tracks_per_day['endTime'].dt.date
# fig = px.line(tracks_per_day, x='endTime', y='PlayCount', title='Tracks played per day')
# fig.write_html('tracks_per_day.html', auto_open=True)

#Create a graph with the number of tracks played per hour
# streaming_df = pd.read_csv('spotify_data/enriched_data/streaming_history.csv')
# streaming_df['endTime'] = pd.to_datetime(streaming_df['endTime'], format='%Y-%m-%d %H:%M')
# streaming_df['hour'] = streaming_df['endTime'].dt.hour
# tracks_per_hour = streaming_df.groupby('hour').count()
# tracks_per_hour.reset_index(inplace=True)
# tracks_per_hour = tracks_per_hour[['hour', 'trackName']]
# tracks_per_hour.rename(columns={'trackName': 'PlayCount'}, inplace=True)
# tracks_per_hour.sort_values(by='hour', inplace=True)
# tracks_per_hour.reset_index(inplace=True)
# tracks_per_hour.drop(columns='index', inplace=True)
# fig = px.bar(tracks_per_hour, x='hour', y='PlayCount', title='Songs listened per hour')
# fig.update_layout(
#     xaxis = dict(
#         tickmode = 'array',
#         tickvals = [*range(0, 25, 1)],
#         ticktext = ['12AM','1AM','2AM','3AM','4AM','5AM','6AM','7AM','8AM','9AM',
#                     '10AM','11AM','12PM','1PM','2PM','3PM','4PM','5PM','6PM','7PM',
#                     '8PM','9PM','10PM','11PM']
#     )
# )
# fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')
# fig.write_html('tracks_per_hour.html', auto_open=True)

#Create a matrix dataframe with the number of tracks played per hour (rows) and day of the week (columns)
# streaming_df = pd.read_csv('spotify_data/enriched_data/streaming_history.csv')
# streaming_df['endTime'] = pd.to_datetime(streaming_df['endTime'], format='%Y-%m-%d %H:%M')
# streaming_df['hour'] = streaming_df['endTime'].dt.hour
# streaming_df['day'] = streaming_df['endTime'].dt.dayofweek
# heatmap = streaming_df.groupby(['day', 'hour']).count()
# heatmap.reset_index(inplace=True)
# heatmap = heatmap[['day', 'hour', 'trackName']]
# heatmap.rename(columns={'trackName': 'Songs Listened'}, inplace=True)
# heatmap.sort_values(by=['day', 'hour'], inplace=True)
# heatmap.reset_index(inplace=True)
# heatmap.drop(columns='index', inplace=True)
# heatmap = heatmap.pivot(index='day', columns='hour', values='Songs Listened')
# #Create the heatmap graph
# fig = px.imshow(heatmap, labels=dict(x='Time of Day', y='Day of the Week', color='Songs Listened', title='Listening activity heatmap'))
# fig.update_layout(
#     yaxis = dict(
#         tickmode = 'array',
#         tickvals = [*range(0, 7, 1)],
#         ticktext = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
#     ),
#     xaxis = dict(
#         tickmode = 'array',
#         tickvals = [*range(0, 24, 1)],
#         ticktext = ['12AM','1AM','2AM','3AM','4AM','5AM','6AM','7AM','8AM','9AM',
#                     '10AM','11AM','12PM','1PM','2PM','3PM','4PM','5PM','6PM','7PM',
#                     '8PM','9PM','10PM','11PM']
#     )
# )
# fig.write_html('heatmap.html', auto_open=True)


#Create an animated heatmap graph. The graph will show the evolution of the number of tracks played per hour (columns) per day of the week (rows), for every week of the year (animation_frame)
#Use the following code as an example of how to use animation_frame, for your heatmap graph:
# import plotly.express as px

# df = px.data.gapminder()
# fig = px.scatter(df, x="gdpPercap", y="lifeExp", animation_frame="year", animation_group="country",
#            size="pop", color="continent", hover_name="country",
#            log_x=True, size_max=55, range_x=[100,100000], range_y=[25,90])

# fig["layout"].pop("updatemenus") # optional, drop animation buttons
# fig.show()

#Now, create the animated heatmap graph:











    fig = go.Figure(
        data=[go.Heatmap(z=heatmap_list[0], colorscale='inferno', colorbar=dict(title='Songs Listened'))],
        layout=go.Layout(
            title="Week 1",
            height=350,
            updatemenus=[dict(
                type="buttons",
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {"duration": 800, "redraw": True}
                            }
                        ]
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 0}
                            }
                        ]
                    )
                ],
                direction =  "left",
                pad = {"t": 35},
                x= 0,
                xanchor= "right",
                y = 0,
                yanchor = 'top',
                bgcolor = '#000000',
                bordercolor = '#FFFFFF',
                active=1,
                )
            ]
        ),
        frames= [
            go.Frame(
                data = [go.Heatmap(z=heatmap_list[i])],
                layout = go.Layout(
                            title_text=f"Week {i}",
                            # yaxis = {
                            #     'zeroline': False,
                            #     'showline': False,
                            #     'showgrid': False
                            # }
                            #Adjust the yaxis range to fit the data, the data is variable for each member of week_list
                            yaxis = dict(
                                tickmode = 'array',
                                tickvals = [*range(0, 7, 1)],
                                ticktext = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                            ),
                            xaxis = dict(
                                tickmode = 'array',
                                tickvals = [*range(0, 24, 1)],
                                ticktext = ['12AM','1AM','2AM','3AM','4AM','5AM','6AM','7AM','8AM','9AM',
                                            '10AM','11AM','12PM','1PM','2PM','3PM','4PM','5PM','6PM','7PM',
                                            '8PM','9PM','10PM','11PM']
                            )

                        )
            ) 
                for i in range(0, len(week_list))]
    )
    # fig.update_layout(
    #     yaxis = dict(
    #         tickmode = 'array',
    #         tickvals = [*range(0, 7, 1)],
    #         ticktext = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    #     ),
    #     xaxis = dict(
    #         tickmode = 'array',
    #         tickvals = [*range(0, 24, 1)],
    #         ticktext = ['12AM','1AM','2AM','3AM','4AM','5AM','6AM','7AM','8AM','9AM',
    #                     '10AM','11AM','12PM','1PM','2PM','3PM','4PM','5PM','6PM','7PM',
    #                     '8PM','9PM','10PM','11PM']
    #     )
    # )
    fig.update_layout(
        font_color="white",
        title_font_color="white",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,4)',
        margin=dict(t=30,b=5),
        xaxis_title="Time",
        yaxis_title="Day",
    )
    fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)





from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from flask_session import Session
from chat import TwitchChannel, TwitchAPI, TwitchVOD
import plotly.graph_objects as go
import re
import pickle
from channel import Channel
from video import Video
import logging

app = Flask(__name__)

# Configure the session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'supersecretkey'
Session(app)

# Set up logging
log_file = 'app_startup.log'
log_level = logging.DEBUG

# Create a rotating file handler
handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=3)
handler.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to both app logger and root logger
app.logger.addHandler(handler)
logging.getLogger().addHandler(handler)

# Set the logger level explicitly
app.logger.setLevel(log_level)

# Log application startup
app.logger.info('Flask application is starting...')

def is_youtube_url(url):
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return youtube_regex.match(url)


def is_channel_url(url):
    return 'channel/' in url or 'user/' in url


@app.route('/input')
def input_page():
    return render_template('input.html')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sphere_game')
def sphere_game():
    return render_template('sphere_game.html')

@app.route('/sphere_game_a_star')
def sphere_game_a_star():
    return render_template('sphere_game_a_star.html')

@app.route('/twitch_analyzer_welcome')
def twitch_analyzer():
    api = TwitchAPI()
    moonmoon_channel = TwitchChannel("moonmoon")
    lirik_channel = TwitchChannel("lirik")
    aceu_channel = TwitchChannel("aceu")
    moonmoon_vods = moonmoon_channel.get_sample_vod_ids()
    lirik_vods = lirik_channel.get_sample_vod_ids()
    aceu_vods = aceu_channel.get_sample_vod_ids()
    return render_template('twitch_analyzer_welcome.html', moonmoon_vods=moonmoon_vods, lirik_vods=lirik_vods, aceu_vods=aceu_vods)

@app.route('/logged_channels')
def logged_channels():
    channels = TwitchChannel.get_logged_channels()
    return channels

@app.route('/twitch_analyzer_vod', methods=['POST'])
def analyze_vod():
    try:
        vod_id = request.form['vod_id']
        api = TwitchAPI()
        video = TwitchVOD(api.get_video_by_video_id(vod_id))
        spikes = video.chat.activity_spikes

        # Create Plotly bar chart
        color_scale = 'Reds'
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=spikes.index,
            y=spikes.values,
            marker=dict(
                color=spikes.values,
                colorscale=color_scale,
                colorbar=dict(title='Z-score')
            )
        ))
        fig.update_layout(
            title="Activity Spikes in VOD",
            xaxis_title="Timestamp",
            yaxis_title="Z-score",
            dragmode=False
        )
        config = {
            'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
            'displayModeBar': True
        }

        chart_html = fig.to_html(full_html=False, config=config)

        return render_template('twitch_analyzer_vod.html', vod_id=vod_id, chart_html=chart_html)
    except IndexError:
        flash('VOD not found. Please enter a valid VOD ID.', 'danger')
        return redirect(url_for('twitch_analyzer'))

@app.route('/results', methods=['POST'])
def results_page():
    input_text = request.form['url']
    num_videos = int(request.form['num_videos'])
    search_word = request.form['search_word']

    if is_youtube_url(input_text):
        video_id = input_text.split('v=')[-1]
        video = Video(video_id)
        video.populate_transcript()
        video.populate_word_occurrences(search_word)
        filtered_videos = [video]
    else:
        channel_id = None
        channel_name = None
        if is_channel_url(input_text):
            if 'channel/' in input_text:
                channel_id = input_text.split('channel/')[-1]
            elif 'user/' in input_text:
                channel_name = input_text.split('user/')[-1]
        else:
            channel_name = input_text

        channel = Channel(channel_id=channel_id, channel_name=channel_name, max_videos_num=num_videos,
                          search_word=search_word)


        channel.populate_video_list()
        channel.search_for_word()

        filtered_videos = channel.video_list_with_searchword

    # Serialize and store the video/channel object in session
    session['filtered_videos'] = pickle.dumps(filtered_videos)

    thumbnails = [{'url': f"https://img.youtube.com/vi/{video.video_id}/0.jpg", 'video_id': video.video_id} for video in
                  filtered_videos]


    return render_template('results.html', thumbnails=thumbnails)


@app.route('/get_occurrences', methods=['POST'])
def get_occurrences():
    data = request.get_json()
    video_id = data['video_id']

    # Retrieve and deserialize the filtered videos object from session
    filtered_videos = pickle.loads(session['filtered_videos'])

    # Find the video in the filtered videos list
    video = next((v for v in filtered_videos if v.video_id == video_id), None)

    if video:
        occurrences = [{'start_time': occ['start'], 'text': occ['text']} for occ in video.search_results]
        return jsonify(occurrences=occurrences)
    else:
        return jsonify(occurrences=[]), 404


if __name__ == '__main__':
    app.logger.debug('Starting Flask application...')
    app.run(host='0.0.0.0')

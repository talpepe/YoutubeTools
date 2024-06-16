from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from channel import Channel
from video import Video
import re
import pickle

app = Flask(__name__)

# Configure the session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'supersecretkey'
Session(app)


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
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, render_template, request
from channel import Channel

app = Flask(__name__)


@app.route('/')
def input_page():
    return render_template('input.html')


@app.route('/results', methods=['POST'])
def results_page():
    url = request.form['url']
    num_videos = int(request.form['num_videos'])
    search_word = request.form['search_word']

    # Extract channel id or name from URL
    #channel_id = url.split('channel/')[-1] if 'channel/' in url else None
    #channel_name = url.split('user/')[-1] if 'user/' in url else None
    channel = Channel(channel_name='schafer5', max_videos_num=num_videos,
                      search_word=search_word)

    # Populate the video list and search for the word
    channel.populate_video_list()
    channel.search_for_word()

    # Collect video thumbnails for display from the filtered list
    thumbnails = [f"https://img.youtube.com/vi/{video.video_id}/0.jpg" for video in channel.video_list_with_searchword]

    return render_template('results.html', thumbnails=thumbnails)


if __name__ == '__main__':
    app.run(debug=True)

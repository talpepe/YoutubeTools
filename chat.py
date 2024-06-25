import json
import os
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

class TwitchAPI:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("TWITCH_CLIENT_ID")
        self.secret = os.getenv("TWITCH_SECRET")
        self.access_token = self.get_access_token()

    def get_access_token(self):
        secret_key_url = f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}&client_secret={self.secret}&grant_type=client_credentials"
        response = requests.post(secret_key_url)
        return response.json()["access_token"]

    def get_user_id(self, user_name):
        user_id_url = f"https://api.twitch.tv/helix/users?login={user_name}"
        response = requests.get(user_id_url, headers={"Client-ID": self.client_id, 'Authorization': f"Bearer {self.access_token}"})
        return response.json()["data"][0]["id"]

    def get_videos(self, user_id):
        find_video_url = f"https://api.twitch.tv/helix/videos?user_id={user_id}"
        response = requests.get(find_video_url, headers={"Client-ID": self.client_id, 'Authorization': f"Bearer {self.access_token}"})
        return response.json()

    def get_video_by_video_id(self, video_id):
        find_video_url = f"https://api.twitch.tv/helix/videos?id={video_id}"
        response = requests.get(find_video_url, headers={"Client-ID": self.client_id, 'Authorization': f"Bearer {self.access_token}"})
        return response.json()




class TwitchVOD:
    def __init__(self, video, bin_size='1min', z_threshold=2):
        self.video = video
        self.vod_id = video['data'][0]['id']
        self.start_time = self.get_video_start_time(self.video)
        self.duration = self.parse_duration(video['data'][0]['duration'])
        self.end_time = self.get_video_end_time(self.start_time, self.duration)
        self.channel_name = video['data'][0]['user_name']
        self.chat = VODChat(self.vod_id, self.channel_name, self.start_time, self.end_time, bin_size, z_threshold)


    def get_video_start_time(self, video):
        created_at = datetime.fromisoformat(video['data'][0]['created_at'].replace('Z', '+00:00'))
        return created_at

    @staticmethod
    def parse_duration(duration):
        hours, minutes, seconds = 0, 0, 0
        if 'h' in duration:
            hours = int(duration.split('h')[0])
            duration = duration.split('h')[1]
        if 'm' in duration:
            minutes = int(duration.split('m')[0])
            duration = duration.split('m')[1]
        if 's' in duration:
            seconds = int(duration.split('s')[0])
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    def get_video_end_time(self, start_time, duration):
        end_time = start_time + duration
        return end_time

class TwitchChannel:
    def __init__(self, user_name):
        self.api = TwitchAPI()
        self.user_name = user_name
        self.user_id = self.api.get_user_id(user_name)


    def display_videos(self):
        videos = self.api.get_videos(self.user_id)
        print(json.dumps(videos, indent=4))

    @staticmethod
    def get_logged_channels():
        logged_channels_url = "https://logs.ivr.fi/channels"
        response = requests.get(logged_channels_url)
        return response.text

    def get_sample_vod_ids(self, num_vods=5):
        videos = self.api.get_videos(self.user_id)
        sample_vod_ids = []
        if len(videos["data"]) < num_vods:
            num_vods =  len(videos["data"])
        for x in range(num_vods):
            sample_vod_ids.append(videos["data"][x]["id"])

        return ", ".join(str(x) for x in sample_vod_ids)


class VODChat:
    def __init__(self, vod_id, channel_name, start_time, end_time, bin_size='30sec', z_threshold=2):
        self.start_time = start_time.replace(tzinfo=None)
        self.end_time = end_time.replace(tzinfo=None)
        self.vod_id = vod_id
        self.channel_name = channel_name

        self.chat_log = self.trim_chat_by_vod_time(self.get_chat(), start_time, end_time)
        self.timestamps = self.extract_timestamps_from_log(self.chat_log)
        self.activity_spikes = self.detect_spikes(self.calculate_timestamp_offset(self.timestamps), bin_size, z_threshold)
        self.formatted_spikes_index = None

    @staticmethod
    def detect_spikes(timestamps, bin_size='30s', z_threshold=2):
        df = pd.DataFrame(timestamps, columns=['timestamp'])
        df.set_index('timestamp', inplace=True)
        binned_counts = df.resample(bin_size).size()
        mean_count = binned_counts.mean()
        std_count = binned_counts.std()
        z_scores = (binned_counts - mean_count) / std_count
        spikes = z_scores[z_scores > z_threshold]

        spikes.index = [str(td).split('.')[0] for td in spikes.index.to_pytimedelta()]

        return spikes

    def extract_timestamps_from_log(self, chat_log):
        lines = chat_log.split('\n')
        timestamps = []
        for line in lines:
            timestamp = self.parse_timestamp(line)
            if timestamp:
                timestamps.append(timestamp)
        return timestamps

    @staticmethod
    def parse_timestamp(line):
        try:
            # Extract the timestamp from the line
            timestamp_str = line.split(']')[0].strip('[')
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

    def calculate_timestamp_offset(self, timestamps):
        offsets = []
        for timestamp in timestamps:
            offsets.append(timestamp - self.start_time)
        return offsets

    def trim_chat_by_vod_time(self, chat_log, created_at, end_time):
        # Convert aware datetime objects to naive by removing timezone information
        if created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)
        if end_time.tzinfo is not None:
            end_time = end_time.replace(tzinfo=None)

        lines = chat_log.split('\n')

        start_index = None
        end_index = None

        for i, line in enumerate(lines):
            timestamp = self.parse_timestamp(line)
            if not timestamp:
                continue

            if start_index is None and timestamp >= created_at:
                start_index = i if i > 0 else 0  # Select the previous line if available

            if end_index is None and timestamp > end_time:
                end_index = i
                break

        if start_index is None:
            start_index = 0

        if end_index is None:
            end_index = len(lines)

        trimmed_chat_log = '\n'.join(lines[start_index:end_index])
        return trimmed_chat_log

    def get_chat(self):
        temp_date = self.start_time
        response = ""
        chat_log = ""

        delta = timedelta(days=1)
        print(self.start_time, self.end_time)
        if temp_date.date() == self.end_time.date():
            user_id_url = f"https://logs.ivr.fi/channel/{self.channel_name}/{temp_date.year}/{temp_date.month}/{temp_date.day}"
            chat_log = requests.get(user_id_url).content.decode()
        else:
            while temp_date.date() <= self.end_time.date():
                user_id_url = f"https://logs.ivr.fi/channel/{self.channel_name}/{temp_date.year}/{temp_date.month}/{temp_date.day}"
                chat_log = chat_log + requests.get(user_id_url).content.decode()
                temp_date += delta

        chat_log = self.trim_chat_by_vod_time(chat_log, self.start_time, self.end_time)
        return chat_log



if __name__ == "__main__":
    user_name = "moonmoon"
    twitch_channel = TwitchChannel(user_name)
    api = TwitchAPI()
    video = TwitchVOD(api.get_video_by_video_id(2179077980), '45s')
    #video = TwitchVOD(api.get_video_by_video_id(2177260242), '30s')

    spikes = video.chat.activity_spikes
    #twitch_channel.display_videos()
    # videos = twitch_channel.api.get_videos(twitch_channel.user_id)["data"]
    # for video in videos:
    #     end_time = twitch_channel.get_vod_end_time(video)
    #     print(f"Video {video['id']} ends at {end_time}")
    # twitch_channel.get_sample_vod_ids()
    # print(twitch_channel.user_id)
    # print(twitch_channel.sample_vod_ids)
    # print(TwitchChannel.get_logged_channels())

    #with open("output.txt", "w", encoding="utf-8") as file:
    #    file.write(api.get_chat_for_vod_id(2177260242))
    #print(api.get_chat_for_vod_id(2177260242).find("\n[2024-06-20 00:00:01] #moonmoon"))
    #twitch_channel.get_sample_vod_ids()
    #print(twitch_channel.sample_vod_ids)
 # Create Plotly chart
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
        'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d',
                                   'resetScale2d'],
        'displayModeBar': True  # Display the mode bar for other functionalities

    }

    # Save chart as HTML
    fig.write_html("activity_spikes.html", config=config)
    # Print spikes data
    print(spikes)
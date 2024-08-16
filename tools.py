import re
import string
import traceback

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi



class ApiTools:
    def __init__(self, api_key, **kwargs):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_video_list_from_channel_id(self, channel_id, max_results=10):
        video_ids = []
        next_page_token = None
        ch_request = self.youtube.channels().list(
            part='contentDetails',
            id=channel_id,
            maxResults=max_results,
            pageToken=next_page_token
        )
        ch_response = ch_request.execute()
        uploads_playlist_id = ch_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        while True:
            playlist_response = self.youtube.playlistItems().list(
                part='contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=max_results,
                pageToken=next_page_token
            ).execute()

            for item in playlist_response['items']:
                video_ids.append(item['contentDetails']['videoId'])

            next_page_token = ch_response.get('nextPageToken')
            if not next_page_token:
                break
        return video_ids

    def get_video_list_from_channel_name(self, channel_name, max_results=10):
        video_ids = []
        next_page_token = None
        ch_request = self.youtube.channels().list(
            part='contentDetails',
            forHandle=channel_name,
            maxResults=max_results
        )

        ch_response = ch_request.execute()
        uploads_playlist_id = ch_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        try:
            while len(video_ids) < max_results:
                playlist_response = self.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=max_results,
                    pageToken=next_page_token
                ).execute()

                for item in playlist_response['items']:
                    video_ids.append(item['contentDetails']['videoId'])
                next_page_token = playlist_response.get('nextPageToken')

                if not next_page_token:
                    break
        except:
            return video_ids
        return video_ids

    @staticmethod
    def get_transcript_from_video_id(video_id):
        transcript = ""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies={"https": "http://abb9e586d4fe28f84671:be19e93541e5db52@gw.dataimpulse.com:10000"})

        except Exception as e:
            with open("TranscriptException.txt", "w") as file:
                file.write(str(e))
                file.write(traceback.format_exc())
        return transcript

    @staticmethod
    def get_word_occurrences_from_transcript(transcript, search_word):
        word_occurrences = []
        for line in transcript:
            pruned_text = ApiTools.remove_punctuation(line.get('text'))
            if ApiTools.search_word_in_line(search_word, pruned_text) is not None:
                word_occurrences.append(line)

        return word_occurrences


    @staticmethod
    def search_word_in_line(word, line):
        return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search(line)

    @staticmethod
    def remove_punctuation(text):
        return text.translate(str.maketrans('', '', string.punctuation))

if __name__ == "__main__":
    from channel import Channel

    channel1 = Channel(channel_name='schafer5', max_videos_num=3, search_word="hey")
    channel1.populate_video_list()
    channel1.search_for_word()
    channel1.get_occurrences()

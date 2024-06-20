#import ApiTools
from tools import ApiTools
from video import Video
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv, find_dotenv
import os
load_dotenv()

class Channel:
    def __init__(self, **kwargs):
        for attr in ('channel_id', 'channel_name', 'max_videos_num', 'search_word'):
            setattr(self, attr, kwargs.get(attr))
        self.video_list = []
        self.api_tool = ApiTools(os.getenv("YT_API_KEY"))
        self.video_list_with_searchword = []

    def populate_video_list(self):
        video_id_list = []
        if self.channel_id is not None:
            video_id_list = ApiTools.get_video_list_from_channel_id(self.api_tool, self.channel_id, self.max_videos_num)
        elif self.channel_name is not None:
            video_id_list = ApiTools.get_video_list_from_channel_name(self.api_tool, self.channel_name, self.max_videos_num)
        else:
            print("no channel id or name given")
            return

        for video_id in video_id_list:
            self.video_list.append(Video(video_id))

    def search_for_word(self):
        self.video_list_with_searchword = []
        if self.search_word is None:
            print("no search word initialized for channel")

        def process_video(video):
            video.populate_transcript()
            video.populate_word_occurrences(self.search_word)
            return video

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(process_video, video) for video in self.video_list]
            for future in as_completed(futures):
                video = future.result()
                if video.get_num_occurrences() > 0:
                    self.video_list_with_searchword.append(video)

    def get_occurrences(self):
        total_occurrences = []
        for video in self.video_list:
            print(video.get_num_occurrences())
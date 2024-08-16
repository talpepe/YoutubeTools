from tools import ApiTools


class Video:
    def __init__(self, video_id, **kwargs):
        self.search_word_occurrences = []
        self.search_results = []
        self.video_id = video_id
        self.transcript = None

    def parse_occurrences(self, occurrences_list):
        for occurrence in occurrences_list:
            self.search_word_occurrences.append(occurrence.get('start'))

    def get_num_occurrences(self):
        return len(self.search_word_occurrences)

    def populate_transcript(self):
        self.transcript = ApiTools.get_transcript_from_video_id(self.video_id)
        with open("transcript.txt", "w") as file:
            for line in self.transcript:
                file.write("%s\n" % line)


    def populate_word_occurrences(self, word):
        self.search_results = ApiTools.get_word_occurrences_from_transcript(self.transcript, word)
        self.parse_occurrences(self.search_results)
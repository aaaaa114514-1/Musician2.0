'''
History management
'''

import json
import pathlib

class HistoryManager:
    def __init__(self, history_path):
        self.history_path = history_path
        self.history_data = self.load_history()

    def load_history(self):
        if pathlib.Path(self.history_path).exists():
            with open(self.history_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("History file is corrupted. Initializing a new history.")
                    return {"songs": {}, "total_count": 0, "total_time": 0}
        else:
            return {"songs": {}, "total_count": 0, "total_time": 0}

    def save_history(self):
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history_data, f, indent=4, ensure_ascii=False)

    def update_history_time(self, play_time):
        self.history_data["total_time"] += play_time

    def update_history_song(self, song_name):
        if song_name not in self.history_data["songs"]:
            self.history_data["songs"][song_name] = {"play_count": 0}
        self.history_data["songs"][song_name]["play_count"] += 1
        self.history_data["total_count"] += 1

    def print_history_summary(self):
        total_seconds = self.history_data["total_time"]
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        total_count = self.history_data["total_count"]
        print(f"You have played your favourite songs {total_count} times for {hours}h {minutes}m {seconds}s!")
        songs = self.history_data["songs"]
        sorted_songs = sorted(songs.items(), key=lambda x: x[1]["play_count"], reverse=True)
        print("Here are your favourite songs:")
        for song_name, data in sorted_songs:
            print(f"{data['play_count']}:\t{song_name.replace('.mp3','')}")
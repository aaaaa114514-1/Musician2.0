'''
Player class and background threads
'''

import os
import time
import pygame
import threading

class player:
    def __init__(self, playpath, playlist, volume, history_manager):
        pygame.mixer.init()
        self.playpath = playpath
        self.playlist = playlist
        self.history_manager = history_manager
        self.nowplaying = 0
        self.playing_songname = playlist[0] if playlist else ""
        self.nowmode = 'stop'
        self.is_single = 0
        self.playtime = 0
        self.set_volume(volume)
        if playlist:
            pygame.mixer.music.load(os.path.join(self.playpath, self.playing_songname))
            pygame.mixer.music.play()
            pygame.mixer.music.pause()

    def set_playlist(self, playlist):
        self.playlist = playlist
        if self.playing_songname in self.playlist:
            self.nowplaying = self.playlist.index(self.playing_songname)

    def add_playlist(self, playlist):
        self.playlist.extend(playlist)
        if self.playing_songname in self.playlist:
            self.nowplaying = self.playlist.index(self.playing_songname)

    def set_volume(self, volume: float):
        self.volume = volume
        pygame.mixer.music.set_volume(self.volume)

    def play(self):
        if (self.nowmode != 'playing'):
            self.playtime = int(time.time())
            self.nowmode = 'playing'
        self.playing_songname = self.playlist[self.nowplaying]
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(os.path.join(self.playpath, self.playing_songname))
        pygame.mixer.music.play()
        self.history_manager.update_history_song(self.playing_songname)
    
    def next(self):
        if not self.playlist: return
        self.nowplaying += 1
        if self.nowplaying == len(self.playlist):
            self.nowplaying = 0
        self.play()

    def last(self):
        if not self.playlist: return
        self.nowplaying -= 1
        if self.nowplaying == -1:
            self.nowplaying = len(self.playlist) - 1
        self.play()

    def check_play(self):
        if self.nowmode == 'playing' and not pygame.mixer.music.get_busy():
            if self.is_single:
                self.play()
            else:
                self.next()

    def pause(self):
        if self.nowmode == 'playing':
            self.nowmode = 'pause'
            pygame.mixer.music.pause()
            self.history_manager.update_history_time(int(time.time())-self.playtime)
            self.playtime = int(time.time())

    def unpause(self):
        if self.nowmode == 'stop':
            self.history_manager.update_history_song(self.playing_songname)
        if self.nowmode in ['pause', 'stop']:
            self.nowmode = 'playing'
            pygame.mixer.music.unpause()
            self.playtime = int(time.time())
    
    def stop(self):
        if (self.nowmode == 'playing'):
            self.history_manager.update_history_time(int(time.time())-self.playtime)
            self.playtime = int(time.time())
        self.nowmode = 'stop'
        pygame.mixer.music.stop()

def keep_checking(player_instance, timelimit:list, lock):
    while True:
        time.sleep(0.5)
        player_instance.check_play()
        with lock:
            timelimit0 = timelimit[0]
        if time.time() > timelimit0:
            player_instance.stop()
            timelimit[0] = int(time.time()) + 1e9
            print('Time limit reached!\n>> ',end='')
'''
Main loop
'''

import os
import time
import pathlib
import threading
import json
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter

from core.player import player, keep_checking
from core.history import HistoryManager
from ui import handlers

def main():
    # 1. Load config from JSON
    config_file = "settings.json"
    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found.")
        return

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading settings.json: {e}")
        return

    # 2. Init environment
    # Always sort library by creation time (ascending)
    folder = pathlib.Path(config['library_dir'])
    files = sorted([f for f in folder.glob("*.mp3")], key=lambda f: f.stat().st_ctime)
    playlist = [f.name for f in files] # Full library sorted by time
    current_view_list = list(playlist)    # Default view is full library
    
    tags = handlers._load_tags(config)
    history_manager = HistoryManager(config['history_path'])
    bgm = player(config['library_dir'], playlist, config['volume'], history_manager)
    
    timelimit = [int(time.time()) + 1e9]
    lock = threading.Lock()
    mode = 'cycle'
    running = 1
    kugou_list, files_cache, songnames = [], [], []

    # 3. Setup Command completion and InMemory History
    base_commands = ['help', ':h', 'quit', 'exit', 'end', ':q', 'check163', ':163_cache', 
                'decode', ':d', 'clear163', ':163_clear', 'search', '/s', 'download', '/d', 
                'showlist', ':l', 'play', ':p', 'mode', ':m', 
                'stop', ':st', 'pause', ':pa', 'next', ':n', 'restart', 'replay', ':r', 
                'volume', ':vol', 'savelist', ':sl', 'save', ':s', 'add', ':a', 
                'clear', ':cl', 'library', ':lib', 'lookup', ':lu', 'timelimit', ':tl', 
                'history', ':his', 'set', 'common', 'tag', '?', ':?', 'last', 'previous', ':prev']
    
    common_cmds = []
    cc_path = config.get('common_commands_path')
    if cc_path and os.path.exists(cc_path):
        try:
            with open(cc_path, "r", encoding="utf-8") as f:
                common_cmds = json.load(f)
        except: pass

    history = InMemoryHistory()
    for cmd_str in common_cmds:
        history.append_string(cmd_str)
    
    session = PromptSession(
        history=history,
        completer=FuzzyCompleter(WordCompleter(base_commands, ignore_case=True))
    )

    # 4. Background thread
    threading.Thread(target=keep_checking, args=(bgm, timelimit, lock), daemon=True).start()

    print('-------------------------------------------------------------------------------------------------')
    print('|Copyright © 2025 aaaaa. All rights reserved.\t\t\t\t\t\t\t|')
    print('-------------------------------------------------------------------------------------------------')
    print('Welcome to musician! Please key in your Command.')

    while running:
        try:
            print()
            res = str(session.prompt('>> ')).strip()
            if not res: continue

            parts = res.lower().split()
            cmd = parts[0]

            if cmd in ['help', ':h']:
                handlers.handle_help()
            elif cmd in ['quit', 'exit', 'end', ':q']:
                running = handlers.handle_quit(res, bgm, history_manager)
            elif cmd in ['check163', ':163_cache']:
                songnames, files_cache = handlers.handle_check163(res, config['netease_cache'])
            elif cmd in ['clear163', ':163_clear']:
                handlers.handle_clear163(res, config['netease_cache'])
            elif cmd in ['search', '/s']:
                kugou_list = handlers.handle_search(res, config['search_threshold'])
            elif cmd in ['download', '/d']:
                handlers.handle_download(res, kugou_list, config['download_dir'], config['kugou_token'])
            elif cmd in ['decode', ':d']:
                handlers.handle_decode(res, files_cache, songnames, config['download_dir'], config['temp_dir'])
            elif cmd in ['showlist', ':l']:
                current_view_list = handlers.handle_showlist(res, config['library_dir'], tags)
            elif cmd in ['play', ':p']:
                mode, current_view_list = handlers.handle_play(res, bgm, playlist, current_view_list, mode, config, tags, timelimit, lock)
            elif cmd in ['mode', ':m']:
                mode = handlers.handle_mode(res, bgm, mode, playlist)
            elif cmd in ['restart', 'replay', ':r']:
                handlers.handle_restart(res, bgm)
            elif cmd in ['volume', ':vol']:
                handlers.handle_volume(res, bgm)
            elif cmd in ['savelist', ':sl']:
                handlers.handle_savelist(res, config['download_dir'])
            elif cmd in ['save', ':s']:
                playlist = handlers.handle_save(res, config['download_dir'], config['library_dir'], playlist, tags, config)
            elif cmd in ['add', ':a']:
                mode, current_view_list = handlers.handle_add(res, bgm, playlist, current_view_list, mode, config, tags)
            elif cmd in ['clear', ':cl']:
                handlers.handle_clear(res, config['download_dir'])
            elif cmd in ['stop', ':st']:
                handlers.handle_stop(res, bgm)
            elif cmd in ['pause', ':pa']:
                handlers.handle_pause(res, bgm)
            elif cmd in ['next', ':n']:
                handlers.handle_next(res, bgm)
            elif cmd in ['last', 'previous', ':prev']:
                handlers.handle_last(res, bgm)
            elif cmd in ['library', ':lib']:
                handlers.handle_library(res, config['library_dir'])
            elif cmd in ['lookup', ':lu']:
                handlers.handle_lookup(res, config['library_dir'], config['search_threshold'])
            elif cmd in ['timelimit', ':tl']:
                handlers.handle_timelimit(res, timelimit, lock)
            elif cmd in ['history', ':his']:
                handlers.handle_history(res, history_manager)
            elif cmd in ['set']:
                handlers.handle_set(res, config)
            elif cmd in ['common']:
                handlers.handle_common(res, config, session)
            elif cmd in ['tag']:
                # Pass playlist (current view used in -a is now explicitly from current_view_list inside handler)
                tags = handlers.handle_tag(res, current_view_list, config, tags)
            elif cmd in ['?', ':?']:
                handlers.handle_current_song(res, bgm)
            else:
                print(f"'{cmd}': Invalid command!")
            
            bgm.check_play()
        except KeyboardInterrupt:
            handlers.handle_quit("quit", bgm, history_manager)
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
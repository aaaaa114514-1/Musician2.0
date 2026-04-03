'''
Handle all user instructions
'''

import os
import shutil
import pathlib
import random
import datetime
import time
import re
import json
from services.netease import get_name, uc_decode
from services.kugou import kugou_getlist, kugou_download
from utils.file_utils import sanitize_filename
from utils.search_utils import fuzzy_match_all
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter

# Help messages for each command
CMD_HELP = {
    'quit': "Usage: quit | exit | end | :q\nFunction: Save history and exit the program.\nExample: quit",
    'check163': "Usage: check163 | :163_cache\nFunction: List all Netease Cloud Music cache (.uc) files.\nExample: check163",
    'decode': "Usage: decode <indices> | :d <indices>\nFunction: Decode selected .uc files to .mp3.\nExample: decode 1 3-5",
    'clear163': "Usage: clear163 | :163_clear\nFunction: Delete all files in the Netease cache directory.\nExample: clear163",
    'search': "Usage: search <keyword> | /s <keyword>\nFunction: Search for songs on Kugou Music.\nExample: search Taylor Swift",
    'download': "Usage: download <indices> | /d <indices>\nFunction: Download songs from the last search result.\nExample: download 1 2",
    'showlist': "Usage: showlist [tag] | :l [tag]\nFunction: Show songs in the library. Filter by tag if provided.\nExample: showlist | showlist myfav",
    'play': "Usage: play [indices] [tag] [flags] | :p [indices] [tag] [flags]\nFlags: -m [s|c|r], -v [0-100], -t [min/time]\nFunction: Play songs from current view or specified tag.\nExample: play 1-10 | play mytag -m r | play 1 -v 40 mytag",
    'mode': "Usage: mode <cycle|single|random> | :m <c|s|r>\nFunction: Change the playback mode.\nExample: mode random",
    'stop': "Usage: stop | :st\nFunction: Stop playback.\nExample: stop",
    'pause': "Usage: pause | :pa\nFunction: Pause the current song.\nExample: pause",
    'next': "Usage: next | :n\nFunction: Play the next song in the playlist.\nExample: next",
    'last': "Usage: last | previous | :prev\nFunction: Play the previous song in the playlist.\nExample: last",
    'restart': "Usage: restart | replay | :r\nFunction: Replay the current song from the beginning.\nExample: restart",
    'volume': "Usage: volume <0-100> | :vol <0-100>\nFunction: Set the player volume.\nExample: volume 80",
    'savelist': "Usage: savelist | :sl\nFunction: Show songs in the temporary save directory.\nExample: savelist",
    'save': "Usage: save [tag1 tag2 ...] | :s [tag1 tag2 ...]\nFunction: Move downloaded songs to library and apply optional tags.\nExample: save | save myfav pop",
    'add': "Usage: add [indices] [tag] [flags] | :a [indices] [tag] [flags]\nFunction: Add selected songs to play queue.\nExample: add 5-8 -m c | add mytag 1",
    'clear': "Usage: clear | :cl\nFunction: Clear all songs in the temporary save directory.\nExample: clear",
    'library': "Usage: library | :lib\nFunction: List all songs in the local music library.\nExample: library",
    'lookup': "Usage: lookup <keyword> | :lu <keyword>\nFunction: Fuzzy search for songs in the local library.\nExample: lookup Love",
    'timelimit': "Usage: timelimit <min> | <HH:MM[:SS]> | :tl <min> | <HH:MM[:SS]>\nFunction: Stop playback after X minutes or at a specific time.\nExample: timelimit 30 | timelimit 14:15",
    'history': "Usage: history | :his\nFunction: Show play counts and total time statistics.\nExample: history",
    'current': "Usage: ? | :?\nFunction: Show information about the song currently playing.\nExample: ?",
    'set': "Usage: set [list | <key> <value>]\nFunction: View or modify settings.\nExample: set volume 0.5",
    'common': "Usage: common [-l | -a <cmd> | -d <indices>]\nFunction: Manage common commands. Delete supports ranges.\nExample: common -l | common -a \"play 1-5\" | common -d 1-3 5",
    'tag': "Usage: tag [tag_name | -l | -a <tag> <indices> | -d <tag> [indices]]\nFunction: Manage song tags. Use alone to list tags and counts.\nExample: tag | tag mytag | tag -a fav 1-3 | tag -d oldtag",
}

def _validate_flags(res, allowed):
    """Check if any unknown flags (starting with -) exist in the command."""
    words = res.split()
    for word in words:
        if word.startswith('-') and word not in allowed:
            print(f"Error: Unknown flag '{word}' for this command.")
            return False
    return True

def _check_help(res, cmd_key):
    """Check if -h is in the command and print help if so."""
    if '-h' in res.split():
        print(f"\n{CMD_HELP.get(cmd_key, 'No help available.')}")
        return True
    return False

def _is_valid_tag(tag):
    """Check if a tag name follows the rules: alphanumeric+underscore, not pure digits."""
    if not tag: return False
    pattern = r'^(?![0-9]+$)[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, tag))

def _load_tags(config):
    path = config.get('tags_path')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_tags(config, tags):
    path = config.get('tags_path')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(tags, f, indent=4, ensure_ascii=False)

def _save_settings(config):
    """Save config dictionary to settings.json."""
    try:
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Failed to save settings: {e}")
        return False

def _parse_flags(res):
    """Extract flags like -m, -v, -t."""
    flags = {}
    pattern = r'-([mvt])\s+([^\s-]+)'
    matches = re.findall(pattern, res)
    for tag, value in matches:
        flags[tag] = value
    clean_res = re.sub(pattern, '', res).strip()
    clean_res = re.sub(r'\s+', ' ', clean_res)
    return clean_res, flags

def _parse_indices(res_parts, max_len):
    tmp = []
    for part in res_parts:
        if '-' in part:
            try:
                sta, end = map(int, part.split('-'))
                if sta > end or sta < 1 or end > max_len:
                    pass
                else:
                    tmp.extend(range(sta, end + 1))
            except ValueError:
                pass
        else:
            try:
                num = int(part)
                if num < 1 or num > max_len:
                    pass
                else:
                    tmp.append(num)
            except ValueError:
                pass
    return sorted(set(tmp))

def handle_help():
    print('''
Command\t\t\tFunction
--------------------------------------------------------------------------
quit/exit/end/:q\tExit the program
check163/:163_cache\tShow 163music cache
decode/:d #\t\tDecode cached songs
clear163/:163_clear\tClear 163music cache
search//s #\t\tSearch in Kugou
download//d #\t\tDownload from Kugou
showlist/:l\t\tShow songs by tag
play/:p\t\t\tPlay/unpause or play indices
add/:a #\t\tAdd to play queue
mode/:m #\t\tMode(cycle/single/random)
stop/:st\t\tStop playing
pause/:pa\t\tPause
next/:n\t\t\tNext song
last/previous/:prev\tPrevious song
restart/replay/:r\tRestart
volume/:vol #\t\tSet volume(1-100)
savelist/:sl\t\tShow save list
save/:s lis/bgm\t\tMove songs to library
clear/:cl\t\tClear save list
library/:lib\t\tShow library
lookup #/:lu\t\tSearch in library
timelimit/:tl #\t\tSet play time limit
history/:his\t\tShow history
set\t\t\tView/Change settings
common\t\t\tManage common commands
tag\t\t\tManage song tags
?/:?\t\t\tCurrent song
--------------------------------------------------------------------------
Tip: Add -h after any command for detailed usage and examples!
''')

def handle_quit(res, bgm, history_manager):
    if not _validate_flags(res, ['-h']): return 1
    if _check_help(res, 'quit'): return 1
    bgm.stop()
    history_manager.save_history()
    return 0

def handle_check163(res, cache_directory):
    if not _validate_flags(res, ['-h']): return [], []
    if _check_help(res, 'check163'): return [], []
    songnames = []
    files = [os.path.join(cache_directory, f) for f in os.listdir(cache_directory) if f.endswith(".uc")]
    files.sort(key=lambda f: os.path.getctime(f), reverse=True)
    if len(files) == 0:
        print('There is no file in your 163music Cache!')
        return songnames, files
    print(f'There is(are) {len(files)} file(s) here:')
    i = 1
    for file in files:
        name = get_name(file.split('\\')[-1].split('-')[0])
        if name == 'NE':
            print('Network error! Please check your network!')
            break
        else:
            songnames.append(name)
            print(f'{i}.\t{sanitize_filename(str(name))}')
            i += 1
    return songnames, files

def handle_clear163(res, cache_directory):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'clear163'): return
    for file in os.listdir(cache_directory):
        file_path = os.path.join(cache_directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    print('163music cache list cleared!')

def handle_search(res, threshold):
    if not _validate_flags(res, ['-h']): return []
    if _check_help(res, 'search'): return []
    try:
        parts = res.split()
        if len(parts) < 2:
            print("Please provide a keyword to search.")
            return []
        keyword = " ".join(parts[1:])
        kugou_list = kugou_getlist(keyword)
        if kugou_list == 0 or len(kugou_list) == 0:
            print(f'Cannot find any song with keyword {keyword}!')
            return []
        i = 1
        for kugou_song in kugou_list:
            print(f'{i}.\t'+str(kugou_song[2])+str(kugou_song[0]))
            i += 1
        return kugou_list
    except:
        print('Invalid command!')
        return []

def handle_download(res, kugou_list, save_directory, token2):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'download'): return
    try:
        parts = res.split()[1:]
        if len(kugou_list) == 0:
            print('Please search before downloading!')
            return
        elif len(parts) == 0:
            print('Please key in the number of the song you want to download!')
            return
        print('Start downloading...')
        indices = _parse_indices(parts, len(kugou_list))
        for i in indices:
            try:
                result = kugou_download(kugou_list, i, save_directory, token2)
                if result == 1:
                    print(f'Successfully Downloaded: {kugou_list[i-1][0]}')
                else:
                    print(f'Cannot download song {i}: {kugou_list[i-1][0]}')
            except Exception as e:
                print(f'Cannot download song {i}: {kugou_list[i-1][0]} - {e}')
    except:
        print('Invalid command!')

def handle_decode(res, files, songnames, save_directory, temp_directory):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'decode'): return
    try:
        if len(files) == 0:
            print('Please key in \'check163\' before decoding!')
            return
        parts = res.split()[1:]
        if not parts:
            print('Invalid input format!')
            return
        decode_list = _parse_indices(parts, len(files))
        if not decode_list:
            print('Please key in the number of the song you want to decode!')
            return
        print('Start decoding...')
        for i in decode_list:
            try:
                uc_decode(files[i-1], save_directory, temp_directory)
                print(f'Successfully Decoded: {songnames[i-1]}')
            except:
                print(f'Cannot decode song {i}: {songnames[i-1]}')
        print('Mission Accomplished!')
    except:
        print('Invalid command!')

def handle_showlist(res, library_dir, tags_dict):
    """Show library songs, sorted by creation time, optionally filtered by tag."""
    if not _validate_flags(res, ['-h']): return []
    if _check_help(res, 'showlist'): return []
    
    files = [f for f in pathlib.Path(library_dir).glob("*.mp3")]
    files.sort(key=lambda f: f.stat().st_ctime)
    all_songs = [f.name for f in files]
    
    parts = res.split()
    filtered_list = []
    if len(parts) == 1:
        print("Your library (All, by time):")
        filtered_list = all_songs
    else:
        tag = parts[1]
        print(f"Your library (Tag: {tag}, by time):")
        filtered_list = [s for s in all_songs if tag in tags_dict.get(s, [])]
        
    if not filtered_list:
        print("No songs found.")
    else:
        for i, song in enumerate(filtered_list, 1):
            print(f'{i}.\t{song}')
    return filtered_list

def handle_play(res, bgm, playlist, current_view_list, mode, config, tags_dict, timelimit=None, lock=None):
    if not _validate_flags(res, ['-m', '-v', '-t', '-h']): return mode, current_view_list
    if _check_help(res, 'play'): return mode, current_view_list
    
    res, flags = _parse_flags(res)
    parts = res.split()[1:]
    target_indices_str = []
    found_tag = None
    for p in parts:
        if re.match(r'^\d+(-\d+)?$', p): target_indices_str.append(p)
        elif _is_valid_tag(p): found_tag = p
            
    source_list = current_view_list
    if found_tag:
        source_list = [s for s in playlist if found_tag in tags_dict.get(s, [])]
        print(f"Playing from tag: {found_tag}")
    
    if 'm' in flags:
        m = flags['m']
        if m == 's': mode = 'single'; bgm.is_single = 1
        elif m == 'c': mode = 'cycle'; bgm.is_single = 0; bgm.set_playlist(source_list)
        elif m == 'r': mode = 'random'; bgm.is_single = 0
        print(f"Mode set to: {mode}")
    if 'v' in flags: handle_volume(f"vol {flags['v']}", bgm)
    if 't' in flags and timelimit is not None: handle_timelimit(f"tl {flags['t']}", timelimit, lock)

    if not target_indices_str and found_tag:
        selected_songs = list(source_list)
        if not selected_songs: return mode, current_view_list
        if mode == 'random': random.shuffle(selected_songs)
        bgm.set_playlist(selected_songs)
        bgm.stop(); bgm.nowplaying = 0; bgm.play()
        print(f"Playing all {len(selected_songs)} songs from tag '{found_tag}'.")
    elif not target_indices_str and not found_tag: bgm.unpause()
    else:
        try:
            tmp = _parse_indices(target_indices_str, len(source_list))
            if not tmp: print('No valid song to play!')
            else:
                print('Start playing:')
                selected_songs = [source_list[i-1] for i in tmp]
                if mode == 'random': random.shuffle(selected_songs)
                for i in tmp: print(f'{i}.\t{source_list[i-1]}')
                bgm.set_playlist(selected_songs)
                bgm.stop(); bgm.nowplaying = 0; bgm.play()
        except: print('Invalid command!')
    return mode, current_view_list

def handle_mode(res, bgm, mode, playlist):
    if not _validate_flags(res, ['-h']): return mode
    if _check_help(res, 'mode'): return mode
    try:
        parts = res.split()
        if len(parts) < 2: 
            print(f"Current mode: {mode}")
            return mode
        requested = parts[1]
        if requested in ['c', 'cycle']: requested = 'cycle'
        elif requested in ['s', 'single']: requested = 'single'
        elif requested in ['r', 'random']: requested = 'random'
        if requested not in ['cycle','single','random']: print('Invalid mode!')
        else:
            if requested != mode or requested == 'random':
                print(f'Playing mode changed: {mode} -> {requested}!')
                mode = requested
                if mode == 'random':
                    bgm.is_single = 0
                    tmp = list(bgm.playlist); random.shuffle(tmp); bgm.set_playlist(tmp)
                elif mode == 'single': bgm.is_single = 1
                else: bgm.is_single = 0; bgm.set_playlist(playlist)
            else: print(f'Playing mode is already {mode}!')
        return mode
    except: print('Invalid command!'); return mode

def handle_restart(res, bgm):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'restart'): return
    bgm.play()

def handle_volume(res, bgm):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'volume'): return
    try:
        volume = float(res.split()[1])
        if volume >= 1 and volume <= 100: volume = volume/100
        if 0 <= volume <= 1:
            bgm.set_volume(volume)
            print(f'Volume changed to {int(volume*100)}%!')
        else: print('Invalid volume!')
    except: print('Invalid volume!')

def handle_savelist(res, save_directory):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'savelist'): return
    savelist = [f.name for f in pathlib.Path(save_directory).glob("*.mp3")]
    if len(savelist) == 0: print('There is no song in your savelist!')
    else:
        print('Your savelist:')
        for i, song in enumerate(savelist, 1): print(f'{i}.\t{song}')

def handle_save(res, save_directory, library_directory, playlist, tags_dict, config):
    """Refactored Save: Moves files from temp to library and applies optional tags."""
    if not _validate_flags(res, ['-h']): return playlist
    if _check_help(res, 'save'): return playlist
    
    savelist_files = [f for f in pathlib.Path(save_directory).glob("*.mp3")]
    if not savelist_files:
        print('There is no song in your savelist!')
        return playlist

    parts = res.split()
    input_tags = parts[1:] # Everything after 'save' are potential tags
    
    # 1. Validate all input tags before any file operations
    for tag in input_tags:
        if not _is_valid_tag(tag):
            print(f"Error: '{tag}' is not a valid tag name. Operation cancelled.")
            return playlist

    # 2. Perform Move and Tagging
    print(f"Saving {len(savelist_files)} song(s) to library...")
    for song_path in savelist_files:
        song_name = song_path.name
        dest_path = os.path.join(library_directory, song_name)
        
        # Move file (preserves ctime)
        shutil.move(str(song_path), dest_path)
        
        # Add to tags_dict
        if input_tags:
            if song_name not in tags_dict:
                tags_dict[song_name] = []
            for tag in input_tags:
                if tag not in tags_dict[song_name]:
                    tags_dict[song_name].append(tag)
    
    # 3. Finalize
    _save_tags(config, tags_dict)
    print(f"Successfully saved and tagged with: {input_tags if input_tags else 'None'}")
    
    # Resort playlist by creation time
    new_files = [f for f in pathlib.Path(library_directory).glob("*.mp3")]
    new_files.sort(key=lambda f: f.stat().st_ctime)
    return [f.name for f in new_files]

def handle_add(res, bgm, playlist, current_view_list, mode, config, tags_dict):
    if not _validate_flags(res, ['-m', '-h']): return mode, current_view_list
    if _check_help(res, 'add'): return mode, current_view_list
    res, flags = _parse_flags(res)
    parts = res.split()[1:]
    target_indices_str = []
    found_tag = None
    for p in parts:
        if re.match(r'^\d+(-\d+)?$', p): target_indices_str.append(p)
        elif _is_valid_tag(p): found_tag = p
            
    source_list = current_view_list
    if found_tag:
        source_list = [s for s in playlist if found_tag in tags_dict.get(s, [])]
        print(f"Adding from tag: {found_tag}")

    if 'm' in flags:
        m = flags['m']
        if m == 's': mode = 'single'; bgm.is_single = 1
        elif m == 'c': mode = 'cycle'; bgm.is_single = 0
        elif m == 'r': mode = 'random'; bgm.is_single = 0
        print(f"Mode set to: {mode}")

    try:
        if not target_indices_str and found_tag: tmp = range(1, len(source_list)+1)
        else: tmp = _parse_indices(target_indices_str, len(source_list))
            
        if not tmp: print('No valid song to add!')
        else:
            print('Added songs:')
            selected_songs = [source_list[i-1] for i in tmp]
            if mode == 'random': random.shuffle(selected_songs)
            for i in tmp: print(f'{i}.\t{source_list[i-1]}')
            bgm.add_playlist(selected_songs)
            if bgm.nowmode in ['stop', 'pause'] or bgm.playing_songname not in bgm.playlist:
                bgm.stop(); bgm.nowplaying = 0; bgm.play()
    except: print('Invalid command!')
    return mode, current_view_list

def handle_clear(res, save_directory):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'clear'): return
    current_savelist = [f.name for f in pathlib.Path(save_directory).glob("*.mp3")]
    for song in current_savelist: os.remove(os.path.join(save_directory, song))
    print('Save list cleared!')
    return

def handle_stop(res, bgm):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'stop'): return
    bgm.stop()

def handle_pause(res, bgm):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'pause'): return
    bgm.pause()

def handle_next(res, bgm):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'next'): return
    bgm.next()
    print(f'Now playing:\t{bgm.playing_songname}')

def handle_last(res, bgm):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'last'): return
    bgm.last()
    print(f'Now playing:\t{bgm.playing_songname}')

def handle_library(res, library_directory):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'library'): return
    files = [f for f in pathlib.Path(library_directory).glob("*.mp3")]
    files.sort(key=lambda f: f.stat().st_ctime)
    print('Your library (by time):')
    for i, f in enumerate(files, 1): print(f'{i}.\t{f.name}')

def handle_lookup(res, library_directory, threshold):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'lookup'): return
    try:
        parts = res.split()
        if len(parts) < 2: return
        tolookup = parts[1]
        library = [f.name.replace('.mp3','') for f in pathlib.Path(library_directory).glob("*.mp3")]
        matches = fuzzy_match_all(tolookup, library, threshold)
        if matches:
            for match in matches: print(f"{match[0]}\t\tSimilarity: {int(match[1])}%")
        else: print("No matched song found.")
    except: print('Invalid command!')

def handle_timelimit(res, timelimit, lock):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'timelimit'): return
    try:
        parts = res.split()
        if len(parts) < 2: return
        target_str = parts[1]
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])(?::([0-5][0-9]))?$'
        match = re.match(time_pattern, target_str)
        if match:
            h, m, s = match.groups(); s = int(s) if s else 0; h, m = int(h), int(m)
            now = datetime.datetime.now(); target_time = now.replace(hour=h, minute=m, second=s, microsecond=0)
            if target_time <= now: target_time += datetime.timedelta(days=1)
            target_epoch = int(target_time.timestamp())
            display_msg = f"at {target_time.strftime('%H:%M:%S')} ({target_time.strftime('%Y-%m-%d')})"
        else:
            minutes = int(target_str); target_epoch = int(time.time()) + minutes * 60
            end_time = datetime.datetime.fromtimestamp(target_epoch)
            display_msg = f"in {minutes} minute(s) (at {end_time.strftime('%H:%M:%S')})"
        with lock: timelimit[0] = target_epoch
        print(f"Time limit set! Playback will stop {display_msg}.")
    except: print('Invalid time format!')

def handle_history(res, history_manager):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'history'): return
    history_manager.print_history_summary()

def handle_current_song(res, bgm):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'current'): return
    print(f'Now playing:\t{bgm.playing_songname}')

def handle_set(res, config):
    if not _validate_flags(res, ['-h']): return
    if _check_help(res, 'set'): return
    parts = res.split()
    if len(parts) == 1 or parts[1] == 'list':
        print("\nCurrent Settings:"); [print(f"{k}: {v}") for k, v in config.items()]
        return
    if len(parts) < 3: return
    key, value_str = parts[1], " ".join(parts[2:])
    if key not in config: return
    try:
        if key == 'volume': config[key] = float(value_str)
        elif key == 'search_threshold': config[key] = int(value_str)
        else: config[key] = value_str
        if _save_settings(config): print(f"Setting '{key}' updated.")
    except: print(f"Error: Invalid value.")

def handle_common(res, config, session):
    if not _validate_flags(res, ['-l', '-a', '-d', '-h']): return
    if _check_help(res, 'common'): return
    path = config.get('common_commands_path')
    common_list = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f: common_list = json.load(f)
    parts = res.split()
    if len(parts) == 1 or '-l' in parts:
        print("\nCommon Commands:"); [print(f"{i}.\t{cmd}") for i, cmd in enumerate(common_list, 1)]
        return
    if '-a' in parts:
        idx = parts.index('-a'); new_cmd = " ".join(parts[idx+1:]).strip().strip('"').strip("'")
        if new_cmd and new_cmd not in common_list:
            common_list.append(new_cmd)
            with open(path, "w", encoding="utf-8") as f: json.dump(common_list, f, indent=4, ensure_ascii=False)
            session.history.append_string(new_cmd)
            print(f"Added common command: {new_cmd}")
        return
    if '-d' in parts:
        idx = parts.index('-d')
        try:
            indices = _parse_indices(parts[idx+1:], len(common_list))
            if not indices: return
            for i in sorted(indices, reverse=True): common_list.pop(i-1)
            with open(path, "w", encoding="utf-8") as f: json.dump(common_list, f, indent=4, ensure_ascii=False)
            print(f"Removed {len(indices)} command(s) from list.")
        except: print("Invalid index format.")

def handle_tag(res, playlist, config, tags_dict):
    """Manage song tags. Sorted by time."""
    if not _validate_flags(res, ['-l', '-a', '-d', '-h']): return tags_dict
    if _check_help(res, 'tag'): return tags_dict
    
    parts = res.split()
    if len(parts) == 1:
        stats = {}
        for song_tags in tags_dict.values():
            for t in song_tags: stats[t] = stats.get(t, 0) + 1
        if not stats: print("No tags defined.")
        else:
            print("\nAll Tags (Count):")
            for t, count in stats.items(): print(f"{t}:\t{count}")
        return tags_dict

    if parts[1] == '-l':
        all_tags = set()
        for tlist in tags_dict.values(): all_tags.update(tlist)
        if not all_tags: print("No tags defined.")
        else:
            for t in sorted(list(all_tags)):
                t_songs = [s for s in playlist if t in tags_dict.get(s, [])]
                print(f"\n[{t}]"); [print(f"{i}.\t{s}") for i, s in enumerate(t_songs, 1)]
        return tags_dict

    if parts[1] == '-a':
        if len(parts) < 4: return tags_dict
        tag_name = parts[2]
        if not _is_valid_tag(tag_name): 
            print(f"Invalid tag name: {tag_name}")
            return tags_dict
        indices = _parse_indices(parts[3:], len(playlist))
        for i in indices:
            song = playlist[i-1]
            if song not in tags_dict: tags_dict[song] = []
            if tag_name not in tags_dict[song]: tags_dict[song].append(tag_name)
        _save_tags(config, tags_dict); print(f"Added tag '{tag_name}'.")
        return tags_dict

    if parts[1] == '-d':
        if len(parts) < 3: return tags_dict
        tag_name = parts[2]
        if len(parts) == 3:
            removed_count = 0
            for song in list(tags_dict.keys()):
                if tag_name in tags_dict[song]: tags_dict[song].remove(tag_name); removed_count += 1
            print(f"Global: Tag '{tag_name}' removed from {removed_count} songs.")
        else:
            tag_songs = [s for s in playlist if tag_name in tags_dict.get(s, [])]
            indices = _parse_indices(parts[3:], len(tag_songs))
            for i in indices:
                song = tag_songs[i-1]; tags_dict[song].remove(tag_name)
            print(f"Removed tag from {len(indices)} songs.")
        _save_tags(config, tags_dict); return tags_dict

    tag_name = parts[1]
    if _is_valid_tag(tag_name):
        tag_songs = [s for s in playlist if tag_name in tags_dict.get(s, [])]
        if not tag_songs: print(f"No songs in '{tag_name}'.")
        else:
            print(f"\nSongs in Tag [{tag_name}]:")
            for i, s in enumerate(tag_songs, 1): print(f"{i}.\t{s}")
    else: print(f"Invalid tag name or command: {tag_name}")
    return tags_dict
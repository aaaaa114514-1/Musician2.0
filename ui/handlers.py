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

# Help messages for each command
CMD_HELP = {
    'quit': "Usage: quit | exit | end | :q\nFunction: Save history and exit the program.\nExample: quit",
    'check163': "Usage: check163 | :163_cache\nFunction: List all Netease Cloud Music cache (.uc) files.\nExample: check163",
    'decode': "Usage: decode <indices> | :d <indices>\nFunction: Decode selected .uc files to .mp3.\nExample: decode 1 3-5",
    'clear163': "Usage: clear163 | :163_clear\nFunction: Delete all files in the Netease cache directory.\nExample: clear163",
    'search': "Usage: search <keyword> | /s <keyword>\nFunction: Search for songs on Kugou Music.\nExample: search Taylor Swift",
    'download': "Usage: download <indices> | /d <indices>\nFunction: Download songs from the last search result.\nExample: download 1 2",
    'showlist': "Usage: showlist | :l\nFunction: Show the current playlist.\nExample: showlist",
    'play': "Usage: play [indices] [flags] | :p [indices] [flags]\nFlags: -m [s|c|r] (mode), -v [0-100] (volume), -t [min] (timer)\nFunction: Play selected songs or resume playing.\nExample: play 1-10 -m r -v 50",
    'mode': "Usage: mode <cycle|single|random> | :m <c|s|r>\nFunction: Change the playback mode.\nExample: mode random",
    'stop': "Usage: stop | :st\nFunction: Stop playback.\nExample: stop",
    'pause': "Usage: pause | :pa\nFunction: Pause the current song.\nExample: pause",
    'next': "Usage: next | :n\nFunction: Play the next song in the playlist.\nExample: next",
    'last': "Usage: last | previous | :prev\nFunction: Play the previous song in the playlist.\nExample: last",
    'restart': "Usage: restart | replay | :r\nFunction: Replay the current song from the beginning.\nExample: restart",
    'volume': "Usage: volume <0-100> | :vol <0-100>\nFunction: Set the player volume.\nExample: volume 80",
    'savelist': "Usage: savelist | :sl\nFunction: Show songs in the temporary save directory.\nExample: savelist",
    'save': "Usage: save <lis|bgm> | :s <lis|bgm>\nFunction: Move downloaded songs to 'lis' (playlist+library) or 'bgm' (library only).\nExample: save lis",
    'add': "Usage: add <indices> [flags] | :a <indices> [flags]\nFunction: Add selected songs from the full list to the current active playlist.\nExample: add 5-8 -m c",
    'clear': "Usage: clear | :cl\nFunction: Clear all songs in the temporary save directory.\nExample: clear",
    'library': "Usage: library | :lib\nFunction: List all songs in the local music library.\nExample: library",
    'lookup': "Usage: lookup <keyword> | :lu <keyword>\nFunction: Fuzzy search for songs in the local library.\nExample: lookup Love",
    'timelimit': "Usage: timelimit <minutes> | :tl <minutes>\nFunction: Set a timer to stop playback automatically.\nExample: timelimit 30",
    'history': "Usage: history | :his\nFunction: Show play counts and total time statistics.\nExample: history",
    'current': "Usage: ? | :?\nFunction: Show information about the song currently playing.\nExample: ?",
    'set': "Usage: set [list | <key> <value>]\nFunction: View or modify settings. Settings are saved to settings.json.\nExample: set list | set volume 0.5",
}

def _check_help(res, cmd_key):
    """Check if -h is in the command and print help if so."""
    if '-h' in res.split():
        print(f"\n{CMD_HELP.get(cmd_key, 'No help available.')}")
        return True
    return False

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
                    print(f'Invalid range: {part}')
                else:
                    tmp.extend(range(sta, end + 1))
            except ValueError:
                print(f'Invalid range format: {part}')
        else:
            try:
                num = int(part)
                if num < 1 or num > max_len:
                    print(f'Invalid number: {num}')
                else:
                    tmp.append(num)
            except ValueError:
                print(f'Invalid number format: {part}')
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
showlist/:l\t\tShow playlist
play/:p\t\t\tPlay/unpause
play/:p #\t\tPlay specific songs
add/:a #\t\tAdd to playlist
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
?/:?\t\t\tCurrent song
--------------------------------------------------------------------------
Tip: Add -h after any command for detailed usage and examples!
''')

def handle_quit(res, bgm, history_manager):
    if _check_help(res, 'quit'): return 1
    bgm.stop()
    history_manager.save_history()
    return 0

def handle_check163(res, cache_directory):
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
    if _check_help(res, 'clear163'): return
    for file in os.listdir(cache_directory):
        file_path = os.path.join(cache_directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    print('163music cache list cleared!')

def handle_search(res, threshold):
    if _check_help(res, 'search'): return []
    try:
        # Standardize command parsing
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

def handle_showlist(res, playlist):
    if _check_help(res, 'showlist'): return
    if len(playlist) == 0:
        print('There is no song in your playlist!')
    else:
        print('Your playlist:')
        for i, song in enumerate(playlist, 1):
            print(f'{i}.\t{song}')

def handle_play(res, bgm, playlist, mode, timelimit=None, lock=None):
    if _check_help(res, 'play'): return mode
    
    res, flags = _parse_flags(res)
    
    if 'm' in flags:
        m = flags['m']
        if m == 's': mode = 'single'; bgm.is_single = 1
        elif m == 'c': mode = 'cycle'; bgm.is_single = 0; bgm.set_playlist(playlist)
        elif m == 'r': mode = 'random'; bgm.is_single = 0
        print(f"Mode set to: {mode}")

    if 'v' in flags:
        handle_volume(f"vol {flags['v']}", bgm)

    if 't' in flags and timelimit is not None:
        handle_timelimit(f"tl {flags['t']}", timelimit, lock)

    if res in ['play', ':p']:
        bgm.unpause()
    else:
        try:
            parts = res.split()[1:]
            tmp = _parse_indices(parts, len(playlist))
            if not tmp:
                print('No valid song to play!')
            else:
                print('Start playing:')
                selected_songs = [playlist[i-1] for i in tmp]
                if mode == 'random':
                    random.shuffle(selected_songs)
                for idx, i in enumerate(tmp):
                    print(f'{i}.\t{playlist[i-1]}')
                bgm.set_playlist(selected_songs)
                if bgm.nowmode in ['stop', 'pause'] or bgm.playing_songname not in bgm.playlist:
                    bgm.stop()
                    bgm.nowplaying = 0
                    bgm.play()
        except:
            print('Invalid command!')
    return mode

def handle_mode(res, bgm, mode, playlist):
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

        if requested not in ['cycle','single','random']:
            print('Invalid mode!')
        else:
            if requested != mode or requested == 'random':
                print(f'Playing mode changed: {mode} -> {requested}!')
                mode = requested
                if mode == 'random':
                    bgm.is_single = 0
                    tmp = list(bgm.playlist)
                    random.shuffle(tmp)
                    bgm.set_playlist(tmp)
                elif mode == 'single':
                    bgm.is_single = 1
                else:
                    bgm.is_single = 0
                    bgm.set_playlist(playlist)
            else:
                print(f'Playing mode is already {mode}!')
        return mode
    except:
        print('Invalid command!')
        return mode

def handle_restart(res, bgm):
    if _check_help(res, 'restart'): return
    bgm.play()

def handle_volume(res, bgm):
    if _check_help(res, 'volume'): return
    try:
        volume = float(res.split()[1])
        if volume >= 1 and volume <= 100:
            volume = volume/100
        if 0 <= volume <= 1:
            bgm.set_volume(volume)
            print(f'Volume changed to {int(volume*100)}%!')
        else:
            print('Invalid volume!')
    except:
        print('Invalid volume!')

def handle_savelist(res, save_directory):
    if _check_help(res, 'savelist'): return
    savelist = [f.name for f in pathlib.Path(save_directory).glob("*.mp3")]
    if len(savelist) == 0:
        print('There is no song in your savelist!')
    else:
        print('Your savelist:')
        for i, song in enumerate(savelist, 1):
            print(f'{i}.\t{song}')

def handle_save(res, save_directory, play_directory, library_directory, playlist):
    if _check_help(res, 'save'): return []
    savelist = [f.name for f in pathlib.Path(save_directory).glob("*.mp3")]
    try:
        if len(savelist) == 0:
            print('There is no song in your savelist!')
        else:
            target = res.split()[1]
            if target not in ['lis','bgm']:
                print('Invalid save list!')
            else:
                if target == 'lis':
                    for song in savelist:
                        if song not in playlist:
                            shutil.copy2(os.path.join(save_directory, song), play_directory)
                            shutil.copy2(os.path.join(save_directory, song), library_directory)
                            playlist.append(song)
                        if os.path.exists(os.path.join(save_directory, song)):
                            os.remove(os.path.join(save_directory, song))
                    print('Songs moved to Lis and library!')
                else:
                    for song in savelist:
                        shutil.copy2(os.path.join(save_directory, song), library_directory)
                        os.remove(os.path.join(save_directory, song))
                    print('Songs moved to library!')
    except:
        print('Invalid command!')
    return []

def handle_add(res, bgm, playlist, mode):
    if _check_help(res, 'add'): return mode
    res, flags = _parse_flags(res)
    if 'm' in flags:
        m = flags['m']
        if m == 's': mode = 'single'; bgm.is_single = 1
        elif m == 'c': mode = 'cycle'; bgm.is_single = 0
        elif m == 'r': mode = 'random'; bgm.is_single = 0
        print(f"Mode set to: {mode}")

    try:
        parts = res.split()[1:]
        tmp = _parse_indices(parts, len(playlist))
        if not tmp:
            print('No valid song to add!')
        else:
            print('Added songs:')
            for i in tmp:
                print(f'{i}.\t{playlist[i-1]}')
            selected_songs = [playlist[i-1] for i in tmp]
            if mode == 'random':
                random.shuffle(selected_songs)
            bgm.add_playlist(selected_songs)
            if bgm.nowmode in ['stop', 'pause'] or bgm.playing_songname not in bgm.playlist:
                bgm.stop()
                bgm.nowplaying = 0
                bgm.play()
    except:
        print('Invalid command!')
    return mode

def handle_clear(res, save_directory):
    if _check_help(res, 'clear'): return []
    current_savelist = [f.name for f in pathlib.Path(save_directory).glob("*.mp3")]
    for song in current_savelist:
        os.remove(os.path.join(save_directory, song))
    print('Save list cleared!')
    return []

def handle_stop(res, bgm):
    if _check_help(res, 'stop'): return
    bgm.stop()

def handle_pause(res, bgm):
    if _check_help(res, 'pause'): return
    bgm.pause()

def handle_next(res, bgm):
    if _check_help(res, 'next'): return
    bgm.next()
    print(f'Now playing:\t{bgm.playing_songname}')

def handle_last(res, bgm):
    if _check_help(res, 'last'): return
    bgm.last()
    print(f'Now playing:\t{bgm.playing_songname}')

def handle_library(res, library_directory):
    if _check_help(res, 'library'): return
    library_files = [f for f in pathlib.Path(library_directory).glob("*.mp3")]
    print('Your library:')
    for i, song in enumerate(library_files, 1):
        print(f'{i}.\t{song.name}')

def handle_lookup(res, library_directory, threshold):
    if _check_help(res, 'lookup'): return
    try:
        parts = res.split()
        if len(parts) < 2:
            print("Please provide a keyword to lookup.")
            return
        tolookup = parts[1]
        library = [f.name.replace('.mp3','') for f in pathlib.Path(library_directory).glob("*.mp3")]
        matches = fuzzy_match_all(tolookup, library, threshold)
        if matches:
            for match in matches:
                print(f"{match[0]}\t\tSimilarity: {int(match[1])}%")
        else:
            print("No matched song found.")
    except:
        print('Invalid command!')

def handle_timelimit(res, timelimit, lock):
    if _check_help(res, 'timelimit'): return
    try:
        timelimit_tmp = int(res.split()[1])
        if timelimit_tmp > 0:
            with lock:
                timelimit[0] = timelimit_tmp*60 + int(time.time())
            print(f'Set time limit to {timelimit_tmp} minute(s).')
            newtime = datetime.datetime.now() + datetime.timedelta(minutes=timelimit_tmp)
            print(f"Keep playing until {newtime.strftime('%H')}:{newtime.strftime('%M')}:{newtime.strftime('%S')}.")
        else:
            print('Invalid time limit!')
    except:
        print('Invalid time limit!')

def handle_history(res, history_manager):
    if _check_help(res, 'history'): return
    history_manager.print_history_summary()

def handle_current_song(res, bgm):
    if _check_help(res, 'current'): return
    print(f'Now playing:\t{bgm.playing_songname}')

def handle_set(res, config):
    """Handle viewing and changing settings."""
    if _check_help(res, 'set'): return

    parts = res.split()
    if len(parts) == 1 or parts[1] == 'list':
        print("\nCurrent Settings:")
        for key, value in config.items():
            print(f"{key}: {value}")
        return

    if len(parts) < 3:
        print("Invalid set command. Use 'set list' or 'set <key> <value>'.")
        return

    key = parts[1]
    value_str = " ".join(parts[2:])

    if key not in config:
        print(f"Error: Setting '{key}' does not exist.")
        return

    # Validation and type conversion
    try:
        if key == 'volume':
            val = float(value_str)
            if not (0 <= val <= 1): raise ValueError
            config[key] = val
        elif key == 'search_threshold':
            val = int(value_str)
            if not (0 <= val <= 100): raise ValueError
            config[key] = val
        elif key in ['netease_cache', 'download_dir', 'temp_dir', 'play_dir', 'library_dir']:
            if not os.path.exists(value_str):
                print(f"Warning: Path '{value_str}' does not exist on this machine.")
            config[key] = value_str
        else:
            # Token and other strings
            config[key] = value_str
        
        if _save_settings(config):
            print(f"Setting '{key}' updated successfully and saved to settings.json.")
        
    except ValueError:
        print(f"Error: Invalid value for '{key}'. Please check the type/range.")
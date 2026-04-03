'''
Handle kugou music
'''

import time
import json
import hashlib
import requests
import os
from utils.file_utils import sanitize_filename

def signature_generator_1(song_id, s_time, token2):
    str_1 = f"NVPh5oo715z5DIWAeQlhMDsWXXQV4hwtappid=1014clienttime={s_time}clientver=20000dfid=11RUG41l0SmY4ZVgnP0fnD0eencode_album_audio_id={song_id}mid=3bbc1d969ff662635c996e5f73d0a7e1platid=4srcappid=2919token=cc953c223e1dcc686b2dfc1a2465e6de{token2}userid=1501763160uuid=3bbc1d969ff662635c996e5f73d0a7e1NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"
    hashobj = hashlib.md5(str_1.encode("utf-8"))
    return hashobj.hexdigest()

def signature_generator_2(keyword, s_time):
    str_1 = f"NVPh5oo715z5DIWAeQlhMDsWXXQV4hwtappid=1014bitrate=0callback=callback123clienttime={s_time}clientver=1000dfid=1txHuC3KMsDa1MoTkF1HWQUXfilter=10inputtype=0iscorrection=1isfuzzy=0keyword={keyword}mid=5c8dee1cc08f313b60b807d8da2d5fddpage=1pagesize=30platform=WebFilterprivilege_filter=0srcappid=2919token=userid=0uuid=5c8dee1cc08f313b60b807d8da2d5fddNVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"
    hashobj = hashlib.md5(str_1.encode("utf-8"))
    return hashobj.hexdigest()

def kugou_getlist(Keyword):
    Headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    clienttime = str(round(time.time() * 1000))
    signature = signature_generator_2(Keyword, clienttime)
    request_url = f'https://complexsearch.kugou.com/v2/search/song?callback=callback123&srcappid=2919&clientver=1000&clienttime={clienttime}&mid=5c8dee1cc08f313b60b807d8da2d5fdd&uuid=5c8dee1cc08f313b60b807d8da2d5fdd&dfid=1txHuC3KMsDa1MoTkF1HWQUX&keyword={Keyword}&page=1&pagesize=30&bitrate=0&isfuzzy=0&inputtype=0&platform=WebFilter&userid=0&iscorrection=1&privilege_filter=0&filter=10&token=&appid=1014&signature={signature}'
    resp = requests.get(request_url, headers=Headers)
    if resp.text != '':
        resp_js = resp.text[12:(len(resp.text) -2)]
        songlist_dict = json.loads(resp_js)
        if songlist_dict['status'] == 1:
            songlist = songlist_dict['data']['lists']
            file_list = []
            for i in songlist:
                if i['PayType'] != 0:
                    file_list.append([i['FileName'],i['EMixSongID'],'【VIP】'])
                else:
                    file_list.append([i['FileName'],i['EMixSongID'],''])
            return file_list
    return 0

def kugou_download(file_list, inp, savepath, token2):
    encode_album_audio_id = file_list[inp - 1][1]
    clienttime = str(round(time.time() * 1000))
    signature = signature_generator_1(encode_album_audio_id, clienttime, token2)
    Headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    request_url = f'https://wwwapi.kugou.com/play/songinfo?srcappid=2919&clientver=20000&clienttime={clienttime}&mid=3bbc1d969ff662635c996e5f73d0a7e1&uuid=3bbc1d969ff662635c996e5f73d0a7e1&dfid=11RUG41l0SmY4ZVgnP0fnD0e&appid=1014&platid=4&encode_album_audio_id={encode_album_audio_id}&token=cc953c223e1dcc686b2dfc1a2465e6de{token2}&userid=1501763160&signature={signature}'
    resp = requests.get(request_url, headers=Headers)
    if resp.text != '':
        songinfo_dict = json.loads(resp.text)
        if songinfo_dict['status'] == 1:
            play_url = songinfo_dict['data']['play_url']
            song_resp = requests.get(play_url, headers=Headers)
            file_name = sanitize_filename(file_list[inp - 1][0])
            with open(os.path.join(savepath, f'{file_name}.mp3'), 'wb') as f:
                f.write(song_resp.content)
                return 1
    return 0
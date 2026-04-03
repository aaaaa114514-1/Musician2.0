'''
Handle netease 163 music
'''

import requests
import re
import os
from bs4 import BeautifulSoup
from utils.file_utils import sanitize_filename, convert_to_mp3

def get_name(songid):
    Headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    request_url = f'https://music.163.com/song?id={songid}'
    try:
        resp = requests.get(request_url, headers=Headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        match = re.search(f'{"data-res-name="}(.*?){"data-res-pic="}', str(soup))
        if match:
            name = match.group(1).replace('\"', '')
            return name
        else:
            return 'Unknown'
    except:
        return 'NE'

def uc_decode(filename:str, savepath:str, temppath:str):
    with open(filename, 'rb') as f:
        data = f.read()

    databyte = bytearray(data)
    for i in range(len(databyte)):
        databyte[i] ^= 163
    
    # 提取ID
    song_id = filename.split('\\')[-1].split('-')[0]
    raw_name = get_name(song_id)
    song_name = sanitize_filename(str(raw_name))
    
    temp_mp3 = os.path.join(temppath, song_name + '.mp3')
    final_mp3 = os.path.join(savepath, song_name + '.mp3')
    
    with open(temp_mp3, 'wb') as f:
        f.write(bytes(databyte))
    
    convert_to_mp3(temp_mp3, final_mp3)
    os.remove(temp_mp3)
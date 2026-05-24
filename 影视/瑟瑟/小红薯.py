# -*- coding: utf-8 -*-
# @name 小红书（手机端图片解密专用）
# @version 1.0.0
import json
import random
import string
import time
import requests
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Hash import MD5
from Crypto.Util.Padding import unpad
from spider_runner import OmniBox, run

# ==================== 原版配置（不动） ====================
hs = ['fhoumpjjih', 'dyfcbkggxn', 'rggwiyhqtg', 'bpbbmplfxc']

def md5(text):
    h = MD5.new()
    h.update(text.encode('utf-8'))
    return h.hexdigest()

def aes(word):
    key = b64decode("SmhiR2NpT2lKSVV6STFOaQ==")
    iv = key
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(b64decode(word)), AES.block_size)
    return json.loads(decrypted.decode('utf-8'))

def dtim(seconds):
    try:
        seconds = int(seconds)
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"
    except:
        return ""

def getdid():
    return md5(str(int(time.time())))

def getsign():
    t = str(int(time.time() * 1000))
    return md5(t[3:8]), t

# 全局只初始化一次（解决播放5秒）
did = getdid()
token, host, phost = "", "", ""

def init_token():
    global token, host, phost
    if token:
        return
    for i in range(len(hs)):
        try:
            domain = f"https://{''.join(random.choices(string.ascii_lowercase+string.digits,k=5))}.{hs[i]}.work"
            sign, t = getsign()
            headers = {
                'deviceid': did,
                't': t,
                's': sign,
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; M2012K10C Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36;SuiRui/xhs/ver=1.2.6',
            }
            data = {'deviceId': did, 'tt': 'U', 'chCode': 'dafe13'}
            res = requests.post(f"{domain}/api/user/traveler", json=data, headers=headers, timeout=3)
            d = res.json()['data']
            token = d['token']
            host = domain
            phost = d['imgDomain']
            return
        except:
            continue

def headers():
    sign, t = getsign()
    return {
        'deviceid': did,
        't': t,
        's': sign,
        'aut': token
    }

# ==================== 标准接口 ====================
async def home(params, context):
    init_token()
    try:
        res = requests.get(f"{host}/api/video/queryClassifyList?mark=4", headers=headers())
        data = aes(res.json()['encData'])
        classes = [{"type_id": str(x['classifyId']), "type_name": x['classifyTitle']} for x in data['data']]
        return {"class": classes, "list": []}
    except:
        return {"class": [], "list": []}

async def category(params, context):
    init_token()
    tid = params.get("categoryId", "")
    pg = params.get("page", 1)
    try:
        url = f"{host}/api/short/video/getShortVideos?classifyId={tid}&videoMark=4&page={pg}&pageSize=20"
        res = requests.get(url, headers=headers())
        data = aes(res.json()['encData'])
        videos = []
        for x in data['data']:
            videos.append({
                "vod_id": str(x['videoId']),
                "vod_name": x.get('title'),
                "vod_pic": x['coverImg'],  # ✅ 原样返回，手机端解密
                "type_id": tid,
                "vod_remarks": dtim(x.get('playTime')),
                "style": {"type": "rect", "ratio": 1.33}
            })
        return {"page": int(pg), "pagecount": 999, "total": 99999, "list": videos}
    except:
        return {"list": []}

async def detail(params, context):
    init_token()
    vid = params.get("videoId")
    try:
        res = requests.get(f"{host}/api/video/getVideoById?videoId={vid}", headers=headers())
        v = aes(res.json()['encData'])
        playId = f'auth_key={v["authKey"]}&path={v["videoUrl"]}'
        return {
            "list": [{
                "vod_id": vid,
                "vod_name": v["title"],
                "vod_pic": v["coverImg"],  # ✅ 原样返回
                "vod_play_sources": [{"name": "官方", "episodes": [{"name": "播放", "playId": playId}]}]
            }]
        }
    except:
        return {"list": []}

async def play(params, context):
    init_token()
    playId = params.get("playId")
    h = headers()
    h['Authorization'] = h.pop('aut')
    del h['deviceid']
    return {
        "urls": [{"name": "高清", "url": f"{host}/api/m3u8/decode/authPath?{playId}"}],
        "header": h,
        "parse": 0
    }

async def search(params, context):
    return {"list": []}

if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "play": play,
        "search": search
    })

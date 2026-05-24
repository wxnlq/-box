# -*- coding: utf-8 -*-
# @name 黄色仓库
# @version 1.0.0

import re
import urllib.parse
import requests
import base64
import json
from pyquery import PyQuery as pq
from spider_runner import OmniBox, run

# 全局配置
header = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Referer": "https://hsck123.com/"
}

# ====================== 工具函数 ======================
def getDynamicHost():
    try:
        initial_host = base64.b64decode('aHR0cDovL2hzY2submV0').decode('utf-8')
        response = requests.get(initial_host, headers=header, timeout=8)
        html = response.text
        strU_match = re.search(r'strU="(.*?)"', html)
        if not strU_match:
            return initial_host
        strU = strU_match.group(1)
        locationU = strU + initial_host.rstrip('/') + '/&p=/'
        redirect_response = requests.get(locationU, headers=header, allow_redirects=False, timeout=8)
        if 'location' in redirect_response.headers:
            return redirect_response.headers['location']
        try:
            data = redirect_response.json()
            return data.get('location', initial_host)
        except:
            return initial_host
    except:
        return "http://1755ck.cc/"

host = getDynamicHost()

def getFullUrl(url):
    if not url:
        return ""
    if url.startswith('http'):
        return url
    if url.startswith('//'):
        return f"https:{url}"
    return f"{host.rstrip('/')}{url}"

def extractM3U8Url(script_text):
    m3u8_urls = []
    player_patterns = [
        r'var\s+player_aaaa\s*=\s*({.*?});',
        r'player_aaaa\s*=\s*({.*?});'
    ]
    for pattern in player_patterns:
        player_match = re.search(pattern, script_text, re.DOTALL)
        if player_match:
            try:
                data = json.loads(player_match.group(1).replace('\\/', '/'))
                url = data.get('url')
                if url and '.m3u8' in url:
                    if not url.startswith('http'):
                        url = 'https:'+url if url.startswith('//') else getFullUrl(url)
                    m3u8_urls.append(url)
                    return m3u8_urls
            except:
                pass
    patterns = [r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*']
    for p in patterns:
        matches = re.findall(p, script_text)
        for m in matches:
            if '.m3u8' in m:
                m = 'https:'+m if m.startswith('//') else getFullUrl(m)
                m3u8_urls.append(m)
                return m3u8_urls
    return m3u8_urls

# ====================== 首页 ======================
async def home(params, context):
    await OmniBox.log("info", "加载黄色仓库")
    classes = [{"type_name": "日韩AV", "type_id": "1"},
            {"type_name": "国产系列", "type_id": "2"}, 
            {"type_name": "欧美", "type_id": "3"},
            {"type_name": "成人动漫", "type_id": "4"},
            {"type_name": "日本有码", "type_id": "7"},
            {"type_name": "一本道高清无码", "type_id": "8"},
            {"type_name": "有码中文字幕", "type_id": "9"},
            {"type_name": "日本无码", "type_id": "10"},
            {"type_name": "国产视频", "type_id": "15"},
            {"type_name": "欧美高清", "type_id": "21"},
            {"type_name": "动漫剧情", "type_id": "22"}
    ]
    try:
        url = f"{host.rstrip('/')}/"
        rsp = requests.get(url, headers=header, timeout=10)
        root = pq(rsp.text)
        videos = []
        for item in root('.stui-vodlist li').items():
            vid = item.find('a').attr('href')
            if not vid or not vid.startswith('/vodplay/'):
                continue
            name = item.find('h4').text()
            img = item.find('a').attr('data-original')
            remark = item.find('.pic-text').text()
            if name and img:
                videos.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": getFullUrl(img),
                    "type_id": "", "type_name": "",
                    "vod_remarks": remark,
                    "vod_year": "", "vod_douban_score": ""
                })
        return {"class": classes, "list": videos}
    except:
        return {"class": classes, "list": []}

# ====================== 分类 ======================
async def category(params, context):
    tid = params.get("categoryId", "1")
    pg = params.get("page", 1)
    try:
        url = f"{host.rstrip('/')}/vodtype/{tid}-{pg}.html"
        rsp = requests.get(url, headers=header, timeout=10)
        root = pq(rsp.text)
        videos = []
        for item in root('.stui-vodlist li').items():
            vid = item.find('a').attr('href')
            if not vid or not vid.startswith('/vodplay/'):
                continue
            name = item.find('h4').text()
            img = item.find('a').attr('data-original')
            remark = item.find('.pic-text').text()
            if name and img:
                videos.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": getFullUrl(img),
                    "type_id": "", "type_name": "",
                    "vod_remarks": remark,
                    "vod_year": "", "vod_douban_score": ""
                })
        return {
            "page": int(pg),
            "pagecount": 9999,
            "total": 999999,
            "list": videos
        }
    except:
        return {"page": 1, "pagecount": 1, "total": 0, "list": []}

# ====================== 详情（新版标准格式） ======================
async def detail(params, context):
    vid = params.get("videoId", "")
    if not vid:
        return {"list": []}
    url = getFullUrl(vid)
    try:
        rsp = requests.get(url, headers=header, timeout=10)
        root = pq(rsp.text)
        title = root('.stui-pannel__head .title').text() or root('title').text().split(' - ')[0]
        pic = root('.stui-vodlist__thumb').attr('data-original') or root('.stui-vodlist__thumb').attr('src')
        pic = getFullUrl(pic)
        m3u8 = extractM3U8Url(rsp.text)
        episodes = []
        if m3u8:
            for i, u in enumerate(m3u8):
                episodes.append({"name": f"线路{i+1}", "playId": u})
        else:
            episodes.append({"name": "默认", "playId": url})
        return {
            "list": [{
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_content": title,
                "vod_year": "", "vod_remarks": "",
                "vod_douban_score": "", "vod_actor": "",
                "vod_director": "", "vod_area": "",
                "vod_play_sources": [{
                    "name": "黄色仓库",
                    "episodes": episodes
                }]
            }]
        }
    except:
        return {"list": []}

# ====================== 搜索 ======================
async def search(params, context):
    key = (params.get("keyword") or params.get("wd") or "").strip()
    if not key:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}
    try:
        url = f"{host.rstrip('/')}/vodsearch/-------------.html?wd={urllib.parse.quote(key)}"
        rsp = requests.get(url, headers=header, timeout=10)
        root = pq(rsp.text)
        videos = []
        for item in root('.stui-vodlist li').items():
            vid = item.find('a').attr('href')
            if not vid or not vid.startswith('/vodplay/'):
                continue
            name = item.find('h4').text()
            img = item.find('a').attr('data-original')
            if name and img:
                videos.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": getFullUrl(img),
                    "type_id": "", "type_name": "",
                    "vod_remarks": item.find('.pic-text').text(),
                    "vod_year": "", "vod_douban_score": ""
                })
        return {"page": 1, "pagecount": 1, "total": len(videos), "list": videos}
    except:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

# ====================== 播放 ======================
async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")
    if ".m3u8" in play_id:
        return {
            "urls": [{"name": "播放", "url": play_id}],
            "flag": "play",
            "header": header,
            "parse": 0
        }
    return {
        "urls": [{"name": "播放", "url": play_id}],
        "flag": "play",
        "header": header,
        "parse": 1
    }

# ====================== 启动 ======================
if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })

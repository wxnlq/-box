# -*- coding: utf-8 -*-
# @name 911爆料网
# @version 1.0.0

import sys
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time
from spider_runner import OmniBox, run

# 全局配置
xurl = "https://barely.vmwzzqom.cc/"
backup_urls = ["https://hlj.fun", "https://911bl16.com"]
headerx = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
    "Referer": "https://911blw.com",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
}
IMAGE_FILTER = ["/usr/themes/ads-close.png", "close", "icon", "logo"]

# ====================== 工具函数（完全保留） ======================
def fetch_page(url, use_backup=False):
    global xurl
    original_url = url
    if use_backup:
        for backup in backup_urls:
            test_url = url.replace(xurl, backup)
            try:
                time.sleep(1)
                res = requests.get(test_url, headers=headerx, timeout=10)
                res.raise_for_status()
                res.encoding = "utf-8"
                text = res.text
                if len(text) > 1000:
                    return text
            except:
                continue
    try:
        time.sleep(1)
        res = requests.get(original_url, headers=headerx, timeout=10)
        res.raise_for_status()
        res.encoding = "utf-8"
        text = res.text
        if len(text) < 1000:
            return fetch_page(original_url, use_backup=True)
        return text
    except Exception as e:
        return None

def extract_content(html, url):
    videos = []
    if not html:
        return videos
    doc = BeautifulSoup(html, "html.parser")
    containers = doc.select("ul.row li, div.article-item, article, .post-item, div[class*='item']")
    for i, vod in enumerate(containers[:20], 1):
        try:
            title_elem = vod.select_one("h2.headline, .headline, a[title]")
            name = title_elem.get("title") or title_elem.get_text(strip=True) if title_elem else ""
            if not name:
                name_match = re.search(r'headline">(.+?)<', str(vod))
                name = name_match.group(1).strip() if name_match else ""
            link_elem = vod.select_one("a")
            vid = urljoin(xurl, link_elem["href"]) if link_elem else ""
            remarks_elem = vod.select_one("span.small, time, .date")
            remarks = remarks_elem.get_text(strip=True) if remarks_elem else ""
            if not remarks:
                remarks_match = re.search(r'datePublished[^>]*>(.+?)<', str(vod))
                remarks = remarks_match.group(1).strip() if remarks_match else ""
            img = vod.select_one("img")
            pic = None
            if img:
                for attr in ["data-lazy-src", "data-original", "data-src", "src"]:
                    pic = img.get(attr)
                    if pic:
                        break
                if not pic:
                    bg_div = vod.select_one("div[style*='background-image']")
                    if bg_div and "background-image" in bg_div.get("style", ""):
                        bg_match = re.search(r'url\([\'"]?(.+?)[\'"]?\)', bg_div["style"])
                        pic = bg_match.group(1) if bg_match else None
                if pic:
                    pic = urljoin(xurl, pic)
                    alt = img.get("alt", "").lower() if img else ""
                    if any(f in pic.lower() or f in alt for f in IMAGE_FILTER):
                        pic = None
            desc_match = re.search(r'og:description" content="(.+?)"', html)
            description = desc_match.group(1) if desc_match else ""
            if name and vid:
                videos.append({
                    "vod_id": vid,
                    "vod_name": name[:100],
                    "vod_pic": pic,
                    "type_id": "",
                    "type_name": "",
                    "vod_remarks": remarks,
                    "vod_year": "",
                    "vod_douban_score": ""
                })
        except:
            continue
    return videos

# ====================== 首页 ======================
async def home(params, context):
    await OmniBox.log("info", "加载 911爆料网")
    try:
        categories = [{"type_id": "/category/jrgb/", "type_name": "最新爆料"},
                      {"type_id": "/category/rmgb/", "type_name": "精选大瓜"},
                      {"type_id": "/category/blqw/", "type_name": "猎奇吃瓜"},
                      {"type_id": "/category/rlph/", "type_name": "TOP5大瓜"},
                      {"type_id": "/category/ssdbl/", "type_name": "社会热点"},
                      {"type_id": "/category/hjsq/", "type_name": "海角社区"},
                      {"type_id": "/category/mrds/", "type_name": "每日大赛"},
                      {"type_id": "/category/xyss/", "type_name": "校园吃瓜"},
                      {"type_id": "/category/mxhl/", "type_name": "明星吃瓜"},
                      {"type_id": "/category/whbl/", "type_name": "网红爆料"},
                      {"type_id": "/category/bgzq/", "type_name": "反差爆料"},
                      {"type_id": "/category/fljq/", "type_name": "网黄福利"},
                      {"type_id": "/category/crfys/", "type_name": "午夜剧场"},
                      {"type_id": "/category/thjx/", "type_name": "探花经典"},
                      {"type_id": "/category/dmhv/", "type_name": "禁漫天堂"},
                      {"type_id": "/category/slec/", "type_name": "吃瓜精选"},
                      {"type_id": "/category/zksr/", "type_name": "重口调教"},
                      {"type_id": "/category/crlz/", "type_name": "精选连载"}]
        url = f"{xurl}/category/jrgb/1/"
        html = fetch_page(url)
        videos = extract_content(html, url)
        return {"class": categories, "list": videos}
    except:
        return {"class": [], "list": []}

# ====================== 分类 ======================
async def category(params, context):
    category_id = params.get("categoryId") or ""
    page = params.get("page") or "1"
    try:
        url = f"{xurl}{category_id}{page}/" if page != "1" else f"{xurl}{category_id}"
        html = fetch_page(url)
        videos = extract_content(html, url)
        return {
            "page": int(page),
            "pagecount": 9999,
            "total": 999999,
            "list": videos
        }
    except:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

# ====================== 详情 ======================
async def detail(params, context):
    video_id = params.get("videoId")
    if not video_id:
        return {"list": []}
    try:
        html = fetch_page(video_id)
        purl = ""
        content = ""
        if html:
            source_match = re.search(r'"url":"(.*?)"', html)
            purl = source_match.group(1).replace("\\", "") if source_match else ""
            cont_match = re.search(r'og:description" content="(.+?)"', html)
            content = cont_match.group(1) if cont_match else ""
        
        episodes = []
        if purl:
            episodes.append({"name": "播放", "playId": purl})

        return {
            "list": [{
                "vod_id": video_id,
                "vod_name": "",
                "vod_pic": "",
                "vod_content": content,
                "vod_year": "",
                "vod_remarks": "",
                "vod_douban_score": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_area": "",
                "vod_play_sources": [{
                    "name": "爆料",
                    "episodes": episodes
                }]
            }]
        }
    except:
        return {"list": []}

# ====================== 搜索 ======================
async def search(params, context):
    keyword = (params.get("keyword") or params.get("wd") or "").strip()
    page = params.get("page") or "1"
    if not keyword:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}
    try:
        url = f"{xurl}/search/{keyword}/{page}/"
        html = fetch_page(url)
        videos = extract_content(html, url)
        return {
            "page": int(page),
            "pagecount": 9999,
            "total": 999999,
            "list": videos
        }
    except:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

# ====================== 播放 ======================
async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")
    return {
        "urls": [{"name": "播放", "url": play_id}],
        "flag": "play",
        "header": headerx,
        "parse": 0
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
    

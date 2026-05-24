# -*- coding: utf-8 -*-
# @name MOTV
# @version 1.0.0
import json
import re
import base64
from urllib.parse import urljoin
import requests
from pyquery import PyQuery as pq
from spider_runner import OmniBox, run

HOST = base64.b64decode("aHR0cHM6Ly9tb3R2LmFwcA==").decode()
HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; SM-G975F Build/QP1A.190711.020) okhttp/5.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": HOST
}

def b64e(s):
    return base64.b64encode(s.encode()).decode()

def b64d(s):
    return base64.b64decode(s).decode()

# 安全获取页面
def get_html(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "utf-8"
        return resp.text
    except:
        return ""

# 安全 PyQuery
def get_pq(html):
    try:
        if not html or len(html) < 100:
            return pq("<div></div>")
        return pq(html)
    except:
        return pq("<div></div>")

# ------------------------------
# home 首页（真实解析）
# ------------------------------
async def home(params, context):
    await OmniBox.log("info", "加载首页")
    html = get_html(HOST + "/label/new/")
    doc = get_pq(html)
    vlist = []

    for item in doc(".movie-list-item").items():
        try:
            name = item(".movie-title").text().strip()
            url = item("a").attr("href")
            if not name or not url:
                continue

            pic = item(".movie-post-lazyload").attr("data-original")
            if not pic:
                style = item(".movie-post-lazyload").attr("style") or ""
                m = re.search(r"url\('([^']+)'\)", style)
                pic = m.group(1) if m else item(".movie-post-lazyload").attr("src")

            if pic:
                if pic.startswith("//"):
                    pic = "https:" + pic
                elif not pic.startswith("http"):
                    pic = urljoin(HOST, pic)

            remark = f"评分:{item('.movie-rating').text().strip()}" if item(".movie-rating").text() else ""
            if not url.startswith("http"):
                url = HOST + url

            vlist.append({
                "vod_id": b64e(url),
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        except Exception as e:
            continue

    return {
        "class": [
            {"type_id": "vodshow/51", "type_name": "精选HD日本破解无码"},
            {"type_id": "vodshow/52", "type_name": "精选HD欧美质量爽片"},
            {"type_id": "vodshow/50", "type_name": "日本无码"},
            {"type_id": "vodshow/25", "type_name": "欧美风情"},
            {"type_id": "vodshow/41", "type_name": "国产原创"}
        ],
        "list": vlist
    }

# ------------------------------
# category 分类
# ------------------------------
async def category(params, context):
    tid = params.get("tid", "vodshow/51")
    pg = params.get("pg", "1")
    extend = params.get("extend", {})
    by = extend.get("by", "")
    cls = extend.get("class", "")

    url = f"{HOST}/{tid}--{by}-{cls}-----{pg}---/"
    html = get_html(url)
    doc = get_pq(html)
    vlist = []

    for item in doc(".movie-list-item").items():
        try:
            name = item(".movie-title").text().strip()
            url = item("a").attr("href")
            if not name or not url: continue
            pic = item(".movie-post-lazyload").attr("data-original")
            if not url.startswith("http"):
                url = HOST + url
            vlist.append({
                "vod_id": b64e(url),
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": f"评分:{item('.movie-rating').text().strip()}" if item(".movie-rating").text() else ""
            })
        except:
            continue

    return {
        "page": pg,
        "pagecount": 9999,
        "total": 999999,
        "list": vlist
    }

# ------------------------------
# detail 详情
# ------------------------------
async def detail(params, context):
    vod_id = params.get("ids", [""])[0]
    detail_url = b64d(vod_id)
    html = get_html(detail_url)
    doc = get_pq(html)

    title = doc("h1").text().strip() or "未知影片"
    actors = [a.text().strip() for a in doc(".starLink a").items()]
    actor_str = " ".join(actors)
    play_from = []
    play_url = []

    if doc(".play_source_tab .titleName"):
        play_from.append("MOTV")
        eps = []
        for e in doc("#tagContent .play_list_box li").items():
            u = e("a").attr("href")
            n = e("a").text().strip()
            if u:
                eps.append(f"{n}${b64e(HOST + u)}")
        play_url.append("#".join(eps))
    else:
        play_from = ["MOTV"]
        eps = []
        for e in doc(".play_list_box li").items():
            u = e("a").attr("href")
            n = e("a").text().strip()
            if u:
                eps.append(f"{n}${b64e(HOST + u)}")
        play_url.append("#".join(eps))

    if not play_from:
        play_from = ["MOTV"]
        play_url = [f"第1集${b64e(detail_url)}"]

    return {
        "list": [{
            "vod_name": title,
            "vod_actor": actor_str,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url)
        }]
    }

# ------------------------------
# search 搜索
# ------------------------------
async def search(params, context):
    key = params.get("key", "")
    pg = params.get("pg", "1")
    if not key:
        return {"page": pg, "list": []}

    try:
        resp = requests.get(f"https://motv.app/index.php/ajax/suggest?mid=1&wd={key}", headers=HEADERS, timeout=10)
        data = resp.json()
    except:
        return {"page": pg, "list": []}

    vlist = []
    for item in data.get("list", []):
        vurl = f"https://motv.app/vodplay/{item['id']}-1-1/"
        vlist.append({
            "vod_id": b64e(vurl),
            "vod_name": item.get("name", ""),
            "vod_pic": item.get("pic", ""),
            "vod_remarks": ""
        })
    return {"page": pg, "list": vlist}

# ------------------------------
# play 播放解析
# ------------------------------
async def play(params, context):
    pid = params.get("id", "")
    play_url = b64d(pid)
    html = get_html(play_url)
    real_url = ""

    m = re.search(r"var\s+player_.+?=\s*(\{.*?\});", html, re.S)
    if m:
        try:
            real_url = json.loads(m.group(1)).get("url", "")
        except:
            m2 = re.search(r'"url":"([^"]+)"', m.group(1))
            real_url = m2.group(1) if m2 else ""

    if not real_url:
        m3 = re.search(r"https?://.+\.(m3u8|mp4)", html)
        real_url = m3.group(0) if m3 else play_url

    real_url = real_url.replace("\\/", "/")
    if real_url.startswith("//"):
        real_url = "https:" + real_url

    return {
        "urls": [real_url],
        "flag": "MOTV",
        "header": {
            "User-Agent": HEADERS["User-Agent"],
            "Referer": play_url,
            "Origin": HOST
        },
        "parse": 0
    }

if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })

#!/usr/bin/env python3
"""
Fetch detail pages and extract: project owner + contract price.

Two-step process:
  1. getDetailPath: resolve /jump.html → real HTML path
  2. Fetch real page and parse with regex

Extraction patterns (with html.unescape before regex):
  Owner:   项目业主为XXX  or  项目业主XXX（无"为"）
  Price:   合同估算价[：:]XXX万元  or  工程合同估算价（万元）[：:]XXX

Input:  JSON list from fetch_list.py (with infoid, title1, postdate)
Output: JSON array with {title, postdate, owner, price_wan, detail_url}

Usage:
  cat list.json | python3 fetch_details.py [--timeout 30]
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import html
import sys
import time

BASE = "https://ggzy.suzhou.gov.cn"
SITEGUID = "7eb5f7f1-9041-43ad-8e13-8fcb82ea831a"

def http_get(url, params=None, timeout=30):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None

def get_real_path(infoid, categorynum="003001001"):
    """Resolve /jump.html -> real path via getDetailPath API."""
    for _ in range(3):
        body = http_get(f"{BASE}/EpointWebBuilder/JyxxSearchAction.action", params={
            "cmd": "getDetailPath",
            "categorynum": categorynum,
            "infoid": infoid,
            "siteguid": SITEGUID,
            "pageIndex": "0",
        }, timeout=30)
        if body:
            try:
                return json.loads(body).get("custom")
            except:
                pass
        time.sleep(2)
    return None

def extract(html_text):
    """Extract owner and price (万元) from detail page HTML."""
    if not html_text:
        return None, None
    # CRITICAL: unescape &nbsp; and other HTML entities BEFORE stripping tags
    text = html.unescape(html_text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    # Owner: try "项目业主为XXX" first, then "项目业主XXX"
    owner = None
    m = re.search(r"项目业主\s*为\s*([^，,。；;]+?)\s*[，,。；;]", text)
    if m:
        owner = m.group(1).strip()
    else:
        m = re.search(r"项目业主\s*([^为，,。；;]+?)\s*[，,。；;]", text)
        if m:
            owner = m.group(1).strip()

    # Price: try "合同估算价：XXX万元", then "工程合同估算价（万元）：XXX"
    price_wan = None
    m = re.search(r"合同估算价[：:][^0-9]*(\d+(?:\.\d+)?)\s*万元", text)
    if m:
        price_wan = float(m.group(1))
    else:
        m = re.search(r"工程合同估算价[（(]万元[）)]\s*[：:]\s*(\d+(?:\.\d+)?)", text)
        if m:
            price_wan = float(m.group(1))

    return owner, price_wan

def main():
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else data.get("items", [])

    results = []
    for it in items:
        infoid = it["infoid"]
        title = it.get("title1") or it.get("title")
        postdate = it["postdate"]
        print(f"[FETCH] {title}", file=sys.stderr)

        path = get_real_path(infoid)
        if not path:
            print(f"  ERROR: getDetailPath failed", file=sys.stderr)
            results.append({"title": title, "postdate": postdate, "owner": None, "price_wan": None, "error": "no path"})
            continue

        page = http_get(path if path.startswith("http") else BASE + path, timeout=30)
        if not page:
            print(f"  ERROR: fetch page failed", file=sys.stderr)
            results.append({"title": title, "postdate": postdate, "owner": None, "price_wan": None, "error": "fetch fail"})
            continue

        owner, price_wan = extract(page)
        detail_url = (path if path.startswith("http") else BASE + path) + "?fzxname=wjCity"
        print(f"  owner={owner} price={price_wan}万", file=sys.stderr)
        results.append({
            "title": title,
            "postdate": postdate,
            "owner": owner,
            "price_wan": price_wan,
            "detail_url": detail_url,
        })
        time.sleep(0.5)

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
苏州市公共资源交易平台 — 吴江区建设工程招标公告列表抓取

API: JyxxSearchAction.action?cmd=getList1
Required params:
  categorynum=003001001  (招标公告/资审公告)
  diqu=吴江区            (must be Chinese, NOT numeric like "035")
  siteguid=7eb5f7f1-9041-43ad-8e13-8fcb82ea831a
  pageIndex=N            (0-based)
  pageSize=15

Optional filter params:
  starttime=2026-06-01   (YYYY-MM-DD)
  endtime=2026-07-17
  xmmc=项目名关键词

CAPTCHA: triggers at pageIndex >= 10; use date range to stay under 9 pages.

Usage:
  python3 fetch_list.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]

Output:
  JSON with {totalCount, fetchedAt, items: [{infoid, title1, postdate, categorynum, ...}]}
"""
import urllib.request
import urllib.parse
import json
import sys
import time
import argparse

BASE = "https://ggzy.suzhou.gov.cn/EpointWebBuilder/JyxxSearchAction.action"
SITEGUID = "7eb5f7f1-9041-43ad-8e13-8fcb82ea831a"
CATEGORY = "003001001"
DIQU = "吴江区"

parser = argparse.ArgumentParser(description="Fetch Suzhou Wujiang bidding announcements")
parser.add_argument("--start", default="", help="Start date YYYY-MM-DD")
parser.add_argument("--end", default="", help="End date YYYY-MM-DD")
parser.add_argument("--xmmc", default="", help="Project name keyword")
args = parser.parse_args()

items = []
page = 0
while page < 10:  # captcha limit
    params = {
        "cmd": "getList1",
        "categorynum": CATEGORY,
        "diqu": DIQU,
        "xmmc": args.xmmc,
        "zstype": "",
        "zblx": "",
        "starttime": args.start,
        "endtime": args.end,
        "siteguid": SITEGUID,
        "pageIndex": str(page),
        "pageSize": "15",
    }
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "Referer": "https://ggzy.suzhou.gov.cn/wjqfzx/035006/wjCity_jyxx.html",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        body = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[ERROR] page {page}: {e}", file=sys.stderr)
        break
    try:
        outer = json.loads(body)
        inner = json.loads(outer.get("custom", "{}"))
    except Exception as e:
        print(f"[ERROR] page {page} parse: {e}", file=sys.stderr)
        break
    table = inner.get("Table") or []
    total = inner.get("TotalCount", 0)
    print(f"[page {page}] {len(table)} items | total={total}", file=sys.stderr)
    if not table:
        break
    items.extend(table)
    if len(items) >= total:
        break
    page += 1
    time.sleep(0.3)

result = {
    "totalCount": len(items),
    "fetchedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
    "params": {"start": args.start, "end": args.end, "xmmc": args.xmmc},
    "items": items,
}
json.dump(result, sys.stdout, ensure_ascii=False, indent=2)

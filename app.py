import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime
import re

st.set_page_config(layout="wide", page_title="Startup Radar JP")

# --- 設定：収集するニュースソース ---
SOURCES = {
    "🚀 資金調達(Google)": "https://news.google.com/rss/search?q=資金調達+OR+第三者割当増資+when:7d&hl=ja&gl=JP&ceid=JP:ja",
    "🏢 スタートアップ(PR TIMES)": "https://prtimes.jp/main/html/index/category_id/44/rdf.xml",
    "💡 THE BRIDGE": "https://thebridge.jp/feed"
}

# --- 処理：企業名の簡易抽出 ---
def extract_company(title):
    # 「株式会社〇〇」などのパターンを抽出（簡易版）
    match = re.search(r'「?(.+?株式会社|株式会社.+?)」?', title)
    return match.group(0) if match else ""

@st.cache_data(ttl=3600) # 1時間ごとに更新
def get_all_news():
    events = []
    for label, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            # 資金調達という文字が入っていたら色を変える(赤系)
            color = "#FF4B4B" if "資金調達" in title or "増資" in title else "#3D5A80"
            
            events.append({
                "title": f"{label} | {title}",
                "start": datetime(*entry.published_parsed[:6]).isoformat(),
                "url": entry.link,
                "backgroundColor": color,
                "borderColor": color,
                "allDay": True
            })
    return events

# --- UI：表示部分 ---
st.title("🚀 Startup & Finance Radar")
st.caption("最新の資金調達・スタートアップニュースを自動集約")

events = get_all_news()

# カレンダー表示
calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"},
    "locale": "ja"
}

state = calendar(events=events, options=calendar_options)

# 詳細表示
if state.get("eventClick"):
    st.info(f"🔗 [記事詳細を開く]({state['eventClick']['event']['url']})")
    st.write(state["eventClick"]["event"]["title"])

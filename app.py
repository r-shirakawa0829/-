import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date
import pandas as pd

st.set_page_config(layout="wide", page_title="B2B Startup Radar")

# --- 設定：BtoBに特化したソースとフィルタ ---
SOURCES = {
    "PR TIMES (B2B/DX)": "https://prtimes.jp/main/html/index/category_id/44/rdf.xml",
    "THE BRIDGE (Startup)": "https://thebridge.jp/feed",
    "Google News (法人向け資金調達)": "https://news.google.com/rss/search?q=法人向け+OR+B2B+OR+SaaS+OR+DX+資金調達+when:7d&hl=ja&gl=JP&ceid=JP:ja"
}

# toC向けを排除する除外キーワード設定（必要に応じて調整してください）
EXCLUDE_KEYWORDS = ["スイーツ", "コスメ", "アパレル", "ゲーム", "個人向け", "おもちゃ", "タレント"]

@st.cache_data(ttl=3600)
def fetch_and_filter_news():
    today_news = []
    all_events = []
    today = date.today()

    for label, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            summary = entry.get("description", "概要なし")
            # HTMLタグの除去（簡易的）
            summary = summary.replace("<br />", "\n").split("続きを読む")[0]
            
            # B2Bフィルタリング：除外ワードが含まれていたらスキップ
            if any(word in title or word in summary for word in EXCLUDE_KEYWORDS):
                continue

            # 日付処理
            pub_date = datetime(*entry.published_parsed[:6])
            is_today = pub_date.date() == today

            event = {
                "title": f"[{label}] {title}",
                "start": pub_date.isoformat(),
                "url": entry.link,
                "summary": summary,
                "source": label,
                "allDay": True,
                "backgroundColor": "#1E3A8A" if is_today else "#3D5A80"
            }
            
            all_events.append(event)
            if is_today:
                today_news.append(event)
                
    return today_news, all_events

# --- UI表示 ---
st.title("🚀 B2B Startup & Finance Radar")
st.caption(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

today_list, calendar_events = fetch_and_filter_news()

# 1. 本日の注目ニュース（最初に見れるように配置）
st.header("📌 本日のB2Bニュース")
if not today_list:
    st.write("本日の該当ニュースはまだありません。")
else:
    for item in today_list:
        with st.expander(f"【{item['source']}】{item['title']}"):
            st.write(f"**概要:** {item['summary'][:300]}...") # 冒頭のみ表示
            st.markdown(f"[📎 記事全文を読む]({item['url']})")

st.divider()

# 2. カレンダー表示（過去分を振り返る用）
st.header("📅 ニュースカレンダー")
calendar_options = {
    "initialView": "dayGridMonth",
    "locale": "ja",
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"}
}

state = calendar(events=calendar_events, options=calendar_options)

if state.get("eventClick"):
    event_data = state["eventClick"]["event"]
    st.sidebar.subheader("選択した記事の詳細")
    st.sidebar.write(event_data["title"])
    st.sidebar.markdown(f"[記事を開く]({event_data['url']})")

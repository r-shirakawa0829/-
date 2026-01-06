import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime

# --- 1. ページ基本設定 ---
st.set_page_config(
    layout="wide", 
    page_title="B2B ニュースカレンダー",
    page_icon="📅"
)

# --- 2. ニュース取得とカレンダー用データ変換 ---
@st.cache_data(ttl=3600)  # 1時間はキャッシュを保持
def get_calendar_events(rss_url):
    feed = feedparser.parse(rss_url)
    events = []
    for entry in feed.entries:
        # 日付の解析（RSSの形式に合わせて調整）
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            event_date = datetime(*published_parsed[:6]).strftime("%Y-%m-%d")
            events.append({
                "title": entry.title,
                "start": event_date,
                "url": entry.link,
                "allDay": True,
                "extendedProps": {
                    "summary": entry.get("summary", "")
                }
            })
    return events

# --- 3. メイン UI ---
st.title("📅 B2B ニュースカレンダー")
st.markdown("カレンダーの日付をクリックすると、その日に公開された記事の詳細が表示されます。")

# RSSフィードURL
default_url = "https://news.google.com/rss/search?q=B2B+スタートアップ+日本&hl=ja&gl=JP&ceid=JP:ja"
all_events = get_calendar_events(default_url)

# レイアウトを2カラムに分割
col1, col2 = st.columns([2, 1])

with col1:
    # カレンダーの表示設定
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth",
        },
        "initialView": "dayGridMonth",
        "selectable": True,
    }
    
    # カレンダーコンポーネントの呼び出し
    state = calendar(
        options=calendar_options,
        events=all_events,
        key='news-calendar',
    )

with col2:
    st.subheader("📌 記事詳細")
    
    # 日付またはイベントがクリックされた時の処理
    if state.get("callback") == "dateClick":
        clicked_date = state["dateClick"]["dateStr"]
        st.info(f"📅 {clicked_date} のニュース")
        
        # クリックされた日付に一致するニュースを抽出
        day_news = [e for e in all_events if e["start"] == clicked_date]
        
        if not day_news:
            st.write("この日のニュースは見つかりませんでした。")
        else:
            for item in day_news:
                st.markdown(f"**[{item['title']}]({item['url']})**")
                # 概要があれば表示
                summary_text = item['extendedProps']['summary'].split('<')[0][:100]
                if summary_text:
                    st.caption(summary_text + "...")
                st.divider()
                
    elif state.get("callback") == "eventClick":
        # カレンダー上のイベント（青い棒）を直接クリックした場合
        event = state["eventClick"]["event"]
        st.success("✅ 記事を選択しました")
        st.markdown(f"### {event['title']}")
        st.markdown(f"[👉 記事をブラウザで開く]({event['url']})")
    else:
        st.write("カレンダーの日付をクリックしてください。")

# --- 4. フッター ---
st.markdown("---")
st.caption("※APIキーを使用していないため、AIによる自動要約はありません。")
st.caption("※RSSで取得可能な最新記事（約20〜30件）のみがカレンダーに表示されます。")

import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date
import re

st.set_page_config(layout="wide", page_title="中小・スタートアップ B2B Radar")

# --- 設定：中小・中堅・スタートアップに特化したソース ---
SOURCES = {
    "🚀 スタートアップ(PR TIMES)": "https://prtimes.jp/main/html/index/category_id/44/rdf.xml",
    "💰 資金調達(THE BRIDGE)": "https://thebridge.jp/feed",
    "🔍 中小・ベンチャー(Google News)": "https://news.google.com/rss/search?q=(株式会社+OR+合同会社)+(資金調達+OR+SaaS+OR+DX+OR+新サービス)+-NTT+-トヨタ+-ソフトバンク+-ソニー+-日立+-楽天+when:7d&hl=ja&gl=JP&ceid=JP:ja"
}

# 除外設定：大手企業やtoC向けワード
EXCLUDE_KEYWORDS = [
    "東証プライム", "メガバンク", "大手銀行", "上場企業", # 大手関連
    "NTT", "トヨタ", "TOYOTA", "ソフトバンク", "SoftBank", "ソニー", "SONY", "パナソニック", # 具体的な大手名
    "スイーツ", "コスメ", "アパレル", "ゲーム", "個人向け", "おもちゃ", "美容液" # toC
]

@st.cache_data(ttl=3600)
def fetch_startup_news():
    today_news = []
    all_events = []
    today = date.today()

    for label, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            summary = entry.get("description", "概要なし")
            summary = summary.replace("<br />", "\n").split("続きを読む")[0]
            
            # 大手除外フィルタリング
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
                "backgroundColor": "#FF5722" if "資金調達" in label else "#4CAF50" # 資金調達はオレンジ、他は緑
            }
            
            all_events.append(event)
            if is_today:
                # 資金調達やスタートアップカテゴリの情報をリストの先頭に入れる
                if "資金調達" in label or "スタートアップ" in label:
                    today_news.insert(0, event)
                else:
                    today_news.append(event)
                
    return today_news, all_events

# --- UI表示 ---
st.title("🚀 中小・スタートアップ B2Bレーダー")
st.caption("大手を除外した、日本国内の若い会社・中堅企業の最新情報を集約")

today_list, calendar_events = fetch_startup_news()

# 1. 本日の注目ニュース（若い会社・資金調達を優先）
st.header("📌 本日の新興企業ニュース")
if not today_list:
    st.info("本日、該当するニュースはまだありません。")
else:
    for item in today_list:
        with st.expander(f"{item['title']}"):
            st.markdown(f"**媒体:** {item['source']}")
            st.write(f"**内容:** {item['summary'][:300]}...")
            st.markdown(f"🔗 [この記事を詳しく見る]({item['url']})")

st.divider()

# 2. カレンダー
st.header("📅 過去の履歴")
calendar_options = {
    "initialView": "dayGridMonth",
    "locale": "ja",
}
calendar(events=calendar_events, options=calendar_options)

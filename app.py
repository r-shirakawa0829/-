import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date
import re

st.set_page_config(layout="wide", page_title="中小・スタートアップ B2B Radar")

# --- 設定：ソースと除外キーワード ---
SOURCES = {
    "🚀 スタートアップ(PR TIMES)": "https://prtimes.jp/main/html/index/category_id/44/rdf.xml",
    "💰 資金調達(THE BRIDGE)": "https://thebridge.jp/feed",
    "🔍 中小・ベンチャー(Google News)": "https://news.google.com/rss/search?q=(株式会社+OR+合同会社)+(資金調達+OR+SaaS+OR+DX+OR+新サービス)+-NTT+-トヨタ+-ソフトバンク+-ソニー+-日立+-楽天+when:7d&hl=ja&gl=JP&ceid=JP:ja"
}

EXCLUDE_KEYWORDS = ["東証プライム", "メガバンク", "上場企業", "NTT", "トヨタ", "ソフトバンク", "ソニー", "パナソニック", "スイーツ", "コスメ", "アパレル", "ゲーム", "個人向け"]

@st.cache_data(ttl=3600)
def fetch_all_data():
    all_events = []
    company_history = {}
    
    for label, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            summary = entry.get("description", "概要なし").replace("<br />", "\n").split("続きを読む")[0]
            if any(word in title or word in summary for word in EXCLUDE_KEYWORDS):
                continue

            # 日付の解析
            pub_dt = datetime(*entry.published_parsed[:6])
            pub_date_str = pub_dt.date().isoformat()
            
            # 企業名の抽出
            company_match = re.search(r'([^\s　]+(?:株式会社|合同会社|有限会社)[^\s　]*)', title)
            company_name = company_match.group(0) if company_match else title[:10]

            # カレンダーに渡すデータ（JSON形式に変換可能なものだけに絞る）
            event = {
                "title": f"{company_name}", 
                "start": pub_date_str,
                "url": entry.link,
                "color": "#FF5722" if "資金調達" in label else "#4CAF50",
                # 以下の独自データは「extendedProps」に入れるのがカレンダーのルール
                "extendedProps": {
                    "full_title": f"[{label}] {title}",
                    "summary": summary,
                    "source": label,
                    "company": company_name,
                    "pub_iso": pub_dt.isoformat() # datetimeオブジェクトではなく文字列にする
                }
            }
            all_events.append(event)
            
            if company_name not in company_history or pub_dt.isoformat() < company_history[company_name]:
                company_history[company_name] = pub_dt.isoformat()

    return all_events, company_history

# --- アプリ起動 ---
all_events, company_history = fetch_all_data()

st.title("🚀 中小・スタートアップ B2Bレーダー")

# 1. カレンダー表示
st.header("📅 ニュースカレンダー")
calendar_options = {
    "initialView": "dayGridMonth",
    "selectable": True,
    "locale": "ja",
}
state = calendar(events=all_events, options=calendar_options, key="news_calendar")

# 2. 日付の決定ロジック
selected_date_str = str(date.today())
if state.get("dateClick"):
    selected_date_str = state["dateClick"]["date"].split("T")[0]

st.divider()

# 3. ニュース詳細一覧
st.header(f"📌 {selected_date_str} のニュース一覧")

target_news = [e for e in all_events if e['start'] == selected_date_str]
target_news.sort(key=lambda x: "資金調達" in x['extendedProps']['source'], reverse=True)

if not target_news:
    st.info(f"{selected_date_str} の該当ニュースはありません。")
else:
    for item in target_news:
        props = item['extendedProps']
        # NEW判定
        is_new = props['pub_iso'] <= company_history.get(props['company'], props['pub_iso'])
        new_badge = "🔴 [NEW!] " if is_new else ""
        
        with st.expander(f"{new_badge}{props['full_title']}", expanded=is_new):
            st.markdown(f"**企業名:** {props['company']}")
            st.markdown(f"**媒体:** {props['source']}")
            st.write(f"**内容:** {props['summary'][:300]}...")
            st.markdown(f"🔗 [この記事を詳しく見る]({item['url']})")

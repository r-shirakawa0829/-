import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date
import re

st.set_page_config(layout="wide", page_title="中小・スタートアップ B2B Radar")

# --- セッション状態の初期化（反応を良くするため） ---
if "selected_date" not in st.session_state:
    st.session_state.selected_date = str(date.today())

# --- ニュース取得設定 ---
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
            pub_dt = datetime(*entry.published_parsed[:6])
            date_str = pub_dt.strftime('%Y-%m-%d')
            iso_str = pub_dt.isoformat()
            company_match = re.search(r'([^\s　]+(?:株式会社|合同会社|有限会社)[^\s　]*)', title)
            company_name = company_match.group(0) if company_match else title[:10]

            event = {
                "title": f"{company_name}", 
                "start": date_str,
                "color": "#FF5722" if "資金調達" in label else "#4CAF50",
                "extendedProps": {
                    "full_title": str(title),
                    "summary": str(summary),
                    "source": str(label),
                    "company": str(company_name),
                    "url": str(entry.link),
                    "pub_iso": iso_str
                }
            }
            all_events.append(event)
            if company_name not in company_history or iso_str < company_history[company_name]:
                company_history[company_name] = iso_str
    return all_events, company_history

all_events, company_history = fetch_all_data()

st.title("🚀 中小・スタートアップ B2Bレーダー")

# --- サイドバーで補助的な日付選択 ---
with st.sidebar:
    st.header("日付選択（補助）")
    side_date = st.date_input("カレンダーの反応が悪い時はこちら", value=date.fromisoformat(st.session_state.selected_date))
    if str(side_date) != st.session_state.selected_date:
        st.session_state.selected_date = str(side_date)
        st.rerun()

# --- メイン：カレンダー表示 ---
st.header("📅 ニュースカレンダー")
calendar_options = {
    "initialView": "dayGridMonth",
    "selectable": True,
    "locale": "ja",
}
state = calendar(events=all_events, options=calendar_options, key="b2b_calendar")

# カレンダーのクリックを検知
if state.get("dateClick"):
    clicked = state["dateClick"]["date"].split("T")[0]
    if clicked != st.session_state.selected_date:
        st.session_state.selected_date = clicked
        st.rerun()

st.divider()

# --- ニュース詳細一覧 ---
st.header(f"📌 {st.session_state.selected_date} のニュース一覧")
target_news = [e for e in all_events if e['start'] == st.session_state.selected_date]
target_news.sort(key=lambda x: "資金調達" in x['extendedProps']['source'], reverse=True)

if not target_news:
    st.info(f"{st.session_state.selected_date} のニュースはありません。他の日を選んでください。")
else:
    for item in target_news:
        p = item['extendedProps']
        is_new = p['pub_iso'] <= company_history.get(p['company'], p['pub_iso'])
        badge = "🔴 [NEW!] " if is_new else ""
        with st.expander(f"{badge}[{p['source']}] {p['full_title']}", expanded=is_new):
            st.markdown(f"**企業名:** {p['company']}")
            st.write(f"**内容:** {p['summary'][:300]}...")
            st.markdown(f"🔗 [この記事を詳しく見る]({p['url']})")

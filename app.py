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
            pub_date = datetime(*entry.published_parsed[:6])
            
            # 企業名の抽出
            company_match = re.search(r'([^\s　]+(?:株式会社|合同会社|有限会社)[^\s　]*)', title)
            company_name = company_match.group(0) if company_match else title[:10]

            event = {
                "title": f"({label[0]}) {company_name}", # カレンダー上は短く
                "start": pub_date.date().isoformat(),
                "full_title": f"[{label}] {title}",
                "url": entry.link,
                "summary": summary,
                "source": label,
                "company": company_name,
                "pub_datetime": pub_date,
                "color": "#FF5722" if "資金調達" in label else "#4CAF50"
            }
            all_events.append(event)
            
            if company_name not in company_history or pub_date < company_history[company_name]:
                company_history[company_name] = pub_date

    return all_events, company_history

# --- アプリ起動 ---
all_events, company_history = fetch_all_data()

st.title("🚀 中小・スタートアップ B2Bレーダー")

# 1. カレンダー表示（ここを修正しました）
st.header("📅 ニュースカレンダー")
st.caption("日付をクリックすると、その下の「詳細一覧」が切り替わります")

calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
    "selectable": True,
    "locale": "ja",
}

# カレンダーの実行
state = calendar(events=all_events, options=calendar_options, key="news_calendar")

# 2. 日付の決定ロジック
# カレンダーがクリックされたらその日を、そうでなければ今日を選択
selected_date_str = str(date.today())
if state.get("dateClick"):
    selected_date_str = state["dateClick"]["date"].split("T")[0]

st.divider()

# 3. ニュース詳細一覧
st.header(f"📌 {selected_date_str} のニュース一覧")

# 選択された日付に一致する記事をフィルタ
target_news = [e for e in all_events if e['start'] == selected_date_str]
# 資金調達を優先
target_news.sort(key=lambda x: "資金調達" in x['source'], reverse=True)

if not target_news:
    st.info(f"{selected_date_str} の該当ニュースはありません。カレンダーから他の日を選んでください。")
else:
    for item in target_news:
        # NEW判定
        is_new = item['pub_datetime'] <= company_history.get(item['company'], item['pub_datetime'])
        new_badge = "🔴 [NEW!] " if is_new else ""
        
        with st.expander(f"{new_badge}{item['full_title']}", expanded=is_new):
            st.markdown(f"**企業名:** {item['company']}")
            st.markdown(f"**媒体:** {item['source']}")
            st.write(f"**内容:** {item['summary'][:300]}...")
            st.markdown(f"🔗 [この記事を詳しく見る]({item['url']})")

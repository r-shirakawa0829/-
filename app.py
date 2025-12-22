import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date
import re

st.set_page_config(layout="wide", page_title="中小・スタートアップ B2B Radar")

# --- ソースと除外ワードの設定 ---
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

            # 日付を確実に「文字列」にする
            pub_dt = datetime(*entry.published_parsed[:6])
            date_str = pub_dt.strftime('%Y-%m-%d')
            iso_str = pub_dt.isoformat()
            
            # 企業名の抽出
            company_match = re.search(r'([^\s　]+(?:株式会社|合同会社|有限会社)[^\s　]*)', title)
            company_name = company_match.group(0) if company_match else title[:10]

            # カレンダーへ渡すデータは最小限の「文字列のみ」にする（エラー防止）
            event = {
                "title": f"{company_name}", 
                "start": date_str,
                "color": "#FF5722" if "資金調達" in label else "#4CAF50",
                # 詳細データ
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

# --- アプリの表示 ---
all_events, company_history = fetch_all_data()

st.title("🚀 中小・スタートアップ B2Bレーダー")

# 1. カレンダー
calendar_options = {
    "initialView": "dayGridMonth",
    "selectable": True,
    "locale": "ja",
}
# keyを毎回変えないように固定し、データを確実に文字列のみで渡す
state = calendar(events=all_events, options=calendar_options, key="b2b_news_calendar")

# 2. 表示する日付の判定
selected_date = str(date.today())
if state.get("dateClick"):
    selected_date = state["dateClick"]["date"].split("T")[0]

st.divider()

# 3. ニュース詳細一覧
st.header(f"📌 {selected_date} のニュース一覧")

# 選択された日付の記事をフィルタ
target_news = [e for e in all_events if e['start'] == selected_date]
# 資金調達を優先
target_news.sort(key=lambda x: "資金調達" in x['extendedProps']['source'], reverse=True)

if not target_news:
    st.info(f"{selected_date} の該当ニュースはありません。カレンダーから他の日を選択してください。")
else:
    for item in target_news:
        p = item['extendedProps']
        # NEW判定
        is_new = p['pub_iso'] <= company_history.get(p['company'], p['pub_iso'])
        badge = "🔴 [NEW!] " if is_new else ""
        
        with st.expander(f"{badge}[{p['source']}] {p['full_title']}", expanded=is_new):
            st.markdown(f"**企業名:** {p['company']}")
            st.write(f"**内容:** {p['summary'][:300]}...")
            st.markdown(f"🔗 [この記事を詳しく見る]({p['url']})")

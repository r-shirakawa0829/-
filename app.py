import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import re

st.set_page_config(layout="wide", page_title="中小・スタートアップ B2B Radar")

# --- 設定：ソースと除外設定 ---
SOURCES = {
    "🚀 スタートアップ(PR TIMES)": "https://prtimes.jp/main/html/index/category_id/44/rdf.xml",
    "💰 資金調達(THE BRIDGE)": "https://thebridge.jp/feed",
    "🔍 中小・ベンチャー(Google News)": "https://news.google.com/rss/search?q=(株式会社+OR+合同会社)+(資金調達+OR+SaaS+OR+DX+OR+新サービス)+-NTT+-トヨタ+-ソフトバンク+-ソニー+-日立+-楽天+when:7d&hl=ja&gl=JP&ceid=JP:ja"
}

EXCLUDE_KEYWORDS = ["東証プライム", "メガバンク", "大手銀行", "上場企業", "NTT", "トヨタ", "ソフトバンク", "ソニー", "パナソニック", "スイーツ", "コスメ", "アパレル", "ゲーム", "個人向け"]

@st.cache_data(ttl=3600)
def fetch_all_data():
    all_events = []
    company_history = {} # 企業の初登場を記録用
    
    for label, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            summary = entry.get("description", "概要なし").replace("<br />", "\n").split("続きを読む")[0]
            if any(word in title or word in summary for word in EXCLUDE_KEYWORDS):
                continue

            pub_date = datetime(*entry.published_parsed[:6])
            
            # 企業名の簡易抽出（「株式会社〇〇」など）
            company_match = re.search(r'([^\s　]+(?:株式会社|合同会社|有限会社)[^\s　]*)', title)
            company_name = company_match.group(0) if company_match else title[:10]

            event = {
                "title": title,
                "start": pub_date.date().isoformat(), # カレンダー用
                "full_title": f"[{label}] {title}",
                "url": entry.link,
                "summary": summary,
                "source": label,
                "company": company_name,
                "pub_datetime": pub_date,
                "backgroundColor": "#FF5722" if "資金調達" in label else "#4CAF50"
            }
            all_events.append(event)
            
            # 企業ごとの最古の掲載日を記録（簡易NEW判定）
            if company_name not in company_history or pub_date < company_history[company_name]:
                company_history[company_name] = pub_date

    return all_events, company_history

# --- アプリメイン処理 ---
st.title("🚀 中小・スタートアップ B2Bレーダー")
st.caption("カレンダーで日付を選ぶと、その日の詳細が一覧表示されます")

all_events, company_history = fetch_all_data()

# サイドバーまたは上部に日付選択状態を表示
selected_date = st.date_input("表示する日付を選択してください", date.today())

# 選択された日付のニュースを抽出
target_news = [e for e in all_events if datetime.fromisoformat(e['start']).date() == selected_date]
# 資金調達を優先的に上に
target_news.sort(key=lambda x: "資金調達" in x['source'], reverse=True)

# 1. ニュース一覧表示（選択された日付分）
st.header(f"📌 {selected_date.strftime('%Y年%m月%d日')} の詳細一覧")

if not target_news:
    st.info("この日の該当ニュースはありません。")
else:
    for item in target_news:
        # NEW判定：その記事の公開日時が、その企業の記録上の最古日時と同じならNEW
        is_new = item['pub_datetime'] <= company_history.get(item['company'], item['pub_datetime'])
        new_badge = "🔴 [NEW!] " if is_new else ""
        
        with st.expander(f"{new_badge}{item['full_title']}"):
            st.markdown(f"**企業名:** {item['company']}")
            st.markdown(f"**媒体:** {item['source']}")
            st.write(f"**概要:** {item['summary'][:300]}...")
            st.markdown(f"🔗 [この記事を詳しく見る]({item['url']})")

st.divider()

# 2. カレンダー表示（日付選択の補助として）
st.header("📅 カレンダーから選ぶ")
calendar_options = {
    "initialView": "dayGridMonth",
    "locale": "ja",
    "selectable": True,
}
state = calendar(events=all_events, options=calendar_options)

# カレンダーで日付がクリックされたら、ページを再読み込みして日付を更新する仕組み
if state.get("dateClick"):
    clicked_date = state["dateClick"]["date"].split("T")[0]
    st.warning(f"上の日付選択欄で {clicked_date} を選ぶと、詳細一覧が更新されます。")

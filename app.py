import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import re

st.set_page_config(layout="wide", page_title="B2B Radar | Prompt Generator")

# --- セッション状態管理 ---
if "selected_date" not in st.session_state:
    st.session_state.selected_date = str(date.today())

# --- ニュース取得 ---
@st.cache_data(ttl=3600)
def fetch_b2b_news():
    feeds = {
        "🚀 PR TIMES": "https://prtimes.jp/main/html/index/category_id/44/rdf.xml",
        "💰 THE BRIDGE": "https://thebridge.jp/feed",
        "🔍 Google News": "https://news.google.com/rss/search?q=(株式会社+OR+合同会社)+(資金調達+OR+SaaS+OR+DX)+-NTT+-トヨタ+-ソフトバンク+-ソニー+when:7d&hl=ja&gl=JP&ceid=JP:ja"
    }
    all_events = []
    for source_name, url in feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            if any(x in title for x in ["東証", "メガバンク", "大企業", "スイーツ", "コスメ"]): continue
            pub_dt = datetime(*entry.published_parsed[:6])
            date_str = pub_dt.strftime('%Y-%m-%d')
            company_match = re.search(r'([^\s　]+(?:株式会社|合同会社|有限会社)[^\s　]*)', title)
            company_name = company_match.group(0) if company_match else title[:10]
            
            all_events.append({
                "title": company_name,
                "start": date_str,
                "extendedProps": {
                    "full_title": title,
                    "summary": entry.get("description", "").replace("<br />", " ").split("続きを読む")[0],
                    "url": entry.link,
                    "source": source_name,
                    "company": company_name
                }
            })
    return all_events

all_events = fetch_b2b_news()

# --- メインレイアウト ---
st.title("🚀 B2B Radar & Prompt Generator")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.header("📅 カレンダー")
    cal = calendar(events=all_events, options={"initialView": "dayGridMonth", "locale": "ja"}, key="main_cal")
    if cal.get("dateClick"):
        clicked = cal["dateClick"]["date"].split("T")[0]
        if clicked != st.session_state.selected_date:
            st.session_state.selected_date = clicked
            st.rerun()

with col2:
    st.header(f"📌 {st.session_state.selected_date} の掲載企業")
    items = [e for e in all_events if e['start'] == st.session_state.selected_date]
    
    for item in items:
        p = item['extendedProps']
        with st.expander(f"[{p['source']}] {p['full_title']}"):
            st.write(f"**企業名:** {p['company']}")
            st.markdown(f"🔗 [記事原文を表示]({p['url']})")
            
            # --- プロンプト作成ロジック ---
            today = date.today()
            dates = []
            check_day = today + timedelta(days=2)
            while len(dates) < 5:
                if check_day.weekday() < 5: dates.append(check_day.strftime("%m月%d日（%a）09:00～18:00"))
                check_day += timedelta(days=1)
            date_text = "\n".join([f"・{d}" for d in dates])

            # Geminiに投げれば完成する魔法の指示文
            magic_prompt = f"""あなたは、企業のビジネスモデルと哲学を見抜く超一流のビジネスアナリスト兼コンサルタントです。
以下の情報に基づき、ステップに従ってアライアンス提案メールを作成してください。

1. 分析対象
企業名: {p['company']}
記事URL: {p['url']}
記事内容: {p['summary']}

2. 私たちの強み
・全国13万社の経営者ネットワーク
・提携により数千万以上の利益確保を支援可能
・資料: https://docs.google.com/presentation/d/1JeqlwgvQ4uSaDEtVVdrj9-ju7EpXhKOK/edit

3. 実行ステップ
ステップ0：認識合わせ（太字一文で要約）
ステップA：ビジネス分析（サービス概要、ターゲット、経営ペインポイント）
ステップB：メールパーツ（心を掴む冒頭文3案、悩みリスト3つ）
ステップC：メール完成形（以下日程案を必ず含むこと）

【日程案】
{date_text}
"""
            
            st.info("下のボタンを押して、コピーした内容をGeminiに貼り付けてください。")
            # コピペ用のテキストエリア
            st.text_area("Gemini用プロンプト", value=magic_prompt, height=200, key=f"p_{p['url']}")
            st.caption("※上の枠内の文字を全選択(Ctrl+A)してコピーしてください。"

import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import re

# レイアウト設定
st.set_page_config(layout="wide", page_title="B2B Radar")

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
            # 除外キーワード
            if any(x in title for x in ["東証", "メガバンク", "大企業", "スイーツ", "コスメ"]):
                continue
            
            # 日付処理
            pub_dt = datetime(*entry.published_parsed[:6])
            date_str = pub_dt.strftime('%Y-%m-%d')
            
            # 会社名抽出（正規表現）
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
    
    # クリックイベントの検知
    if cal.get("dateClick"):
        clicked = cal["dateClick"]["date"].split("T")[0]
        if clicked != st.session_state.selected_date:
            st.session_state.selected_date = clicked
            st.rerun()

with col2:
    st.header(f"📌 {st.session_state.selected_date} の掲載企業")
    items = [e for e in all_events if e['start'] == st.session_state.selected_date]
    
    if not items:
        st.info("この日のニュースはありません。")
    
    for item in items:
        p = item['extendedProps']
        with st.expander(f"[{p['source']}] {p['full_title']}"):
            st.write(f"**企業名:** {p['company']}")
            st.markdown(f"🔗 [記事原文を表示]({p['url']})")
            
            # 日程候補の作成（土日を除外）
            today = date.today()
            dates = []
            for i in range(2, 10): # 候補を少し広めに探索
                target_date = today + timedelta(days=i)
                if target_date.weekday() < 5: # 平日のみ
                    dates.append(target_date.strftime("%m月%d日（%a）09:00～18:00"))
                if len(dates) >= 3: # 3件溜まったら終了
                    break
                    
            date_text = "\n".join([f"・{d}" for d in dates])

            magic_prompt = f"""あなたは一流コンサルです。以下を分析しアライアンス提案メールを作って。

企業名: {p['company']}
URL: {p['url']}
内容: {p['summary']}

【強み】全国13万社の経営者ネットワーク、数千万の利益支援可
【資料】https://docs.google.com/presentation/d/1JeqlwgvQ4uSaDEtVVdrj9-ju7EpXhKOK/edit

【日程】
{date_text}
"""
            st.text_area("Geminiに貼り付ける指示文", value=magic_prompt, height=250, key=f"p_{p['url']}")
            st.caption("全選択してコピーし、Geminiに貼り付けてください。")

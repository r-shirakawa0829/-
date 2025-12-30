import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import re
import google.generativeai as genai

st.set_page_config(layout="wide", page_title="B2B Radar & AI Outreach")

# --- AI設定 ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("Secretsに GEMINI_API_KEY を登録してください。")

# --- セッション状態（メモリ）の管理 ---
if "selected_date" not in st.session_state:
    st.session_state.selected_date = str(date.today())
# AIの生成結果を保存しておく場所
if "ai_results" not in st.session_state:
    st.session_state.ai_results = {}

# --- ニュース取得 (PR TIMES, THE BRIDGE, Google News) ---
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
st.title("🚀 B2Bスタートアップ分析 & 提案ツール")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.header("📅 ニュースカレンダー")
    cal = calendar(events=all_events, options={"initialView": "dayGridMonth", "locale": "ja"}, key="cal")
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
            
            btn_key = f"btn_{p['url']}"
            
            # AI提案メールを生成ボタン
            if st.button(f"📧 一流コンサルの提案メールを生成", key=btn_key):
                # 日程提案の自動計算（今日から2日後〜5日間）
                today = date.today()
                dates = []
                check_day = today + timedelta(days=2)
                while len(dates) < 5:
                    if check_day.weekday() < 5: dates.append(check_day.strftime("%m月%d日（%a）09:00～18:00"))
                    check_day += timedelta(days=1)
                date_text = "\n".join([f"・{d}" for d in dates])

                # プロンプト作成
                prompt = f"""
                あなたは、企業のビジネスモデルと哲学を見抜く超一流のビジネスアナリスト兼マーケティングコンサルタントです。
                
                以下の企業を分析し、13万社の経営者ネットワークを持つ我々との提携メリットを強調したアライアンス提案メールを作成してください。
                
                企業名: {p['company']}
                URL: {p['url']}
                記事タイトル: {p['full_title']}
                記事概要: {p['summary']}
                資料URL: https://docs.google.com/presentation/d/1JeqlwgvQ4uSaDEtVVdrj9-ju7EpXhKOK/edit

                【必須条件】
                1. ステップ0〜Cに従って、ビジネス分析を詳しく行うこと。
                2. 日程案は以下を必ず使用すること：
                {date_text}
                """

                # ストリーミング表示の開始
                st.divider()
                st.subheader(f"🤖 {p['company']} の分析結果")
                placeholder = st.empty()
                full_response = ""
                
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    for chunk in model.generate_content(prompt, stream=True):
                        full_response += chunk.text
                        placeholder.markdown(full_response + "▌") # タイピング風
                    
                    placeholder.markdown(full_response)
                    # 結果を保存
                    st.session_state.ai_results[p['url']] = full_response
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

            # すでに生成済みの結果がある場合は、ボタンを押さなくても表示
            elif p['url'] in st.session_state.ai_results:
                st.divider()
                st.subheader(f"🤖 {p['company']} の生成済み提案案")
                st.markdown(st.session_state.ai_results[p['url']])
                st.text_area("コピペ用", value=st.session_state.ai_results[p['url']], height=300, key=f"text_{p['url']}")

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

# --- 【重要】セッション状態（メモリ）の管理 ---
if "selected_date" not in st.session_state:
    st.session_state.selected_date = str(date.today())
if "ai_results" not in st.session_state:
    st.session_state.ai_results = {}

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
st.title("🚀 B2Bスタートアップ分析 & 提案ツール")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.header("📅 ニュースカレンダー")
    # keyを固定して反応を安定させます
    cal = calendar(events=all_events, options={"initialView": "dayGridMonth", "locale": "ja"}, key="b2b_calendar_main")
    
    # --- 【解決】日付クリックの反応を強制的に同期させるロジック ---
    if cal.get("dateClick"):
        clicked_date = cal["dateClick"]["date"].split("T")[0]
        if clicked_date != st.session_state.selected_date:
            st.session_state.selected_date = clicked_date
            st.rerun() # 強制再描画で即座に右側を更新

with col2:
    st.header(f"📌 {st.session_state.selected_date} の掲載企業")
    items = [e for e in all_events if e['start'] == st.session_state.selected_date]
    
    if not items:
        st.info("この日のニュースはありません。")
    
    for item in items:
        p = item['extendedProps']
        # 過去のAI生成結果があるかチェック
        has_ai_result = p['url'] in st.session_state.ai_results
        
        # タイトルにAI済みマークをつける
        label = f"✅ [{p['source']}] {p['full_title']}" if has_ai_result else f"[{p['source']}] {p['full_title']}"
        
        with st.expander(label):
            st.write(f"**企業名:** {p['company']}")
            st.markdown(f"🔗 [記事原文を表示]({p['url']})")
            
            btn_key = f"btn_{p['url']}"
            
            if st.button(f"📧 AI提案メールを生成", key=btn_key):
                # 日程提案の自動計算
                today = date.today()
                dates = []
                check_day = today + timedelta(days=2)
                while len(dates) < 5:
                    if check_day.weekday() < 5: dates.append(check_day.strftime("%m月%d日（%a）09:00～18:00"))
                    check_day += timedelta(days=1)
                date_text = "\n".join([f"・{d}" for d in dates])

                prompt = f"""
                あなたは超一流のコンサルタントです。企業 {p['company']} ({p['url']}) を分析し、アライアンス提案メールを作成してください。
                13万社の経営者ネットワークを持つ我々との提携メリットを強調し、以下の日程案を含めてください：
                {date_text}
                
                資料URL: https://docs.google.com/presentation/d/1JeqlwgvQ4uSaDEtVVdrj9-ju7EpXhKOK/edit
                ステップに沿って深く分析し、最後にメール完成形を出力してください。
                """

                st.divider()
                st.subheader(f"🤖 {p['company']} の分析結果")
                placeholder = st.empty()
                full_response = ""
                
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    # ストリーミング表示
                    for chunk in model.generate_content(prompt, stream=True):
                        full_response += chunk.text
                        placeholder.markdown(full_response + "▌")
                    
                    placeholder.markdown(full_response)
                    # メモリに保存
                    st.session_state.ai_results[p['url']] = full_response
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

            # 既に結果がある場合は表示
            elif has_ai_result:
                st.divider()
                st.info("生成済みの提案があります")
                st.markdown(st.session_state.ai_results[p['url']])
                st.text_area("コピペ用", value=st.session_state.ai_results[p['url']], height=300, key=f"text_{p['url']}")

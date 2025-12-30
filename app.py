import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import re
import google.generativeai as genai

st.set_page_config(layout="wide", page_title="B2B Radar & AI Outreach")

# --- AI設定 (Secretsから取得) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("Streamlit CloudのSecretsに GEMINI_API_KEY を登録してください。")

# --- セッション状態の初期化 ---
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

# --- AIメール作成関数 ---
def generate_ai_email(p):
    # 日程提案の自動作成（今日から2日後から5日間、土日除外）
    today = date.today()
    proposal_dates = []
    check_day = today + timedelta(days=2)
    while len(proposal_dates) < 5:
        if check_day.weekday() < 5: # 月〜金
            proposal_dates.append(check_day.strftime("%m月%d日（%a）09:00～18:00"))
        check_day += timedelta(days=1)
    
    date_text = "\n".join([f"・{d}" for d in proposal_dates])
    
    prompt = f"""
    あなたは、企業のビジネスモデルと、その根底にある哲学までを的確に見抜き、心を動かす効果的なコミュニケーション戦略を立案する、超一流のビジネスアナリスト兼マーケティングコンサルタントです。

    以下の情報とステップに従い、企業分析とアライアンス提案メールの作成を完璧に実行してください。

    1. 分析対象の情報
    企業名/サービス名: {p['company']}
    関連URL: {p['url']}
    記事タイトル: {p['full_title']}
    記事概要: {p['summary']}

    【私たちの提供価値・アライアンスの根拠】
    ・中堅中小企業様を中心に全国13万社の経営者との企業ネットワークを有している。
    ・貴社と提携することで、ターゲット企業群へのアプローチが可能になり、数千万以上の利益確保に貢献できる。
    ・私たちのサービス詳細資料: https://docs.google.com/presentation/d/1JeqlwgvQ4uSaDEtVVdrj9-ju7EpXhKOK/edit

    2. 実行ステップ
    ステップ0：認識合わせ（対象企業をどう理解したか太字一文で要約）
    ステップA：ビジネス分析（サービス概要、ターゲット、経営レベルのペインポイントを分析の根拠と共に）
    ステップB：メール文章のパーツ作成（心を掴む冒頭文3パターン、経営者が頷く悩みリスト3つ）
    ステップC：メール文章の完成（最も効果的な冒頭文と悩みリストを組み合わせた、そのまま使えるメール作成）

    ※候補日程は以下を必ず使用すること：
    {date_text}
    """
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

# --- UI表示 ---
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
            
            if st.button(f"📧 一流コンサルの提案メールを生成", key=f"btn_{p['url']}"):
                with st.spinner("ビジネスモデルを深く分析中..."):
                    result = generate_ai_email(p)
                    st.divider()
                    st.subheader("🤖 AI分析 & 提案メール案")
                    st.markdown(result)
                    st.text_area("コピペ用（文章全体）", value=result, height=400)

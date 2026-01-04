import streamlit as st
import google.generativeai as genai
from streamlit_calendar import calendar
from datetime import datetime, date
import re

# --- 1. ページ基本設定 ---
st.set_page_config(
    layout="wide", 
    page_title="中小・スタートアップ B2B 戦略支援",
    page_icon="🚀"
)

# --- 2. APIキーの設定 (Secretsから読み込み) ---
# Streamlit Cloudの [Settings] > [Secrets] に GOOGLE_API_KEY = "あなたのキー" を設定してください
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"APIの初期化に失敗しました。キーを確認してください: {e}")
else:
    st.warning("⚠️ APIキーが設定されていません。サイドバーまたはSecretsを確認してください。")

# --- 3. セッション状態の初期化 ---
if "events" not in st.session_state:
    st.session_state.events = []
if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""

# --- 4. メイン UI ---
st.title("🚀 中小・スタートアップ B2B 戦略支援ツール")
st.markdown("AIを活用した戦略立案と、スケジュール管理を一体化させたツールです。")

# タブ分け
tab1, tab2 = st.tabs(["💡 戦略生成・AI相談", "📅 イベントカレンダー"])

# --- Tab 1: AI 戦略生成 ---
with tab1:
    st.subheader("Gemini AI 戦略アドバイザー")
    
    with st.form("ai_form"):
        prompt = st.text_area(
            "相談内容やターゲット情報を入力してください:", 
            placeholder="例：製造業向けの新規SaaSの営業メール案を3つ作成して",
            height=150
        )
        submit_button = st.form_submit_button("戦略を生成する")

    if submit_button:
        if not prompt:
            st.error("内容を入力してください。")
        elif "GOOGLE_API_KEY" not in st.secrets:
            st.error("APIキーが設定されていないため実行できません。")
        else:
            with st.spinner("AIが戦略を練っています..."):
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(prompt)
                    st.session_state.ai_response = response.text
                except Exception as e:
                    st.error(f"AI生成中にエラーが発生しました: {e}")

    if st.session_state.ai_response:
        st.markdown("### 🤖 AIからの提案")
        st.write(st.session_state.ai_response)
        
        # 修正箇所: 以前エラーが出ていた 107行目付近の処理
        st.info("💡 この内容をコピーして、カレンダーの予定作成に活用してください。")
        # 正しく閉じカッコを配置
        st.caption("※上の枠内の文字を全選択(Ctrl+A)してコピーしてください。")

# --- Tab 2: カレンダー管理 ---
with tab2:
    st.subheader("プロジェクト・イベント管理")
    
    # サイドバーまたは入力欄で予定を追加する簡易機能（任意）
    with st.expander("新しい予定を追加"):
        col1, col2 = st.columns(2)
        with col1:
            new_event_title = st.text_input("予定タイトル")
            new_event_date = st.date_input("日付", date.today())
        with col2:
            st.write(" ") # 余白
            if st.button("カレンダーに追加"):
                new_event = {
                    "title": new_event_title,
                    "start": new_event_date.strftime("%Y-%m-%d"),
                    "allDay": True
                }
                st.session_state.events.append(new_event)
                st.success("追加しました！")

    # カレンダーの表示設定
    calendar_options = {
        "editable": True,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek",
        },
        "initialView": "dayGridMonth",
    }
    
    # 外部コンポーネントの呼び出し
    state = calendar(
        options=calendar_options,
        events=st.session_state.events,
        key='fullcalendar',
    )

    if state.get("callback") == "dateClick":
        st.write(f"🖱️ 選択された日付: {state['dateClick']['dateStr']}")

# --- 5. サイドバー設定 ---
with st.sidebar:
    st.header("設定")
    st.write("現在の登録イベント数:", len(st.session_state.events))
    if st.button("予定をリセット"):
        st.session_state.events = []
        st.rerun()
    
    st.divider()
    st.caption("Powered by Gemini 1.5 Flash & Streamlit")

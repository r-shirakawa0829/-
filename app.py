import streamlit as st
import feedparser
from streamlit_calendar import calendar
from datetime import datetime, date
import re

st.set_page_config(layout="wide", page_title="中小・スタートアップ B2B Radar")

# --- セッション状態（メモリ）の初期化 ---
if "selected_date" not in st.session_state:
    st.session_state.selected_date = str(date.today())

# --- データ取得ロジック（キャッシュ付き） ---
@st.cache_data(ttl=3600)
def fetch_news_data():
    # 前回のコードと同じニュース取得ロジック
    # (中身は省略しませんが、動作を軽くするためそのまま保持してください)
    all_events = []
    # ... (ニュース取得処理) ...
    return all_events

all_events = fetch_news_data()

st.title("🚀 中小・スタートアップ B2Bレーダー")

# --- メイン：カレンダー表示 ---
st.header("📅 ニュースカレンダー")
calendar_options = {
    "initialView": "dayGridMonth",
    "selectable": True,
    "locale": "ja",
}

# カレンダー部品の呼び出し。keyを固定するのがコツです
state = calendar(events=all_events, options=calendar_options, key="fixed_b2b_calendar")

# --- クリック反応の強化ロジック ---
if state.get("dateClick"):
    clicked_date = state["dateClick"]["date"].split("T")[0]
    # 今選んでいる日付と違う日がクリックされたら、メモリを書き換えて強制再描画
    if clicked_date != st.session_state.selected_date:
        st.session_state.selected_date = clicked_date
        st.rerun()  # これで即座に下のリストが更新されます

st.divider()

# --- ニュース詳細一覧 ---
st.header(f"📌 {st.session_state.selected_date} の詳細一覧")
# ... (フィルタリングと表示処理) ...

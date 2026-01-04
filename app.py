import streamlit as st
import google.generativeai as genai
import feedparser
import pandas as pd
from datetime import datetime
import re

# --- 1. ページ基本設定 ---
st.set_page_config(
    layout="wide", 
    page_title="B2B ニュースまとめ AI",
    page_icon="📰"
)

# --- 2. APIキーの設定 (Secretsから読み込み) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ APIキーが設定されていません。Streamlit CloudのSecretsを確認してください。")
    st.stop()

# --- 3. ニュース取得用関数 ---
def get_news(rss_url):
    feed = feedparser.parse(rss_url)
    news_list = []
    for entry in feed.entries[:5]:  # 最新5件を取得
        news_list.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", ""),
            "summary": entry.get("summary", "")
        })
    return news_list

# --- 4. メイン UI ---
st.title("📰 B2B ニュースまとめ AI")
st.markdown("最新のビジネスニュースを取得し、Geminiが要約・分析します。")

# RSSフィードの設定（例：Google ニュースのビジネスカテゴリなど）
target_rss = st.text_input("取得するRSSフィードURL:", "https://news.google.com/rss/search?q=B2B+スタートアップ+日本&hl=ja&gl=JP&ceid=JP:ja")

if st.button("ニュースを取得して要約"):
    with st.spinner("ニュースを読み込み中..."):
        news_data = get_news(target_rss)
        
        if not news_data:
            st.error("ニュースを取得できませんでした。URLを確認してください。")
        else:
            for i, item in enumerate(news_data):
                with st.container():
                    st.markdown(f"### {i+1}. {item['title']}")
                    st.caption(f"公開日: {item['published']}")
                    
                    # AIで要約
                    try:
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        prompt = f"""
                        以下のニュース記事の内容を、B2Bビジネスの観点から3行で要約してください。
                        また、中小企業やスタートアップにとってのメリットを1点挙げてください。

                        記事タイトル: {item['title']}
                        元の概要: {item['summary']}
                        """
                        response = model.generate_content(prompt)
                        
                        st.markdown("**AIによる分析:**")
                        st.write(response.text)
                        st.markdown(f"[記事元を読む]({item['link']})")
                        st.divider()
                    except Exception as e:
                        st.error(f"AI要約中にエラーが発生しました: {e}")

# --- 修正箇所 (以前エラーが出ていた箇所に対応) ---
st.markdown("---")
# カッコを確実に閉じて記述
st.caption("※情報の正確性はAIの生成結果に依存します。必ずソース元を確認してください。")
st.caption("※上の枠内の文字を全選択(Ctrl+A)してコピーし、社内共有などに活用してください。")

# --- 5. サイドバー ---
with st.sidebar:
    st.header("設定・ヘルプ")
    st.info("""
    このアプリはGoogleニュース等のRSSフィードを取得し、Gemini 1.5 Flashを使用して要約を作成します。
    """)
    if st.button("キャッシュをクリア"):
        st.cache_data.clear()
        st.rerun()

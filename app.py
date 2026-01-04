import streamlit as st
import google.generativeai as genai
import feedparser
from datetime import datetime

# --- 1. ページ基本設定 ---
st.set_page_config(
    layout="wide", 
    page_title="B2B ニュースまとめ AI",
    page_icon="📰"
)

# --- 2. APIキーの設定 (Secretsから読み込み) ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    # 前後の空白を削除して設定（Illegal header valueエラー対策）
    genai.configure(api_key=api_key.strip())
else:
    st.error("⚠️ APIキーが設定されていません。Streamlit CloudのSecrets設定を確認してください。")
    st.stop()

# --- 3. ニュース取得関数 ---
def get_news(rss_url):
    feed = feedparser.parse(rss_url)
    return feed.entries[:5]  # 最新5件を返す

# --- 4. メイン UI ---
st.title("📰 B2B ニュースまとめ AI")
st.markdown("登録したRSSフィードから最新ニュースを取得し、GeminiがB2B視点で要約・分析します。")

# 取得先URLの入力（デフォルトはB2B/スタートアップ関連のGoogleニュースRSS）
default_url = "https://news.google.com/rss/search?q=B2B+スタートアップ+日本&hl=ja&gl=JP&ceid=JP:ja"
target_rss = st.text_input("RSSフィードURL:", default_url)

if st.button("ニュースを更新して要約"):
    with st.spinner("最新ニュースを取得中..."):
        entries = get_news(target_rss)
        
        if not entries:
            st.error("ニュースの取得に失敗しました。URLが正しいか確認してください。")
        else:
            for i, entry in enumerate(entries):
                with st.container():
                    st.subheader(f"{i+1}. {entry.title}")
                    st.caption(f"公開日: {entry.get('published', '不明')}")
                    
                    # Geminiによる要約と分析
                    try:
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        prompt = f"""
                        以下のニュース記事を読み、B2Bビジネスの観点から以下の2点を回答してください。
                        1. 記事の3行要約
                        2. 中小・スタートアップ企業が活用できるヒントやメリット

                        記事タイトル: {entry.title}
                        記事概要: {entry.get('summary', '')}
                        """
                        response = model.generate_content(prompt)
                        
                        st.markdown("**🤖 AIによる分析:**")
                        st.write(response.text)
                        st.markdown(f"[🔗 記事原文を見る]({entry.link})")
                        st.divider()
                    except Exception as e:
                        st.error(f"AI要約エラー: {e}")

# --- 5. フッター（エラー修正箇所） ---
st.markdown("---")
# 107行目付近で発生していたSyntaxError（カッコ閉じ忘れ）を確実に修正
st.caption("※情報の正確性はAIの生成結果に依存します。必ず元の記事を確認してください。")
st.caption("※枠内のテキストを全選択(Ctrl+A)してコピーし、チャットツール等での共有に活用してください。")

# --- 6. サイドバー ---
with st.sidebar:
    st.header("アプリについて")
    st.info("RSSフィードから情報を抽出し、Google Gemini 1.5 Flashを使用して要約を作成しています。")
    if st.button("キャッシュをクリア"):
        st.cache_data.clear()
        st.rerun()

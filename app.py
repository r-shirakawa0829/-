import streamlit as st
import feedparser

# --- 1. ページ基本設定 ---
st.set_page_config(
    layout="wide", 
    page_title="B2B ニュースリーダー",
    page_icon="📰"
)

# --- 2. メイン UI ---
st.title("📰 B2B ニュースリーダー")
st.markdown("最新のビジネス・スタートアップ関連ニュースを一覧表示します。（要約機能なし・APIキー不要）")

# RSSフィードURLの設定（B2B・スタートアップ関連のGoogleニュース）
default_url = "https://news.google.com/rss/search?q=B2B+スタートアップ+日本&hl=ja&gl=JP&ceid=JP:ja"
target_rss = st.text_input("RSSフィードURL:", default_url)

if st.button("ニュースを更新"):
    with st.spinner("最新ニュースを取得中..."):
        # RSSフィードを解析
        feed = feedparser.parse(target_rss)
        
        if not feed.entries:
            st.error("ニュースの取得に失敗しました。URLが正しいか確認するか、しばらく時間を置いて試してください。")
        else:
            st.success(f"最新のニュースを {len(feed.entries[:10])} 件表示します。")
            st.divider()
            
            # ニュースをループで表示（最新10件）
            for i, entry in enumerate(feed.entries[:10]):
                with st.container():
                    # タイトルをリンクにして表示
                    st.markdown(f"### {i+1}. [{entry.title}]({entry.link})")
                    
                    # 公開日があれば表示
                    if hasattr(entry, 'published'):
                        st.caption(f"📅 公開日: {entry.published}")
                    
                    # 記事の抜粋があれば表示（HTMLタグを除去して短く表示）
                    summary = entry.get('summary', '')
                    if summary:
                        # 簡易的なタグ除去と文字数制限
                        clean_summary = summary.split('<')[0][:200] 
                        st.write(clean_summary + "...")
                    
                    st.markdown(f"[👉 記事全文をブラウザで開く]({entry.link})")
                    st.divider()

# --- 3. サイドバー ---
with st.sidebar:
    st.header("設定")
    st.info("このアプリは外部通信（API）を使用せず、公開されているRSSフィードを直接読み込んでいます。")
    if st.button("表示をリセット"):
        st.rerun()

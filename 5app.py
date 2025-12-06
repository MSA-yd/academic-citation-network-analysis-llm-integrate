"""
Streamlit Web Application
Citation Network Visualization & Analysis Dashboard

Usage:
    streamlit run 5app.py
"""

import streamlit as st
import pandas as pd
import os
import requests
import json
import time
from pathlib import Path
from typing import Optional
from config import Config
from utils.logger import setup_logger
from openai import OpenAI

logger = setup_logger(__name__)

# Set page config
st.set_page_config(page_title="Citation Network Analysis", layout="wide")

# Ensure directories exist
Config.ensure_directories()

# Environment validation
missing_files, missing_env_vars = Config.validate_environment()
if missing_env_vars:
    st.sidebar.warning("⚠️ Some optional environment variables are not set:")
    for var in missing_env_vars:
        st.sidebar.text(f"  • {var}")

# Title
st.title("📚 Citation Network Visualization & Community Analysis")

# ========== Unified Data Loading Function ==========
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_all_data():
    """Load all data with caching"""
    from utils.data_loader import load_data_files
    
    try:
        papers, edges, node_df = load_data_files(raise_on_missing=False)
        
        if node_df.empty:
            st.warning("⚠️ Node community data not found. Run visualization script first.")
            comm_stats = pd.DataFrame()
        else:
            comm_stats = node_df.groupby(['leiden_comm', 'node_type']).size().unstack(fill_value=0)
            comm_stats['total'] = comm_stats.sum(axis=1)
        
        # Load PageRank results (if available)
        pagerank_df = None
        if Config.PAGERANK_RESULTS.exists():
            pagerank_df = pd.read_csv(Config.PAGERANK_RESULTS)
        
        return papers, edges, node_df, comm_stats, pagerank_df
    except FileNotFoundError as e:
        st.error(f"❌ Required data files not found: {e}")
        st.stop()
        return None, None, None, None, None

# ========== HTML File Caching ==========
@st.cache_data(ttl=3600)  # Cache HTML files for 1 hour
def load_html_file(file_path: Path) -> Optional[str]:
    """Load and cache HTML file content"""
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading HTML file {file_path}: {e}")
            return None
    return None

# ========== CSV File Caching ==========
@st.cache_data(ttl=3600)  # Cache CSV files for 1 hour
def load_csv_file(file_path: Path) -> pd.DataFrame:
    """Load and cache CSV file"""
    if file_path.exists():
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

papers, edges, node_df, comm_stats, pagerank_df = load_all_data()

# ========== Create Tabs ==========
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Network Visualization", 
    "Community Analysis", 
    "Paper Recommendations", 
    "LLM Analysis",
    "Rising Papers",
    "Topic Benchmarking"
])

# ========== Tab 1: Network Visualization ==========
with tab1:
    st.subheader("🖼️ Static Network Layouts")
    layout_options = ["kamada_kawai", "community_based", "multipart", "spring_improved"]
    selected_layout = st.selectbox("Choose a layout to view:", layout_options)
    
    image_path = Config.FIG_DIR / f"full_network_{selected_layout}.png"
    if image_path.exists():
        # 修复：移除width=True参数，让Streamlit自动处理
        st.image(str(image_path), caption=f"Layout: {selected_layout}")
    else:
        st.warning(f"Image not found: {image_path}")
    
    st.subheader("🌐 Interactive Network Graph")
    html_path = Config.FIG_DIR / "full_interactive_leiden_only.html"
    
    # 添加延迟加载选项，避免初始加载时卡顿
    show_interactive = st.checkbox("显示交互式网络图", value=False, help="大型网络图可能加载较慢")
    
    if show_interactive:
        html_content = load_html_file(html_path)
        if html_content:
            with st.spinner("正在加载交互式网络图..."):
                st.components.v1.html(html_content, height=900, scrolling=True)
        else:
            st.warning("Interactive graph not found.")
            st.info("💡 Run 'python 3visual.py' to generate visualizations.")
    else:
        st.info("💡 勾选上方复选框以加载交互式网络图")

# ========== Tab 2: Community Analysis ==========
with tab2:
    st.subheader("📊 Leiden Community Statistics")
    st.dataframe(comm_stats)
    
    st.subheader("🧾 Paper Label Mapping")
    label_map_path = Config.FIG_DIR / "paper_label_mapping.csv"
    if label_map_path.exists():
        label_df = load_csv_file(label_map_path)
        if not label_df.empty:
            st.dataframe(label_df)
        else:
            st.warning("Label mapping file is empty.")
    else:
        st.warning("Label mapping file not found.")
        st.info("💡 Run 'python 3visual.py' to generate label mappings.")

# ========== Tab 3: Paper Recommendations (Enhanced) ==========
with tab3:
    st.subheader("🎯 Enhanced PageRank-Based Paper Recommendation System")
    
    if pagerank_df is not None:
        # ===== 数据质量检查 =====
        if pagerank_df['pagerank_score'].nunique() == 1 and pagerank_df['temporal_pagerank_score'].nunique() == 1:
            st.error("❌ PageRank analysis appears to have failed: all scores are identical.")
            st.warning("This usually happens when the citation network lacks valid internal citation relationships.")
            st.info("💡 Please check your data collection and ensure you have papers that cite each other.")
        else:
            # ===== 1. 综合推荐概览 =====
            st.markdown("### 📊 Recommendation Overview")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                top_hybrid = pagerank_df.iloc[0]
                st.metric("Top Hybrid Recommendation", 
                         f"{top_hybrid['title'][:30]}...",
                         f"HS: {top_hybrid['hybrid_score']:.4f}")
            
            with col2:
                top_citation = pagerank_df.loc[pagerank_df['citationCount'].idxmax()]
                st.metric("Most Cited Paper", 
                         f"{top_citation['title'][:30]}...",
                         f"Citations: {top_citation['citationCount']}")
            
            with col3:
                newest_top = pagerank_df[pagerank_df['year'] == pagerank_df['year'].max()].iloc[0]
                st.metric("Top Recent Paper", 
                         f"{newest_top['title'][:30]}...",
                         f"Year: {newest_top['year']}")
            
            # ===== 2. 多维度推荐列表 =====
            st.markdown("### 📚 Classic Must-Read Papers (Standard PageRank)")
            st.info("💡 These papers have the highest influence in the citation network.")
            
            top_std = pagerank_df.sort_values('pagerank_score', ascending=False).head(15).copy()
            top_std['Rank'] = range(1, len(top_std) + 1)
            top_std_display = top_std[['Rank', 'title', 'year', 'pagerank_score', 'citationCount']].copy()
            top_std_display.columns = ['Rank', 'Paper Title', 'Year', 'PageRank Score', 'Citations']
            st.dataframe(top_std_display, hide_index=True)

            st.markdown("### 🔥 Emerging Hot Papers (Temporal PageRank)")
            st.info("💡 These papers are gaining traction in recent citations.")
            
            top_temp = pagerank_df.sort_values('temporal_pagerank_score', ascending=False).head(15).copy()
            top_temp['Rank'] = range(1, len(top_temp) + 1)
            top_temp_display = top_temp[['Rank', 'title', 'year', 'temporal_pagerank_score', 'citationCount']].copy()
            top_temp_display.columns = ['Rank', 'Paper Title', 'Year', 'Temporal Score', 'Citations']
            st.dataframe(top_temp_display, hide_index=True)

            st.markdown("### ⭐ Quality-Weighted Recommendations")
            st.info("💡 These papers are cited by high-quality/influential papers.")
            
            top_quality = pagerank_df.sort_values('quality_pagerank_score', ascending=False).head(15).copy()
            top_quality['Rank'] = range(1, len(top_quality) + 1)
            top_quality_display = top_quality[['Rank', 'title', 'year', 'quality_pagerank_score', 'citationCount', 'influentialCitationCount']].copy()
            top_quality_display.columns = ['Rank', 'Paper Title', 'Year', 'Quality Score', 'Citations', 'Influential Citations']
            st.dataframe(top_quality_display, hide_index=True)

            # ===== 3. 年度趋势分析 =====
            st.markdown("### 📈 Yearly Trends Analysis")
            year_stats = pagerank_df.groupby('year').agg({
                'pagerank_score': 'mean',
                'temporal_pagerank_score': 'mean',
                'hybrid_score': 'mean',
                'citationCount': 'mean',
                'arxiv_id': 'count'
            }).round(4)
            year_stats.columns = ['Avg Standard PR', 'Avg Temporal PR', 'Avg Hybrid Score', 'Avg Citations', 'Paper Count']
            st.dataframe(year_stats)
            
            # ===== 4. 对比分析图表 =====
            st.markdown("### 📊 Interactive Visualization Analysis")
            
            # 检查图表文件是否存在
            temporal_viz_path = Config.FIG_DIR / "temporal_recommendations.html"
            comparison_viz_path = Config.FIG_DIR / "pagerank_comparison.html"
            hybrid_viz_path = Config.FIG_DIR / "hybrid_analysis.html"
            
            viz_tabs = st.tabs(["Temporal Recommendations", "PageRank Comparison", "Hybrid Analysis"])
            
            with viz_tabs[0]:
                html_content = load_html_file(temporal_viz_path)
                if html_content:
                    st.components.v1.html(html_content, height=600, scrolling=True)
                else:
                    st.info("Temporal recommendations chart not available. Run PageRank analysis to generate it.")
            
            with viz_tabs[1]:
                html_content = load_html_file(comparison_viz_path)
                if html_content:
                    st.components.v1.html(html_content, height=600, scrolling=True)
                else:
                    st.info("PageRank comparison chart not available. Run PageRank analysis to generate it.")
            
            with viz_tabs[2]:
                html_content = load_html_file(hybrid_viz_path)
                if html_content:
                    st.components.v1.html(html_content, height=600, scrolling=True)
                else:
                    st.info("Hybrid analysis chart not available. Run PageRank analysis to generate it.")

            # ===== 5. 高级搜索和筛选 =====
            st.markdown("### 🔍 Advanced Paper Search & Filtering")
            
            # 年份筛选
            col1, col2 = st.columns(2)
            with col1:
                min_year, max_year = int(pagerank_df['year'].min()), int(pagerank_df['year'].max())
                selected_years = st.slider("Select Year Range", min_year, max_year, (min_year, max_year))
            
            with col2:
                min_citations = st.number_input("Minimum Citations", min_value=0, value=0)
            
            # 排名类型选择
            rank_type = st.selectbox("Sort by Ranking Type", 
                                   ["Hybrid Score", "Standard PageRank", "Temporal PageRank", "Quality PageRank", "Citation Count"])
            
            # 应用筛选
            filtered_df = pagerank_df[
                (pagerank_df['year'] >= selected_years[0]) & 
                (pagerank_df['year'] <= selected_years[1]) &
                (pagerank_df['citationCount'] >= min_citations)
            ].copy()
            
            # 应用排序
            if rank_type == "Hybrid Score":
                filtered_df = filtered_df.sort_values('hybrid_score', ascending=False)
            elif rank_type == "Standard PageRank":
                filtered_df = filtered_df.sort_values('pagerank_score', ascending=False)
            elif rank_type == "Temporal PageRank":
                filtered_df = filtered_df.sort_values('temporal_pagerank_score', ascending=False)
            elif rank_type == "Quality PageRank":
                filtered_df = filtered_df.sort_values('quality_pagerank_score', ascending=False)
            else:  # Citation Count
                filtered_df = filtered_df.sort_values('citationCount', ascending=False)
            
            # 显示结果
            if not filtered_df.empty:
                filtered_df['Rank'] = range(1, len(filtered_df) + 1)
                display_cols = ['Rank', 'title', 'year', 'citationCount']
                if rank_type == "Hybrid Score":
                    display_cols.extend(['hybrid_score'])
                elif rank_type == "Standard PageRank":
                    display_cols.extend(['pagerank_score'])
                elif rank_type == "Temporal PageRank":
                    display_cols.extend(['temporal_pagerank_score'])
                elif rank_type == "Quality PageRank":
                    display_cols.extend(['quality_pagerank_score'])
                
                st.dataframe(filtered_df[display_cols].head(20), hide_index=True)
                st.caption(f"Showing {min(20, len(filtered_df))} of {len(filtered_df)} papers")
            else:
                st.warning("No papers match your criteria.")

            # ===== 6. 论文详情查看 =====
            st.markdown("### 📄 Paper Details")
            paper_search = st.text_input("Search for a specific paper by title or arXiv ID:")
            
            if paper_search:
                search_results = pagerank_df[
                    pagerank_df['title'].str.contains(paper_search, case=False, na=False) |
                    pagerank_df['arxiv_id'].str.contains(paper_search, case=False, na=False)
                ]
                
                if not search_results.empty:
                    selected_paper = search_results.iloc[0]
                    st.subheader(f"📝 {selected_paper['title']}")
                    
                    # 基本信息
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Year", selected_paper['year'])
                    with col2:
                        st.metric("Citations", selected_paper['citationCount'])
                    with col3:
                        st.metric("Influential Citations", selected_paper.get('influentialCitationCount', 'N/A'))
                    
                    # 排名信息
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.metric("Hybrid Rank", selected_paper['rank_hybrid'])
                    with col5:
                        st.metric("Standard PR Rank", selected_paper['rank_std'])
                    with col6:
                        st.metric("Temporal PR Rank", selected_paper['rank_temp'])
                    
                    # 分数详情
                    st.markdown("#### 📊 Detailed Scores")
                    score_cols = st.columns(5)
                    score_cols[0].metric("Hybrid Score", f"{selected_paper['hybrid_score']:.4f}")
                    score_cols[1].metric("Standard PR", f"{selected_paper['pagerank_score']:.6f}")
                    score_cols[2].metric("Temporal PR", f"{selected_paper['temporal_pagerank_score']:.6f}")
                    score_cols[3].metric("Quality PR", f"{selected_paper['quality_pagerank_score']:.6f}")
                    score_cols[4].metric("Citation Rank", f"{selected_paper['rank_citation']}")
                    
                else:
                    st.warning("No matching papers found.")
            
    else:
        st.warning("⚠️ PageRank analysis results not found. Please run `python pagerank_analyzer.py` first.")
        st.code("python pagerank_analyzer.py", language="bash")

# ========== Tab 4: LLM Analysis ==========
with tab4:
    st.subheader("📄 LLM Paper Citation Analyzer")
    
    # Load API configuration from config
    from config import Config
    
    # Determine which API to use (优先级: DashScope > OpenAI > OpenRouter)
    use_dashscope = Config.USE_DASHSCOPE and Config.DASHSCOPE_API_KEY
    use_openai = Config.USE_OPENAI and Config.OPENAI_API_KEY and not use_dashscope
    use_openrouter = Config.OPENROUTER_API_KEY and not use_dashscope and not use_openai
    
    # Initialize OpenAI client if needed
    openai_client = None
    
    if use_dashscope:
        API_KEY = Config.DASHSCOPE_API_KEY
        MODEL = Config.DASHSCOPE_MODEL
        url = Config.DASHSCOPE_URL
        api_name = "DashScope (百炼)"
        headers = {
            "X-DashScope-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
    elif use_openai:
        API_KEY = Config.OPENAI_API_KEY
        MODEL = Config.OPENAI_MODEL
        url = None  # 使用 OpenAI 客户端，不需要 URL
        api_name = "OpenAI (ChatAnywhere)"
        headers = None  # OpenAI 客户端会自动处理 headers
        openai_client = OpenAI(
            api_key=API_KEY,
            base_url=Config.OPENAI_BASE_URL
        )
    elif use_openrouter:
        API_KEY = Config.OPENROUTER_API_KEY
        MODEL = Config.OPENROUTER_MODEL
        url = Config.OPENROUTER_URL
        api_name = "OpenRouter"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    else:
        API_KEY = None
        MODEL = None
        url = None
        api_name = None
        headers = None
    
    if not API_KEY:
        st.warning("⚠️ No LLM API key set. LLM analysis features will be disabled.")
        st.info("💡 Set DASHSCOPE_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY environment variable to enable LLM analysis.")
    else:
        st.success(f"✅ Using {api_name} API")
    
    # Helper functions
    def get_paper(arxiv_id):
        arxiv_id = arxiv_id.lower().replace("arxiv:", "").strip()
        papers_local = papers.copy()
        papers_local['arxiv_id'] = papers_local['arxiv_id'].astype(str).str.lower().str.replace("arxiv:", "").str.strip()
        match = papers_local[papers_local['arxiv_id'] == arxiv_id]
        if not match.empty:
            return match.iloc[0]
        match = papers_local[papers_local['arxiv_id'].str.contains(arxiv_id, na=False)]
        if not match.empty:
            return match.iloc[0]
        return None
    
    def get_citation_context(arxiv_id):
        # Convert arxiv_id to match edge format
        arxiv_id_formatted = f"arXiv:{arxiv_id}"
        cited_by = edges[edges['target'] == arxiv_id]['source'].tolist()
        cites = edges[edges['source'] == arxiv_id_formatted]['target'].tolist()
        return cited_by, cites
    
    def build_prompt(task, arxiv_id):
        paper = get_paper(arxiv_id)
        if paper is None:
            return None
        title = paper['title']
        abstract = paper['abstract']
        cited_by, cites = get_citation_context(arxiv_id)
        if task == "context":
            return (
                f"Paper Title: {title}\n"
                f"Abstract: {abstract}\n"
                f"Cited by: {', '.join(cited_by[:10]) if cited_by else 'None'}\n"
                f"Cites: {', '.join(str(c)[:20] for c in cites[:10]) if cites else 'None'}\n"
                "Classify the citation context of this paper."
            )
        elif task == "summary":
            return f"Summarize the following abstract:\n\n{abstract}"
        elif task == "sentiment":
            return f"Analyze the sentiment of this abstract:\n\n{abstract}"
        else:
            return None
    
    def chat_with_model(prompt):
        """Call LLM API (DashScope, OpenAI, or OpenRouter) with rate limiting"""
        if not API_KEY:
            return "API key not configured"
        
        # 使用 OpenAI 客户端
        if use_openai and openai_client:
            rate_limit = Config.OPENAI_RATE_LIMIT
            time.sleep(1.0 / rate_limit)  # Rate limiting
            try:
                response = openai_client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return f"Error: {str(e)}"
        
        # 使用 REST API (DashScope 或 OpenRouter)
        if not headers:
            return "API key not configured"
        
        # Determine rate limit based on API provider
        if use_dashscope:
            rate_limit = Config.DASHSCOPE_RATE_LIMIT
            payload = {
                "model": MODEL,
                "input": {
                    "messages": [{"role": "user", "content": prompt}]
                },
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            }
        else:
            rate_limit = Config.OPENROUTER_RATE_LIMIT
            payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}]
            }
        
        time.sleep(1.0 / rate_limit)  # Rate limiting
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            if response.status_code == 200:
                if use_dashscope:
                    # DashScope response format
                    return response.json()["output"]["choices"][0]["message"]["content"]
                else:
                    # OpenRouter response format
                    return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            return f"Network error: {str(e)}"
    
    task = st.selectbox("Choose a task", ["summary", "context", "sentiment"])
    arxiv_id = st.text_input("Enter arXiv ID (e.g., 2510.14973)")
    
    if st.button("Analyze"):
        if not API_KEY:
            st.error("❌ LLM API key not configured. Cannot perform LLM analysis.")
            st.info("💡 Set DASHSCOPE_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY environment variable.")
        else:
            prompt = build_prompt(task, arxiv_id)
            if prompt:
                with st.spinner("Calling model..."):
                    result = chat_with_model(prompt)
                st.subheader("🧠 Model Response")
                st.write(result)
            else:
                st.error("Invalid arXiv ID or paper not found.")
    
    # Optional: show paper metadata
    if arxiv_id:
        paper = get_paper(arxiv_id)
        if paper is not None:
            st.subheader("📑 Paper Metadata")
            st.write({
                'arxiv_id': paper.get('arxiv_id', 'N/A'),
                'title': paper.get('title', 'N/A'),
                'year': paper.get('year', 'N/A'),
                'abstract': paper.get('abstract', 'N/A')[:500] + '...' if len(str(paper.get('abstract', ''))) > 500 else paper.get('abstract', 'N/A')
            })

# ========== Tab 5: Rising Papers ==========
with tab5:
    st.subheader("🚀 Next-Breakthrough Candidates (Rising PageRank)")
    st.info("💡 Papers with rising PageRank scores over time - potential breakthrough candidates")
    
    # Check if using predictions or real history
    if Config.PAGERANK_HISTORY.exists():
        try:
            history_df = pd.read_csv(Config.PAGERANK_HISTORY)
            unique_timestamps = history_df['timestamp'].nunique() if not history_df.empty else 0
            if unique_timestamps < 2:
                st.warning("⚠️ Limited history data. Showing predictions based on current metrics.")
            else:
                st.success(f"✅ Using real history data ({unique_timestamps} time points)")
        except:
            pass
    
    if Config.RISING_PAGERANK_PAPERS.exists():
        try:
            rising_df = pd.read_csv(Config.RISING_PAGERANK_PAPERS)
            
            if not rising_df.empty:
                st.markdown(f"### Found {len(rising_df)} Rising Papers")
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    min_growth = st.slider("Minimum Growth Rate", 0.0, 1.0, 0.1, 0.05)
                with col2:
                    show_early_only = st.checkbox("Show Early Stage Only (< 50 citations)", value=False)
                
                # Filter data
                filtered_df = rising_df[rising_df['growth_rate'] >= min_growth]
                if show_early_only:
                    filtered_df = filtered_df[filtered_df['is_early_stage'] == True]
                
                if not filtered_df.empty:
                    # Check if prediction type column exists
                    if 'prediction_type' in filtered_df.columns:
                        # This is predicted data
                        display_cols = ['title', 'year', 'growth_rate', 'temporal_pagerank', 
                                       'current_pagerank', 'citationCount', 'is_early_stage']
                        display_df = filtered_df[display_cols].copy()
                        display_df.columns = ['Title', 'Year', 'Potential Score', 'Temporal PageRank', 
                                            'Current PageRank', 'Citations', 'Early Stage']
                        st.caption("ℹ️ Based on current metrics prediction (high temporal PageRank, low citations, recent papers)")
                    else:
                        # This is real history data
                        display_cols = ['title', 'year', 'growth_rate', 'current_pagerank', 
                                       'citationCount', 'is_early_stage']
                        display_df = filtered_df[display_cols].copy()
                        display_df.columns = ['Title', 'Year', 'Growth Rate', 'Current PageRank', 'Citations', 'Early Stage']
                        st.caption("ℹ️ Based on historical PageRank tracking")
                    
                    display_df = display_df.sort_values('Potential Score' if 'Potential Score' in display_df.columns else 'Growth Rate', ascending=False)
                    
                    st.dataframe(display_df, hide_index=True, width='stretch')
                    
                    # Show top paper details
                    if len(filtered_df) > 0:
                        top_paper = filtered_df.iloc[0]
                        st.markdown("### 📈 Top Rising Paper")
                        st.write(f"**{top_paper['title']}**")
                        if 'prediction_type' in top_paper:
                            st.metric("Potential Score", f"{top_paper['growth_rate']:.3f}")
                            if 'temporal_pagerank' in top_paper:
                                st.metric("Temporal PageRank", f"{top_paper['temporal_pagerank']:.6f}")
                        else:
                            st.metric("Growth Rate", f"{top_paper['growth_rate']:.1%}")
                        st.metric("Current PageRank", f"{top_paper['current_pagerank']:.6f}")
                        st.metric("Citations", int(top_paper['citationCount']))
                else:
                    st.warning("No papers match the selected criteria.")
            else:
                st.info("No rising papers found yet.")
                st.info("💡 The system will automatically use predictions based on current metrics if history is unavailable.")
        except Exception as e:
            st.error(f"Error loading rising papers: {e}")
    else:
        st.warning("⚠️ Rising papers data not found.")
        st.info("💡 Run `python 4pagerank_analyzer.py` to generate rising paper predictions.")
        st.info("   The system will use current metrics (temporal PageRank, citations, recency) to identify potential rising papers.")

# ========== Tab 6: Topic Benchmarking ==========
with tab6:
    st.subheader("📊 Community Topics vs QS Taxonomy")
    st.info("💡 Compare detected research communities with established academic taxonomies")
    
    if Config.TAXONOMY_BENCHMARK.exists():
        try:
            taxonomy_df = pd.read_csv(Config.TAXONOMY_BENCHMARK)
            
            if not taxonomy_df.empty:
                st.markdown(f"### Benchmarking Results for {len(taxonomy_df)} Communities")
                
                # Filter by similarity score
                min_similarity = st.slider("Minimum Similarity Score", 0.0, 1.0, 0.0, 0.05)
                filtered_tax = taxonomy_df[taxonomy_df['similarity_score'] >= min_similarity]
                
                if not filtered_tax.empty:
                    display_tax = filtered_tax[[
                        'community_id', 'community_topic', 
                        'matched_qs_category', 'similarity_score'
                    ]].copy()
                    display_tax.columns = [
                        'Community ID', 'Detected Topic', 
                        'Matched QS Category', 'Similarity Score'
                    ]
                    display_tax = display_tax.sort_values('Similarity Score', ascending=False)
                    
                    st.dataframe(display_tax, hide_index=True, width='stretch')
                    
                    # Show statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Similarity", f"{filtered_tax['similarity_score'].mean():.3f}")
                    with col2:
                        st.metric("High Match (>0.5)", len(filtered_tax[filtered_tax['similarity_score'] > 0.5]))
                    with col3:
                        st.metric("Total Communities", len(filtered_tax))
                else:
                    st.warning("No communities match the similarity threshold.")
            else:
                st.info("No taxonomy benchmarking data available.")
        except Exception as e:
            st.error(f"Error loading taxonomy benchmark: {e}")
    else:
        st.warning("⚠️ Taxonomy benchmark data not found.")
        st.info("💡 Run topic analysis to generate this data.")
        st.info("   Note: This requires OPENROUTER_API_KEY to be set for LLM topic generation.")
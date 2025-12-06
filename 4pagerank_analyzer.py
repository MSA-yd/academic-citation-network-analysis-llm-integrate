#!/usr/bin/env python3
"""
PageRank Analysis Module - Optimized Academic Citation Analysis
Computes standard PageRank and Temporal PageRank for paper recommendations
with proper academic citation network structure and quality-weighted analysis
"""

import pandas as pd
import networkx as nx
import math
import ast
from pathlib import Path
from typing import Dict, Tuple, Optional
from config import Config
from utils.logger import setup_logger
from utils.data_loader import load_data_files, validate_papers_dataframe, validate_edges_dataframe

# 🔥 新增：图表生成相关导入
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = setup_logger(__name__)


def load_and_prepare_data(
    paper_file: Optional[Path] = None,
    edge_file: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and prepare data
    
    Parameters:
    -----------
    paper_file : Optional[Path]
        Path to paper CSV file (default: Config.PAPERS_CLEANED)
    edge_file : Optional[Path]
        Path to edge CSV file (default: Config.EDGES_CLEANED)
        
    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame]
        (papers, edges) DataFrames
    """
    paper_file = paper_file or Config.PAPERS_CLEANED
    edge_file = edge_file or Config.EDGES_CLEANED
    
    logger.info("Loading data...")
    papers, edges, _ = load_data_files(paper_file, edge_file, None)
    
    validate_papers_dataframe(papers)
    validate_edges_dataframe(edges)
    
    logger.info(f"Loaded: {len(papers)} papers, {len(edges)} citation edges")
    
    return papers, edges


def parse_references(references_str):
    """Parse references string to list"""
    if pd.isna(references_str) or references_str == '' or references_str == '[]':
        return []
    
    try:
        if isinstance(references_str, str):
            references = ast.literal_eval(references_str)
        else:
            references = references_str
        
        if isinstance(references, list):
            return references
        else:
            return []
    except (ValueError, SyntaxError):
        return []


def build_academic_citation_graph_optimized(
    papers: pd.DataFrame,
    edges: pd.DataFrame
) -> Tuple[nx.DiGraph, Dict[str, Dict]]:
    """
    Build academic citation graph using reference network for PageRank
    Reference network: paper -> reference (reverse for PageRank: reference <- paper)
    """
    logger.info("Building optimized academic citation graph using reference network...")
    
    # Create paper dictionary
    paper_dict = {}
    s2_to_arxiv = {}  # Map S2 IDs to arXiv IDs
    
    for _, row in papers.iterrows():
        arxiv_id = str(row['arxiv_id']).strip()
        s2_id = str(row['s2_paperId']).strip() if pd.notna(row['s2_paperId']) else None
        
        paper_dict[arxiv_id] = {
            'title': row['title'],
            'year': int(row['year']) if pd.notna(row['year']) else None,
            's2_paperId': s2_id,
            'citationCount': int(row.get('citationCount', 0)) if pd.notna(row.get('citationCount')) else 0,
            'influentialCitationCount': int(row.get('influentialCitationCount', 0)) if pd.notna(row.get('influentialCitationCount')) else 0
        }
        
        if s2_id and s2_id not in ['nan', '']:
            s2_to_arxiv[s2_id] = arxiv_id
    
    logger.info(f"Internal papers in dataset: {len(paper_dict)}")
    
    # Build graph with only our papers as nodes
    G = nx.DiGraph()
    for arxiv_id in paper_dict:
        G.add_node(arxiv_id, **paper_dict[arxiv_id])
    
    # Process reference edges: paper -> reference
    # For PageRank, we want: reference <- paper (who cites this reference)
    reference_edges = edges[edges['type'] == 'reference'] if 'type' in edges.columns else edges
    
    internal_references = 0
    external_references = 0
    
    for _, row in reference_edges.iterrows():
        paper_raw = str(row['source']).strip()
        reference_raw = str(row['target']).strip()
        
        # Extract paper ID (remove "arXiv:" prefix if present)
        paper_id = paper_raw[6:] if paper_raw.startswith('arXiv:') else paper_raw
        
        if paper_id in paper_dict:
            if reference_raw in s2_to_arxiv:
                # Reference is in our dataset - create reverse edge for PageRank
                reference_arxiv = s2_to_arxiv[reference_raw]
                if paper_id != reference_arxiv:
                    # Add edge: reference_arxiv <- paper_id
                    # This means paper_id cites reference_arxiv
                    # 👇 添加边属性：年份和质量（来自引用者 paper_id）
                    citing_paper_info = paper_dict[paper_id]
                    source_year = citing_paper_info['year']
                    source_quality = citing_paper_info['citationCount'] + 2 * citing_paper_info['influentialCitationCount']
                    
                    G.add_edge(
                        reference_arxiv, 
                        paper_id, 
                        year=source_year,          # 引用者发表年份
                        quality=source_quality     # 引用者质量分
                    )
                    internal_references += 1
            else:
                # Reference is external - we can't include it in our PageRank
                external_references += 1
    
    logger.info(f"Internal references used: {internal_references}, External references: {external_references}")
    logger.info(f"Graph stats: {len(G.nodes())} nodes, {G.number_of_edges()} edges")
    
    return G, paper_dict


def compute_optimized_pagerank(
    G: nx.DiGraph,
    alpha: float = None
) -> Dict[str, float]:
    """
    Compute optimized PageRank using NetworkX implementation
    
    Parameters:
    -----------
    G : nx.DiGraph
        Academic citation graph with external node
    alpha : float, optional
        Damping factor (default: Config.PAGERANK_ALPHA)
        
    Returns:
    --------
    Dict[str, float]
        PageRank scores for internal nodes only
    """
    alpha = alpha or Config.PAGERANK_ALPHA
    logger.info(f"Computing optimized PageRank (alpha={alpha})...")
    
    # Remove external node temporarily for standard PageRank calculation
    G_internal = G.copy()
    if 'EXTERNAL' in G_internal.nodes():
        G_internal.remove_node('EXTERNAL')
    
    if len(G_internal.nodes()) == 0:
        logger.warning("No internal nodes for PageRank calculation")
        return {}
    
    try:
        # Use NetworkX's optimized PageRank implementation
        pr_scores = nx.pagerank(G_internal, alpha=alpha, max_iter=100, tol=1e-6)
        logger.info("PageRank computation completed successfully")
        return pr_scores
    except Exception as e:
        logger.warning(f"NetworkX PageRank failed, using fallback: {e}")
        # Fallback to manual implementation if needed
        return manual_pagerank_fallback(G_internal, alpha)


def manual_pagerank_fallback(
    G: nx.DiGraph,
    alpha: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6
) -> Dict[str, float]:
    """Manual PageRank implementation as fallback"""
    N = len(G.nodes())
    if N == 0:
        return {}
    
    # Initialize PageRank values
    pr = {node: 1.0 / N for node in G.nodes()}
    
    for iteration in range(max_iter):
        pr_new = {}
        
        for node in G.nodes():
            # Calculate incoming PageRank
            incoming_pr = 0
            for pred in G.predecessors(node):
                # Calculate out-degree for the predecessor
                out_degree = G.out_degree(pred)
                if out_degree > 0:
                    incoming_pr += pr[pred] / out_degree
            
            # Calculate new PageRank
            pr_new[node] = (1 - alpha) / N + alpha * incoming_pr
        
        # Check for convergence
        diff = sum(abs(pr_new[node] - pr[node]) for node in G.nodes())
        if diff < tol:
            logger.info(f"Manual PageRank converged after {iteration + 1} iterations")
            break
            
        pr = pr_new
    
    return pr


def compute_temporal_weighted_pagerank(
    G: nx.DiGraph,
    paper_dict: Dict[str, Dict],
    decay_lambda: float = None,
    alpha: float = None
) -> Dict[str, float]:
    """
    Compute Temporal Weighted PageRank with exponential time decay
    """
    decay_lambda = decay_lambda or Config.TEMPORAL_DECAY_LAMBDA
    alpha = alpha or Config.PAGERANK_ALPHA
    
    logger.info(f"Computing Temporal Weighted PageRank (λ={decay_lambda}, alpha={alpha})...")
    
    # Get current year from data
    years = [paper['year'] for paper in paper_dict.values() if paper['year'] is not None]
    current_year = max(years) if years else 2025
    logger.info(f"Using current year: {current_year}")
    
    # Create weighted graph based on citation time
    G_weighted = nx.DiGraph()
    
    # Copy nodes
    for node in G.nodes():
        if node != 'EXTERNAL':
            G_weighted.add_node(node)
    
    # Add weighted edges based on exponential time decay
    # 👇 从边属性中读取年份，而不是从 paper_dict 中查找
    for source, target, edge_data in G.edges(data=True):
        if source != 'EXTERNAL' and target != 'EXTERNAL':
            source_year = edge_data.get('year')  # 从边属性获取
            if source_year:
                time_diff = current_year - source_year
                weight = math.exp(-decay_lambda * time_diff)
            else:
                weight = 1.0
            
            G_weighted.add_edge(source, target, weight=weight)
    
    if len(G_weighted.nodes()) == 0:
        logger.warning("No internal nodes for temporal PageRank calculation")
        return {}
    
    try:
        pr_scores = nx.pagerank(G_weighted, alpha=alpha, weight='weight', max_iter=100, tol=1e-6)
        logger.info("Temporal weighted PageRank computation completed")
        return pr_scores
    except Exception as e:
        logger.warning(f"Weighted PageRank failed: {e}")
        return compute_optimized_pagerank(G, alpha)


def compute_quality_weighted_pagerank(
    G: nx.DiGraph,
    papers_df: pd.DataFrame,
    alpha: float = None
) -> Dict[str, float]:
    """
    Compute Quality Weighted PageRank considering citation quality
    """
    alpha = alpha or Config.PAGERANK_ALPHA
    logger.info(f"Computing Quality Weighted PageRank (alpha={alpha})...")
    
    # Create weighted graph based on citing paper quality
    G_weighted = nx.DiGraph()
    
    # Copy nodes
    for node in G.nodes():
        if node != 'EXTERNAL':
            G_weighted.add_node(node)
    
    # Add weighted edges based on citing paper quality
    # 👇 从边属性中读取质量，而不是重新计算
    for source, target, edge_data in G.edges(data=True):
        if source != 'EXTERNAL' and target != 'EXTERNAL':
            source_quality = edge_data.get('quality', 1.0)  # 从边属性获取
            weight = math.log(1 + source_quality)
            
            G_weighted.add_edge(source, target, weight=weight)
    
    if len(G_weighted.nodes()) == 0:
        logger.warning("No internal nodes for quality weighted PageRank calculation")
        return {}
    
    try:
        pr_scores = nx.pagerank(G_weighted, alpha=alpha, weight='weight', max_iter=100, tol=1e-6)
        logger.info("Quality weighted PageRank computation completed")
        return pr_scores
    except Exception as e:
        logger.warning(f"Quality weighted PageRank failed: {e}")
        return compute_optimized_pagerank(G, alpha)


def generate_charts(results: pd.DataFrame, output_dir: Path):
    """
    Generate HTML visualization charts
    
    Parameters:
    -----------
    results : pd.DataFrame
        PageRank results DataFrame
    output_dir : Path
        Directory to save HTML charts
    """
    logger.info("Generating visualization charts...")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Temporal Recommendations Chart - Top 20 papers with highest temporal PageRank
    top_temp = results.nsmallest(20, 'rank_temp').sort_values('temporal_pagerank_score', ascending=False)
    
    fig1 = px.bar(
        top_temp,
        x='temporal_pagerank_score',
        y='title',
        orientation='h',
        title='Top 20 Emerging Hot Papers (Temporal PageRank)',
        labels={'temporal_pagerank_score': 'Temporal PageRank Score', 'title': 'Paper Title'},
        hover_data=['year', 'rank_temp', 'pagerank_score', 'citationCount']
    )
    fig1.update_layout(
        height=800,
        xaxis_title='Temporal PageRank Score',
        yaxis_title='Paper Title'
    )
    
    # Ensure fig subdirectory exists
    fig_output_dir = output_dir / "fig"
    fig_output_dir.mkdir(parents=True, exist_ok=True)
    fig1.write_html(fig_output_dir / "temporal_recommendations.html")
    
    # 2. Comparison Chart - Top 10 papers showing both scores
    top_comparison = results.nsmallest(10, 'rank_temp').sort_values('temporal_pagerank_score', ascending=False)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=top_comparison['title'],
        x=top_comparison['pagerank_score'],
        name='Standard PageRank',
        orientation='h',
        marker_color='blue',
        hovertemplate='<b>%{y}</b><br>Standard PR: %{x:.6f}<extra></extra>'
    ))
    fig2.add_trace(go.Bar(
        y=top_comparison['title'],
        x=top_comparison['temporal_pagerank_score'],
        name='Temporal PageRank',
        orientation='h',
        marker_color='red',
        hovertemplate='<b>%{y}</b><br>Temporal PR: %{x:.6f}<extra></extra>'
    ))
    
    fig2.update_layout(
        title='Top 10 Papers: Standard vs Temporal PageRank Comparison',
        xaxis_title='PageRank Score',
        yaxis_title='Paper Title',
        height=600,
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig2.write_html(fig_output_dir / "pagerank_comparison.html")
    
    # 3. Enhanced hybrid score analysis
    top_hybrid = results.head(20)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=top_hybrid['year'],
        y=top_hybrid['citationCount'],
        mode='markers',
        marker=dict(
            size=top_hybrid['hybrid_score'] * 1000,  # Scale for visibility
            color=top_hybrid['pagerank_score'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="PageRank Score")
        ),
        text=top_hybrid['title'],
        hovertemplate='<b>%{text}</b><br>Year: %{x}<br>Citations: %{y}<br>Hybrid Score: %{marker.size}<extra></extra>',
        name='Papers'
    ))
    
    fig3.update_layout(
        title='Hybrid Score Analysis: Year vs Citation Count (Size = Hybrid Score)',
        xaxis_title='Publication Year',
        yaxis_title='Citation Count',
        height=600
    )
    
    fig3.write_html(fig_output_dir / "hybrid_analysis.html")
    
    logger.info(f"Charts saved to {fig_output_dir}")


def generate_recommendations_enhanced(
    papers: pd.DataFrame,
    pr_std: Dict[str, float],
    pr_temp: Dict[str, float],
    pr_quality: Dict[str, float],
    output_file: Optional[Path] = None
) -> pd.DataFrame:
    """
    Enhanced recommendation system with multiple scoring methods
    Combines standard, temporal, and quality-weighted PageRank with citation factors
    
    Parameters:
    -----------
    papers : pd.DataFrame
        Papers DataFrame
    pr_std : Dict[str, float]
        Standard PageRank scores
    pr_temp : Dict[str, float]
        Temporal PageRank scores
    pr_quality : Dict[str, float]
        Quality weighted PageRank scores
    output_file : Optional[Path]
        Output CSV file path (default: Config.PAGERANK_RESULTS)
        
    Returns:
    --------
    pd.DataFrame
        Results DataFrame with rankings
    """
    output_file = output_file or Config.PAGERANK_RESULTS
    logger.info("Generating enhanced recommendation results with multiple scoring methods...")
    
    # Create result DataFrame
    results = papers[['arxiv_id', 'title', 'year']].copy()
    results['arxiv_id'] = results['arxiv_id'].astype(str)
    
    # Add citation metrics
    results['citationCount'] = papers.get('citationCount', 0).fillna(0).astype(int)
    results['influentialCitationCount'] = papers.get('influentialCitationCount', 0).fillna(0).astype(int)
    
    # Add PageRank scores
    results['pagerank_score'] = results['arxiv_id'].map(pr_std).fillna(0)
    results['temporal_pagerank_score'] = results['arxiv_id'].map(pr_temp).fillna(0)
    results['quality_pagerank_score'] = results['arxiv_id'].map(pr_quality).fillna(0)
    
    # Normalize scores using ranking percentiles for fair comparison
    results['pagerank_rank'] = results['pagerank_score'].rank(pct=True)
    results['temporal_pagerank_rank'] = results['temporal_pagerank_score'].rank(pct=True)
    results['quality_pagerank_rank'] = results['quality_pagerank_score'].rank(pct=True)
    results['citation_rank'] = results['citationCount'].rank(pct=True)
    results['year_rank'] = results['year'].rank(pct=True)  # Higher for newer papers
    
    # Calculate hybrid score with weighted combination
    weights = {
        'pagerank': 0.25,        # Standard network influence
        'temporal': 0.2,         # Time-based influence  
        'quality': 0.2,          # Quality-weighted influence
        'citation': 0.25,        # External impact (from Semantic Scholar)
        'recency': 0.1           # Newness factor
    }
    
    results['hybrid_score'] = (
        weights['pagerank'] * results['pagerank_rank'] +
        weights['temporal'] * results['temporal_pagerank_rank'] +
        weights['quality'] * results['quality_pagerank_rank'] +
        weights['citation'] * results['citation_rank'] +
        weights['recency'] * results['year_rank']
    )
    
    # Compute rankings (smaller rank number = higher score)
    results['rank_std'] = results['pagerank_score'].rank(method='dense', ascending=False).astype(int)
    results['rank_temp'] = results['temporal_pagerank_score'].rank(method='dense', ascending=False).astype(int)
    results['rank_quality'] = results['quality_pagerank_score'].rank(method='dense', ascending=False).astype(int)
    results['rank_citation'] = results['citationCount'].rank(method='dense', ascending=False).astype(int)
    results['rank_hybrid'] = results['hybrid_score'].rank(method='dense', ascending=False).astype(int)
    
    # Sort by hybrid score to get the main recommendation
    results = results.sort_values('hybrid_score', ascending=False)
    
    # Save results
    results.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"Results saved: {output_file}")
    
    # 🔥 新增：生成图表
    try:
        chart_dir = output_file.parent if output_file else Config.FIG_DIR
        generate_charts(results, chart_dir)
    except Exception as e:
        logger.warning(f"Failed to generate charts: {e}")
    
    # Display Top 10 by Standard PageRank
    logger.info("\n🏆 Top 10 Papers (Standard PageRank):")
    top10_std = results.sort_values('pagerank_score', ascending=False).head(10)
    for idx, row in top10_std.iterrows():
        logger.info(
            f"  {row['rank_std']:3d}. [{row['year']}] "
            f"{row['title'][:60]}... (PR: {row['pagerank_score']:.6f}, Citations: {row['citationCount']})"
        )
    
    # Display Top 10 by Temporal PageRank
    logger.info("\n🔥 Top 10 Papers (Temporal PageRank - Emerging Trends):")
    top10_temp = results.sort_values('temporal_pagerank_score', ascending=False).head(10)
    for idx, row in top10_temp.iterrows():
        logger.info(
            f"  {row['rank_temp']:3d}. [{row['year']}] "
            f"{row['title'][:60]}... (T-PR: {row['temporal_pagerank_score']:.6f}, Citations: {row['citationCount']})"
        )
    
    # Display Top 10 by Quality PageRank
    logger.info("\n⭐ Top 10 Papers (Quality PageRank - Influential Citations):")
    top10_quality = results.sort_values('quality_pagerank_score', ascending=False).head(10)
    for idx, row in top10_quality.iterrows():
        logger.info(
            f"  {row['rank_quality']:3d}. [{row['year']}] "
            f"{row['title'][:60]}... (Q-PR: {row['quality_pagerank_score']:.6f}, Citations: {row['citationCount']})"
        )
    
    # Display Top 10 by Citation Count
    logger.info("\n📊 Top 10 Papers (Citation Count):")
    top10_citation = results.sort_values('citationCount', ascending=False).head(10)
    for idx, row in top10_citation.iterrows():
        logger.info(
            f"  {row['rank_citation']:3d}. [{row['year']}] "
            f"{row['title'][:60]}... (Citations: {row['citationCount']}, PR: {row['pagerank_score']:.6f})"
        )
    
    # Display Top 10 by Hybrid Score (Main Recommendation)
    logger.info("\n🎯 Top 10 Papers (Hybrid Score - Recommended):")
    top10_hybrid = results.head(10)  # Already sorted by hybrid score
    for idx, row in top10_hybrid.iterrows():
        logger.info(
            f"  {row['rank_hybrid']:3d}. [{row['year']}] "
            f"{row['title'][:60]}... (HS: {row['hybrid_score']:.4f}, "
            f"PR: {row['pagerank_score']:.4f}, T-PR: {row['temporal_pagerank_score']:.4f}, "
            f"Q-PR: {row['quality_pagerank_score']:.4f}, Citations: {row['citationCount']})"
        )
    
    # Show comparison summary
    logger.info(f"\n📈 Recommendation Summary:")
    logger.info(f"  - Standard PR top paper: {top10_std.iloc[0]['title'][:50]}... [{top10_std.iloc[0]['year']}]")
    logger.info(f"  - Temporal PR top paper: {top10_temp.iloc[0]['title'][:50]}... [{top10_temp.iloc[0]['year']}]")
    logger.info(f"  - Quality PR top paper: {top10_quality.iloc[0]['title'][:50]}... [{top10_quality.iloc[0]['year']}]")
    logger.info(f"  - Citation top paper: {top10_citation.iloc[0]['title'][:50]}... [{top10_citation.iloc[0]['year']}]")
    logger.info(f"  - Hybrid top paper: {top10_hybrid.iloc[0]['title'][:50]}... [{top10_hybrid.iloc[0]['year']}]")
    
    return results


def run_pagerank_analysis(
    paper_file: Optional[Path] = None,
    edge_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
    decay_lambda: Optional[float] = None,
    alpha: Optional[float] = None
) -> Optional[pd.DataFrame]:
    """
    Run complete optimized PageRank analysis pipeline
    
    Parameters:
    -----------
    paper_file : Optional[Path]
        Path to paper data file (default: Config.PAPERS_CLEANED)
    edge_file : Optional[Path]
        Path to citation edge data file (default: Config.EDGES_CLEANED)
    output_file : Optional[Path]
        Path to output file (default: Config.PAGERANK_RESULTS)
    decay_lambda : Optional[float]
        Temporal PageRank time decay parameter (default: Config.TEMPORAL_DECAY_LAMBDA)
    alpha : Optional[float]
        PageRank damping factor (default: Config.PAGERANK_ALPHA)
        
    Returns:
    --------
    Optional[pd.DataFrame]
        Results DataFrame or None if error
    """
    try:
        # 1. Load data
        papers, edges = load_and_prepare_data(paper_file, edge_file)
        
        # 2. Build optimized academic citation graph
        G, paper_dict = build_academic_citation_graph_optimized(papers, edges)
        
        if G.number_of_edges() == 0:
            logger.warning("No valid edges in graph, cannot compute PageRank")
            return None
        
        # DEBUG: Show network statistics
        years = [paper['year'] for paper in paper_dict.values() if paper['year'] is not None]
        if years:
            logger.info(f"Dataset year range: {min(years)} - {max(years)} (current year: {max(years)})")
        
        # 3. Compute optimized standard PageRank
        pr_std = compute_optimized_pagerank(G, alpha=alpha)
        
        # 4. Compute Temporal weighted PageRank
        pr_temp = compute_temporal_weighted_pagerank(G, paper_dict, decay_lambda=decay_lambda, alpha=alpha)
        
        # 5. Compute Quality weighted PageRank
        pr_quality = compute_quality_weighted_pagerank(G, papers, alpha=alpha)
        
        # 6. Generate enhanced recommendation results with all three scores
        results = generate_recommendations_enhanced(papers, pr_std, pr_temp, pr_quality, output_file)
        
        # 7. Track PageRank history and identify rising papers
        try:
            from utils.pagerank_tracker import (
                track_pagerank_history, 
                identify_rising_pagerank_papers,
                identify_potential_rising_papers,
                generate_simulated_history
            )
            
            logger.info("Tracking PageRank history...")
            history_df = track_pagerank_history(papers, pr_std, Config.PAGERANK_HISTORY)
            
            # Check if we have enough history points
            unique_timestamps = history_df['timestamp'].nunique() if not history_df.empty else 0
            has_sufficient_history = unique_timestamps >= Config.RISING_PAGERANK_MIN_HISTORY_POINTS
            
            if has_sufficient_history:
                # Use real history to identify rising papers
                logger.info("Using real history data to identify rising papers...")
                rising_papers = identify_rising_pagerank_papers(
                    history_df,
                    papers,
                    min_growth_rate=Config.RISING_PAGERANK_MIN_GROWTH_RATE,
                    min_history_points=Config.RISING_PAGERANK_MIN_HISTORY_POINTS
                )
            else:
                # Not enough history - use prediction based on current metrics
                logger.info("Insufficient history. Using current metrics to predict potential rising papers...")
                rising_papers = identify_potential_rising_papers(
                    papers,
                    pr_std,
                    pr_temp,
                    min_temp_pr_rank=0.7
                )
                
                # Also generate simulated history for demonstration
                if not rising_papers.empty:
                    logger.info("Generating simulated history for demonstration...")
                    simulated_history = generate_simulated_history(
                        papers,
                        pr_std,
                        Config.PAGERANK_HISTORY,
                        days_back=30
                    )
            
            # Save results
            if not rising_papers.empty:
                rising_papers.to_csv(Config.RISING_PAGERANK_PAPERS, index=False)
                if has_sufficient_history:
                    logger.info(f"✅ Identified {len(rising_papers)} rising PageRank papers (from history)")
                else:
                    logger.info(f"✅ Identified {len(rising_papers)} potential rising papers (predicted from current metrics)")
                logger.info(f"   Saved to: {Config.RISING_PAGERANK_PAPERS}")
        except Exception as e:
            logger.warning(f"PageRank tracking failed: {e}")
        
        logger.info("✅ Optimized PageRank analysis completed!")
        return results
        
    except Exception as e:
        logger.error(f"Error during PageRank analysis: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    # Ensure directories exist
    Config.ensure_directories()
    
    # Run analysis with default config
    logger.info("Starting optimized PageRank analysis...")
    results = run_pagerank_analysis()
    
    if results is not None:
        logger.info("✅ Analysis completed successfully!")
    else:
        logger.error("❌ Analysis failed!")
        exit(1)
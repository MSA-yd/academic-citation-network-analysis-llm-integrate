#!/usr/bin/env python3
"""
Niche Detector - Identify Under-explored High-Impact Research Areas
Analyzes community characteristics to find small but influential research niches
"""

import pandas as pd
import networkx as nx
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


def analyze_community_characteristics(
    G: nx.Graph,
    node_df: pd.DataFrame,
    papers_df: pd.DataFrame,
    pagerank_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Analyze characteristics of each community
    
    Parameters:
    -----------
    G : nx.Graph
        Network graph
    node_df : pd.DataFrame
        DataFrame with columns: id, node_type, leiden_comm
    papers_df : pd.DataFrame
        Papers DataFrame with arxiv_id, citationCount, etc.
    pagerank_df : pd.DataFrame
        PageRank results DataFrame
        
    Returns:
    --------
    pd.DataFrame
        Community statistics DataFrame
    """
    comm_stats = []
    
    for comm_id in node_df['leiden_comm'].unique():
        comm_nodes = node_df[node_df['leiden_comm'] == comm_id]['id'].tolist()
        comm_papers = [
            str(n) for n in comm_nodes 
            if G.nodes.get(n, {}).get('node_type') == 'paper'
        ]
        
        if len(comm_papers) == 0:
            continue
        
        # Get paper data for this community
        comm_papers_df = papers_df[papers_df['arxiv_id'].astype(str).isin(comm_papers)]
        
        if comm_papers_df.empty:
            continue
        
        # Calculate community metrics
        avg_citations = comm_papers_df['citationCount'].mean() if 'citationCount' in comm_papers_df.columns else 0
        max_citations = comm_papers_df['citationCount'].max() if 'citationCount' in comm_papers_df.columns else 0
        total_citations = comm_papers_df['citationCount'].sum() if 'citationCount' in comm_papers_df.columns else 0
        
        # Get PageRank scores
        comm_pagerank = pagerank_df[pagerank_df['arxiv_id'].astype(str).isin(comm_papers)]
        avg_pagerank = comm_pagerank['pagerank_score'].mean() if not comm_pagerank.empty else 0
        max_pagerank = comm_pagerank['pagerank_score'].max() if not comm_pagerank.empty else 0
        
        # Calculate cross-community links (interdisciplinary connections)
        cross_comm_edges = 0
        for paper in comm_papers:
            if paper not in G.nodes():
                continue
            for neighbor in G.neighbors(paper):
                neighbor_comm = node_df[node_df['id'] == str(neighbor)]['leiden_comm'].values
                if len(neighbor_comm) > 0 and neighbor_comm[0] != comm_id:
                    cross_comm_edges += 1
        
        # Exploration score: small community but high impact
        # Higher score = fewer papers but higher citations/PageRank
        exploration_score = (avg_pagerank * avg_citations) / (len(comm_papers) + 1)
        
        comm_stats.append({
            'community_id': comm_id,
            'paper_count': len(comm_papers),
            'avg_citations': avg_citations,
            'max_citations': max_citations,
            'total_citations': total_citations,
            'avg_pagerank': avg_pagerank,
            'max_pagerank': max_pagerank,
            'cross_community_links': cross_comm_edges,
            'exploration_score': exploration_score,
            'density': cross_comm_edges / (len(comm_papers) + 1)  # Links per paper
        })
    
    if not comm_stats:
        logger.warning("No community statistics generated")
        return pd.DataFrame()
    
    result_df = pd.DataFrame(comm_stats)
    logger.info(f"Analyzed {len(result_df)} communities")
    return result_df


def identify_under_explored_niches(
    comm_stats_df: pd.DataFrame,
    min_pagerank: float = 0.01,
    max_paper_count: int = 20,
    min_exploration_score: Optional[float] = None
) -> pd.DataFrame:
    """
    Identify under-explored but high-impact research niches
    
    Parameters:
    -----------
    comm_stats_df : pd.DataFrame
        Community statistics DataFrame
    min_pagerank : float
        Minimum average PageRank to be considered high-impact
    max_paper_count : int
        Maximum number of papers to be considered "under-explored"
    min_exploration_score : Optional[float]
        Minimum exploration score (if None, uses 75th percentile)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with under-explored niches
    """
    if comm_stats_df.empty:
        return pd.DataFrame()
    
    # Set minimum exploration score if not provided
    if min_exploration_score is None:
        min_exploration_score = comm_stats_df['exploration_score'].quantile(0.75)
    
    # Filter niches
    niches = comm_stats_df[
        (comm_stats_df['avg_pagerank'] > min_pagerank) &
        (comm_stats_df['paper_count'] < max_paper_count) &
        (comm_stats_df['exploration_score'] > min_exploration_score)
    ].copy()
    
    if niches.empty:
        logger.info("No under-explored niches found with current criteria")
        return pd.DataFrame()
    
    # Sort by exploration score
    niches = niches.sort_values('exploration_score', ascending=False)
    
    logger.info(f"Identified {len(niches)} under-explored niches")
    return niches


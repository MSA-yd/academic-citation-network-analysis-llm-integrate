#!/usr/bin/env python3
"""
PageRank History Tracker
Tracks PageRank scores over time to identify rising papers
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


def track_pagerank_history(
    papers_df: pd.DataFrame,
    current_pr_scores: Dict[str, float],
    history_file: Path
) -> pd.DataFrame:
    """
    Save current PageRank scores to history record
    
    Parameters:
    -----------
    papers_df : pd.DataFrame
        Papers DataFrame with arxiv_id column
    current_pr_scores : Dict[str, float]
        Current PageRank scores (arxiv_id -> score)
    history_file : Path
        Path to history CSV file
        
    Returns:
    --------
    pd.DataFrame
        Complete history DataFrame
    """
    # Read existing history
    if history_file.exists():
        try:
            history = pd.read_csv(history_file)
            logger.info(f"Loaded existing history with {len(history)} records")
        except Exception as e:
            logger.warning(f"Error reading history file: {e}. Creating new history.")
            history = pd.DataFrame()
    else:
        history = pd.DataFrame()
        logger.info("Creating new PageRank history")
    
    # Add current timestamp and PageRank scores
    current_timestamp = datetime.now()
    current_data = pd.DataFrame({
        'arxiv_id': papers_df['arxiv_id'].astype(str),
        'timestamp': current_timestamp,
        'pagerank_score': [current_pr_scores.get(str(pid), 0.0) for pid in papers_df['arxiv_id']]
    })
    
    # Merge with history
    if not history.empty:
        history = pd.concat([history, current_data], ignore_index=True)
    else:
        history = current_data
    
    # Save updated history
    history.to_csv(history_file, index=False)
    logger.info(f"Saved PageRank history to {history_file}")
    
    return history


def identify_rising_pagerank_papers(
    history_df: pd.DataFrame,
    papers_df: pd.DataFrame,
    min_growth_rate: float = 0.1,
    min_history_points: int = 2
) -> pd.DataFrame:
    """
    Identify papers with rising PageRank scores
    
    Parameters:
    -----------
    history_df : pd.DataFrame
        History DataFrame with columns: arxiv_id, timestamp, pagerank_score
    papers_df : pd.DataFrame
        Papers DataFrame with arxiv_id, title, citationCount, year
    min_growth_rate : float
        Minimum growth rate to be considered "rising" (default: 0.1 = 10%)
    min_history_points : int
        Minimum number of history points required (default: 2)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with rising papers and their metrics
    """
    rising_papers = []
    
    for arxiv_id in history_df['arxiv_id'].unique():
        paper_history = history_df[history_df['arxiv_id'] == str(arxiv_id)].sort_values('timestamp')
        
        if len(paper_history) < min_history_points:
            continue
        
        # Calculate growth rate
        initial_pr = paper_history.iloc[0]['pagerank_score']
        latest_pr = paper_history.iloc[-1]['pagerank_score']
        
        # Avoid division by zero
        if initial_pr < 1e-6:
            continue
        
        growth_rate = (latest_pr - initial_pr) / initial_pr
        
        # Get paper info
        paper_info = papers_df[papers_df['arxiv_id'].astype(str) == str(arxiv_id)]
        if paper_info.empty:
            continue
        
        paper_info = paper_info.iloc[0]
        
        # Check if early stage (low citations but rising PageRank)
        is_early_stage = paper_info.get('citationCount', 0) < 50  # Adjustable threshold
        
        if growth_rate > min_growth_rate:
            rising_papers.append({
                'arxiv_id': arxiv_id,
                'title': paper_info.get('title', 'N/A'),
                'year': paper_info.get('year', 'N/A'),
                'growth_rate': growth_rate,
                'initial_pagerank': initial_pr,
                'current_pagerank': latest_pr,
                'citationCount': paper_info.get('citationCount', 0),
                'is_early_stage': is_early_stage,
                'history_points': len(paper_history)
            })
    
    if not rising_papers:
        logger.info("No rising PageRank papers found")
        return pd.DataFrame()
    
    result_df = pd.DataFrame(rising_papers)
    result_df = result_df.sort_values('growth_rate', ascending=False)
    
    logger.info(f"Identified {len(result_df)} rising PageRank papers")
    return result_df


def identify_potential_rising_papers(
    papers_df: pd.DataFrame,
    pr_std: Dict[str, float],
    pr_temp: Dict[str, float],
    min_temp_pr_rank: float = 0.7  # Top 30% in temporal PageRank
) -> pd.DataFrame:
    """
    Identify potential rising papers based on current metrics (no history required)
    Uses temporal PageRank, citation count, and recency as indicators
    
    Parameters:
    -----------
    papers_df : pd.DataFrame
        Papers DataFrame with arxiv_id, title, citationCount, year
    pr_std : Dict[str, float]
        Standard PageRank scores
    pr_temp : Dict[str, float]
        Temporal PageRank scores
    min_temp_pr_rank : float
        Minimum temporal PageRank percentile to be considered (default: 0.7 = top 30%)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with potential rising papers
    """
    if papers_df.empty:
        return pd.DataFrame()
    
    # Create results DataFrame
    results = papers_df[['arxiv_id', 'title', 'year', 'citationCount']].copy()
    results['arxiv_id'] = results['arxiv_id'].astype(str)
    
    # Add PageRank scores
    results['pagerank_score'] = results['arxiv_id'].map(pr_std).fillna(0)
    results['temporal_pagerank_score'] = results['arxiv_id'].map(pr_temp).fillna(0)
    
    # Calculate percentiles
    results['temp_pr_percentile'] = results['temporal_pagerank_score'].rank(pct=True)
    results['std_pr_percentile'] = results['pagerank_score'].rank(pct=True)
    
    # Identify potential rising papers:
    # 1. High temporal PageRank (recent citations)
    # 2. Low citation count (early stage)
    # 3. Recent publication year
    current_year = datetime.now().year
    results['years_since_publication'] = current_year - results['year']
    
    # Calculate potential score
    results['potential_score'] = (
        0.4 * results['temp_pr_percentile'] +  # Temporal PageRank weight
        0.3 * (1 - results['citationCount'] / results['citationCount'].max()) +  # Low citations = high potential
        0.2 * results['std_pr_percentile'] +  # Standard PageRank
        0.1 * (1 - results['years_since_publication'] / results['years_since_publication'].max())  # Recent papers
    )
    
    # Filter: high temporal PageRank, low citations, recent
    potential_papers = results[
        (results['temp_pr_percentile'] >= min_temp_pr_rank) &
        (results['citationCount'] < 50) &  # Early stage
        (results['years_since_publication'] <= 2)  # Recent (last 2 years)
    ].copy()
    
    if potential_papers.empty:
        logger.info("No potential rising papers found with current criteria")
        return pd.DataFrame()
    
    # Sort by potential score
    potential_papers = potential_papers.sort_values('potential_score', ascending=False)
    
    # Format output similar to rising papers format
    output = pd.DataFrame({
        'arxiv_id': potential_papers['arxiv_id'],
        'title': potential_papers['title'],
        'year': potential_papers['year'],
        'growth_rate': potential_papers['potential_score'],  # Use potential_score as proxy
        'initial_pagerank': 0.0,  # Not available without history
        'current_pagerank': potential_papers['pagerank_score'],
        'temporal_pagerank': potential_papers['temporal_pagerank_score'],
        'citationCount': potential_papers['citationCount'],
        'is_early_stage': True,
        'history_points': 0,  # No history
        'prediction_type': 'potential'  # Mark as prediction
    })
    
    logger.info(f"Identified {len(output)} potential rising papers (based on current metrics)")
    return output


def generate_simulated_history(
    papers_df: pd.DataFrame,
    current_pr_scores: Dict[str, float],
    history_file: Path,
    days_back: int = 30
) -> pd.DataFrame:
    """
    Generate simulated historical PageRank data for demonstration
    
    Parameters:
    -----------
    papers_df : pd.DataFrame
        Papers DataFrame
    current_pr_scores : Dict[str, float]
        Current PageRank scores
    history_file : Path
        Path to history file
    days_back : int
        Number of days to simulate back (default: 30)
        
    Returns:
    --------
    pd.DataFrame
        Simulated history DataFrame
    """
    logger.info(f"Generating simulated history (going back {days_back} days)...")
    
    history_records = []
    base_date = datetime.now() - timedelta(days=days_back)
    
    for _, row in papers_df.iterrows():
        arxiv_id = str(row['arxiv_id'])
        current_pr = current_pr_scores.get(arxiv_id, 0.0)
        
        # Simulate 3 historical points
        for i in range(3):
            days_ago = days_back - (i * (days_back // 3))
            timestamp = base_date + timedelta(days=days_ago)
            
            # Simulate lower PageRank in the past (with some randomness)
            # Papers with higher current PR had lower growth, newer papers had higher growth
            year = row.get('year', 2024)
            years_ago = datetime.now().year - year
            
            # Growth factor: newer papers grow faster
            growth_factor = 1.0 - (0.1 * i) - (0.05 * max(0, years_ago - 1))
            growth_factor = max(0.3, growth_factor)  # At least 30% of current
            
            # Add some randomness
            noise = np.random.uniform(0.9, 1.1)
            simulated_pr = current_pr * growth_factor * noise
            
            history_records.append({
                'arxiv_id': arxiv_id,
                'timestamp': timestamp,
                'pagerank_score': max(0.0, simulated_pr)
            })
    
    # Add current data
    current_timestamp = datetime.now()
    for _, row in papers_df.iterrows():
        arxiv_id = str(row['arxiv_id'])
        history_records.append({
            'arxiv_id': arxiv_id,
            'timestamp': current_timestamp,
            'pagerank_score': current_pr_scores.get(arxiv_id, 0.0)
        })
    
    history_df = pd.DataFrame(history_records)
    history_df = history_df.sort_values('timestamp')
    
    # Save
    history_df.to_csv(history_file, index=False)
    logger.info(f"Generated simulated history with {len(history_df)} records")
    logger.info(f"   Saved to: {history_file}")
    
    return history_df


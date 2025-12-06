#!/usr/bin/env python3
"""
Data loading utilities
Provides unified data loading functions with validation
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from config import Config
import logging

logger = logging.getLogger(__name__)


def load_data_files(
    papers_file: Optional[Path] = None,
    edges_file: Optional[Path] = None,
    node_comm_file: Optional[Path] = None,
    raise_on_missing: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all required data files
    
    Parameters:
    -----------
    papers_file : Optional[Path]
        Path to papers CSV file
    edges_file : Optional[Path]
        Path to edges CSV file
    node_comm_file : Optional[Path]
        Path to node community CSV file
    raise_on_missing : bool
        If True, raise FileNotFoundError for missing files
        
    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        (papers, edges, node_comm) DataFrames
        
    Raises:
    -------
    FileNotFoundError
        If required files are missing and raise_on_missing=True
    """
    papers_file = papers_file or Config.PAPERS_CLEANED
    edges_file = edges_file or Config.EDGES_CLEANED
    node_comm_file = node_comm_file or Config.NODE_COMM
    
    missing_files = []
    for file_path, name in [
        (papers_file, "papers"),
        (edges_file, "edges"),
        (node_comm_file, "node_comm")
    ]:
        if not file_path.exists():
            missing_files.append((file_path, name))
            if raise_on_missing:
                raise FileNotFoundError(f"Required file not found: {file_path}")
            else:
                logger.warning(f"File not found: {file_path}")
    
    if missing_files and raise_on_missing:
        raise FileNotFoundError(
            f"Missing required files: {[f[0] for f in missing_files]}"
        )
    
    logger.info(f"Loading data files...")
    papers = pd.read_csv(papers_file) if papers_file.exists() else pd.DataFrame()
    edges = pd.read_csv(edges_file) if edges_file.exists() else pd.DataFrame()
    node_comm = pd.read_csv(node_comm_file) if node_comm_file.exists() else pd.DataFrame()
    
    logger.info(f"Loaded: {len(papers)} papers, {len(edges)} edges, {len(node_comm)} nodes")
    
    return papers, edges, node_comm


def validate_papers_dataframe(df: pd.DataFrame) -> None:
    """
    Validate papers DataFrame structure
    
    Parameters:
    -----------
    df : pd.DataFrame
        Papers DataFrame to validate
        
    Raises:
    -------
    ValueError
        If required columns are missing
    """
    required_cols = {"arxiv_id", "title"}
    missing_cols = required_cols - set(df.columns)
    
    if missing_cols:
        raise ValueError(f"Missing required columns in papers data: {missing_cols}")


def validate_edges_dataframe(df: pd.DataFrame) -> None:
    """
    Validate edges DataFrame structure
    
    Parameters:
    -----------
    df : pd.DataFrame
        Edges DataFrame to validate
        
    Raises:
    -------
    ValueError
        If required columns are missing
    """
    required_cols = {"source", "target"}
    missing_cols = required_cols - set(df.columns)
    
    if missing_cols:
        raise ValueError(f"Missing required columns in edges data: {missing_cols}")


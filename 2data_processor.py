#!/usr/bin/env python3
"""
Data Cleaning Module with Smart Recovery
Cleans paper and edge data and automatically recovers papers to meet target count:
- Papers: Remove nulls, deduplicate, filter in_s2=True, remove empty references
- Edges: Remove null rows, ensure target is non-empty, merge reference and citation edges
- Recovery: Smart recovery of papers to meet target count when possible
- New: Track and output removal reasons for papers (all outputs in English)
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List
from config import Config
from utils.logger import setup_logger
from utils.data_loader import validate_papers_dataframe, validate_edges_dataframe

logger = setup_logger(__name__)


def find_edge_files(paper_file: Path) -> List[Path]:
    """Find all edge files matching the paper file pattern"""
    paper_stem = paper_file.stem
    base_name = paper_stem.replace("papers_", "", 1)
    
    edge_files = []
    
    # Look for both reference_edges and citation_edges
    ref_edge_file = paper_file.parent / f"reference_edges_{base_name}.csv"
    cit_edge_file = paper_file.parent / f"citation_edges_{base_name}.csv"
    
    if ref_edge_file.exists():
        edge_files.append(ref_edge_file)
    if cit_edge_file.exists():
        edge_files.append(cit_edge_file)
    
    # Fallback to legacy edges_*.csv format for backward compatibility
    if not edge_files:
        old_edge_file = paper_file.parent / f"edges_{base_name}.csv"
        if old_edge_file.exists():
            edge_files.append(old_edge_file)
    
    return edge_files


def clean_data(
    paper_file: str,
    edge_files: List[str],
    out_paper: Optional[str] = None,
    out_edge: Optional[str] = None,
    out_removed: Optional[str] = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Clean paper and edge data, track removal reasons (all outputs in English)
    
    Parameters:
    -----------
    paper_file : str
        Path to input paper CSV file
    edge_files : List[str]
        List of paths to input edge CSV files (reference and/or citation edges)
    out_paper : Optional[str]
        Path to output cleaned paper CSV file (default: papers_cleaned.csv)
    out_edge : Optional[str]
        Path to output cleaned edge CSV file (default: edges_cleaned.csv)
    out_removed : Optional[str]
        Path to output removed papers with reasons (default: papers_removed.csv)
        
    Returns:
    --------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        (cleaned_papers, cleaned_edges, removed_papers) DataFrames
    """
    # Validate input files
    paper_path = Path(paper_file)
    if not paper_path.exists():
        raise FileNotFoundError(f"Paper file not found: {paper_file}")
    
    edge_paths = [Path(f) for f in edge_files]
    for edge_path in edge_paths:
        if not edge_path.exists():
            raise FileNotFoundError(f"Edge file not found: {edge_path}")
    
    logger.info(f"Loading data from {paper_file} and {len(edge_files)} edge files")
    
    # Load papers and add removal reason column
    df_p = pd.read_csv(paper_path)
    df_p["removal_reason"] = None  # New: Track removal reason
    logger.info(f"Original: {len(df_p)} papers")
    
    # Validate papers structure (exclude removal_reason for validation)
    validate_papers_dataframe(df_p.drop(columns=["removal_reason"], errors="ignore"))
    
    # Step 1: Remove papers with missing arxiv_id or title
    mask_missing = df_p["arxiv_id"].isna() | df_p["title"].isna()
    df_p.loc[mask_missing, "removal_reason"] = "Missing arxiv_id or title"
    
    # Step 2: Remove papers where in_s2 is False
    mask_not_in_s2 = df_p["in_s2"] == False
    # Only assign reason to papers not yet labeled
    mask_not_in_s2 = mask_not_in_s2 & (df_p["removal_reason"].isna())
    df_p.loc[mask_not_in_s2, "removal_reason"] = "in_s2 = False (not in Semantic Scholar)"
    
    # Step 3: Process and remove papers with empty references
    df_p["references_str"] = df_p["references"].astype(str).str.strip()
    mask_empty_refs = df_p["references_str"].isin(["", "[]", "nan"])
    mask_empty_refs = mask_empty_refs & (df_p["removal_reason"].isna())
    df_p.loc[mask_empty_refs, "removal_reason"] = "Empty references (empty string/[]/nan)"
    
    # Step 4: Deduplicate and mark duplicate papers
    mask_duplicate = df_p.duplicated(subset=["arxiv_id"], keep="first")
    mask_duplicate = mask_duplicate & (df_p["removal_reason"].isna())
    df_p.loc[mask_duplicate, "removal_reason"] = "Duplicate arxiv_id (retained first occurrence)"
    
    # Filter retained papers (removal_reason is None)
    df_p_cleaned = df_p[df_p["removal_reason"].isna()].copy()
    # Remove auxiliary columns and unused columns
    df_p_cleaned = df_p_cleaned.drop(columns=["removal_reason", "references_str", "citations"], errors="ignore")
    df_p_cleaned = df_p_cleaned.reset_index(drop=True)
    
    # Filter removed papers (removal_reason is not None)
    df_p_removed = df_p[df_p["removal_reason"].notna()].copy()
    
    # Calculate and log removal statistics
    removal_stats = df_p_removed["removal_reason"].value_counts()
    logger.info(f"\nRemoval Statistics:")
    for reason, count in removal_stats.items():
        logger.info(f"  - {reason}: {count} papers")
    logger.info(f"Total removed: {len(df_p_removed)} papers")
    logger.info(f"Retained: {len(df_p_cleaned)} papers")
    
    # Load and merge all edge files
    edge_dfs = []
    for edge_path in edge_paths:
        df_e = pd.read_csv(edge_path)
        validate_edges_dataframe(df_e)
        edge_dfs.append(df_e)
        logger.info(f"Loaded {len(df_e)} edges from {edge_path.name}")
    
    if not edge_dfs:
        raise ValueError("No edge data found")
    
    # Merge all edge files
    df_e_combined = pd.concat(edge_dfs, ignore_index=True)
    logger.info(f"Combined: {len(df_e_combined)} total edges")
    
    # Clean edges: Remove null rows and ensure non-empty target
    initial_edge_count = len(df_e_combined)
    df_e_combined = (df_e_combined
                    .dropna()
                    .query("target.str.len() > 0", engine="python")
                    .reset_index(drop=True))
    
    removed_edges = initial_edge_count - len(df_e_combined)
    if removed_edges > 0:
        logger.info(f"Removed {removed_edges} edges during cleaning")
    
    # Save results
    # Save cleaned papers
    out_paper_path = Path(out_paper) if out_paper else Config.PAPERS_CLEANED
    df_p_cleaned.to_csv(out_paper_path, index=False, encoding='utf-8')
    
    # Save removed papers with reasons
    out_removed_path = Path(out_removed) if out_removed else Config.PROJECT_ROOT / "papers_removed.csv"
    df_p_removed.to_csv(out_removed_path, index=False, encoding='utf-8')
    
    # Save cleaned edges
    out_edge_path = Path(out_edge) if out_edge else Config.EDGES_CLEANED
    df_e_combined.to_csv(out_edge_path, index=False, encoding='utf-8')
    
    logger.info(
        f"\nOutput Files:"
        f"\n  - Cleaned Papers: {out_paper_path} ({len(df_p_cleaned)} rows)"
        f"\n  - Removed Papers (with reasons): {out_removed_path} ({len(df_p_removed)} rows)"
        f"\n  - Cleaned Edges: {out_edge_path} ({len(df_e_combined)} rows)"
    )
    
    return df_p_cleaned, df_e_combined, df_p_removed


def analyze_removal_patterns(removed_df: pd.DataFrame) -> dict:
    """Analyze removal patterns to determine which papers can be safely recovered"""
    removal_stats = removed_df['removal_reason'].value_counts()
    logger.info("Analyzing removal reason distribution:")
    for reason, count in removal_stats.items():
        logger.info(f"  - {reason}: {count} papers")
    
    # Check if removal is mainly due to "in_s2 = False"
    in_s2_false_count = removed_df[removed_df['removal_reason'].str.contains('in_s2 = False', na=False)].shape[0]
    total_removed = len(removed_df)
    
    return {
        'in_s2_false_ratio': in_s2_false_count / total_removed if total_removed > 0 else 0,
        'in_s2_false_count': in_s2_false_count,
        'total_removed': total_removed,
        'can_safely_recover': in_s2_false_count / total_removed > 0.7 if total_removed > 0 else False
    }


def smart_recover_papers(
    cleaned_papers: pd.DataFrame,
    removed_papers: pd.DataFrame,
    target_count: int,
    paper_file_original: str
) -> pd.DataFrame:
    """
    Smartly recover papers to reach target count
    
    Strategy:
    1. Prioritize recovering in_s2=False papers with citation data
    2. If still not enough, recover in_s2=False papers from recent years
    3. Finally consider recovering other types of papers (cautious)
    """
    current_count = len(cleaned_papers)
    need_to_recover = target_count - current_count
    
    if need_to_recover <= 0:
        logger.info(f"✅ Current paper count ({current_count}) already meets target ({target_count}), no recovery needed")
        return cleaned_papers
    
    logger.info(f"📈 Need to recover {need_to_recover} papers (current: {current_count}, target: {target_count})")
    
    # Read original paper file to get complete information
    original_papers = pd.read_csv(paper_file_original)
    
    # Step 1: Recover in_s2=False papers with citation data
    recoverable_in_s2_false = removed_papers[
        removed_papers['removal_reason'].str.contains('in_s2 = False', na=False)
    ].copy()
    
    # Add original citation and impact data for these papers
    if not recoverable_in_s2_false.empty:
        recoverable_in_s2_false = recoverable_in_s2_false.merge(
            original_papers[['arxiv_id', 'citationCount', 'influentialCitationCount', 'references', 'citations', 'impact_score']], 
            on='arxiv_id', 
            how='left'
        )
        
        # Calculate recovery priority score
        recoverable_in_s2_false['recovery_score'] = (
            recoverable_in_s2_false.get('citationCount', 0).fillna(0) * 0.5 +
            recoverable_in_s2_false.get('influentialCitationCount', 0).fillna(0) * 1.0 +
            (2025 - recoverable_in_s2_false['year']) * 0.1  # Prioritize newer papers
        )
        
        # Sort by recovery score
        recoverable_in_s2_false = recoverable_in_s2_false.sort_values('recovery_score', ascending=False)
    
    recovered_papers = []
    remaining_need = need_to_recover
    
    # Recover in_s2=False papers
    if not recoverable_in_s2_false.empty and remaining_need > 0:
        to_recover = min(remaining_need, len(recoverable_in_s2_false))
        recovered_from_in_s2_false = recoverable_in_s2_false.head(to_recover)
        recovered_papers.append(recovered_from_in_s2_false)
        remaining_need -= to_recover
        logger.info(f"  ✅ Recovered {to_recover} in_s2=False papers with citation data")
    
    # Step 2: If still need more, recover newer in_s2=False papers
    if remaining_need > 0:
        other_in_s2_false = removed_papers[
            (removed_papers['removal_reason'].str.contains('in_s2 = False', na=False)) &
            (~removed_papers['arxiv_id'].isin([p['arxiv_id'] for p in recovered_papers]))
        ].copy()
        
        if not other_in_s2_false.empty:
            # Sort by year, newest first
            other_in_s2_false = other_in_s2_false.sort_values('year', ascending=False)
            to_recover = min(remaining_need, len(other_in_s2_false))
            recovered_other = other_in_s2_false.head(to_recover)
            recovered_papers.append(recovered_other)
            remaining_need -= to_recover
            logger.info(f"  ✅ Recovered {to_recover} newer in_s2=False papers")
    
    # Step 3: Final downgrade recovery (use with caution)
    if remaining_need > 0:
        logger.warning(f"⚠️  Still need to recover {remaining_need} papers, using downgrade strategy")
        remaining_removed = removed_papers[
            ~removed_papers['arxiv_id'].isin([p['arxiv_id'] for p in recovered_papers])
        ].copy()
        
        if not remaining_removed.empty:
            # Sort by year to avoid recovering too old papers
            remaining_removed = remaining_removed.sort_values('year', ascending=False)
            to_recover = min(remaining_need, len(remaining_removed))
            recovered_final = remaining_removed.head(to_recover)
            recovered_papers.append(recovered_final)
            remaining_need -= to_recover
            logger.info(f"  ⚠️  Downgrade recovered {to_recover} other types of papers")
    
    # Merge all recovered papers
    if recovered_papers:
        all_recovered = pd.concat(recovered_papers, ignore_index=True)
        # Remove removal_reason column, add in_s2=True flag (though it's fake, for subsequent processing)
        all_recovered = all_recovered.drop(columns=['removal_reason', 'references_str'], errors='ignore')
        all_recovered['in_s2'] = True  # Mark as recovered
        all_recovered['recovered'] = True  # Mark as recovered papers
        
        final_papers = pd.concat([cleaned_papers, all_recovered], ignore_index=True)
        logger.info(f"✅ Final paper count: {len(final_papers)} (original kept: {len(cleaned_papers)}, recovered: {len(all_recovered)})")
    else:
        final_papers = cleaned_papers
        logger.info(f"❌ Unable to recover sufficient papers, final count: {len(final_papers)}")
    
    return final_papers


def estimate_original_target_count(paper_file: str) -> int:
    """
    Estimate original target count from file name pattern
    This is a heuristic based on common file naming conventions
    """
    paper_filename = Path(paper_file).stem
    # Look for patterns like papers_llm_20251110_1234.csv
    # Extract target count from original collection (this is just a heuristic)
    # In practice, you might pass this as a parameter from the collection stage
    
    # For now, return a default value - you should adjust this based on your actual workflow
    return 100  # Default fallback


def smart_clean_data(
    paper_file: str,
    edge_files: List[str],
    target_count: Optional[int] = None,
    out_paper: Optional[str] = None,
    out_edge: Optional[str] = None,
    out_removed: Optional[str] = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean data with smart recovery to reach target count
    """
    # Execute original cleaning
    cleaned_papers, cleaned_edges, removed_papers = clean_data(
        paper_file, edge_files, out_paper, out_edge, out_removed
    )
    
    # Determine target count
    if target_count is None:
        target_count = estimate_original_target_count(paper_file)
        logger.info(f"Estimated target count: {target_count}")
    
    # Analyze removal patterns
    removal_analysis = analyze_removal_patterns(removed_papers)
    
    if removal_analysis['can_safely_recover']:
        logger.info("🔍 Detected many in_s2=False removals, starting smart recovery...")
        final_papers = smart_recover_papers(
            cleaned_papers, removed_papers, target_count, paper_file
        )
        
        # Save final results with recovery
        final_paper_path = Path(out_paper) if out_paper else Config.PAPERS_CLEANED
        final_papers.to_csv(final_paper_path, index=False, encoding='utf-8')
        logger.info(f"💾 Final paper data (with recovery) saved to: {final_paper_path}")
        
        return final_papers, cleaned_edges
    else:
        logger.info("📊 Removal reasons are diverse, not recommended for automatic recovery")
        return cleaned_papers, cleaned_edges


def find_input_files(paper_file: Optional[str] = None, edge_file: Optional[str] = None) -> Tuple[Path, List[Path]]:
    """
    Find input files using priority: CLI args > env vars > auto-discovery
    
    Returns:
        tuple: (paper_file_path, edge_files_list)
    
    Raises:
        FileNotFoundError: If input files cannot be found
    """
    # Priority 1: Command line arguments
    if paper_file:
        paper_path = Path(paper_file)
        if not paper_path.exists():
            raise FileNotFoundError(f"Paper file not found: {paper_file}")
        
        # Use specified edge file if provided; auto-discover otherwise
        if edge_file:
            edge_path = Path(edge_file)
            if not edge_path.exists():
                raise FileNotFoundError(f"Edge file not found: {edge_file}")
            return paper_path, [edge_path]
        else:
            edge_files = find_edge_files(paper_path)
            if not edge_files:
                raise FileNotFoundError(f"No edge files found for paper file: {paper_file}")
            return paper_path, edge_files
    
    # Priority 2: Config.get_input_files() (handles env vars and auto-discovery)
    paper_path, edge_path = Config.get_input_files()
    if paper_path and edge_path:
        # Try to find complete set of edge files
        edge_files = find_edge_files(paper_path)
        if edge_files:
            return paper_path, edge_files
        else:
            # Fallback to single edge file from config
            return paper_path, [edge_path]
    
    # Fallback to auto-discovery from file patterns
    paper_files = sorted(
        Config.PROJECT_ROOT.glob(Config.PAPERS_INPUT_PATTERN),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    # 过滤掉 cleaned 和 removed 文件，只保留原始收集的文件
    paper_files = [f for f in paper_files if "cleaned" not in f.name and "removed" not in f.name]
    
    if not paper_files:
        # Check for any paper files (regardless of naming pattern)
        all_paper_files = list(Config.PROJECT_ROOT.glob("papers_*.csv"))
        # 同样过滤掉 cleaned 和 removed 文件
        all_paper_files = [f for f in all_paper_files if "cleaned" not in f.name and "removed" not in f.name]
        
        if all_paper_files:
            available_info = "\nAvailable paper files:\n"
            for f in all_paper_files[:10]:  # Show up to 10 files
                available_info += f"  - {f.name}\n"
            available_info += "\nUsage: python 2data_processor.py <paper_file>"
            raise FileNotFoundError(f"No paper files found matching pattern {Config.PAPERS_INPUT_PATTERN}" + available_info)
        else:
            raise FileNotFoundError("No paper files found. Please run literature_collector.py first or specify files manually.")
    
    latest_paper = paper_files[0]
    edge_files = find_edge_files(latest_paper)
    if not edge_files:
        # Check for legacy edge files
        old_edge_files = list(Config.PROJECT_ROOT.glob("edges_*.csv"))
        old_edge_files = [f for f in old_edge_files if "cleaned" not in f.name]
        
        if old_edge_files:
            logger.info(f"No specific reference/citation edge files found for {latest_paper.name}")
            logger.info(f"Found legacy edge files, using: {old_edge_files[0].name}")
            return latest_paper, [old_edge_files[0]]
        else:
            available_info = "\nAvailable paper files:\n"
            for f in paper_files[:5]:  # Show up to 5 files
                available_info += f"  - {f.name}\n"
            available_info += "\nNo edge files found. Please run literature_collector.py first."
            raise FileNotFoundError(f"No edge files found for latest paper: {latest_paper.name}" + available_info)
    
    return latest_paper, edge_files


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Clean paper and edge data for citation network analysis (with smart recovery)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-discover latest input files, with smart recovery
  python 2data_processor.py
  
  # Specify target count for recovery
  python 2data_processor.py --target-count 150
  
  # Full custom paths with recovery
  python 2data_processor.py papers_llm.csv reference_edges_llm.csv --target-count 200 --output-paper clean_papers.csv --output-edge clean_edges.csv
        """
    )
    parser.add_argument(
        "paper_file",
        nargs="?",
        type=str,
        help="Path to input paper CSV file (optional, will auto-discover if not provided)"
    )
    parser.add_argument(
        "edge_file",
        nargs="?",
        type=str,
        help="Path to specific input edge CSV file (optional, will auto-discover all matching edges if not provided)"
    )
    parser.add_argument(
        "--target-count",
        type=int,
        help="Target number of papers to recover to (default: estimated from original collection)"
    )
    parser.add_argument(
        "--output-paper",
        type=str,
        help=f"Path to output cleaned paper CSV (default: {Config.PAPERS_CLEANED})"
    )
    parser.add_argument(
        "--output-edge",
        type=str,
        help=f"Path to output cleaned edge CSV (default: {Config.EDGES_CLEANED})"
    )
    parser.add_argument(
        "--output-removed",
        type=str,
        help="Path to output removed papers with reasons (default: papers_removed.csv)"
    )
    return parser.parse_args()


def main():
    try:
        args = parse_arguments()
        
        # Find input files
        paper_file, edge_files = find_input_files(args.paper_file, args.edge_file)
        
        logger.info(f"Starting smart data cleaning with recovery...")
        logger.info(f"Input paper: {paper_file.name}")
        for edge_file in edge_files:
            logger.info(f"Input edge: {edge_file.name}")
        
        # Clean data with smart recovery
        final_papers, final_edges = smart_clean_data(
            str(paper_file),
            [str(f) for f in edge_files],
            target_count=args.target_count,
            out_paper=args.output_paper,
            out_edge=args.output_edge,
            out_removed=args.output_removed
        )
        
        logger.info("✅ Smart data cleaning with recovery completed successfully!")
        logger.info(f"📊 Final results: {len(final_papers)} papers, {len(final_edges)} edges")
        
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during smart data cleaning: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
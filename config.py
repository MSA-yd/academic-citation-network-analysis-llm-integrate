#!/usr/bin/env python3
"""
Configuration Management
Centralized configuration for the Citation Network Analysis project
"""

import os
from pathlib import Path
from typing import Optional, Tuple, Dict, List

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  .env file not found at {env_path}")
        print(f"💡 Create a .env file with your API keys (see .env.example)")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Environment variables must be set manually.")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")


class Config:
    """Project configuration"""
    
    # =============================================================================
    # PROJECT PATHS AND DATA MANAGEMENT
    # =============================================================================
    
    # Project root directory
    PROJECT_ROOT = Path(__file__).parent
    
    # Data files (output)
    PAPERS_CLEANED = PROJECT_ROOT / "papers_cleaned.csv"
    EDGES_CLEANED = PROJECT_ROOT / "edges_cleaned.csv"
    NODE_COMM = PROJECT_ROOT / "node_leiden_comm.csv"
    PAGERANK_RESULTS = PROJECT_ROOT / "top_papers_pagerank.csv"
    
    # Advanced analysis output files
    PAGERANK_HISTORY = PROJECT_ROOT / "pagerank_history.csv"
    RISING_PAGERANK_PAPERS = PROJECT_ROOT / "rising_pagerank_papers.csv"
    TAXONOMY_BENCHMARK = PROJECT_ROOT / "taxonomy_benchmark.csv"
    
    # Input file patterns (for auto-discovery)
    PAPERS_INPUT_PATTERN = "papers_*.csv"
    EDGES_INPUT_PATTERN = "edges_*.csv"
    
    # Input files (can be set via environment variables or auto-discovered)
    PAPERS_INPUT: Optional[Path] = None
    EDGES_INPUT: Optional[Path] = None
    
    # Output directories
    FIG_DIR = PROJECT_ROOT / "fig"
    LOG_DIR = PROJECT_ROOT / "logs"
    
    # =============================================================================
    # PAPER COLLECTION PARAMETERS (Internal超参数)
    # =============================================================================
    
    # Basic collection settings
    MAX_PAPERS_DEFAULT: int = 100           # Default number of papers to collect
    MAX_PAPERS_LIMIT: int = 500             # Maximum allowed papers
    DEFAULT_YEAR_RANGE: int = 2             # Years back from current year
    INITIAL_FETCH_MULTIPLIER: int = 2       # Collect X times more papers for filtering
    
    # Year distribution strategy
    # If True, collect papers with custom year distribution (not equal distribution)
    USE_CUSTOM_YEAR_DISTRIBUTION: bool = True
    
    # Custom year distribution weights (must sum to 1.0 or will be normalized)
    # Keys are relative years (0 = current year, -1 = previous year, etc.)
    # Example: {0: 0.4, -1: 0.3, -2: 0.2, -3: 0.1} means 40% current year, 30% last year, etc.
    CUSTOM_YEAR_DISTRIBUTION: Dict[int, float] = {
        0: 0.3,    # Current year: 30%
        -1: 0.3,   # Previous year: 30%
        -2: 0.25,  # 2 years ago: 25%
        -3: 0.15   # 3 years ago: 15%
    }
    
    # Alternative: Exponential decay distribution (if CUSTOM_YEAR_DISTRIBUTION is empty)
    EXPONENTIAL_DECAY_FACTOR: float = 0.7   # Decay factor for older years (0-1)
    
    # API request settings
    API_MAX_RETRIES: int = 3                # Maximum retry attempts for failed requests
    ARXIV_CLIENT_DELAY: float = 3.0         # Delay between arXiv API requests (seconds)
    ARXIV_CLIENT_PAGE_SIZE: int = 100       # Number of results per arXiv API page
    
    # Paper filtering and ranking weights
    INFLUENTIAL_CITATION_WEIGHT: float = 2.0    # Weight for influential citations in scoring
    IN_S2_BONUS_SCORE: int = 100               # Bonus points for Semantic Scholar indexed papers
    CITING_PAPERS_WEIGHT: float = 0.5          # Weight for citing papers count in scoring
    
    # =============================================================================
    # NETWORK BUILDING PARAMETERS
    # =============================================================================
    
    # Network analysis flags
    INCLUDE_CITATIONS_DEFAULT: bool = True      # Whether to include citing papers by default
    FILTER_HIGH_IMPACT_DEFAULT: bool = True     # Whether to filter to high-impact papers by default
    
    # =============================================================================
    # PAGERANK AND NETWORK ANALYSIS PARAMETERS
    # =============================================================================
    
    # PageRank algorithm parameters
    PAGERANK_ALPHA: float = 0.85          # Damping factor (0-1, default 0.85)
    PAGERANK_MAX_ITER: int = 100          # Maximum iterations for convergence
    
    # Temporal decay for time-aware PageRank
    TEMPORAL_DECAY_LAMBDA: float = 0.6    # Decay factor for older papers (0-1)
    
    # =============================================================================
    # API CONFIGURATION AND RATE LIMITING
    # =============================================================================
    
    # API keys (from environment variables)
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # OpenRouter settings
    OPENROUTER_MODEL: str = "tngtech/deepseek-r1t-chimera:free"
    OPENROUTER_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    
    # DashScope (百炼) settings
    DASHSCOPE_MODEL: str = "qwen-plus"  # 或其他百炼模型：qwen-turbo, qwen-plus, qwen-max
    DASHSCOPE_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    # OpenAI (ChatAnywhere) settings
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # 或其他 OpenAI 兼容模型
    OPENAI_BASE_URL: str = "https://api.chatanywhere.tech/v1"  # 或 "https://api.chatanywhere.org/v1"
    
    # API selection (优先级: DashScope > OpenAI > OpenRouter)
    USE_DASHSCOPE: bool = False  # True优先使用DashScope (当前禁用，因为API key可能无效)
    USE_OPENAI: bool = True  # 是否使用 OpenAI (ChatAnywhere)
    
    # API rate limiting (requests per second)
    SEMANTIC_SCHOLAR_RATE_LIMIT: float = 1.0  # Default: 1 req/sec without API key
    OPENROUTER_RATE_LIMIT: float = 0.33       # ~3 seconds between requests
    DASHSCOPE_RATE_LIMIT: float = 1.0         # DashScope请求速率限制
    OPENAI_RATE_LIMIT: float = 1.0            # OpenAI请求速率限制
    
    # =============================================================================
    # VISUALIZATION AND LAYOUT PARAMETERS
    # =============================================================================
    
    # Figure settings
    FIGURE_DPI: int = 400                       # DPI for saved figures
    INTERACTIVE_GRAPH_HEIGHT: str = "900px"     # Height for interactive network graphs
    
    # Layout algorithm settings
    SKIP_KAMADA_KAWAI_AUTO_THRESHOLD: int = 5000  # Auto-skip Kamada-Kawai for large graphs
    SKIP_KAMADA_KAWAI_DEFAULT: bool = False       # Default: don't skip layout calculation
    
    # Community detection
    LEIDEN_SEED: int = 42                         # Random seed for reproducible Leiden communities
    
    # =============================================================================
    # ADVANCED ANALYSIS PARAMETERS
    # =============================================================================
    
    # PageRank tracking
    RISING_PAGERANK_MIN_GROWTH_RATE: float = 0.1  # Minimum growth rate (10%) to be considered "rising"
    RISING_PAGERANK_MIN_HISTORY_POINTS: int = 2    # Minimum history points required
    
    # Niche detection
    NICHE_MIN_PAGERANK: float = 0.01               # Minimum avg PageRank for high-impact
    NICHE_MAX_PAPER_COUNT: int = 20                # Max papers to be "under-explored"
    
    # Topic embedding
    QS_TAXONOMY_FILE: Optional[Path] = None        # Optional: path to custom QS taxonomy file
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure required directories exist"""
        cls.FIG_DIR.mkdir(exist_ok=True)
        cls.LOG_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def find_latest_input_files(cls) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Automatically find the latest input files matching the pattern
        
        Returns:
            tuple: (latest_paper_file, latest_edge_file) or (None, None) if not found
        """
        # Find all matching files
        paper_files = sorted(
            cls.PROJECT_ROOT.glob(cls.PAPERS_INPUT_PATTERN),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        edge_files = sorted(
            cls.PROJECT_ROOT.glob(cls.EDGES_INPUT_PATTERN),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Filter out cleaned files
        paper_files = [f for f in paper_files if "cleaned" not in f.name]
        edge_files = [f for f in edge_files if "cleaned" not in f.name]
        
        latest_paper = paper_files[0] if paper_files else None
        latest_edge = edge_files[0] if edge_files else None
        
        return latest_paper, latest_edge
    
    @classmethod
    def get_input_files(cls) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Get input files from environment variables, config, or auto-discovery
        
        Returns:
            tuple: (paper_file, edge_file)
        """
        # Try environment variables first
        paper_env = os.getenv("PAPERS_INPUT_FILE")
        edge_env = os.getenv("EDGES_INPUT_FILE")
        
        if paper_env:
            paper_file = Path(paper_env)
            if paper_file.exists():
                return paper_file, Path(edge_env) if edge_env and Path(edge_env).exists() else None
        
        # Try config class attributes
        if cls.PAPERS_INPUT and cls.PAPERS_INPUT.exists():
            return cls.PAPERS_INPUT, cls.EDGES_INPUT if cls.EDGES_INPUT and cls.EDGES_INPUT.exists() else None
        
        # Auto-discover latest files
        return cls.find_latest_input_files()
    
    @classmethod
    def validate_environment(cls) -> Tuple[list[str], list[str]]:
        """
        Validate environment configuration
        
        Returns:
            tuple: (missing_files, missing_env_vars)
        """
        missing_files = []
        missing_env_vars = []
        
        # Check required data files (optional - may be generated)
        # Only check if they're expected to exist
        
        # Check optional environment variables (warnings only)
        if not cls.OPENROUTER_API_KEY:
            missing_env_vars.append("OPENROUTER_API_KEY (optional, for LLM analysis)")
        
        if not cls.SEMANTIC_SCHOLAR_API_KEY:
            missing_env_vars.append("SEMANTIC_SCHOLAR_API_KEY (optional, for faster data collection)")
        
        return missing_files, missing_env_vars
    
    @classmethod
    def get_year_distribution_weights(cls, start_year: int, end_year: int) -> Dict[int, float]:
        """
        Get year distribution weights based on configuration
        
        Args:
            start_year: Starting year of collection range
            end_year: Ending year of collection range
            
        Returns:
            Dict mapping year to its collection weight
        """
        if cls.USE_CUSTOM_YEAR_DISTRIBUTION and cls.CUSTOM_YEAR_DISTRIBUTION:
            # Use custom distribution
            weights = {}
            for i, (year_offset, weight) in enumerate(cls.CUSTOM_YEAR_DISTRIBUTION.items()):
                year = end_year + year_offset
                if start_year <= year <= end_year:
                    weights[year] = weight
        else:
            # Use exponential decay distribution
            total_years = end_year - start_year + 1
            weights = {}
            total_weight = 0.0
            
            # Calculate weights with exponential decay (newer years get higher weights)
            for i in range(total_years):
                year = end_year - i  # Start from most recent
                weight = cls.EXPONENTIAL_DECAY_FACTOR ** i
                weights[year] = weight
                total_weight += weight
            
            # Normalize weights to sum to 1.0
            if total_weight > 0:
                for year in weights:
                    weights[year] /= total_weight
        
        return weights


# =============================================================================
# CONFIGURATION SUMMARY
# =============================================================================
# 
# This configuration file manages all parameters for the citation network analysis project:
# 
# 1. PATHS: Project directories and file locations
# 2. COLLECTION: Paper collection parameters including year distribution
# 3. PAGERANK: Algorithm parameters for network analysis
# 4. API: API keys, models, and rate limiting
# 5. NETWORK: Settings for network building and analysis
# 6. VISUALIZATION: Display and layout parameters
# 
# Key Year Distribution Parameters:
# - USE_CUSTOM_YEAR_DISTRIBUTION: Whether to use custom year distribution (True/False)
# - CUSTOM_YEAR_DISTRIBUTION: Dict mapping relative year offsets to weights
# - EXPONENTIAL_DECAY_FACTOR: Decay factor for automatic exponential distribution
# 
# Key Internal超参数 (可调优参数):
# - API_MAX_RETRIES: API请求失败重试次数
# - INITIAL_FETCH_MULTIPLIER: 初始收集论文数量倍数
# - INFLUENTIAL_CITATION_WEIGHT: 影响力引用权重
# - CITING_PAPERS_WEIGHT: 施引文献权重
# - ARXIV_CLIENT_PAGE_SIZE: arXiv API页面大小
# - SKIP_KAMADA_KAWAI_AUTO_THRESHOLD: 大图自动跳过布局的节点阈值
# 
# Usage: Import this config in other modules using:
# from config import Config
# print(Config.PAGERANK_ALPHA)  # Access any parameter
# weights = Config.get_year_distribution_weights(2022, 2025)  # Get year weights
# 
# =============================================================================
#!/usr/bin/env python3
"""
Topic Embedder - LLM-based Topic Generation and Taxonomy Benchmarking
Generates topic descriptions for communities using LLM and compares with QS taxonomy
"""

import pandas as pd
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from config import Config
from utils.logger import setup_logger
from openai import OpenAI

logger = setup_logger(__name__)

# QS Subject Taxonomy (Computer Science related)
QS_TAXONOMY = [
    "Computer Science - Artificial Intelligence",
    "Computer Science - Machine Learning",
    "Computer Science - Natural Language Processing",
    "Computer Science - Computer Vision",
    "Computer Science - Data Mining",
    "Computer Science - Information Systems",
    "Mathematics - Statistics",
    "Mathematics - Applied Mathematics",
    "Engineering - Software Engineering",
    "Engineering - Electrical Engineering",
    "Linguistics - Computational Linguistics",
    "Psychology - Cognitive Science"
]


def generate_community_topics_llm(
    comm_papers: List[str],
    papers_df: pd.DataFrame,
    max_papers: int = 10
) -> Optional[str]:
    """
    Use LLM to generate topic description for a community
    
    Parameters:
    -----------
    comm_papers : List[str]
        List of arxiv_ids in the community
    papers_df : pd.DataFrame
        Papers DataFrame
    max_papers : int
        Maximum number of papers to include in prompt
        
    Returns:
    --------
    Optional[str]
        Topic description or None if failed
    """
    if not Config.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set. Cannot generate topics.")
        return None
    
    # Get paper titles and abstracts
    comm_papers_df = papers_df[papers_df['arxiv_id'].astype(str).isin(comm_papers)]
    if comm_papers_df.empty:
        return None
    
    # Limit number of papers
    comm_papers_df = comm_papers_df.head(max_papers)
    
    titles = comm_papers_df['title'].tolist()
    abstracts = comm_papers_df['abstract'].fillna('').tolist()
    
    # Build prompt
    papers_text = "\n".join([
        f"{i+1}. {title}\n   Abstract: {abstract[:200]}..." if len(abstract) > 200 else f"{i+1}. {title}\n   Abstract: {abstract}"
        for i, (title, abstract) in enumerate(zip(titles, abstracts))
    ])
    
    prompt = f"""Analyze the following research papers from a citation network community and identify the main research themes.

Papers:
{papers_text}

Provide 3-5 key research themes or topics that characterize this community. Format as comma-separated keywords or short phrases.
Example: "machine learning, neural networks, deep learning, natural language processing"

Topics:"""
    
    # Determine which API to use (优先级: DashScope > OpenAI > OpenRouter)
    use_dashscope = Config.USE_DASHSCOPE and Config.DASHSCOPE_API_KEY
    use_openai = Config.USE_OPENAI and Config.OPENAI_API_KEY and not use_dashscope
    use_openrouter = Config.OPENROUTER_API_KEY and not use_dashscope and not use_openai
    
    if not use_dashscope and not use_openai and not use_openrouter:
        logger.warning("No API key available. Cannot generate topics.")
        return None
    
    # 使用 OpenAI 客户端
    if use_openai:
        try:
            client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_BASE_URL
            )
            rate_limit = Config.OPENAI_RATE_LIMIT
            time.sleep(1.0 / rate_limit)  # Rate limiting
            
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            result = response.choices[0].message.content.strip()
            logger.info(f"Generated topic for community with {len(comm_papers)} papers (using OpenAI)")
            return result
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    # 使用 REST API (DashScope 或 OpenRouter)
    # Prepare API call based on selected provider
    if use_dashscope:
        # DashScope (百炼) API - 使用X-DashScope-API-Key认证头
        headers = {
            "X-DashScope-API-Key": Config.DASHSCOPE_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "model": Config.DASHSCOPE_MODEL,
            "input": {
                "messages": [{"role": "user", "content": prompt}]
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 200
            }
        }
        api_url = Config.DASHSCOPE_URL
        rate_limit = Config.DASHSCOPE_RATE_LIMIT
    else:
        # OpenRouter API (fallback)
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": Config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
        api_url = Config.OPENROUTER_URL
        rate_limit = Config.OPENROUTER_RATE_LIMIT
    
    try:
        time.sleep(1.0 / rate_limit)  # Rate limiting
        response = requests.post(
            api_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        if response.status_code == 200:
            if use_dashscope:
                # DashScope response format
                result = response.json()["output"]["choices"][0]["message"]["content"].strip()
            else:
                # OpenRouter response format
                result = response.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"Generated topic for community with {len(comm_papers)} papers (using {'DashScope' if use_dashscope else 'OpenRouter'})")
            return result
        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error generating topics: {e}")
        return None


def embed_topics_simple_similarity(
    community_topics: List[str],
    qs_taxonomy: List[str] = QS_TAXONOMY
) -> pd.DataFrame:
    """
    Simple keyword-based similarity matching (fallback when embeddings unavailable)
    
    Parameters:
    -----------
    community_topics : List[str]
        List of community topic descriptions
    qs_taxonomy : List[str]
        List of QS taxonomy categories
        
    Returns:
    --------
    pd.DataFrame
        Matching results with similarity scores
    """
    matches = []
    
    for i, comm_topic in enumerate(community_topics):
        if not comm_topic or pd.isna(comm_topic):
            continue
        
        # Simple keyword matching
        comm_keywords = set(comm_topic.lower().split())
        best_match = None
        best_score = 0
        
        for qs_category in qs_taxonomy:
            qs_keywords = set(qs_category.lower().split())
            # Calculate Jaccard similarity
            intersection = len(comm_keywords & qs_keywords)
            union = len(comm_keywords | qs_keywords)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > best_score:
                best_score = similarity
                best_match = qs_category
        
        matches.append({
            'community_id': i,
            'community_topic': comm_topic,
            'matched_qs_category': best_match if best_match else 'N/A',
            'similarity_score': best_score
        })
    
    return pd.DataFrame(matches)


def benchmark_against_taxonomy(
    community_topics: List[str],
    qs_taxonomy: List[str] = QS_TAXONOMY,
    use_embeddings: bool = False
) -> pd.DataFrame:
    """
    Benchmark community topics against QS taxonomy
    
    Parameters:
    -----------
    community_topics : List[str]
        List of community topic descriptions
    qs_taxonomy : List[str]
        List of QS taxonomy categories
    use_embeddings : bool
        Whether to use sentence transformers (requires installation)
        
    Returns:
    --------
    pd.DataFrame
        Benchmarking results
    """
    if use_embeddings:
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Generate embeddings
            model = SentenceTransformer('all-MiniLM-L6-v2')
            all_topics = community_topics + qs_taxonomy
            embeddings = model.encode(all_topics)
            
            # Calculate similarity
            comm_embeddings = embeddings[:len(community_topics)]
            qs_embeddings = embeddings[len(community_topics):]
            
            similarity_matrix = cosine_similarity(comm_embeddings, qs_embeddings)
            
            matches = []
            for i, comm_topic in enumerate(community_topics):
                if not comm_topic or pd.isna(comm_topic):
                    continue
                best_match_idx = np.argmax(similarity_matrix[i])
                matches.append({
                    'community_id': i,
                    'community_topic': comm_topic,
                    'matched_qs_category': qs_taxonomy[best_match_idx],
                    'similarity_score': float(similarity_matrix[i][best_match_idx])
                })
            
            return pd.DataFrame(matches)
        except ImportError:
            logger.warning("sentence-transformers not installed. Using simple keyword matching.")
            return embed_topics_simple_similarity(community_topics, qs_taxonomy)
    else:
        return embed_topics_simple_similarity(community_topics, qs_taxonomy)


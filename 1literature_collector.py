#!/usr/bin/env python3
"""
Academic Literature Collector with Integrated Quality Control
Fetches papers from arXiv and enriches them with citation data from Semantic Scholar.
Includes integrated data quality control to ensure exact target count after cleaning.
Supports custom domains, year ranges, and paper counts via interactive input.
Now includes citation network analysis (both references and citations).
"""

import os
import requests
import arxiv
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
import numpy as np

# 导入配置
try:
    from config import Config
except ImportError:
    print("⚠️  Config module not found. Using default parameters.")
    # 定义默认配置以保持向后兼容
    class Config:
        INITIAL_FETCH_MULTIPLIER = 2
        API_MAX_RETRIES = 3
        ARXIV_CLIENT_DELAY = 3.0
        ARXIV_CLIENT_PAGE_SIZE = 100
        INFLUENTIAL_CITATION_WEIGHT = 2.0
        IN_S2_BONUS_SCORE = 100
        CITING_PAPERS_WEIGHT = 0.5
        USE_CUSTOM_YEAR_DISTRIBUTION = False
        CUSTOM_YEAR_DISTRIBUTION = {}
        EXPONENTIAL_DECAY_FACTOR = 0.7


def load_api_key():
    """Load Semantic Scholar API key from .env (without quotes!)"""
    env_path = Path(".env").resolve()
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"⚠️  Warning: .env file not found at {env_path}")
    
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if not key:
        print("ℹ️  No valid Semantic Scholar API key found. Using rate-limited mode (1 request/sec).")
    return key


def get_user_input():
    print("\n📚 Welcome to the Academic Literature Collector!\n")
    
    domain = input("🔍 Enter research domain (e.g., 'large language model', 'robotics'): ").strip()
    if not domain:
        domain = "large language model"
        print(f"  → Using default domain: '{domain}'")
    
    while True:
        try:
            max_papers = int(input("📄 Enter max number of papers (1–500, default=100): ").strip() or 100)
            if 1 <= max_papers <= 500:
                break
            print("  → Please enter a number between 1 and 500.")
        except ValueError:
            print("  → Please enter a valid integer.")
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # 设置默认年份范围，避免太新的论文（至少3个月前）
    default_start = current_year - 3  # 3年前开始
    default_end = current_year - 1 if current_month < 4 else current_year  
    
    start_year = int(input(f"📅 Enter start year (default={default_start}): ").strip() or default_start)
    end_year = int(input(f"📅 Enter end year (default={default_end}, avoid very recent papers): ").strip() or default_end)
    
    if not (1900 <= start_year <= end_year <= current_year + 1):
        print(f"  → Invalid years. Using default range: {default_start}–{default_end}")
        start_year, end_year = default_start, default_end
    
    # 询问是否只保留有影响力的论文
    print("\n🎯 Quality filter options:")
    filter_choice = input("   Filter to only high-impact papers (indexed in Semantic Scholar)? [Y/n]: ").strip().lower()
    filter_high_impact = filter_choice != 'n'
    
    if filter_high_impact:
        print("   ✅ Will prioritize papers indexed in Semantic Scholar (more likely to have citations)")
    
    # 询问是否包含施引文献分析
    print("\n🔗 Citation network options:")
    include_citations = input("   Include citing papers (find which papers cite your selected papers)? [Y/n]: ").strip().lower() != 'n'
    
    if include_citations:
        print("   ✅ Will include citation network analysis (both references and citations)")
    
    # 询问年份分布策略
    print("\n📅 Year distribution options:")
    print(f"   Current config: USE_CUSTOM_YEAR_DISTRIBUTION = {Config.USE_CUSTOM_YEAR_DISTRIBUTION}")
    if Config.USE_CUSTOM_YEAR_DISTRIBUTION and Config.CUSTOM_YEAR_DISTRIBUTION:
        print(f"   Custom distribution: {Config.CUSTOM_YEAR_DISTRIBUTION}")
    else:
        print(f"   Exponential decay factor: {Config.EXPONENTIAL_DECAY_FACTOR}")
    
    return domain, max_papers, start_year, end_year, filter_high_impact, include_citations


def fetch_papers_by_domain(domain, max_papers, start_year, end_year):
    """
    Fetch papers from arXiv with custom year distribution based on configuration.
    Uses keyword search without strict category filters to maximize results.
    """
    print(f"\n🔍 Searching arXiv for: '{domain}' ({start_year}–{end_year}) ...")
    
    papers_by_year = {year: [] for year in range(start_year, end_year + 1)}
    total_collected = 0
    
    # Use simple keyword query without restrictive categories
    query = domain
    search = arxiv.Search(
        query=query,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending
    )
    
    client = arxiv.Client(page_size=Config.ARXIV_CLIENT_PAGE_SIZE, delay_seconds=Config.ARXIV_CLIENT_DELAY)
    result_count = 0
    
    print("   Collecting papers...")
    for result in client.results(search):
        result_count += 1
        year = result.published.year
        
        # Filter by target year range
        if start_year <= year <= end_year:
            arxiv_id = result.get_short_id().split('v')[0]
            papers_by_year[year].append({
                "arxiv_id": arxiv_id,
                "title": result.title,
                "abstract": result.summary.replace("\n", " "),
                "year": year,
                "published": result.published.strftime("%Y-%m-%d"),
                "pdf_url": result.pdf_url,
                "doi": result.doi or "",
                "domain": domain
            })
            total_collected += 1
        
        # Prevent excessive loading
        if total_collected >= max_papers * Config.INITIAL_FETCH_MULTIPLIER:
            break
            
        if result_count % 100 == 0:
            print(f"      Processed {result_count} results, {total_collected} in target range")
    
    print(f"   Papers collected by year:")
    for year in range(start_year, end_year + 1):
        count = len(papers_by_year[year])
        print(f"      {year}: {count} papers")
    
    # 根据配置的年份分布权重分配论文
    print("\n🎯 Distributing papers according to configured year distribution...")
    
    # 获取年份分布权重
    year_weights = Config.get_year_distribution_weights(start_year, end_year)
    
    # 计算每个年份的目标论文数量
    selected_papers = []
    total_weight = sum(year_weights.values()) if year_weights else 1.0
    
    for year, weight in year_weights.items():
        if year in papers_by_year:
            # 计算该年份应该分配的论文数量
            target_count = int(max_papers * (weight / total_weight))
            available_papers = papers_by_year[year]
            
            # 取该年份的前target_count篇论文（按相关性排序）
            selected_papers.extend(available_papers[:min(target_count, len(available_papers))])
            print(f"      {year}: {min(target_count, len(available_papers))}/{target_count} papers (weight: {weight:.2f})")
    
    # 如果论文总数不足max_papers，从剩余年份中补充
    remaining_slots = max_papers - len(selected_papers)
    if remaining_slots > 0:
        print(f"   🔄 Filling remaining {remaining_slots} slots from other years...")
        all_remaining = []
        for year in range(start_year, end_year + 1):
            if year in papers_by_year:
                already_selected = len([p for p in selected_papers if p['year'] == year])
                remaining_from_year = papers_by_year[year][already_selected:]
                all_remaining.extend(remaining_from_year)
        
        # 按年份顺序补充剩余论文
        selected_papers.extend(all_remaining[:remaining_slots])
    
    print(f"✅ Final selection: {len(selected_papers)} papers")
    return selected_papers


def enrich_with_semantic_scholar(arxiv_id, api_key, include_citations=False, max_retries=None, verbose=True):
    """
    Enrich arXiv paper with Semantic Scholar data, including citation metrics and citation network.
    
    Args:
        arxiv_id: arXiv ID (e.g., '2511.05491')
        api_key: Semantic Scholar API key (optional)
        include_citations: Whether to fetch citing papers (citations)
        max_retries: Maximum retry attempts (defaults to config value)
        verbose: If False, suppress 404 error messages (for cleaner output)
    
    Returns:
        dict with 'in_s2', 's2_paperId', 'references', 'citations', 'citationCount', 'influentialCitationCount' keys
    """
    if max_retries is None:
        max_retries = Config.API_MAX_RETRIES
    
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
    # 获取引用数、影响力引用数等指标
    fields = "paperId,references.paperId,citationCount,influentialCitationCount"
    if include_citations:
        fields += ",citations.paperId"
    
    params = {"fields": fields}
    headers = {"x-api-key": api_key} if api_key else {}
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                refs = data.get("references") or []
                ref_ids = [r["paperId"] for r in refs if r.get("paperId")]
                
                # 获取施引文献（被哪些文章引用）
                citations = data.get("citations") or []
                citation_ids = [c["paperId"] for c in citations if c.get("paperId")]
                
                citation_count = data.get("citationCount", 0)
                influential_citations = data.get("influentialCitationCount", 0)
                
                if verbose:
                    msg = f"  ✅ arXiv:{arxiv_id} → {len(ref_ids)} refs, {citation_count} citations"
                    if include_citations:
                        msg += f", {len(citation_ids)} citing papers"
                    print(msg)
                
                result = {
                    "in_s2": True,
                    "s2_paperId": data.get("paperId"),
                    "references": ref_ids,
                    "citations": citation_ids,  # 施引文献列表
                    "citationCount": citation_count,
                    "influentialCitationCount": influential_citations
                }
                return result
            
            elif response.status_code == 404:
                # Paper not found in Semantic Scholar (common for very new papers)
                if verbose:
                    print(f"  ⚠️  arXiv:{arxiv_id} → Not indexed in Semantic Scholar yet")
                return {
                    "in_s2": False,
                    "references": [],
                    "citations": [],
                    "citationCount": 0,
                    "influentialCitationCount": 0
                }
            
            elif response.status_code == 429:
                wait = 2 ** attempt  # 指数退避: 1s, 2s, 4s...
                if verbose:
                    print(f"  ⚠️  arXiv:{arxiv_id} → Rate limited (429). Retry in {wait}s (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(wait)
                    continue
                else:
                    if verbose:
                        print(f"  ❌ arXiv:{arxiv_id} → Failed after {max_retries} retries (429)")
                    return {
                        "in_s2": False,
                        "references": [],
                        "citations": [],
                        "citationCount": 0,
                        "influentialCitationCount": 0
                    }
            
            else:
                # 其他 HTTP 错误（5xx, 403 等）
                if verbose:
                    print(f"  ⚠️  arXiv:{arxiv_id} → HTTP {response.status_code}. Retry in 2s...")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                else:
                    if verbose:
                        print(f"  ❌ arXiv:{arxiv_id} → Failed after {max_retries} retries (HTTP {response.status_code})")
                    return {
                        "in_s2": False,
                        "references": [],
                        "citations": [],
                        "citationCount": 0,
                        "influentialCitationCount": 0
                    }
        
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"  ⚠️  arXiv:{arxiv_id} → Network error: {e}. Retry in 2s...")
            if attempt < max_retries:
                time.sleep(2)
                continue
            else:
                if verbose:
                    print(f"  ❌ arXiv:{arxiv_id} → Failed after {max_retries} retries (network error)")
                return {
                    "in_s2": False,
                    "references": [],
                    "citations": [],
                    "citationCount": 0,
                    "influentialCitationCount": 0
                }
    
    return {
        "in_s2": False,
        "references": [],
        "citations": [],
        "citationCount": 0,
        "influentialCitationCount": 0
    }


def build_citation_network(enriched_papers, include_citations):
    """Build both reference and citation edges for network analysis"""
    reference_edges = []  # 引用关系：paper -> its references
    citation_edges = []   # 被引用关系：citing_paper -> cited_paper
    
    for paper in enriched_papers:
        if paper.get("in_s2"):
            source = f"arXiv:{paper['arxiv_id']}"
            
            # 构建引用边（该论文引用了哪些文献）
            for ref_id in paper.get("references", []):
                if ref_id:
                    reference_edges.append({
                        "source": source, 
                        "target": ref_id,
                        "type": "reference"  # 该论文引用了target
                    })
            
            # 构建施引边（哪些文献引用了该论文）
            if include_citations:
                for citing_id in paper.get("citations", []):
                    if citing_id:
                        citation_edges.append({
                            "source": citing_id,  # 引用者
                            "target": source,     # 被引用者
                            "type": "citation"    # source被target引用
                        })
    
    return reference_edges, citation_edges


def integrated_quality_control_and_recovery(
    enriched_papers: list,
    max_papers: int,
    filter_high_impact: bool,
    include_citations: bool
):
    """
    Integrated quality control and recovery to ensure exact target count
    This simulates the cleaning process to predict what will be removed and adjust accordingly
    """
    print(f"\n🔄 Integrated quality control and recovery to ensure {max_papers} papers after cleaning...")
    
    # 计算影响力分数
    for paper in enriched_papers:
        citation_count = paper.get("citationCount", 0)
        influential_citations = paper.get("influentialCitationCount", 0)
        in_s2 = paper.get("in_s2", False)
        
        # 影响力分数：引用数 + 影响力引用数 * 2 + 是否在S2中（额外加分）
        paper["impact_score"] = citation_count + influential_citations * Config.INFLUENTIAL_CITATION_WEIGHT + (Config.IN_S2_BONUS_SCORE if in_s2 else 0)
        
        # 如果包含施引文献分析，可以考虑施引文献数量
        if include_citations:
            citing_papers_count = len(paper.get("citations", []))
            paper["impact_score"] += citing_papers_count * Config.CITING_PAPERS_WEIGHT  # 给施引文献数量加权
    
    # 排序：优先选择在S2中的、引用数高的论文
    enriched_papers.sort(
        key=lambda p: (
            p.get("in_s2", False),  # 首先按是否在S2中（True > False）
            p.get("impact_score", 0)  # 然后按影响力分数
        ),
        reverse=True
    )
    
    def simulate_cleaning_condition(paper):
        """模拟清洗代码的所有四个移除条件"""
        # 条件1: 缺失 arxiv_id 或 title
        if pd.isna(paper.get("arxiv_id")) or pd.isna(paper.get("title")):
            return False, "Missing arxiv_id or title"
        
        # 条件2: in_s2 = False (当启用高质量过滤时)
        if filter_high_impact and not paper.get("in_s2", False):
            return False, "in_s2 = False (not in Semantic Scholar)"
        
        # 条件3: 空引用 (empty string/[]/nan)
        references_str = str(paper.get("references", "[]")).strip()
        if references_str in ["", "[]", "nan", "None", "[]"]:
            return False, "Empty references (empty string/[]/nan)"
        
        # 条件4: 重复的 arxiv_id (需要检查重复)
        # 注意：这个条件在实际清洗时才检测，这里我们假设收集阶段已经去重
        # 如果需要完全模拟重复检查，需要在整个列表中检查
        # 但考虑到收集阶段已经按相关性排序且arXiv通常不会返回重复，这里暂时忽略
        
        return True, "Valid"
    
    # 模拟清洗过程：预测哪些论文会被移除
    papers_to_remove = []
    removal_reasons = []
    
    for i, paper in enumerate(enriched_papers):
        is_valid, reason = simulate_cleaning_condition(paper)
        if not is_valid:
            papers_to_remove.append(i)
            removal_reasons.append(reason)
    
    # 创建清洗后的论文列表（预测）
    cleaned_papers = [paper for i, paper in enumerate(enriched_papers) if i not in papers_to_remove]
    
    print(f"   📊 Predicted after cleaning: {len(cleaned_papers)}/{max_papers} papers")
    if papers_to_remove:
        print(f"   📊 Predicted removals: {len(papers_to_remove)} papers")
        # 统计预测的移除原因
        from collections import Counter
        reason_counts = Counter(removal_reasons)
        for reason, count in reason_counts.items():
            print(f"      - {reason}: {count}")
    
    if len(cleaned_papers) >= max_papers:
        # 如果清洗后数量足够，直接选择前max_papers个
        final_papers = cleaned_papers[:max_papers]
    else:
        # 如果清洗后数量不够，需要从原始列表中选择更多论文来补偿
        print(f"   🔄 Need to select more papers to compensate for cleaning...")
        
        # 从原始排序列表中选择，但要确保最终清洗后有max_papers个
        candidate_papers = []
        for paper in enriched_papers:
            candidate_papers.append(paper)
            
            # 模拟清洗当前候选列表
            current_cleaned = []
            for cp in candidate_papers:
                is_valid, _ = simulate_cleaning_condition(cp)
                if is_valid:
                    current_cleaned.append(cp)
            
            if len(current_cleaned) >= max_papers:
                final_papers = current_cleaned[:max_papers]
                print(f"   ✅ Selected {len(candidate_papers)} papers to ensure {len(final_papers)} after cleaning")
                break
        else:
            # 如果所有论文都选了还是不够，就返回所有清洗后的论文
            final_papers = cleaned_papers
            print(f"   ⚠️  Could not reach target count: {len(final_papers)}/{max_papers}")
    
    return final_papers

def main():
    S2_API_KEY = load_api_key()
    domain, max_papers, start_year, end_year, filter_high_impact, include_citations = get_user_input()
    
    # 先获取更多论文（用于筛选）
    initial_papers = fetch_papers_by_domain(domain, max_papers * Config.INITIAL_FETCH_MULTIPLIER, start_year, end_year)
    if not initial_papers:
        print("❌ No papers found. Try broader keywords or adjust year range.")
        return
    
    print(f"\n🔄 Enriching papers with citation data and impact metrics...")
    print(f"   📊 Including citation network: {'Yes' if include_citations else 'No'}")
    
    enriched_papers = []
    stats = {"found": 0, "not_found": 0}
    
    # ✅ Fixed rate: 1 request per second (safe for all cases)
    # Use verbose=False to suppress individual 404 messages, show summary at end
    for paper in tqdm(initial_papers, desc="Fetching impact data"):
        arxiv_id = paper["arxiv_id"]
        s2_info = enrich_with_semantic_scholar(arxiv_id, S2_API_KEY, include_citations, verbose=False)
        enriched_papers.append({**paper, **s2_info})
        
        if s2_info.get("in_s2"):
            stats["found"] += 1
        else:
            stats["not_found"] += 1
        
        time.sleep(1.0)  # 🚦 Enforce 1 request/sec
    
    # Print initial statistics
    print(f"\n📊 Semantic Scholar enrichment summary:")
    print(f"   ✅ Found: {stats['found']} papers indexed in Semantic Scholar")
    print(f"   ⚠️  Not indexed: {stats['not_found']} papers (may be too new)")
    
    # 集成质量控制和恢复以确保精确数量（模拟清洗后的最终数量）
    final_papers = integrated_quality_control_and_recovery(
        enriched_papers, 
        max_papers, 
        filter_high_impact, 
        include_citations
    )
    
    # 构建引用网络和施引网络
    reference_edges, citation_edges = build_citation_network(final_papers, include_citations)
    
    # 显示最终统计
    avg_citations = sum(p.get("citationCount", 0) for p in final_papers) / len(final_papers) if final_papers else 0
    indexed_count = sum(1 for p in final_papers if p.get("in_s2", False))
    
    print(f"\n📈 Final paper selection:")
    print(f"   📄 Total papers: {len(final_papers)} (target: {max_papers})")
    print(f"   ✅ Indexed in S2: {indexed_count}/{len(final_papers)}")
    print(f"   📊 Average citations: {avg_citations:.1f}")
    print(f"   🔗 Reference edges: {len(reference_edges)} (papers → their references)")
    if include_citations:
        print(f"   📈 Citation edges: {len(citation_edges)} (citing papers → cited papers)")
        print(f"   🌐 Total network edges: {len(reference_edges) + len(citation_edges)}")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe_domain = "".join(c if c.isalnum() else "_" for c in domain[:20])
    paper_file = f"papers_{safe_domain}_{timestamp}.csv"
    ref_edge_file = f"reference_edges_{safe_domain}_{timestamp}.csv"
    cit_edge_file = f"citation_edges_{safe_domain}_{timestamp}.csv"  # 新增施引边文件
    
    # 保存论文数据
    pd.DataFrame(final_papers).to_csv(paper_file, index=False, encoding='utf-8')
    
    # 保存引用边（参考文献）
    pd.DataFrame(reference_edges, columns=["source", "target", "type"]).to_csv(ref_edge_file, index=False, encoding='utf-8')
    
    # 保存施引边（被引用关系）
    if include_citations:
        pd.DataFrame(citation_edges, columns=["source", "target", "type"]).to_csv(cit_edge_file, index=False, encoding='utf-8')
    
    print(f"\n🎉 Collection complete!")
    print(f"  📁 Papers saved to: {paper_file}")
    print(f"  📚 Reference edges saved to: {ref_edge_file}")
    if include_citations:
        print(f"  📈 Citation edges saved to: {cit_edge_file}")
    
    total_edges = len(reference_edges) + len(citation_edges) if include_citations else len(reference_edges)
    print(f"  📊 Network stats: {len(final_papers)} papers, {total_edges} citation edges")
    
    # 额外验证：确保数量准确
    if len(final_papers) == max_papers:
        print(f"  ✅ SUCCESS: Exact target count achieved: {len(final_papers)} papers = {max_papers} (requested)")
    else:
        print(f"  ⚠️  WARNING: Target count not fully achieved: {len(final_papers)} papers ≠ {max_papers} (requested)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
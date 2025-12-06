# 跨学科分析模块 (Interdisciplinary Analysis Module)

> ⚠️ **注意**：此模块已被移除
> 
> 跨学科分析模块（`6interdisciplinary_analyzer.py`）和相关的工具模块（`utils/interdisciplinary_analyzer.py`）已从项目中删除。
> 
> **删除原因**：
> - 桥接论文检测功能在当前数据集上效果不佳，未找到有效的桥接论文
> - 网络结构主要为 `paper -> reference` 连接，缺乏直接的 `paper -> paper` 连接
> - 功能与项目核心目标关联度较低
> 
> **替代方案**：
> - 社区主题生成和分类法对比功能已集成到 `utils/topic_embedder.py` 中
> - 可通过 `5app.py` 的 "Topic Benchmarking" 标签页访问
> 
> **历史文档**：
> 以下内容保留作为历史参考，实际代码已不存在。

---

## 项目概述（历史）

这是一个用于分析学术引用网络的跨学科分析模块，能够识别未被充分探索但高影响力的研究领域、检测连接不同研究社区的桥接论文，以及使用LLM生成社区主题并与QS学科分类法进行对比。

## 核心功能（历史）

### 1. 未被充分探索领域检测
- **社区特征分析**：计算每个社区的论文数量、平均引用数、平均PageRank等指标
- **探索评分**：基于"高影响力/小规模"的公式识别潜在研究机会
- **跨社区连接**：分析社区间的连接数量

### 2. 跨学科桥接论文检测
- **Betweenness Centrality**：计算论文的中介中心性
- **社区桥接**：识别连接多个不同社区的论文
- **跨学科评分**：综合连接社区数和中介中心性

### 3. 社区主题生成与分类法对比
- **LLM主题生成**：使用大语言模型为每个社区生成主题描述
- **QS分类法对比**：将检测到的主题与QS学科分类法进行匹配
- **相似度计算**：使用关键词匹配或嵌入向量计算相似度

## 代码结构（历史）

```
6interdisciplinary_analyzer.py (已删除)
├── load_network_data()                    # 加载网络数据
├── build_network_graph()                  # 构建网络图
├── analyze_niches()                       # 分析未被充分探索领域
│   ├── analyze_community_characteristics() # 分析社区特征
│   └── identify_under_explored_niches()    # 识别未被充分探索领域
├── analyze_interdisciplinary_links()      # 分析跨学科连接
│   └── detect_interdisciplinary_links()    # 检测桥接论文
└── analyze_community_topics()              # 分析社区主题
    ├── generate_community_topics_llm()     # LLM生成主题
    └── benchmark_against_taxonomy()        # 与分类法对比
```

## 主要函数说明（历史）

### `load_network_data()`
加载论文、边数据和社区数据，以及PageRank结果。

**返回：**
- `papers`: 论文DataFrame
- `edges`: 边DataFrame
- `node_df`: 节点社区归属DataFrame
- `pagerank_df`: PageRank结果DataFrame

### `build_network_graph(papers, edges, node_df)`
构建NetworkX图对象，包含论文和参考文献节点。

**参数：**
- `papers`: 论文DataFrame
- `edges`: 边DataFrame
- `node_df`: 节点社区归属DataFrame

**返回：**
- `G`: NetworkX图对象

### `analyze_niches(G, node_df, papers, pagerank_df)`
分析未被充分探索但高影响力的研究领域。

**参数：**
- `G`: 网络图
- `node_df`: 节点社区归属DataFrame
- `papers`: 论文DataFrame
- `pagerank_df`: PageRank结果DataFrame

**返回：**
- `niches`: 未被充分探索领域DataFrame

### `detect_interdisciplinary_links(G, node_df, papers_df)`
检测连接不同社区的桥接论文。

**参数：**
- `G`: 网络图
- `node_df`: 节点社区归属DataFrame
- `papers_df`: 论文DataFrame

**返回：**
- `bridging_papers`: 桥接论文DataFrame

### `analyze_community_topics(G, node_df, papers_df)`
生成社区主题并与QS分类法对比。

**参数：**
- `G`: 网络图
- `node_df`: 节点社区归属DataFrame
- `papers_df`: 论文DataFrame

**返回：**
- `topics`: 社区主题列表
- `benchmark`: 分类法对比结果DataFrame

## 输出文件（历史）

- `under_explored_niches.csv`: 未被充分探索领域
- `interdisciplinary_links.csv`: 跨学科桥接论文
- `taxonomy_benchmark.csv`: 主题分类法对比结果

## 配置参数（历史）

- `NICHE_MIN_PAGERANK`: 最小平均PageRank（默认0.01）
- `NICHE_MAX_PAPER_COUNT`: 最大论文数（默认20）

## 使用说明（历史）

```bash
# 此脚本已删除，不再可用
python 6interdisciplinary_analyzer.py
```

## 迁移指南

如果您需要类似的功能，请参考：

1. **社区主题生成**：使用 `utils/topic_embedder.py` 中的 `generate_community_topics_llm()` 函数
2. **分类法对比**：使用 `utils/topic_embedder.py` 中的 `benchmark_against_taxonomy()` 函数
3. **Web界面**：在 `5app.py` 的 "Topic Benchmarking" 标签页中查看结果

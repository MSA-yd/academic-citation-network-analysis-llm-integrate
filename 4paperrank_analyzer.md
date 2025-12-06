# PageRank分析模块 (PageRank Analysis Module)

## 项目概述

这是一个用于学术引用网络分析的优化PageRank模块，能够计算标准PageRank、时间加权PageRank和质量加权PageRank，为论文推荐提供多维度的分析结果。模块支持完整的学术引用网络结构和质量加权分析。同时集成了PageRank历史追踪功能，可以识别上升论文或基于当前指标预测潜在上升论文。

## 核心功能

### 1. 多维度PageRank计算
- **标准PageRank**：基于传统PageRank算法的影响力分析
- **时间加权PageRank**：考虑引用时间的指数衰减权重
- **质量加权PageRank**：基于引用论文质量的权重分配
- **混合推荐系统**：综合多种指标生成最终推荐

### 2. 学术引用网络构建
- **引用方向处理**：正确处理论文→参考文献的引用方向
- **内部论文识别**：区分数据集内部论文和外部参考文献
- **边属性存储**：存储引用年份和引用者质量信息
- **网络优化**：仅包含内部论文节点，提高计算效率

### 3. 可视化分析
- **交互式图表**：使用Plotly生成HTML可视化图表
- **多维度对比**：标准PageRank vs 时间PageRank vs 质量PageRank
- **混合分数分析**：综合评分的散点图和柱状图
- **排行榜展示**：Top 10论文的详细对比分析

### 4. 增强推荐系统
- **排名归一化**：使用百分位排名确保公平比较
- **权重配置**：可配置的混合评分权重
- **多指标输出**：提供5种不同的排名结果
- **详细日志**：完整的TOP论文信息展示

### 5. PageRank历史追踪与上升论文识别
- **历史追踪**：记录每次分析的PageRank分数
- **上升论文识别**：基于历史数据识别PageRank上升的论文
- **预测模式**：当历史不足时，基于当前指标预测潜在上升论文
- **模拟历史生成**：为演示生成模拟历史数据

## 主要参数

### 配置文件参数
通过 `config.py` 文件可配置的内部参数：

#### PageRank参数
- `PAGERANK_ALPHA`：PageRank阻尼因子（默认0.85）
- `TEMPORAL_DECAY_LAMBDA`：时间衰减系数（默认0.1）

#### 混合评分权重
- `pagerank`：标准PageRank权重（25%）
- `temporal`：时间PageRank权重（20%）
- `quality`：质量PageRank权重（20%）
- `citation`：引用数权重（25%）
- `recency`：新近度权重（10%）

## 使用方法

### 1. 环境准备
```bash
pip install pandas networkx matplotlib plotly ast
```

### 2. 基本使用
```bash
# 使用默认配置运行
python 4pagerank.py

# 模块化调用（在其他脚本中）
from pagerank_analyzer import run_pagerank_analysis

results = run_pagerank_analysis(
    paper_file=Path("papers_cleaned.csv"),
    edge_file=Path("edges_cleaned.csv"),
    decay_lambda=0.15,
    alpha=0.9
)
```

## 输出文件

### 数据文件
- `pagerank_results.csv`：完整的PageRank分析结果
  - 包含arxiv_id、标题、年份、引用数等基本信息
  - 三种PageRank分数和排名
  - 混合评分和综合排名

### 可视化文件
- `fig/temporal_recommendations.html`：时间PageRank推荐图
- `fig/pagerank_comparison.html`：PageRank对比图  
- `fig/hybrid_analysis.html`：混合分数分析图

## 代码结构

```
4pagerank.py
├── load_and_prepare_data()               # 数据加载和准备
├── parse_references()                    # 引用解析
├── build_academic_citation_graph_optimized()  # 学术引用网络构建
├── compute_optimized_pagerank()          # 标准PageRank计算
├── manual_pagerank_fallback()            # 手动PageRank备用方案
├── compute_temporal_weighted_pagerank()  # 时间加权PageRank
├── compute_quality_weighted_pagerank()   # 质量加权PageRank
├── generate_charts()                     # 可视化图表生成
├── generate_recommendations_enhanced()   # 增强推荐系统
└── run_pagerank_analysis()               # 主分析流程
```

## PageRank算法详解

### 1. 标准PageRank（Standard PageRank）
- **基础算法**：传统PageRank公式
- **网络结构**：反向引用网络（被引用→引用者）
- **阻尼因子**：可配置的alpha参数（默认0.85）
- **收敛标准**：tol=1e-6，max_iter=100

### 2. 时间加权PageRank（Temporal Weighted PageRank）
- **时间衰减**：指数衰减权重 `weight = exp(-λ * time_diff)`
- **当前年份**：自动从数据中获取最大年份
- **时间差计算**：引用年份与当前年份的差值
- **权重应用**：作为边权重传递给PageRank算法

### 3. 质量加权PageRank（Quality Weighted PageRank）
- **质量分数**：`citationCount + 2 * influentialCitationCount`
- **权重计算**：`weight = log(1 + quality_score)`
- **质量来源**：引用者的学术影响力
- **重要性体现**：高质量引用获得更高权重

## 混合推荐系统

### 1. 排名归一化
```python
# 使用百分位排名确保各指标可比性
results['pagerank_rank'] = results['pagerank_score'].rank(pct=True)
results['temporal_pagerank_rank'] = results['temporal_pagerank_score'].rank(pct=True)
results['quality_pagerank_rank'] = results['quality_pagerank_score'].rank(pct=True)
results['citation_rank'] = results['citationCount'].rank(pct=True)
results['year_rank'] = results['year'].rank(pct=True)
```

### 2. 混合评分公式
```
hybrid_score = 
  0.25 * pagerank_rank +      # 标准网络影响力
  0.20 * temporal_pagerank_rank +  # 时间影响力
  0.20 * quality_pagerank_rank +   # 质量影响力  
  0.25 * citation_rank +      # 外部引用影响力
  0.10 * year_rank            # 新近度因子
```

### 3. 多维度排名输出
- `rank_std`：标准PageRank排名
- `rank_temp`：时间PageRank排名（新兴趋势）
- `rank_quality`：质量PageRank排名（影响力引用）
- `rank_citation`：引用数排名
- `rank_hybrid`：混合评分排名（主推荐）

## 可视化特性

### 1. 时间推荐图（Temporal Recommendations）
- **图表类型**：水平柱状图
- **数据范围**：Top 20时间PageRank论文
- **悬停信息**：年份、排名、引用数等详细信息
- **标题截断**：自动截断长标题保持可读性

### 2. PageRank对比图（PageRank Comparison）
- **图表类型**：分组柱状图
- **对比维度**：标准PageRank vs 时间PageRank
- **Top 10论文**：展示两种算法的差异
- **颜色区分**：蓝色（标准）、红色（时间）

### 3. 混合分析图（Hybrid Analysis）
- **图表类型**：散点图
- **X轴**：发表年份
- **Y轴**：引用数
- **点大小**：混合分数
- **颜色**：标准PageRank分数

## 应用场景

- **文献推荐**：基于网络影响力的高质量论文推荐
- **趋势分析**：识别新兴研究趋势和热点论文
- **影响力评估**：综合评估论文的学术影响力
- **AI for Science**：为智能文献搜索提供算法支持
- **学术网络研究**：分析引用网络的结构特征

## 性能优化

### 1. 算法优化
- **NetworkX集成**：使用高度优化的PageRank实现
- **图结构优化**：仅包含内部论文节点
- **边属性存储**：避免重复计算引用信息
- **备用方案**：手动PageRank实现作为后备

### 2. 内存管理
- **数据结构优化**：使用字典存储论文信息
- **惰性计算**：按需计算各种PageRank分数
- **错误处理**：完善的异常处理和日志记录

### 3. 计算效率
- **并行友好**：各PageRank计算相互独立
- **缓存机制**：避免重复的图构建操作
- **阈值控制**：合理的收敛阈值和迭代次数

## 注意事项

- **数据依赖**：需要先运行数据清洗步骤生成输入文件
- **网络连通性**：确保引用网络有足够的连接性
- **时间范围**：建议避免包含太新的论文（引用数据不完整）
- **权重调整**：根据具体需求调整混合评分的权重配置
- **可视化依赖**：图表生成功能需要安装plotly库
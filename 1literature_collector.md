# 学术文献收集器 (Academic Literature Collector)

## 项目概述

这是一个用于从arXiv收集学术论文并构建引用网络的工具。它能够：

- 从arXiv搜索指定领域的论文
- 获取论文的引用数据（参考文献和施引文献）
- 构建完整的学术引用网络
- 支持自定义年份分布和影响力评估
- **集成质量控制**：确保最终输出数量与用户指定数量一致

## 核心功能

### 1. 论文收集
- **领域搜索**：按关键词搜索arXiv论文
- **年份范围**：自定义收集论文的年份区间
- **数量控制**：限制收集论文总数（1-500篇）

### 2. 引用网络构建
- **参考文献**：获取每篇论文引用了哪些文献
- **施引文献**：获取哪些文献引用了该论文
- **网络分析**：构建完整的引用关系网络

### 3. 智能筛选与质量保证
- **影响力评估**：基于引用数、影响力引用数计算论文影响力
- **质量过滤**：可选择只保留Semantic Scholar索引的高质量论文
- **自定义权重**：通过配置文件调整影响力计算参数
- **集成质量控制**：**在收集阶段预测清洗影响，确保最终数量精确**

## 主要参数

### 用户交互参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `domain` | 研究领域关键词 | "large language model" |
| `max_papers` | 最大论文数量 | 100 |
| `start_year` | 开始年份 | 当前年-3 |
| `end_year` | 结束年份 | 当前年-1 |
| `filter_high_impact` | 是否只保留高质量论文 | True |
| `include_citations` | 是否包含施引文献分析 | True |

### 配置文件参数
通过 `config.py` 文件可配置的内部参数：

#### 论文收集参数
- `INITIAL_FETCH_MULTIPLIER`：初始收集倍数（默认2倍）
- `ARXIV_CLIENT_PAGE_SIZE`：arXiv API页面大小（默认100）
- `ARXIV_CLIENT_DELAY`：arXiv API请求延迟（默认3秒）

#### 影响力计算权重
- `INFLUENTIAL_CITATION_WEIGHT`：影响力引用权重（默认2.0）
- `IN_S2_BONUS_SCORE`：Semantic Scholar索引奖励分（默认100）
- `CITING_PAPERS_WEIGHT`：施引文献权重（默认0.5）

#### 年份分布策略
- `USE_CUSTOM_YEAR_DISTRIBUTION`：是否使用自定义年份分布
- `CUSTOM_YEAR_DISTRIBUTION`：自定义年份权重分布
- `EXPONENTIAL_DECAY_FACTOR`：指数衰减因子（用于自动分布）

## 使用方法

### 1. 环境准备
```bash
pip install arxiv requests pandas tqdm python-dotenv
```

### 2. API密钥配置（可选）
创建 `.env` 文件：
```
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
```

### 3. 运行程序
```bash
python literature_collector.py
```

按提示输入参数，程序将自动收集论文并生成结果文件。

## 输出文件

- `papers_*.csv`：收集的论文详细信息
- `reference_edges_*.csv`：引用关系（论文→参考文献）
- `citation_edges_*.csv`：施引关系（引用者→被引用者）

## 代码结构

```
literature_collector.py
├── get_user_input()                    # 获取用户输入参数
├── fetch_papers_by_domain()            # 收集论文（支持年份分布）
├── enrich_with_semantic_scholar()      # 获取引用数据
├── build_citation_network()            # 构建引用网络
├── integrated_quality_control_and_recovery()  # 集成质量控制与数量保证
└── main()                              # 主函数
```

## 特色功能

### 1. 自定义年份分布
不再是平均分配各年份论文，而是根据配置文件中的权重分布收集论文，可以：
- 重点收集近期论文（如40%当前年，30%前一年）
- 按指数衰减分布收集
- 自定义任意年份权重

### 2. 智能影响力评估
综合考虑多个指标计算论文影响力：
- 普通引用数
- 影响力引用数（更重的引用）
- Semantic Scholar索引状态
- 施引文献数量

### 3. 完整引用网络
同时构建：
- **引用网络**：论文→其参考文献
- **施引网络**：引用者→被引用者
- 支持完整的网络分析和可视化

### 4. 集成质量控制与数量保证
**核心改进**：在收集阶段就考虑后续清洗的影响
- **预测性清洗**：模拟数据清洗过程，预测哪些论文会被移除
- **补偿性选择**：根据预测结果，提前选择更多论文来补偿可能的移除
- **精确数量保证**：确保最终输出的论文数量与用户指定的数量完全一致
- **避免后续清洗导致的数量损失**：即使经过数据清洗，也能保持目标数量

## 应用场景

- **文献综述**：系统性收集某一领域的核心论文
- **网络分析**：构建学术引用网络进行PageRank等分析
- **影响力研究**：分析论文的学术影响力传播

## 注意事项

- 新论文可能在Semantic Scholar中尚未索引（建议避免收集最近6个月的论文）
- API调用有速率限制，无密钥时限制为1请求/秒
- 网络不稳定时可能需要调整重试参数
- **数量保证机制**：即使启用高质量筛选，也会确保最终输出精确的论文数量
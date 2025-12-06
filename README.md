# 学术引用网络分析工具包 (Academic Citation Network Analysis Toolkit)

## 项目概述

这是一个完整的学术文献分析工具包，集成了论文收集、数据清洗、网络可视化、PageRank分析和交互式仪表板功能。项目使用arXiv和Semantic Scholar API构建学术引用网络，通过Leiden社区检测和PageRank算法识别高影响力论文，并提供基于LLM的智能分析功能。

## 核心特性

### 📊 网络分析功能
- **多维度PageRank**：标准PageRank、时间加权PageRank、质量加权PageRank
- **社区检测**：使用Leiden算法进行学术社区发现
- **引用网络**：构建完整的论文-参考文献引用网络
- **影响力评估**：综合多种指标的论文推荐系统

### 🎯 智能推荐系统
- **混合评分**：综合PageRank、引用数、时间因素的加权评分
- **多维度排序**：经典论文、新兴趋势、质量导向等不同推荐策略
- **时间感知**：考虑引用时间的指数衰减权重
- **质量感知**：基于引用者质量的权重分配

### 🌐 可视化分析
- **多种布局**：Kamada-Kawai、社区基础、多部分、改进Spring布局
- **交互式图表**：基于Pyvis和Plotly的交互式网络图
- **社区着色**：使用Leiden算法检测的社区进行颜色编码
- **动态过滤**：支持按年份、引用数等条件筛选论文

## 系统架构

```
学术引用网络分析工具包
├── 1literature_collector.py   # 论文收集器
├── 2data_processor.py        # 数据清洗与智能恢复
├── 3visual.py               # 网络可视化
├── 4pagerank_analyzer.py     # PageRank分析
├── 5app.py                  # Streamlit仪表板
├── config.py                # 配置管理
├── utils/                   # 工具模块
│   ├── logger.py            # 日志系统
│   ├── data_loader.py       # 数据加载器
│   ├── pagerank_tracker.py  # PageRank历史追踪
│   ├── niche_detector.py       # 未被充分探索领域检测
│   └── topic_embedder.py    # 主题嵌入与分类法对比
└── .env.example            # 环境变量示例
```

## 快速开始

### 1. 环境配置
```bash
# 克隆项目
git clone <repository-url>
cd academic-network-analysis

# 安装依赖
pip install -r requirements.txt

# 配置API密钥（可选）
cp .env.example .env
# 编辑 .env 文件添加你的API密钥
```

### 2. 运行分析流程
```bash
# 步骤1: 收集论文数据
python 1literature_collector.py

# 步骤2: 清洗数据
python 2data_processor.py

# 步骤3: 生成可视化
python 3visual.py

# 步骤4: 运行PageRank分析
python 4pagerank_analyzer.py

# 步骤5: 启动Web仪表板
streamlit run 5app.py
```

## 详细功能说明

### 1. 论文收集器 (`1literature_collector.py`)
```bash
# 交互式收集
python 1literature_collector.py
```

**主要功能：**
- 按领域关键词搜索arXiv论文
- 获取Semantic Scholar引用数据
- 构建引用网络（参考文献+施引文献）
- 集成质量控制确保目标数量

**配置参数：**
- `INITIAL_FETCH_MULTIPLIER`: 初始收集倍数（默认2倍）
- `ARXIV_CLIENT_DELAY`: arXiv API请求延迟（默认3秒）
- `INFLUENTIAL_CITATION_WEIGHT`: 影响力引用权重（默认2.0）
- `EXPONENTIAL_DECAY_FACTOR`: 年份指数衰减因子（默认0.7）

### 2. 数据清洗器 (`2data_processor.py`)
```bash
# 自动发现并清洗最新数据
python 2data_processor.py

# 指定目标数量
python 2data_processor.py --target-count 150

# 指定具体文件
python 2data_processor.py papers_llm.csv reference_edges_llm.csv
```

**主要功能：**
- 数据完整性验证和清洗
- 智能论文恢复机制
- 详细移除原因追踪
- 多格式边文件支持

### 3. 网络可视化 (`3visual.py`)
```bash
# 使用默认设置
python 3visual.py

# 跳过大图布局计算
python 3visual.py --skip-kamada-kawai
```

**主要功能：**
- 四种布局算法（Kamada-Kawai、社区基础、多部分、Spring）
- Leiden社区检测
- 静态和交互式图表
- PageRank可视化分析

### 4. PageRank分析 (`4pagerank_analyzer.py`)
```bash
# 运行PageRank分析
python 4pagerank_analyzer.py
```

**主要功能：**
- 标准PageRank计算
- 时间加权PageRank
- 质量加权PageRank
- 混合推荐系统
- PageRank历史追踪
- 上升论文识别（基于历史或预测）
- 交互式可视化图表

### 5. Web仪表板 (`5app.py`)
```bash
# 启动Web界面
streamlit run 5app.py
```

**主要功能：**
- 六标签页统一界面
- 网络可视化展示（支持延迟加载）
- 社区分析统计
- 智能论文推荐
- LLM智能分析（支持DashScope、OpenAI、OpenRouter）
- 上升论文识别
- 主题分类法对比
- 性能优化（HTML/CSV缓存、延迟加载）

## 配置文件详解 (`config.py`)

### 论文收集参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `MAX_PAPERS_DEFAULT` | 默认收集论文数量 | 100 |
| `INITIAL_FETCH_MULTIPLIER` | 初始收集倍数 | 2 |
| `USE_CUSTOM_YEAR_DISTRIBUTION` | 是否使用自定义年份分布 | True |
| `CUSTOM_YEAR_DISTRIBUTION` | 自定义年份权重分布 | {0:0.3, -1:0.3, -2:0.25, -3:0.15} |

### 网络分析参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `PAGERANK_ALPHA` | PageRank阻尼因子 | 0.85 |
| `TEMPORAL_DECAY_LAMBDA` | 时间衰减系数 | 0.6 |
| `INFLUENTIAL_CITATION_WEIGHT` | 影响力引用权重 | 2.0 |
| `LEIDEN_SEED` | Leiden社区检测随机种子 | 42 |

### API配置参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API密钥 | 从环境变量读取 |
| `OPENROUTER_API_KEY` | OpenRouter API密钥 | 从环境变量读取 |
| `OPENROUTER_MODEL` | 使用的LLM模型 | "tngtech/deepseek-r1t-chimera:free" |
| `DASHSCOPE_API_KEY` | DashScope (百炼) API密钥 | 从环境变量读取 |
| `DASHSCOPE_MODEL` | DashScope模型 | "qwen-plus" |
| `USE_DASHSCOPE` | 是否优先使用DashScope | False（默认使用OpenAI） |
| `OPENAI_API_KEY` | OpenAI API密钥（ChatAnywhere） | 从环境变量读取 |
| `OPENAI_BASE_URL` | OpenAI API基础URL | "https://api.chatanywhere.tech/v1" |
| `OPENAI_MODEL` | OpenAI模型 | "gpt-3.5-turbo" |
| `USE_OPENAI` | 是否使用OpenAI | True |

### 高级分析参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `RISING_PAGERANK_MIN_GROWTH_RATE` | 上升论文最小增长率 | 0.1 (10%) |
| `RISING_PAGERANK_MIN_HISTORY_POINTS` | 最小历史点数 | 2 |
| `NICHE_MIN_PAGERANK` | 未被充分探索领域最小PageRank | 0.01 |
| `NICHE_MAX_PAPER_COUNT` | 未被充分探索领域最大论文数 | 20 |

## 输出文件说明

### 数据文件
- `papers_cleaned.csv`: 清洗后的论文数据
- `edges_cleaned.csv`: 清洗后的引用网络数据
- `node_leiden_comm.csv`: 节点社区归属数据
- `top_papers_pagerank.csv`: PageRank分析结果
- `pagerank_history.csv`: PageRank历史记录
- `rising_pagerank_papers.csv`: 上升论文列表
- `taxonomy_benchmark.csv`: 主题分类法对比结果

### 可视化文件
- `fig/full_network_*.png`: 静态网络图（四种布局）
- `fig/full_interactive_leiden_only.html`: 交互式网络图
- `fig/temporal_recommendations.html`: 时间PageRank图表
- `fig/pagerank_comparison.html`: PageRank对比图表

### 临时文件
- `papers_removed.csv`: 被移除的论文记录
- `paper_label_mapping.csv`: 论文标签映射

## API配置

### Semantic Scholar API
1. 访问 [Semantic Scholar API](https://www.semanticscholar.org/product/api) 申请API密钥
2. 在 `.env` 文件中设置：
```
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
```

### LLM API配置（用于LLM分析）

**方案1：DashScope (百炼) API（推荐）**
1. 访问 [阿里云百炼](https://dashscope.aliyun.com/) 注册账户
2. 在 `.env` 文件中设置：
```
DASHSCOPE_API_KEY=your_dashscope_key_here
```

**方案2：OpenAI API（ChatAnywhere，推荐）**
1. 访问 [ChatAnywhere](https://chatanywhere.tech/) 获取API密钥
2. 在 `.env` 文件中设置：
```
OPENAI_API_KEY=your_openai_key_here
OPENAI_BASE_URL=https://api.chatanywhere.tech/v1
OPENAI_MODEL=gpt-3.5-turbo
```

**方案3：OpenRouter API（备选）**
1. 访问 [OpenRouter](https://openrouter.ai) 注册账户
2. 在 `.env` 文件中设置：
```
OPENROUTER_API_KEY=your_openrouter_key_here
```

**注意**：API优先级为 DashScope > OpenAI > OpenRouter。默认使用 OpenAI (ChatAnywhere)。

## 环境要求

### Python版本
- Python 3.8+
- 推荐使用虚拟环境

### 依赖包
```bash
# 核心依赖
pip install pandas networkx matplotlib seaborn
pip install plotly pyvis streamlit requests
pip install arxiv igraph leidenalg python-dotenv

# 可选依赖（用于LLM分析）
pip install openai>=1.0.0  # 如果使用OpenAI模型（ChatAnywhere）
```

## 使用场景

### 🎓 学术研究
- **文献综述**：快速发现领域内核心论文和新兴趋势
- **影响力分析**：识别高影响力论文和研究方向
- **社区检测**：分析学术研究的社区结构

### 🔬 AI for Science
- **智能推荐**：为研究人员提供个性化论文推荐
- **网络分析**：分析学术引用网络的结构特征
- **趋势预测**：基于时间PageRank预测研究趋势
- **上升论文识别**：识别潜在的突破性研究
- **跨学科发现**：发现连接不同领域的桥接论文
- **研究机会**：识别未被充分探索但高潜力的研究领域

### 📚 教学演示
- **可视化展示**：课堂展示引用网络的结构特征
- **互动分析**：学生可交互探索学术网络
- **案例研究**：分析特定领域的学术发展

## 性能优化

### 大图处理
- 自动跳过Kamada-Kawai布局（>5000节点）
- 支持多种布局算法选择
- 内存优化的数据结构

### API调用优化
- 智能重试机制
- 速率限制控制
- 缓存机制

### 计算优化
- 并行处理支持
- 算法复杂度优化
- 结果缓存机制

## 故障排除

### 常见问题
1. **API限制**：确保配置了Semantic Scholar API密钥
2. **文件依赖**：按顺序运行分析流程
3. **内存不足**：使用 `--skip-kamada-kawai` 参数处理大图
4. **网络错误**：检查网络连接和API密钥配置

### 调试信息
- 查看 `logs/` 目录下的日志文件
- 检查各阶段的输出文件是否存在
- 验证API密钥是否正确配置

## 贡献指南

### 开发环境
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 代码规范
- 遵循PEP 8代码风格
- 使用类型提示
- 编写单元测试
- 更新文档

## 文档说明

每个主要脚本都有对应的详细文档：

- [1literature_collector.md](1literature_collector.md) - 论文收集器详细说明
- [2data_processor.md](2data_processor.md) - 数据清洗模块详细说明
- [3visual.md](3visual.md) - 网络可视化模块详细说明
- [4paperrank_analyzer.md](4paperrank_analyzer.md) - PageRank分析模块详细说明
- [5app.md](5app.md) - Streamlit仪表板详细说明

## 许可证

[MIT License](LICENSE)

## 致谢

- [arXiv API](https://arxiv.org/help/api/index) - 论文数据源
- [Semantic Scholar API](https://www.semanticscholar.org/product/api) - 引用数据源
- [NetworkX](https://networkx.org/) - 网络分析库
- [Leiden Algorithm](https://leidenalg.readthedocs.io/) - 社区检测算法
- [Streamlit](https://streamlit.io/) - Web应用框架
# Streamlit 网络分析仪表板 (Streamlit Citation Network Dashboard)

## 项目概述

这是一个交互式学术引用网络分析仪表板，集成了网络可视化、社区检测、论文推荐和LLM分析功能。它为研究人员提供了一个统一的平台，用于探索和分析学术文献的引用结构与影响力。

## 核心功能

### 1. 网络可视化
- **静态布局**：支持四种网络布局算法（Kamada-Kawai、社区基础、多部分、改进Spring）
- **交互式图谱**：基于Pyvis的可交互网络图，支持缩放、拖拽和悬停查看
- **节点区分**：论文节点（正方形）与参考文献节点（圆形）清晰区分
- **社区着色**：使用Leiden算法检测的社区进行颜色编码

### 2. 社区分析
- **Leiden社区统计**：显示各社区中论文与参考文献的数量分布
- **标签映射**：提供论文节点的简化标签与原始arXiv ID的对应关系
- **社区规模**：展示每个社区的总论文数量

### 3. 智能论文推荐
- **多维度评分**：标准PageRank、时间加权PageRank、质量加权PageRank
- **混合推荐系统**：综合五种指标的加权评分
- **动态排序**：支持按不同评分标准排序
- **高级筛选**：按年份范围、引用数量等条件筛选论文
- **详情查看**：点击搜索查看单篇论文的详细评分和排名信息

### 4. LLM智能分析
- **摘要生成**：自动生成论文摘要的简明摘要
- **引用上下文分析**：分析论文被哪些文献引用，引用了哪些文献
- **情感分析**：评估论文摘要的情感倾向
- **多API支持**：支持DashScope、OpenAI (ChatAnywhere)、OpenRouter三种API

### 5. 上升论文识别
- **历史追踪**：基于PageRank历史数据识别上升趋势
- **预测分析**：使用当前指标预测潜在上升论文
- **早期阶段识别**：识别低引用但高潜力的论文
- **增长评分**：计算论文的PageRank增长率

### 6. 主题分类法对比
- **社区主题生成**：使用LLM为每个社区生成主题描述
- **QS分类法匹配**：与QS学科分类法进行自动匹配
- **相似度评分**：计算检测主题与标准分类法的相似度

## 主要特性

### 1. 数据集成
- 自动加载所有分析阶段的输出文件
- 数据缓存机制（1小时缓存）
- HTML/CSV文件缓存优化
- 完善的错误处理和用户提示
- 环境变量验证

### 2. 用户体验
- **多标签页设计**：清晰的功能分区
- **响应式布局**：适配不同屏幕尺寸
- **交互式控件**：滑块、下拉菜单、搜索框等
- **即时反馈**：操作后立即更新结果

### 3. 可视化增强
- **HTML嵌入**：直接嵌入Plotly生成的交互式图表（支持缓存）
- **延迟加载**：大型交互式网络图支持按需加载
- **数据表格**：格式化展示Top论文列表
- **指标卡片**：关键数据的可视化指标展示
- **趋势分析**：年度论文影响力趋势图

### 4. 性能优化
- **HTML文件缓存**：所有HTML文件内容缓存1小时
- **CSV文件缓存**：CSV文件读取结果缓存
- **延迟加载**：交互式网络图默认不加载，用户需要时再加载
- **加载提示**：显示加载进度和状态

## 使用方法

### 1. 环境准备
```bash
pip install streamlit pandas networkx plotly requests
```

### 2. 运行仪表板
```bash
streamlit run 5app.py
```

### 3. 工作流程
1. 运行 `literature_collector.py` 收集论文
2. 运行 `2data_processor.py` 清洗数据
3. 运行 `3visual.py` 生成网络可视化
4. 运行 `4pagerank.py` 生成推荐结果
5. 运行 `5app.py` 启动Web仪表板

## 功能模块详解

### 1. 网络可视化标签页 (Tab 1)
| 功能 | 说明 |
|------|------|
| 静态布局选择 | 选择四种布局算法查看网络结构 |
| 图像显示 | 显示对应的PNG静态图 |
| 交互式图谱 | 嵌入HTML格式的可交互网络图（支持延迟加载） |
| 延迟加载选项 | 复选框控制是否加载大型交互式网络图 |
| 生成提示 | 指导用户运行可视化脚本 |

### 2. 社区分析标签页 (Tab 2)
| 功能 | 说明 |
|------|------|
| 社区统计表 | 显示各社区论文与参考文献的数量分布 |
| 标签映射表 | 提供论文简化标签（P0, P1...）与arXiv ID的对应关系 |
| 数据导出 | 可直接复制表格数据用于进一步分析 |

### 3. 论文推荐标签页 (Tab 3)
#### 3.1 推荐概览
- **混合推荐**：基于综合评分的Top论文
- **高引用论文**：引用数最多的论文
- **最新论文**：最近发表的高影响力论文

#### 3.2 多维度推荐列表
| 推荐类型 | 说明 | 关键指标 |
|----------|------|----------|
| 经典必读 | 网络影响力最大的论文 | 标准PageRank |
| 新兴热点 | 近期被大量引用的论文 | 时间加权PageRank |
| 质量导向 | 被高质量论文引用的论文 | 质量加权PageRank |

#### 3.3 年度趋势分析
- 展示每年的平均PageRank分数、引用数和论文数量
- 识别学术影响力的时间演变趋势

#### 3.4 交互式图表
- **时间推荐图**：Top 20新兴论文的可视化
- **PageRank对比图**：标准与时间PageRank的对比
- **混合分析图**：年份vs引用数vs混合评分的散点图

#### 3.5 高级搜索与筛选
- **年份范围筛选**：滑块选择发表年份区间
- **引用数量过滤**：设置最低引用数
- **多维度排序**：按五种不同评分标准排序
- **结果展示**：显示前20篇匹配论文

#### 3.6 论文详情查看
- 按标题或arXiv ID搜索特定论文
- 显示详细评分、排名和引用信息
- 多维度指标卡片展示

### 4. LLM分析标签页 (Tab 4)
| 功能 | 说明 |
|------|------|
| 任务选择 | 摘要生成、引用上下文分析、情感分析 |
| arXiv ID输入 | 输入论文ID进行分析 |
| API密钥检查 | 自动检测API密钥配置（DashScope/OpenAI/OpenRouter） |
| API优先级 | DashScope > OpenAI > OpenRouter |
| 智能响应 | 返回大语言模型的分析结果 |
| 元数据展示 | 显示论文的基本信息 |

### 5. 上升论文标签页 (Tab 5)
| 功能 | 说明 |
|------|------|
| 上升论文列表 | 显示PageRank上升的论文 |
| 增长率筛选 | 按最小增长率筛选 |
| 早期阶段过滤 | 筛选低引用但高潜力的论文 |
| 历史追踪 | 基于历史数据识别上升趋势 |
| 预测分析 | 使用当前指标预测潜在上升论文 |
| Top论文详情 | 显示上升最快的论文详细信息 |

### 6. 主题分类法对比标签页 (Tab 6)
| 功能 | 说明 |
|------|------|
| 分类法对比表 | 显示社区主题与QS分类法的匹配结果 |
| 相似度评分 | 计算每个社区主题与标准分类法的相似度 |
| 统计信息 | 显示平均相似度、匹配率等指标 |
| 数据生成提示 | 指导用户运行主题分析脚本 |

## 配置文件参数

通过 `config.py` 文件可配置的内部参数：

### LLM分析参数
- `DASHSCOPE_API_KEY`：DashScope (百炼) API密钥（优先级1）
- `DASHSCOPE_MODEL`：DashScope模型名称（默认：qwen-plus）
- `DASHSCOPE_URL`：DashScope API端点
- `USE_DASHSCOPE`：是否使用DashScope（默认False）
- `DASHSCOPE_RATE_LIMIT`：DashScope请求速率限制
- `OPENAI_API_KEY`：OpenAI API密钥（ChatAnywhere，优先级2，默认使用）
- `OPENAI_BASE_URL`：OpenAI API基础URL（默认：https://api.chatanywhere.tech/v1）
- `OPENAI_MODEL`：OpenAI模型（默认：gpt-3.5-turbo）
- `USE_OPENAI`：是否使用OpenAI（默认True）
- `OPENAI_RATE_LIMIT`：OpenAI请求速率限制
- `OPENROUTER_API_KEY`：OpenRouter API密钥（优先级3，备选）
- `OPENROUTER_MODEL`：使用的LLM模型名称
- `OPENROUTER_URL`：OpenRouter API端点
- `OPENROUTER_RATE_LIMIT`：OpenRouter请求速率限制

### 文件路径参数
- `FIG_DIR`：可视化图表输出目录
- `PAGERANK_RESULTS`：PageRank结果文件路径
- `NODE_COMM`：节点社区归属文件路径
- `PAPERS_CLEANED`：清洗后论文文件路径
- `EDGES_CLEANED`：清洗后边文件路径

## 输出文件依赖

| 功能 | 所需文件 | 生成脚本 |
|------|----------|----------|
| 静态网络图 | `full_network_*.png` | `3visual.py` |
| 交互式网络图 | `full_interactive_leiden_only.html` | `3visual.py` |
| 社区统计 | `node_leiden_comm.csv` | `3visual.py` |
| 标签映射 | `paper_label_mapping.csv` | `3visual.py` |
| PageRank结果 | `top_papers_pagerank.csv` | `4pagerank_analyzer.py` |
| 上升论文 | `rising_pagerank_papers.csv` | `4pagerank_analyzer.py` |
| 主题对比 | `taxonomy_benchmark.csv` | `utils/topic_embedder.py` |

## 应用场景

- **文献综述**：快速发现领域内核心论文和新兴趋势
- **研究选题**：识别高影响力和高增长潜力的研究方向
- **学术推荐**：为研究人员提供个性化论文推荐
- **教学演示**：课堂展示引用网络的结构特征
- **AI for Science**：为智能科研助手提供可视化界面

## 注意事项

- **数据依赖**：必须按顺序运行前置分析脚本才能正常显示
- **API密钥**：LLM功能需要配置API密钥（推荐OpenAI ChatAnywhere，或DashScope/OpenRouter）
- **API优先级**：DashScope > OpenAI > OpenRouter
- **网络连接**：LLM分析需要互联网连接
- **缓存机制**：数据、HTML、CSV文件缓存1小时，修改文件后需等待或重启应用
- **性能优化**：
  - 交互式网络图支持延迟加载（默认不加载，用户需要时勾选）
  - 所有HTML和CSV文件使用缓存机制
  - 首次加载可能较慢，后续访问会明显加快
- **文件命名**：确保所有文件使用标准命名格式

## 系统架构

```
5app.py
├── load_all_data()                    # 统一数据加载与缓存
├── load_html_file()                   # HTML文件缓存加载
├── load_csv_file()                    # CSV文件缓存加载
├── Tab 1: Network Visualization       # 网络可视化
│   └── 延迟加载交互式网络图
├── Tab 2: Community Analysis          # 社区分析
├── Tab 3: Paper Recommendations       # 论文推荐系统
│   ├── Recommendation Overview        # 推荐概览
│   ├── Multi-dimensional Rankings     # 多维度排名
│   ├── Yearly Trends                  # 年度趋势
│   ├── Interactive Visualizations     # 交互式图表（缓存）
│   ├── Advanced Filtering             # 高级筛选
│   └── Paper Details                  # 论文详情
├── Tab 4: LLM Analysis                # LLM智能分析
│   ├── API Configuration              # API密钥配置（DashScope/OpenAI/OpenRouter）
│   ├── Helper Functions               # 辅助函数
│   └── User Interface                 # 用户界面
├── Tab 5: Rising Papers               # 上升论文识别
│   ├── Historical Tracking            # 历史追踪
│   ├── Prediction Analysis            # 预测分析
│   └── Early Stage Detection          # 早期阶段识别
└── Tab 6: Topic Benchmarking          # 主题分类法对比
    ├── Community Topics               # 社区主题
    └── QS Taxonomy Matching           # QS分类法匹配
```
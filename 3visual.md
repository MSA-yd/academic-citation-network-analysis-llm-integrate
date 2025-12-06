# 网络可视化模块 (Network Visualization Module)

## 项目概述

这是一个用于生成学术引用网络可视化图表的完整模块，支持Leiden社区检测和PageRank分析。它能够：

- **全网络可视化**：主节点为论文，小节点为参考文献
- **社区检测**：使用Leiden算法进行社区发现
- **多种布局**：支持多种图形布局算法
- **交互式图表**：生成可交互的HTML网络图
- **PageRank集成**：支持PageRank结果的可视化分析

## 核心功能

### 1. 网络构建
- **论文节点**：使用正方形表示，较大尺寸
- **参考文献节点**：使用圆形表示，较小尺寸
- **引用边**：连接论文与其参考文献
- **节点类型标记**：区分论文节点和参考文献节点

### 2. 社区检测
- **Leiden算法**：使用Leiden算法进行社区发现
- **模块化分区**：基于ModularityVertexPartition
- **种子控制**：可配置随机种子确保结果可重现
- **社区统计**：生成详细的社区分布统计

### 3. 多种布局算法
- **Kamada-Kawai布局**：基于图距离的布局（大图可跳过）
- **社区基础布局**：基于社区信息的分层布局
- **多部分布局**：按节点类型分层的布局
- **改进Spring布局**：优化参数的力导向布局

### 4. 可视化输出
- **静态图**：PNG格式的高质量静态图表
- **交互式图**：HTML格式的可交互网络图
- **标签映射**：生成论文显示标签的映射表
- **PageRank分析**：PageRank结果的散点图和对比图

## 主要参数

### 命令行参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--skip-kamada-kawai` | 跳过Kamada-Kawai布局 | False |
| `--no-auto-skip` | 禁用大图自动跳过 | False |

### 配置文件参数
通过 `config.py` 文件可配置的内部参数：

#### 布局参数
- `LEIDEN_SEED`：Leiden算法随机种子
- `SKIP_KAMADA_KAWAI_AUTO_THRESHOLD`：自动跳过Kamada-Kawai的节点数阈值
- `FIGURE_DPI`：静态图DPI设置

#### 可视化参数
- `INTERACTIVE_GRAPH_HEIGHT`：交互式图高度
- `FIG_DIR`：输出图表目录

## 使用方法

### 1. 环境准备
```bash
pip install networkx igraph leidenalg matplotlib pyvis plotly pandas numpy
```

### 2. 基本使用
```bash
# 使用默认设置（大图自动跳过Kamada-Kawai）
python 3visual.py

# 强制跳过Kamada-Kawai布局（推荐用于大图）
python 3visual.py --skip-kamada-kawai

# 强制计算Kamada-Kawai布局（即使对大图）
python 3visual.py --no-auto-skip

# 组合使用
python 3visual.py --skip-kamada-kawai --no-auto-skip
```

## 输出文件

### 图表文件
- `full_network_kamada_kawai.png`：Kamada-Kawai布局静态图
- `full_network_community_based.png`：社区基础布局静态图
- `full_network_multipart.png`：多部分布局静态图
- `full_network_spring_improved.png`：改进Spring布局静态图
- `full_interactive_leiden_only.html`：交互式网络图

### 数据文件
- `node_comm.csv`：节点社区归属数据
- `paper_label_mapping.csv`：论文显示标签映射

### PageRank可视化文件
- `temporal_recommendations.html`：时间PageRank散点图
- `pagerank_comparison.html`：PageRank对比图

## 代码结构

```
3visual.py
├── parse_arguments()                     # 解析命令行参数
├── load_data_files()                     # 加载数据文件
├── build_graph()                         # 构建网络图
├── leiden_community_detection()          # Leiden社区检测
├── export_community_table()              # 导出社区数据
├── multiple_layout_algorithms()          # 多种布局算法
│   ├── kamada_kawai_layout()             # Kamada-Kawai布局
│   ├── community_based_layout()          # 社区基础布局
│   ├── multipart_layout()                # 多部分布局
│   └── spring_layout()                   # Spring布局
├── static_graph_generation()             # 静态图生成
├── interactive_graph_generation()        # 交互式图生成
├── save_label_mapping()                  # 保存标签映射
├── community_statistics()                # 社区统计
└── pagerank_visualization()              # PageRank可视化
```

## 布局算法详解

### 1. Kamada-Kawai布局
- **特点**：基于图距离，保持节点间的真实距离关系
- **适用**：中小规模网络（<5000节点）
- **自动跳过**：超过阈值时自动跳过以避免长时间计算

### 2. 社区基础布局
- **特点**：基于社区信息组织节点位置
- **优势**：突出社区结构，便于识别社区间关系
- **实现**：每个社区分配圆形区域，内部使用Spring布局

### 3. 多部分布局
- **特点**：按节点类型分层排列
- **结构**：论文节点在上层，参考文献节点在下层
- **连接**：参考文献靠近其引用的论文节点

### 4. 改进Spring布局
- **参数优化**：调整k值和迭代次数
- **规模适应**：支持大规模网络的快速布局
- **质量保证**：保持良好的节点分布

## 可视化特性

### 1. 节点样式
- **论文节点**：正方形，较大尺寸(400)，黑色边框，社区颜色
- **参考文献节点**：圆形，较小尺寸(80)，社区颜色，透明度较高

### 2. 颜色编码
- **社区颜色**：使用tab20配色方案区分不同社区
- **节点类型**：形状区分（正方形vs圆形）
- **边线颜色**：灰色半透明边线

### 3. 标签显示
- **简化标签**：论文显示为P0, P1, P2...格式
- **完整信息**：交互式图中显示完整节点信息
- **映射文件**：保存arxiv_id到显示标签的映射

## PageRank集成

### 1. 时间PageRank分析
- **散点图**：年份vs时间PageRank分数，点大小=标准PageRank
- **颜色编码**：基于时间PageRank排名的颜色渐变
- **悬停信息**：显示论文标题和排名信息

### 2. 对比分析
- **柱状图**：标准PageRank vs 时间PageRank的排名对比
- **双色显示**：不同颜色区分两种算法的Top10
- **标题截断**：长标题自动截断以保持可读性

## 性能优化

### 1. 大图处理
- **自动阈值**：超过5000节点自动跳过Kamada-Kawai
- **布局选择**：推荐使用社区基础或Spring布局
- **内存管理**：优化数据结构减少内存占用

### 2. 计算优化
- **种子固定**：确保结果可重现
- **参数调优**：优化布局算法参数
- **并行处理**：支持部分操作的并行计算

## 应用场景

- **网络分析**：可视化学术引用网络的社区结构
- **文献推荐**：基于PageRank的论文推荐系统
- **影响力研究**：分析论文在引用网络中的影响力
- **AI for Science**：为智能代理提供网络可视化支持

## 注意事项

- **大图性能**：超过5000节点时建议使用`--skip-kamada-kawai`参数
- **内存需求**：大规模网络可视化需要较多内存
- **依赖安装**：PageRank可视化需要额外安装plotly
- **文件依赖**：确保已运行数据清洗步骤生成必要的输入文件
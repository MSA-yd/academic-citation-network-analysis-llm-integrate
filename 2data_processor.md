# 数据清洗模块 (Data Cleaning Module)

## 项目概述

这是一个用于清洗学术论文和引用网络数据的智能模块，具备自动恢复功能。它能够：

- **数据清洗**：移除无效论文和边数据，去重并验证数据完整性
- **智能恢复**：自动恢复论文以达到目标数量
- **移除追踪**：详细记录每篇被移除论文的原因（英文输出）
- **多格式支持**：同时处理参考文献和施引文献网络

## 核心功能

### 1. 论文数据清洗
- **完整性检查**：移除缺失 `arxiv_id` 或 `title` 的论文
- **质量过滤**：移除 `in_s2 = False` 的论文（非 Semantic Scholar 索引）
- **引用验证**：移除引用字段为空（`[]`, `""`, `"nan"`）的论文
- **去重处理**：保留相同 `arxiv_id` 的第一篇论文

### 2. 边数据清洗
- **空值移除**：删除包含空值的边记录
- **目标验证**：确保 `target` 字段非空
- **网络合并**：自动合并参考文献和施引文献网络

### 3. 智能恢复机制
- **优先级恢复**：优先恢复 `in_s2 = False` 但有引用数据的论文
- **影响力排序**：基于引用数和影响力引用数排序恢复
- **时间优先**：优先恢复较新的论文
- **降级策略**：必要时恢复其他类型的移除论文

### 4. 移除原因追踪
- **详细记录**：记录每篇被移除论文的具体原因
- **统计分析**：提供移除原因的详细统计
- **英文输出**：所有输出信息使用英文

## 主要参数

### 命令行参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `paper_file` | 输入论文CSV文件路径 | 自动发现 |
| `edge_file` | 输入边CSV文件路径 | 自动发现 |
| `--target-count` | 目标论文数量 | 估计值 |
| `--output-paper` | 输出清洗后论文文件 | `papers_cleaned.csv` |
| `--output-edge` | 输出清洗后边文件 | `edges_cleaned.csv` |
| `--output-removed` | 输出移除论文记录 | `papers_removed.csv` |

### 配置文件参数
通过 `config.py` 文件可配置的内部参数：

#### 清洗策略参数
- `PAPERS_CLEANED`：清洗后论文文件路径
- `EDGES_CLEANED`：清洗后边文件路径
- `PAPERS_INPUT_PATTERN`：输入论文文件匹配模式

## 使用方法

### 1. 环境准备
```bash
# 确保已安装依赖
pip install pandas
```

### 2. 基本使用
```bash
# 自动发现最新文件并清洗
python 2data_processor.py

# 指定目标数量进行智能恢复
python 2data_processor.py --target-count 150

# 指定具体文件路径
python 2data_processor.py papers_llm.csv reference_edges_llm.csv --target-count 200

# 完自定义路径
python 2data_processor.py papers_llm.csv reference_edges_llm.csv --target-count 200 --output-paper clean_papers.csv --output-edge clean_edges.csv
```

## 输出文件

- `papers_cleaned.csv`：清洗后的论文数据
- `edges_cleaned.csv`：清洗后的边数据（合并的引用网络）
- `papers_removed.csv`：被移除的论文及其移除原因

## 代码结构

```
2data_processor.py
├── find_input_files()                    # 自动发现输入文件
├── find_edge_files()                     # 查找匹配的边文件
├── clean_data()                          # 基础数据清洗
├── analyze_removal_patterns()            # 分析移除模式
├── smart_recover_papers()                # 智能论文恢复
├── estimate_original_target_count()      # 估计原始目标数量
├── smart_clean_data()                    # 智能清洗主函数
├── parse_arguments()                     # 解析命令行参数
└── main()                                # 主函数入口
```

## 移除原因类型

### 论文移除原因
- `"Missing arxiv_id or title"`：缺失arxiv_id或标题
- `"in_s2 = False (not in Semantic Scholar)"`：未在Semantic Scholar索引中
- `"Empty references (empty string/[]/nan)"`：引用字段为空
- `"Duplicate arxiv_id (retained first occurrence)"`：重复的arxiv_id（保留第一篇）

### 边数据移除原因
- 空值行：包含任何空值的边记录
- 空目标：`target` 字段为空的边记录

## 智能恢复策略

### 1. 优先级恢复
- **高优先级**：`in_s2 = False` 但有引用数据的论文
- **中优先级**：`in_s2 = False` 的较新论文
- **低优先级**：其他类型的移除论文（谨慎恢复）

### 2. 影响力评分
恢复优先级基于以下公式：
```
recovery_score = citationCount * 0.5 + influentialCitationCount * 1.0 + (2025 - year) * 0.1
```

### 3. 分析决策
- **安全恢复**：当超过70%的移除原因是 `in_s2 = False` 时启用
- **降级策略**：当安全恢复无法达到目标时启用
- **统计监控**：实时监控恢复进度和质量

## 特色功能

### 1. 自动文件发现
- 按修改时间自动发现最新的论文和边文件
- 支持参考文献和施引文献的自动匹配
- 向后兼容旧版的 `edges_*.csv` 格式

### 2. 详细移除追踪
- 为每篇被移除论文添加 `removal_reason` 字段
- 提供移除原因的详细统计报告
- 英文输出便于国际化使用

### 3. 智能恢复机制
- **预测性分析**：分析移除模式以决定是否进行恢复
- **分级恢复**：基于论文质量和影响力进行分级恢复
- **数量保证**：尽可能达到用户指定的目标数量

### 4. 完整的数据验证
- 调用 `validate_papers_dataframe()` 验证论文结构
- 调用 `validate_edges_dataframe()` 验证边数据结构
- 确保清洗后的数据完整性

## 应用场景

- **网络分析准备**：为PageRank等网络分析准备干净数据
- **文献综述**：清洗收集的文献数据以进行后续分析
- **AI for Science**：为智能代理提供高质量的训练数据
- **引用网络研究**：构建完整的学术引用网络进行研究

## 注意事项

- 智能恢复会标记恢复的论文为 `recovered = True`
- 恢复的论文会标记 `in_s2 = True`（尽管实际可能不是）
- 建议在恢复后验证数据质量
- 降级恢复策略可能影响数据质量，需谨慎使用
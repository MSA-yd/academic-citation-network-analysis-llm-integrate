## 1. PageRank 算法

### 1.1 标准 PageRank 公式

PageRank 的基本迭代公式：

$$PR(p_i) = \frac{1 - \alpha}{N} + \alpha \sum_{p_j \in M(p_i)} \frac{PR(p_j)}{L(p_j)}$$

其中：
- $PR(p_i)$：页面 $p_i$ 的 PageRank 值
- $\alpha$：阻尼因子（damping factor），通常取 0.85
- $N$：网络中节点的总数
- $M(p_i)$：指向页面 $p_i$ 的页面集合（入链页面）
- $L(p_j)$：页面 $p_j$ 的出链数量（出度）

### 1.2 矩阵形式表示

$$\mathbf{PR} = (1 - \alpha) \cdot \frac{1}{N} \cdot \mathbf{1} + \alpha \cdot \mathbf{S}^T \cdot \mathbf{PR}$$

其中：
- $\mathbf{PR}$：PageRank 向量
- $\mathbf{S}$：随机转移矩阵（stochastic matrix）
- $\mathbf{1}$：全1向量

### 1.3 收敛条件

迭代收敛当满足：
$$\|\mathbf{PR}^{(k+1)} - \mathbf{PR}^{(k)}\|_1 < \epsilon$$

其中 $\epsilon$ 为收敛阈值（通常为 $10^{-6}$）。

## 2. 时间加权 PageRank（Temporal Weighted PageRank）

### 2.1 时间衰减权重

指数衰减函数：
$$w(t) = e^{-\lambda \cdot (t_{\text{current}} - t_{\text{cite}})}$$

其中：
- $\lambda$：时间衰减系数（decay factor）
- $t_{\text{current}}$：当前年份
- $t_{\text{cite}}$：引用发生的年份（引用论文的发表年份）

### 2.2 加权 PageRank 公式

$$PR_{\text{temporal}}(p_i) = \frac{1 - \alpha}{N} + \alpha \sum_{p_j \in M(p_i)} w(t_j) \cdot \frac{PR_{\text{temporal}}(p_j)}{\sum_{p_k \in M(p_i)} w(t_k)}$$

或者使用边权重的矩阵形式：
$$\mathbf{PR}_{\text{temporal}} = (1 - \alpha) \cdot \frac{1}{N} \cdot \mathbf{1} + \alpha \cdot \mathbf{S}_{\text{weighted}}^T \cdot \mathbf{PR}_{\text{temporal}}$$

其中权重矩阵元素：
$$S_{\text{weighted}}(p_j, p_i) = \frac{w_{ji}}{\sum_k w_{jk}}$$

## 3. 质量加权 PageRank（Quality Weighted PageRank）

### 3.1 引用质量分数

论文质量评估函数：
$$Q(p) = C(p) + \beta \cdot IC(p)$$

其中：
- $Q(p)$：论文 $p$ 的质量分数
- $C(p)$：论文 $p$ 的总引用数（citationCount）
- $IC(p)$：论文 $p$ 的影响力引用数（influentialCitationCount）
- $\beta$：影响力引用权重（在配置中为 `INFLUENTIAL_CITATION_WEIGHT = 2.0`）

### 3.2 质量权重计算

对数转换避免权重过大：
$$w_{\text{quality}}(p) = \log(1 + Q(p))$$

### 3.3 质量加权 PageRank 公式

$$PR_{\text{quality}}(p_i) = \frac{1 - \alpha}{N} + \alpha \sum_{p_j \in M(p_i)} w_{\text{quality}}(p_j) \cdot \frac{PR_{\text{quality}}(p_j)}{\sum_{p_k \in M(p_i)} w_{\text{quality}}(p_k)}$$

## 4. 混合推荐系统

### 4.1 排名归一化

将各种分数转换为百分位排名：
$$R_{\text{std}}(p) = \text{rank}_{\text{pct}}(PR(p))$$
$$R_{\text{temp}}(p) = \text{rank}_{\text{pct}}(PR_{\text{temporal}}(p))$$
$$R_{\text{quality}}(p) = \text{rank}_{\text{pct}}(PR_{\text{quality}}(p))$$
$$R_{\text{citation}}(p) = \text{rank}_{\text{pct}}(C(p))$$
$$R_{\text{year}}(p) = \text{rank}_{\text{pct}}(\text{year}(p))$$

其中 $\text{rank}_{\text{pct}}$ 表示百分位排名（0 到 1 之间）。

### 4.2 混合评分公式

加权线性组合：
$$HS(p) = w_1 \cdot R_{\text{std}}(p) + w_2 \cdot R_{\text{temp}}(p) + w_3 \cdot R_{\text{quality}}(p) + w_4 \cdot R_{\text{citation}}(p) + w_5 \cdot R_{\text{year}}(p)$$

其中权重配置为：
- $w_1 = 0.25$（标准 PageRank 权重）
- $w_2 = 0.20$（时间 PageRank 权重）
- $w_3 = 0.20$（质量 PageRank 权重）
- $w_4 = 0.25$（引用数权重）
- $w_5 = 0.10$（新近度权重）

约束条件：$\sum_{i=1}^5 w_i = 1.0$

## 5. 年份分布策略

### 5.1 自定义年份分布

直接使用权重配置：
$$W(y) = \text{CUSTOM\_YEAR\_DISTRIBUTION}[y - y_{\text{end}}]$$

其中 $y_{\text{end}}$ 为结束年份。

### 5.2 指数衰减年份分布

当启用指数衰减时：
$$W(y) = \frac{\gamma^{(y_{\text{end}} - y)}}{\sum_{y'=y_{\text{start}}}^{y_{\text{end}}} \gamma^{(y_{\text{end}} - y')}}$$

其中：
- $\gamma$：指数衰减因子（`EXPONENTIAL_DECAY_FACTOR = 0.7`）
- $y_{\text{start}}$：开始年份
- $y_{\text{end}}$：结束年份

## 6. 社区检测（Leiden 算法）

### 6.1 模块度（Modularity）公式

Leiden 算法优化的模块度目标函数：

$$Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$

其中：
- $A_{ij}$：邻接矩阵元素（边存在为1，不存在为0）
- $k_i, k_j$：节点 $i$ 和 $j$ 的度数
- $m$：网络中边的总数
- $c_i, c_j$：节点 $i$ 和 $j$ 所属的社区
- $\delta(c_i, c_j)$：当 $c_i = c_j$ 时为1，否则为0

### 6.2 优化目标

最大化模块度 $Q$，使得社区内部连接密度高于随机期望。

## 7. 论文影响力评分（收集阶段）

### 7.1 影响力分数计算

在论文收集和筛选阶段使用的影响力分数：

$$\text{ImpactScore}(p) = C(p) + \beta \cdot IC(p) + \delta \cdot I_{\text{S2}}(p) + \eta \cdot |Citing(p)|$$

其中：
- $C(p)$：引用数
- $IC(p)$：影响力引用数
- $I_{\text{S2}}(p)$：Semantic Scholar 索引指示函数（1 如果索引，0 如果未索引）
- $|Citing(p)|$：施引论文数量
- $\beta = 2.0$（`INFLUENTIAL_CITATION_WEIGHT`）
- $\delta = 100$（`IN_S2_BONUS_SCORE`）
- $\eta = 0.5$（`CITING_PAPERS_WEIGHT`）

## 8. 恢复论文评分（数据清洗阶段）

### 8.1 恢复优先级分数

用于智能恢复被移除论文的评分：

$$\text{RecoveryScore}(p) = 0.5 \cdot C(p) + 1.0 \cdot IC(p) + 0.1 \cdot (2025 - \text{year}(p))$$

这个公式平衡了：
- 引用数量（权重 0.5）
- 影响力引用数量（权重 1.0）
- 新近度（权重 0.1，越新分数越高）

## 9. 网络构建权重

### 9.1 边属性权重

在构建引用网络时，边的权重属性：

- **时间权重**：$w_{\text{time}} = e^{-\lambda \cdot (t_{\text{current}} - t_{\text{source}})}$
- **质量权重**：$w_{\text{quality}} = \log(1 + Q(p_{\text{source}}))$

其中 $p_{\text{source}}$ 是引用论文（source 节点）。

## 10. 算法复杂度分析

### 10.1 PageRank 计算复杂度

- **时间复杂度**：$O(k \cdot |E|)$，其中 $k$ 为迭代次数，$|E|$ 为边数
- **空间复杂度**：$O(|V| + |E|)$，其中 $|V|$ 为节点数

### 10.2 Leiden 社区检测复杂度

- **时间复杂度**：$O(|E| \cdot \log |V|)$（近似）
- **空间复杂度**：$O(|V| + |E|)$

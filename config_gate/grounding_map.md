# Grounding map — what each part of the system rests on (for the paper)

每个组件 → 我们声称的 → 可引依据。**"engineering (tune)" = 没有理论出处的工程参数,论文里要诚实标成"标定参数",别假装有理论。**

| 组件 / 模块 | 我们声称什么 | 依据 / 引用 | 性质 |
|---|---|---|---|
| **关系类型** (perceive.py): touching/overlapping/inside | 拓扑空间关系的标准集合 | **RCC-8** — Randell, Cui & Cohn, *A spatial logic based on regions and connection*, KR 1992. (EC=touching, PO=overlapping, TPP/NTPP=inside) | 形式化,可引 |
| 重叠度量 | 交并比 | **IoU = Jaccard index**;检测领域标准 (PASCAL VOC, Everingham et al. 2010) | 标准度量 |
| 方向关系 above/below/left/right | 投影式基本方向 | **Frank 1991**, qualitative reasoning about cardinal directions (projection vs cone) | 形式化,可引 |
| "near" / 邻近 | 定性距离,相对于参照系与尺度;**无普适常数** | **Hernández, Clementini & Di Felice 1995** (Qualitative distances); **Clementini, Di Felice & Hernández, *Qualitative representation of positional information*, Artif. Intell. 1997** | 形式化 + 明确支持"阈值需按场景标定" |
| near/surface 的具体阈值 (0.18 / 0.33 / 0.75) | — | 无理论出处 | **engineering (标定参数)** |
| surface 降级规则 | 大背景物体降级成"只承载",抑制 hub | 无直接出处(工程);可类比 scene-graph 稀疏化 | **engineering** |
| 用几何关系而非 VLM/SGG 读关系 | VLM/SGG 逐帧关系不稳(intra-class 变化、inter-class 相似) | **PE-Net** — Lyu et al., CVPR 2023 (arXiv:2303.07096):正是这个不稳问题的证据 | 动机引用 |
| **门控 = 事件边界** | 把连续经验切成事件,切点在不可预测的变化处;6 类边界特征(地点/进出/物体互动/目标/因果/时间) | **Event Segmentation Theory** — Zacks, Speer, Swallow, Braver & Reynolds, *Psychological Bulletin* 2007 | 认知科学,核心引用 |
| 新颖 / 习惯化 / 厌倦 | 惊奇=先验↔后验的差;重复→KL→0 | **Bayesian Surprise** — Itti & Baldi, *Vision Research* 2009 | 可引(我们用习惯化-recency 作其廉价代理) |
| 噪声抑制 = learning progress | 抑制"永远新但学不会"的源(闪屏);关注可学习的中等新颖 | **IAC / 内在动机** — Oudeyer, Kaplan & Hafner, IEEE TEC 2007 | 可引 |
| **口味 = 可报告性** | "值得讲"= 对惯常脚本的破坏 | **Tellability/reportability** — Labov 1972; **Bruner 1991** ("breach of canonical script"); Ochs & Capps 2001 | 叙事学,核心引用 |
| 可报告性的具体轴 (people/relevance/consequence/continuity) | 什么算"值得报道" | **News values** — Galtung & Ruge 1965; Harcup & O'Neill 2001/2017 | 可引(我们做了向"个体化/情境化"的改写——这是贡献) |
| **cheap-gate → VLM 的两段式** | 用便宜信号选择性触发昂贵 VLM | **Bu & Ju et al. 2025** (arXiv:2512.07177, HRI,最近邻,需区分);**ColorTrigger 2026**(常开廉价触发) | 相邻工作,需对比 |
| 委派注意力 / 安置式陪伴 (HCI 框架) | 把"留意"委派给一个放置式有 taste 的伙伴 | SenseCam (Hodges et al.); "total capture" 批评 (Sellen & Whittaker, CACM 2010); Slow Technology (Hallnäs & Redström); Research Products / Photobox (Odom, CHI'14/'16); Calm Tech (Weiser & Brown); Mixed-Initiative (Horvitz CHI'99); Google Clips(无理论先例,对比项) | HCI 谱系,related work |
| 当代定位(说明方向正热、且占 placed+noticing 空位) | — | Vinci (IMWUT'25), EgoLife (CVPR'25), SensibleAgent (UIST'25), proactive agents (CHI'25), always-on 隐私 (WatchThis UIST'24) | 当代 related work |
| **未来:自扩展词表** | 从少数常见词出发,自动发现并纳入新物体 | **Open-World Object Detection** — Joseph et al., CVPR 2021 (ORE);open-vocab: YOLO-World (Cheng et al. CVPR'24), Grounding DINO | 未来工作,可引 |

> 一句话原则:**形式(RCC/方向/距离的"类型与度量")有据,具体阈值是标定参数;门控锚 Event Segmentation,口味锚 tellability/news values;不稳定性动机锚 PE-Net;HCI 贡献锚 delegated noticing 那一簇。**

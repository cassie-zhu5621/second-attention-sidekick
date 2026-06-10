# 代码导览 —— 按这个顺序逐行读就不会迷路

写给"看得懂结构、但不打算从零学编程"的你。所有文件在 `SecondAttention/config_gate/`。
在另一个 chat 里,可以一个文件一个文件地说:**"我是设计师不是程序员,请把这个文件逐行、用大白话讲,并说明它和其它文件怎么连。"** 那个 chat 能直接读这些文件、也能跑来给你看中间结果。

---

## 先分清:哪些是"系统",哪些是"当初验证想法的脚手架"

**要理解的(部署系统,6 个):**
`perceive.py` → `config_surprise.py` → `judge.py` → `sidekick.py` → `viz.py` → `run_perception.py`

**可以跳过/略看的(早期模拟验证用,不在机器人上跑):**
`sim.py`、`eval.py`、`eval_final.py`、`FINDINGS.md` —— 这些是当初用合成数据证明"配置新颖度这个想法成不成立"的,结论已记在 `FINDINGS.md`,代码本身不必精读。

**文档(不用读代码,直接看):** `README_perception.md`(怎么跑)、`grounding_map.md`(每块的引用)、本文件。

---

## 一帧画面的"旅程"(整个系统的主线,先记住这条)

```
一帧图  →  perceive: 物体框 + 几何关系 → 场景图(nodes, edges)
        →  config_surprise: 这个构型相对习惯化基线"新不新"? 是事件吗?
        →  (是事件才) judge: VLM 看图 → worth / why / 一句 field note
        →  worth 够高 → 报告; 落到 salience map; 用户回话可改 taste
        →  viz: 把以上全部画在画面上(实时可读)
```
`sidekick.py` 就是把这条线串起来的"指挥"。`run_perception.py` 是只跑前两步、整批离线测感知的。

---

## 阅读顺序(由具体到抽象)

### 1. `perceive.py` —— 图像变成场景图(最具体,从这开始)
- `Detection`:一个被检测到的物体(label 类型、box 像素框、score)。看 `.cx/.cy/.area` 怎么算。
- `_iou` / `_frac_inside`:两个小几何函数(重叠度、包含比)。
- `build_graph()`:**核心**。读三段:(a) 给每个物体编号成节点;(b) `is_surface` 判大背景;(c) 两两之间按几何连边(near/overlapping/inside,以及给了 up 才有的方向)。
- `SceneGraph` / `perceive()` / `YoloWorldDetector`:输出结构、总入口、真检测器适配口。

### 2. `config_surprise.py` —— 门控(整套最核心的逻辑)
- `motifs()`:场景图 → 一袋"motif"(单边、长度2路径、共现对)。门控就在这袋东西上算新颖度。
- `HabituatedPrior`:**习惯化记忆**。重点看 `per_motif_novelty()`(= `exp(-看过的次数)`,见过越多越不新)和 `observe()`(衰减+累加)。
- `ChurnSuppressor`:**噪声抑制**(learning-progress)。看 `trust_by_anchor()`——"一个源是反复出现(可学)还是每次都新(噪声)"。
- `ConfigSurpriseGate.step()`:把上面合成一个判断:这帧 score 多高、是否超阈值。
- `TemporalConfigGate.step()`:**时间层**——只在"从旧构型跳到新构型"的那一拍报一次事件,并给出"变了什么"(delta)。

### 3. `judge.py` —— VLM 判断脑 + 可改写的 taste
- `AXES` / `ReportabilityTaste`:那 4 个可报告性轴 + 权重。看 `compose()`(算 worth)、`nudge()`(用户一句话怎么改权重)。
- `relations_text()`:把场景图变成给 VLM 的一句"现场/变化"说明。
- `judge()`:**核心**。看它怎么拼 prompt、调 VLM、返回 `{worth, why, note}`;`SECONDATTN_OFFLINE=1` 时走假数据(无需 API)。

### 4. `sidekick.py` —— 指挥(把 1–3 串起来)
- `Look` / `Camera`:相机适配口(给一帧 + 位姿 + 变没变)。
- `SalienceMap`:空间记忆,看 `deposit()`(在某朝向落权重)、`as_grid()`。
- `Sidekick.tick()`:**核心,一拍循环**——逐行就是那条"旅程"。`tell()` 是用户改 taste。
- `__main__` 里的 `_ScriptedCamera`:一个假相机演示,跑 `python sidekick.py` 就能看整条链动起来。

### 5. `viz.py` —— 把管线状态画在画面上(可读性)
- `draw_overlay()`:**核心**。逐段:画 surface、画关系线+标签、画物体框、底部 HUD(四个环节)。

### 6. `run_perception.py` —— 整批离线测感知(你明天用的)
- `main()`:遍历文件夹 → 检测 → `build_graph` → `draw_overlay` 存图 → 存 `graphs.json/csv/summary`。看 for 循环那段即可。

---

## 小贴士
- 想"看到"某段在干嘛,就让那个 chat **加几行 print 跑给你看**(像我们之前那样,真实数据最直观)。
- 每个文件**顶部的三引号说明**已经写了"它是干嘛、为什么这么做",先读那段再读函数。
- 读不懂某个词(motif、IoU、prior…)直接问那个 chat 要"大白话 + 一个例子"。

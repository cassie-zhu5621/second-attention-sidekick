# 逐行精读 —— config_gate 的部署系统(写给不写代码的你)

这份文档是 `CODE_TOUR.md` 的"放大版"。`CODE_TOUR.md` 告诉你**先读哪个、各块大概干嘛**;这份文档把那 6 个部署文件**一行一行**用大白话讲清楚,并在每个函数后说明"它和别的文件怎么连"。

读法建议:对照着代码看。每段我都标了**行号范围**(比如 `L44–L92`),你可以在编辑器里跳过去对着读。遇到看不懂的词,先翻到最后的【词汇表】。

---

## 0. 先记住这条主线(每个文件都挂在它上面)

```
一帧图  →  perceive.py     : 物体框 + 几何关系  →  场景图(nodes 节点, edges 关系边)
        →  config_surprise.py : 这个"构型"相对习惯化基线新不新? 是事件吗?
        →  judge.py        : (是事件才) VLM 看真图 → worth(值不值得说) / why / 一句 field note
        →  sidekick.py     : 把上面三步串起来的"指挥";worth 够高就报告 + 记到 salience map
        →  viz.py          : 把以上所有状态画在画面上(让你肉眼看到系统在想什么)
        →  run_perception.py : 只跑前两步,整批离线测"感知"这一环(你拍完数据集后用的)
```

一句话:**便宜的几何 + 习惯化先筛**,只有"真的变了构型"才花钱叫一次 VLM。这就是整个项目省钱又省事的核心思路。

---

## 关于 Python 的几个最小常识(后面反复出现,先认一下)

- **函数(`def 名字(...)`)**:一段起了名字、可以反复调用的步骤。括号里是"输入",`return` 后面是"输出"。
- **`@dataclass` + `class`**:一个"数据盒子",把一组相关的数字/列表打包起来,还能带几个处理自己的函数(叫"方法")。你可以把它想成一张带格子的表单 + 几个按钮。
- **`for x in 列表:`**:对列表里每个元素挨个做同一件事(循环)。
- **`dict`(字典)**:`键 → 值` 的查找表,比如 `{"l1": "laptop"}` 表示"编号 l1 这个东西的类型是 laptop"。
- **`list`(列表)**:有顺序的一串东西,比如 `[(a, r, b), ...]`。
- **`Counter`**:一种特殊字典,专门数"每样东西出现了几次"。
- **`None`**:表示"没有/空"。
- 行首的 `#` 是**注释**,给人看的,程序会忽略。文件最上面三个引号 `"""..."""` 之间的也是说明文字。

---

# 1. `perceive.py` —— 把一帧图变成"场景图"(最具体,从这开始)

**它在主线里的位置:** 第一棒。输入一张图,输出一个"场景图"——也就是"画面里有哪些物体(节点)" + "它们之间是什么空间关系(边)"。后面所有判断都建立在这个场景图上。

**为什么要它(顶部 L1–L27 的说明在讲这件事):** 门控(下一站)要能"习惯化",前提是**同样的情况每次都要变成同样的图**。但 VLM 和那些学出来的关系模型每帧给的标签会乱跳(一会儿叫"科学家"一会儿叫"研究员")。所以这里用最笨但最稳的办法拿到稳定结构:**用成熟的物体检测器给稳定的框 + 用几何规则(而不是猜)给关系**。VLM 在这一步完全不参与,它是后面 judge 那一步的"判断脑"。

还有一个现实问题(L18–L23):相机装在云台上,画面会歪。"在……上面 / 上方 / 下方"这类方向关系,只有知道"哪边是上"才靠谱。所以关系分两类——**不怕旋转的**(near 靠近 / overlapping 重叠 / inside 包含)永远算;**需要方向的**(on/above/below/left/right)只有在外部给了"上方向 up"时才算。

---

### 1.1 开头的导入与类型别名(L29–L38)

```python
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Protocol

Box = Tuple[float, float, float, float]   # x1, y1, x2, y2 in pixels
```

- `from __future__ import annotations`:一句技术性开关,让"类型标注"写起来更省事,对功能没影响,可忽略。
- `import math`:借用数学工具箱(后面要算平方根、对数)。
- `from dataclasses import ...` / `from typing import ...`:把上面说的"数据盒子"工具和"类型提示"工具拿进来。
- `Box = Tuple[...]`:给"一个框"起个别名。一个框就是 4 个数 `(x1, y1, x2, y2)`,代表方框左上角和右下角的像素坐标。以后看到 `Box` 就知道"这是一个矩形框"。

---

### 1.2 `Detection` —— 一个被检测到的物体(L40–L55)

```python
@dataclass
class Detection:
    label: str            # 物体类型,如 "laptop";会变成节点的"type"
    box: Box
    score: float = 1.0
```

这是个"数据盒子",装**一个**检测到的物体,三样东西:

- `label`:类型名字(`"laptop"`、`"person"`)。这就是这个节点的"种类"。
- `box`:它的方框(上面说的 4 个数)。
- `score`:检测器对"这真是个 laptop"的信心,0~1。默认 `1.0`(=很确定)。

下面 5 个带 `@property` 的是"顺手算出来的属性",你用的时候像读数据一样读(`d.cx`),其实它现场算:

```python
    @property
    def cx(self): return 0.5 * (self.box[0] + self.box[2])   # 中心点的 x(左右居中)
    @property
    def cy(self): return 0.5 * (self.box[1] + self.box[3])   # 中心点的 y(上下居中)
    @property
    def w(self):  return self.box[2] - self.box[0]           # 宽 = 右减左
    @property
    def h(self):  return self.box[3] - self.box[1]           # 高 = 下减上
    @property
    def area(self): return max(self.w, 0) * max(self.h, 0)   # 面积 = 宽×高(负数当 0)
```

- `cx, cy`:框的中心点。后面判断"两个东西离得近不近"就靠中心点。
- `w, h`:框的宽和高。
- `area`:面积。`max(..., 0)` 是保险:万一框是反的算出负数,就当 0,免得面积变负。
- 一句话:`Detection` 就是"一个物体 + 一些一算就有的几何小数据"。

---

### 1.3 `Detector` —— 检测器的"插口"(L58–L60)

```python
class Detector(Protocol):
    def detect(self, image) -> List[Detection]: ...
```

这是一个**约定**(Protocol = "接口/插口"):任何"能把一张图变成一串 `Detection`"的东西,都算合格的检测器。`...` 表示这里只写约定、不写具体做法。

为什么这样写?这样真假检测器可以随便换:测试时插假的(`MockDetector`),上机器人时插真的(`YoloWorldDetector`),后面的代码一行都不用改。这就是文档里反复说的"可插拔适配器(adapter)"。

---

### 1.4 两个几何小工具:`_iou` 和 `_frac_inside`(L66–L80)

名字前的下划线 `_` 是惯例,表示"内部小工具,别人一般不直接用"。

**`_iou(a, b)` —— 两个框的"重叠程度"(L66–L72):**

```python
def _iou(a: Box, b: Box) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])   # 交叠区左上角
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])   # 交叠区右下角
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)   # 交叠区的宽、高(没交叠就是 0)
    inter = iw * ih                                # 交叠面积
    ua = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter   # 两框合起来覆盖的面积
    return inter / ua if ua > 0 else 0.0           # 交 / 并 = IoU
```

IoU(Intersection over Union,交并比)就是**"两个框重叠区 ÷ 两个框合起来的区"**,0 表示完全不挨着,1 表示完全重合。
- 前两行:求"重叠那一小块"的左上角和右下角。
- 第三行:算出这块的宽高;如果两框根本不挨着,`ix2-ix1` 会是负的,`max(0.0, ...)` 把它压成 0 → 重叠面积 0。
- `inter`:重叠面积。`ua`:两框面积相加再减去重叠(否则重叠被算两次)。
- 最后:`inter / ua`。`if ua > 0 else 0.0` 是防止除以 0。

**`_frac_inside(inner, outer)` —— inner 有多大比例"落在" outer 里(L75–L80):**

```python
def _frac_inside(inner: Box, outer: Box) -> float:
    ix1, iy1 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix2, iy2 = min(inner[2], outer[2]), min(inner[3], outer[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inner_area = (inner[2]-inner[0]) * (inner[3]-inner[1])
    return (iw * ih) / inner_area if inner_area > 0 else 0.0
```

跟 IoU 几乎一样,但分母换成 **inner 自己的面积**。结果含义:**"inner 这个小东西,有百分之几被 outer 罩住了"**。比如手机有 90% 落在桌子的框里,就返回 0.9。后面判断"X 在某个大平面上""A 装在 B 里面"全靠它。

---

### 1.5 `SceneGraph` —— 场景图这个"数据盒子"(L86–L93)

```python
@dataclass
class SceneGraph:
    nodes: Dict[str, str]               # 节点编号 -> 类型,如 {"laptop1": "laptop"}
    edges: List[Tuple[str, str, str]]   # 关系边:(源编号, 关系名, 目标编号)
    boxes: Dict[str, Box] = field(default_factory=dict)   # 节点编号 -> 框(画图/salience 用)

    def as_gate_input(self):
        return self.nodes, self.edges
```

场景图就装三样:
- `nodes`:谁在画面里。键是**唯一编号**(`laptop1`),值是**类型**(`laptop`)。
- `edges`:谁和谁有什么关系。每条边是 `(源, 关系, 目标)`,例如 `("cup1", "near", "laptop1")` = "cup1 靠近 laptop1"。
- `boxes`:每个节点的框,留着后面画图和定位用。`field(default_factory=dict)` 意思是"默认给个空字典"。
- `as_gate_input()`:一个小便利方法,把 `nodes` 和 `edges` 一起递出去——下一站门控正好要这两样。

**怎么连:** `perceive` / `build_graph` 产出 `SceneGraph`;门控吃它的 `nodes, edges`;`viz` 吃它的 `boxes` 来画。

---

### 1.6 `build_graph(...)` —— 整个文件的核心:框 → 场景图(L96–L182)

这是最重要的函数。输入一堆 `Detection`,输出一个 `SceneGraph`。分四步:**编号 → 找大平面 → 两两连边 → 打包**。

**函数签名和参数(L96–L99):**

```python
def build_graph(dets, image_wh, up=None,
                near_frac=0.18, min_score=0.30,
                surface_frac=0.33, surface_min_holds=3):
```

- `dets`:检测到的物体列表。
- `image_wh`:图片宽高 `(W, H)`。
- `up`:"上方向"。给了才算方向关系;不给只算不怕旋转的关系。默认 `None`(不给)。
- `near_frac=0.18`:多近算"靠近"——两中心距离小于"画面对角线 × 0.18"就算近。
- `min_score=0.30`:信心低于 0.3 的检测直接丢掉。
- `surface_frac=0.33` / `surface_min_holds=3`:判定"大平面/背景"的两个门槛,下面讲。

**准备工作(L114–L117):**

```python
    W, H = image_wh
    diag = math.hypot(W, H)          # 画面对角线长度(勾股定理)
    frame_area = max(W * H, 1)       # 整张图面积(至少为 1,防除零)
    dets = [d for d in dets if d.score >= min_score]   # 只留信心够高的检测
```

- `diag`:对角线,用来把"近"的标准换算成像素。`math.hypot(W,H)` 就是 √(W²+H²)。
- 最后一行是"过滤":把信心低于 `min_score` 的噪声检测扔掉。

**第一步:给每个物体编唯一编号(L119–L128):**

```python
    dets = sorted(dets, key=lambda d: (round(d.cy / max(H, 1), 2), d.cx))
    counts = {}
    nodes, boxes, ids = {}, {}, []
    for d in dets:
        counts[d.label] = counts.get(d.label, 0) + 1
        nid = f"{d.label}{counts[d.label]}"
        nodes[nid] = d.label
        boxes[nid] = d.box
        ids.append(nid)
```

- `sorted(...)`:把物体**按阅读顺序排**——先上后下、同高再左到右(`cy` 是上下,`cx` 是左右)。这样每帧编号尽量一致,有利于稳定。
- `counts`:数每种类型出现几次。`for` 循环里:每遇到一个 `laptop`,计数 +1,编号就成 `laptop1`、`laptop2`……
- `nodes[nid] = d.label`:登记"这个编号是什么类型"。`boxes[nid] = d.box`:登记它的框。`ids` 按顺序记下所有编号,后面两两配对要用。

**第二步:找出"大平面/背景"(L130–L137):**

```python
    is_surface = [False] * len(dets)
    for k, s in enumerate(dets):
        if s.area >= surface_frac * frame_area:
            holds = sum(1 for m, o in enumerate(dets)
                        if m != k and _frac_inside(o.box, s.box) >= 0.5 and o.area < s.area)
            if holds >= surface_min_holds:
                is_surface[k] = True
```

这一步解决一个很实际的麻烦:桌子、垫子、墙这种**又大又托着很多东西**的背景。如果不特殊处理,它会和画面里每个小东西都连上"靠近/重叠",边数爆炸(顶部注释叫它 "O(N²) 的 hub")。

- `is_surface`:一串"是不是平面"的开关,先全设 `False`。
- 对每个物体 `s`:先看它**够不够大**(面积 ≥ 全图的 33%);
- 再数它**托着几个东西** `holds`:有多少别的物体有一半以上落在它框里、而且比它小;
- 如果又大又托着 ≥3 个东西,就认定它是"平面",`is_surface[k] = True`。
- 妙处:如果画面里没有这种大块,这条规则自动不触发,所以对任何数据都安全。

**第三步:两两之间连关系边(L139–L178):**

```python
    edges = []
    for i in range(len(dets)):
        for j in range(len(dets)):
            if i == j:
                continue                  # 自己跟自己不连
            a, b = dets[i], dets[j]
            ai, bi = ids[i], ids[j]
```

两层 `for` = 把所有物体**两两组合**都看一遍。`i == j` 时跳过(自己不连自己)。`a,b` 是这一对物体,`ai,bi` 是它俩的编号。

下面是这一对要走的"关系判定流水线":

**(a) 如果其中一个是平面(L148–L151):**

```python
            if is_surface[i] or is_surface[j]:
                if is_surface[j] and not is_surface[i] and _frac_inside(a.box, b.box) >= 0.5:
                    edges.append((ai, "on", bi))   # a 放在平面 b 上
                continue                            # 平面只产生 "on",别的关系一律不连
```

只要这一对里有平面:唯一允许的边是"小东西 a **on**(在)平面 b 上"(条件:a 有一半以上落在 b 里)。其它关系全部跳过(`continue`)。这就是上一步找平面的目的——**保留有用的"X 在桌上",砍掉没用的一堆"X 靠近桌子"**。

**(b) 不怕旋转的关系——包含 inside(L153–L157):**

```python
            fi = _frac_inside(a.box, b.box)
            if fi >= 0.75 and b.area > a.area:
                edges.append((ai, "inside", bi))
                continue
```

`a` 有 75% 以上落在更大的 `b` 里 → "a **inside** b"(a 装在 b 里面),连完就跳过这一对。

**(c) 不怕旋转的关系——重叠 overlapping(L158–L164):**

```python
            if _iou(a.box, b.box) > 0.02 and i < j:
                edges.append((ai, "overlapping", bi)); edges.append((bi, "overlapping", ai))
```

两框 IoU > 0.02(有点重叠)就连 "overlapping"。注意注释强调:**画面里重叠 ≠ 现实里接触**,多半只是一个挡住另一个(前后遮挡)。所以这里诚实地叫 "overlapping(画面重叠)",不敢叫 "touching(接触)"。真正的物理接触留给后面 VLM 判断。
- `i < j` 是为了**每对只处理一次**(否则 i、j 互换会重复)。
- 连了两条方向相反的边(a→b 和 b→a),因为"重叠"是对称的:你重叠我,我也重叠你。

**(d) 不怕旋转的关系——靠近 near(L165–L167):**

```python
            dist = math.hypot(a.cx - b.cx, a.cy - b.cy)
            if i < j and dist < near_frac * diag and _iou(a.box, b.box) == 0:
                edges.append((ai, "near", bi)); edges.append((bi, "near", ai))
```

- `dist`:两个中心点的距离。
- 条件:距离 < `near_frac × 对角线`(够近),而且**完全不重叠**(`IoU == 0`,因为重叠的已经在上一步连过了)。
- 满足就连对称的两条 "near"。

**(e) 需要"上方向"才算的方向关系(L169–L178):**

```python
            if up is not None and i < j:
                ux, uy = up
                dx, dy = a.cx - b.cx, a.cy - b.cy
                along_up = dx * ux + dy * uy           # a 相对 b 沿"上"方向的分量
                along_right = dx * (-uy) + dy * ux      # 沿"右"方向的分量
                if dist < 0.45 * diag:
                    if abs(along_up) > abs(along_right):
                        edges.append((ai, "above" if along_up > 0 else "below", bi))
                    else:
                        edges.append((ai, "right_of" if along_right > 0 else "left_of", bi))
```

只有外部给了 `up`(比如云台告诉你"哪边朝上")才进来:
- 把"a 相对 b 的位移"分解到"上方向"和"右方向"两个轴上(这是高中向量投影,`along_up`、`along_right`)。
- 哪个轴上的偏移更大,就用哪个轴命名:上下偏移大 → above/below;左右偏移大 → left_of/right_of。
- 正负号决定到底是 above 还是 below(上还是下)。
- `dist < 0.45*diag`:离太远就不谈方向了。

**第四步:打包返回(L180–L182):**

```python
    sg = SceneGraph(nodes=nodes, edges=edges, boxes=boxes)
    sg.surfaces = [ids[k] for k in range(len(dets)) if is_surface[k]]   # 记下哪些是平面(透明可查)
    return sg
```

把 `nodes / edges / boxes` 装进 `SceneGraph`,再额外记一份"哪些节点是平面"(`sg.surfaces`,给画图和调试用),交出去。

**怎么连:** `build_graph` 是 perceive 文件的成品出口。`sidekick.py`、`run_perception.py`、各文件的自测都直接调它。它的 `nodes, edges` 喂给门控,`boxes/surfaces` 喂给 `viz`。

---

### 1.7 `perceive(...)` —— 一步到位的总入口(L185–L188)

```python
def perceive(image, detector, image_wh, up=None):
    return build_graph(detector.detect(image), image_wh, up=up)
```

把"检测"和"建图"合成一步:先让检测器看图(`detector.detect(image)`)拿到物体,再 `build_graph` 建图。一行话:**图片 → 检测 → 场景图**。`sidekick` 里用的就是它。

---

### 1.8 `MockDetector` —— 假检测器(测试用)(L194–L199)

```python
class MockDetector:
    def __init__(self, dets):
        self._dets = dets
    def detect(self, image=None):
        return self._dets
```

一个"假"检测器:你提前塞给它一组固定的 `Detection`,它每次 `detect` 都原样吐回。用途:**在没有真模型、没有 GPU 的情况下测试建图逻辑**。`__init__` 是"出生时"存下那组检测,`detect` 不管给什么图都返回它们。

---

### 1.9 `YoloWorldDetector` —— 真检测器(上机器人用)(L202–L229)

```python
class YoloWorldDetector:
    def __init__(self, vocabulary, weights="yolov8s-world.pt", conf=0.25, device=None):
        try:
            from ultralytics import YOLO
        except ImportError:
            raise SystemExit("YOLO-World needs ultralytics. Install it: pip install ultralytics ...")
        self.model = YOLO(weights)
        self.model.set_classes(vocabulary)
        self.conf = conf
        self.device = device
```

这是真正在机器人/笔记本上用的检测器,基于 YOLO-World(开放词表:你给一串想找的物体名,它就找那些,不需要重新训练)。

- `try / except ImportError`:试着引入 `ultralytics` 这个库;没装就友好地报错告诉你 `pip install ultralytics`,而不是崩溃。这种"懒加载"让你在没装这个库的沙箱里也能用 `MockDetector` 跑通其它部分。
- `self.model = YOLO(weights)`:加载模型权重文件(第一次用会自动下载)。
- `set_classes(vocabulary)`:告诉模型"我只关心这些类别"。
- `conf`:信心阈值;`device`:用 CPU 还是哪块 GPU(`None`=自动)。

```python
    def detect(self, image):
        r = self.model.predict(image, conf=self.conf, device=self.device, verbose=False)[0]
        names = r.names
        out = []
        for b in r.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            out.append(Detection(names[int(b.cls)], (x1, y1, x2, y2), float(b.conf)))
        return out
```

`detect` 把 YOLO 的输出**翻译**成我们自己的 `Detection` 格式:
- `predict(...)` 跑模型,`[0]` 取第一张图的结果。
- 对每个检测框 `b`:取出坐标 `xyxy`、类别名 `names[...]`、信心 `conf`,包成一个 `Detection`。
- 这样无论底层换成 YOLOv8 还是 Grounding DINO,**只要在这里翻译成 `Detection`,后面全不用改**——这就是"适配器"的价值。

**怎么连:** 它和 `MockDetector` 是可互换的两个检测器。`sidekick` / `run_perception` 不关心用的是哪个,只要它有 `detect`。

---

### 1.10 文件自测 `if __name__ == "__main__":`(L232–L276)

这段的意思是:**只有当你直接运行 `python perceive.py` 时才执行**(被别处 import 时不执行)。它是一个"自带的小演示"。

- L240–L261:用两帧**真实验室画面**手工写死了一堆框(`desk` 桌面场景、`pegboard` 洞洞板墙),当作"假装是 YOLO 输出的"。
- L263–L276:对每帧分别在"关闭平面规则"和"打开平面规则"两种情况下建图,然后数 motif 数量,打印出"打开规则后删掉了百分之几的无用 hub 边",并把保留的边列出来。

作用:让你**亲眼看到**"平面规则"确实把边数砍下来了。`CODE_TOUR.md` 里说的"想看到某段在干嘛,就让它 print 跑给你看",指的就是这种自测。

---

# 2. `config_surprise.py` —— 门控:整套最核心的逻辑

**它在主线里的位置:** 第二棒,也是这个项目的"主角"。输入场景图(`nodes, edges`),输出一个判断:**这个画面的"构型"相对我习惯化的基线,新不新?要不要花钱叫 VLM?**

**核心思想(顶部 L1–L28):** 新颖度不在"单条边",而在"构型"——也就是**很多条边怎么组合**。例子:
- 人在打字→笔记本、杯子在→笔记本旁边、笔记本在→桌上 = **在工作**(看多了,习惯了)
- 人在看→笔记本、**杯子被打翻**、笔记本在桌上 = **打翻了**(新的组合)

注意:节点还是那几个(人、杯子、笔记本),**变的是边的组合方式**。所以系统不是去记"具体哪个人",而是抽象到"类型 + 关系"层面,把场景拆成一袋叫 **motif(模式片段)** 的小零件,在这袋零件上算新颖度。看得越多 → 习惯化 → 新颖度趋近 0(无聊);一个永远在乱变、学不出规律的源(闪烁的屏幕)永远"新"但没价值,要被压低权重(这是 IAC / 学习进度的思想)。

文件分 4 块:① `motifs()` 把图拆成零件;② `HabituatedPrior` 习惯化记忆;③ `ChurnSuppressor` 噪声抑制;④ 两个 Gate 把前面合成判断。

---

### 2.1 导入与类型别名(L30–L38)

```python
from __future__ import annotations
import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Iterable

Node = str
Edge = Tuple[str, str, str]            # (源编号, 关系, 目标编号)
```

- `Counter`:数数用的字典(每个东西出现几次)。`defaultdict`:一种"查不到时自动给默认值"的字典(省去每次判断"键在不在")。`deque` 这里其实没用上。
- `Node = str` / `Edge = ...`:起别名,让后面读起来更清楚——"节点就是个字符串编号""边就是 (源, 关系, 目标) 三元组"。

---

### 2.2 `motifs(...)` —— 把场景图拆成"一袋零件"(L44–L92)

这是门控的"原料加工"。一张场景图进来,出去是一个 `Counter`:**每种 motif 出现了几次**。motif 有三种:

**① 单边 motif(长度 1)(L58–L61):**

```python
    t = nodes  # 编号 -> 类型
    bag = Counter()
    for (a, r, b) in edges:
        if a in t and b in t:
            bag[("E", t[a], r, t[b])] += 1
```

- `t` 就是"编号→类型"的查表。`bag` 是要装零件的袋子。
- 对每条边 `(a, r, b)`:把**具体编号换成类型**,造一个零件 `("E", 类型A, 关系, 类型B)`,袋子里这种零件计数 +1。
- `"E"` 是标签,表示"这是一条边(Edge)型 motif"。
- **关键**:用的是类型不是编号,所以"换一个人打字"和"原来那个人打字"是**同一个** motif——这就是顶部说的"对类型习惯化,而不是对具体实例",避免组合爆炸。

**② 长度 2 的路径 motif:A —r1→ B —r2→ C(L64–L75):**

```python
    out_by_node = defaultdict(list)
    in_by_node = defaultdict(list)
    for e in edges:
        out_by_node[e[0]].append(e)    # 按"从谁出发"归类
        in_by_node[e[2]].append(e)     # 按"到谁结束"归类
    for mid in t:
        for (a, r1, _b) in in_by_node.get(mid, []):
            for (_b2, r2, c) in out_by_node.get(mid, []):
                if a == c:
                    continue           # 跳过 A-r-B-r-A 这种来回打转
                if a in t and c in t:
                    bag[("P", t[a], r1, t[mid], r2, t[c])] += 1
```

- 先把边按"出发点"和"到达点"各归一次类。
- 然后找所有"经过中间点 mid 的两段链":有边进 mid(来自 a),又有边从 mid 出(去 c),就拼成一条 `A→B→C` 的路径零件 `("P", ...)`。`"P"` = Path。
- `if a == c: continue`:防止 A→B→A 这种无意义的来回。
- 含义:这种零件抓的是"三个东西串成的小链条",比单边更能描述结构。

**③ 共现 motif:同一个节点上挂着两条边(L81–L91):**

```python
    incident = defaultdict(list)
    for (a, r, b) in edges:
        if a in t and b in t:
            sig = (t[a], r, t[b])
            incident[a].append(sig)
            incident[b].append(sig)
    for n, sigs in incident.items():
        uniq = sorted(set(sigs))
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                bag[("C", t[n], uniq[i], uniq[j])] += 1
    return bag
```

- 先给每个节点收集"挂在它身上的所有边的类型签名"(`incident`)。
- 然后对每个节点,把它身上的边**两两配对**,造共现零件 `("C", 该节点类型, 边签名1, 边签名2)`。`"C"` = Co-occurrence(共现)。
- **这是让"构型新颖度"成立的关键零件**:它表达的是"两条本来各自都眼熟的边,现在同时出现在同一个东西上"。打翻杯子那个例子里——"人看笔记本"和"杯子翻倒"这两条边可能各自都见过,但**它们一起出现在桌面这个场景里**是新的。单看一条边永远发现不了这一点。
- `return bag`:把装好三种零件的袋子交出去。

**怎么连:** 下面的 Gate 每来一帧都先调 `motifs()` 把图变成袋子,再在袋子上算新颖度。

---

### 2.3 `HabituatedPrior` —— 习惯化记忆(L98–L181)

这是一个"数据盒子",代表**这一个空间**里"我对各种 motif 看过多少次"的记忆。看得越多越不稀奇。

**参数(L109–L116):**

```python
    decay: float = 0.997     # 慢慢遗忘:看过一次能"记住/习惯"很久(约 230 帧半衰期)
    alpha: float = 0.5       # 平滑项,让"从没见过的"有有限的高惊讶,而不是无穷大
    counts: Counter = field(default_factory=Counter)   # 每种 motif 的(带衰减的)累计次数
    total: float = 0.0       # 所有次数的总和
    vocab: set = field(default_factory=set)            # 见过的所有 motif 种类(算平滑分母用)
```

- `decay=0.997`:每过一帧,所有记忆乘以 0.997,即**缓慢遗忘**。好处:一个长期不再出现的构型,记忆会慢慢淡掉,以后再出现又能让人惊讶;而一直重复的构型记忆饱和,就不再惊讶了。
- `alpha=0.5`:数学上的"加一点底"(Dirichlet 平滑),让"从没见过的 motif"惊讶值是个有限的大数,而不是除零变无穷。
- `counts / total / vocab`:分别是"每种看过几次""总次数""见过哪些种类"。

**`p(motif)` —— 某个 motif 当前的(平滑)概率(L118–L121):**

```python
    def p(self, motif) -> float:
        V = max(len(self.vocab), 1)
        return (self.counts.get(motif, 0.0) + self.alpha) / (self.total + self.alpha * V)
```

"这个 motif 占了我全部记忆的多大比例"。分子是它的次数 + 平滑;分母是总次数 + 平滑×种类数。次数越多 → 概率越高 → 越眼熟。

**`self_information(bag)` —— MVP 版惊讶:平均 −log p(L123–L133):**

```python
    def self_information(self, bag) -> float:
        if not bag: return 0.0
        s = 0.0; n = 0
        for motif, k in bag.items():
            s += k * (-math.log(self.p(motif)))
            n += k
        return s / max(n, 1)
```

- `-math.log(p)` 是信息论里的"自信息":概率越小,这个值越大 → 越意外。
- 把袋子里每个 motif 的意外值按出现次数加权求和,再除以总数 → **平均意外度**。这是概念简报里最朴素的"惊讶 = 当前构型的 −log p"。
- 注意:文件后面会解释,这个朴素版本在实测里**输给**了下面的"习惯化-近因"版本,所以它不是最终用的。

**`per_motif_si(bag)` —— 每个 motif 各自的 −log p,不汇总(L135–L137):** 返回一个"motif→意外值"的表,留给 Gate 自己决定怎么汇总(取最大还是平均)。

**`per_motif_novelty(bag, beta)` —— 习惯化-近因新颖度(真正在用的)(L139–L149):**

```python
    def per_motif_novelty(self, bag, beta=1.0):
        return {m: math.exp(-beta * self.counts.get(m, 0.0)) for m in bag}
```

这是**最终采用**的新颖度公式:`nov(m) = exp(−次数)`。
- 没见过(次数 0)→ `exp(0)=1` → 最新颖。
- 见过很多次 → 次数大 → `exp(−大数)≈0` → 一点不新。
- **它和 −log p 的关键区别**(注释 L141–L148 重点):它衡量的是"**我见没见过这个**",而不是"它有多罕见"。一个**罕见但反复出现**的正常布局(比如偶尔伸个懒腰带出来的"椅子在桌边")次数会涨上去,于是习惯化到 0,不会反复误报;而一个**真正从没出现过**的组合,哪怕由眼熟的边拼成,次数也是 0 → 新颖度 1。这正是能把"新组合"和"少见但认识的东西"分开的关键。

**`bayesian_surprise(bag)` —— Itti & Baldi 的贝叶斯惊讶(L151–L170):** 用 KL 散度衡量"看完这帧后我的信念改变了多少"。改变大 = 惊讶。这是论文里更"正统"的版本,但 `FINDINGS.md` 记录它实测表现不如上面的习惯化版本,所以备而不用。这段细节是数学近似,**第一次读可以跳过**,知道"它是另一种惊讶算法、最后没选它"即可。

**`observe(bag)` —— 习惯化:看过就记下来(L172–L181):**

```python
    def observe(self, bag) -> None:
        if self.decay < 1.0:
            for m in list(self.counts):
                self.counts[m] *= self.decay     # 所有旧记忆先衰减一点
            self.total *= self.decay
        for motif, k in bag.items():
            self.counts[motif] += k              # 再把这帧的 motif 加进记忆
            self.total += k
            self.vocab.add(motif)
```

每帧的"记忆更新":**先把所有旧记忆乘 decay(遗忘一点点),再把这一帧看到的 motif 累加进去**。这就是"习惯化"的机械实现——见得越勤,次数堆得越高,越不惊讶。

**怎么连:** Gate 每帧先用 `per_motif_novelty`(或别的模式)算分,**打完分之后**才调 `observe` 把这帧记进去(顺序很重要:先评分,再习惯化)。

---

### 2.4 `ChurnSuppressor` —— 噪声抑制 / 学习进度(L187–L233)

**要解决的难题(注释 L189–L202):** 一个**忙碌但有意义**的源(人:打字、喝水、起身)本身就很"多样",看起来跟"闪烁的屏幕"一样乱。如果用"乱 = 噪声"的天真规则,会**误伤真人**,把真正的事件也压掉。

正确的区分标准是 **学习进度(learning progress)**:人的动作会**反复出现、慢慢变得可预测**;屏幕的内容每帧都是一次性的、**永远学不会**。所以对每个"锚点(anchor)"统计**重复率**——它身上出现的 motif,有多少是"以前见过、这次又见到"的。

```python
    warm: int = 6     # 一个锚点至少观察 6 次,才开始信它的重复率
    n_obs = defaultdict(float)     # 每个锚点总共观察了多少 motif
    n_repeat = defaultdict(float)  # 其中"以前见过的"有多少
    seen = defaultdict(set)        # 每个锚点见过哪些 motif
```

**`anchor(motif)` —— 一个 motif "挂在"哪个节点类型上(L208–L213):**

```python
    @staticmethod
    def anchor(motif) -> str:
        if motif[0] == "E":  return motif[1]   # 单边:取源类型
        if motif[0] == "P":  return motif[3]   # 路径:取中间节点类型
        return motif[1]                         # 共现:取共享节点类型
```

每个 motif 都能算出一个"主体/锚点"——它主要是围绕哪个类型的。屏幕相关的 motif 锚在 "screen",人相关的锚在 "person"。重复率就是**按这个锚点**分别统计的。`@staticmethod` 表示这个函数不依赖盒子里的数据,纯算。

**`trust_by_anchor(bag)` —— 算每个锚点的"可信度"(L215–L233):**

```python
    def trust_by_anchor(self, bag):
        trust = {}
        anchors = set(self.anchor(m) for m in bag)
        for m in bag:                            # 先用这帧更新统计
            a = self.anchor(m)
            if m in self.seen[a]:
                self.n_repeat[a] += 1            # 这个 motif 以前在该锚点见过 → 重复 +1
            self.n_obs[a] += 1
            self.seen[a].add(m)
        for a in anchors:
            if self.n_obs[a] < self.warm:
                trust[a] = 1.0                   # 新锚点/观察还太少:先别压,默认完全信任
            else:
                trust[a] = self.n_repeat[a] / self.n_obs[a]   # 重复率 = 可信度
        return trust
```

- 对这一帧每个 motif:看它在自己的锚点上以前见过没,见过就给该锚点"重复 +1";总观察 +1;记下见过。
- 然后给每个锚点算可信度:
  - 观察次数还不到 `warm=6` → 默认 `1.0`(**新来的不压制**,比如刚进门的一只狗,我们恰恰想注意它)。
  - 够了 → 可信度 = **重复率**(重复多 = 可学 = 可信 ≈ 1;每次都新 = 学不会 = 噪声 ≈ 0)。
- 妙处:**人**这个锚点重复率高 → 可信度高 → 一个真正新的、以人为中心的时刻**不会被压**;**屏幕**锚点重复率近 0 → 被压。

**怎么连:** Gate 把这个"可信度"逐 motif 乘到新颖度上——闪烁屏幕的 motif 被打折,同一帧里真人的事件不受影响。

---

### 2.5 `ConfigSurpriseGate` —— 帧级门控(把上面合成一个判断)(L239–L293)

**参数(L254–L261):**

```python
    threshold: float = 0.5          # 分数超过它就"开火"(叫 VLM)
    mode: str = "habituation"       # 用哪种新颖度:habituation(在用)/ selfinfo / bayes
    agg: str = "max"                # 怎么把多个 motif 的分汇总:max(在用)/ mean / topk
    topk: int = 3
    beta: float = 1.0
    suppress_noise: bool = True     # 是否启用上面的噪声抑制
    prior: HabituatedPrior          # 习惯化记忆
    churn: ChurnSuppressor          # 噪声抑制器
```

**`step(nodes, edges)` —— 处理一帧,给出决定(L263–L293):**

```python
        bag = motifs(nodes, edges)
        top = []
```

第一步:把图拆成 motif 袋子。`top` 待会儿放"最该负责的几个 motif"(便于解释为什么开火)。

```python
        if self.mode == "bayes":
            raw = self.prior.bayesian_surprise(bag)
            trust = (min(self.churn.trust_by_anchor(bag).values(), default=1.0)
                     if self.suppress_noise else 1.0)
            score = raw * trust
```

如果用 bayes 模式:整体算一个贝叶斯惊讶,乘上"最低可信度",得到分数。(这是备用分支。)

```python
        else:
            si = (self.prior.per_motif_novelty(bag, self.beta) if self.mode == "habituation"
                  else self.prior.per_motif_si(bag))
            trust_anc = self.churn.trust_by_anchor(bag) if self.suppress_noise else {}
            wmap = {m: s * trust_anc.get(self.churn.anchor(m), 1.0) for m, s in si.items()}
            weighted = list(wmap.values())
```

默认分支(在用的):
- `si`:每个 motif 的新颖度(habituation 模式用 `per_motif_novelty`)。
- `trust_anc`:每个锚点的可信度。
- `wmap`:把每个 motif 的新颖度**乘上它锚点的可信度**——这就是"逐 motif 做噪声抑制"。
- `weighted`:所有这些加权后的分,凑成一串。

```python
            if not weighted:
                score = 0.0
            elif self.agg == "mean":
                score = sum(weighted) / len(weighted)
            elif self.agg == "topk":
                score = sum(sorted(weighted, reverse=True)[:self.topk]) / min(self.topk, len(weighted))
            else:  # max
                score = max(weighted)
```

把那一串分**汇总成一个总分**:
- 默认 `max`(取最大):**只要袋子里有任何一个零件特别新,整个构型就算新**。这点很重要——打翻杯子那种"一个新共现被一堆眼熟 motif 包围"的情况,如果用平均(mean)会被稀释、漏掉;取最大才抓得住。`FINDINGS.md` 里说"第一次 reconfig 测试失败"就是因为当时用了平均。

```python
            raw = max(si.values()) if si else 0.0
            trust = min(trust_anc.values()) if trust_anc else 1.0
            top = sorted(wmap.items(), key=lambda kv: -kv[1])[:3]
        fire = score >= self.threshold
        self.prior.observe(bag)           # 打完分之后才习惯化
        return {"fire": fire, "score": score, "raw": raw, "trust": trust,
                "n_motifs": sum(bag.values()), "bag": bag, "top": top}
```

- `top`:挑出贡献最大的 3 个 motif,方便事后解释。
- `fire = score >= threshold`:**总分过线就开火**(值得叫 VLM)。
- `self.prior.observe(bag)`:**先评分、后习惯化**——把这帧记进记忆(下次再见就没这么新了)。
- 最后返回一个"决定字典":开不开火、分数、原始分、可信度、motif 数、袋子、top 零件。

**怎么连:** 这是"帧级"判断。但它有个毛病:只要新构型一直在,它会一直开火。所以上面还要套一层"时间层"。

---

### 2.6 `TemporalConfigGate` —— 时间层:一次转变 = 一个事件(L296–L347)

**要解决的问题(注释 L298–L312):** 上面的帧级门控,只要"新构型"持续存在就会**每帧都开火**。但一个放在那儿的陪伴体应该:在"场景刚跳进新构型的那一拍"**报一次**,然后安静下来。这层就干这件事——**只在上升沿(从平静/眼熟 → 新)报一次事件**,并附上"到底变了什么(delta)"。

```python
    gate: ConfigSurpriseGate          # 里面包着上面的帧级门控
    refractory: int = 1               # 事件后,需要连续几帧"眼熟"才能重新待命
    armed: bool = True                # 是否"待命"(可以触发下一个事件)
    last_stable: Counter              # 上一个稳定构型(用来算 delta)
    _quiet_run: int = 0               # 已经连续安静了几帧
```

**`step(nodes, edges)`(L319–L337):**

```python
        d = self.gate.step(nodes, edges)   # 先让帧级门控判断
        bag = d["bag"]
        event = False
        delta_added = []
        if d["fire"]:
            if self.armed:
                event = True
                self.armed = False
                delta_added = [(m, c) for m, c in bag.items() if m not in self.last_stable]
            self._quiet_run = 0
        else:
            self._quiet_run += 1
            if self._quiet_run >= self.refractory:
                self.armed = True
                self.last_stable = bag       # 这个平静构型成为新的基线
        d.update(event=event, delta_added=delta_added, armed=self.armed)
        return d
```

逐句:
- 先拿帧级门控的结果 `d`。
- 如果这帧**开火**了:
  - 而且当前**待命中**(`armed`)→ 这才算一个真正的 `event=True`,然后**撤防**(`armed=False`),避免后面持续的新构型反复报。
  - `delta_added`:把"这袋里、上一个稳定构型里没有的 motif"挑出来——这就是**"新增了什么结构"**,正是要交给 VLM 的"变化点"。
  - `_quiet_run` 归零。
- 如果这帧**没开火**(安静):
  - 连续安静计数 +1;连续安静够 `refractory` 帧 → **重新待命**,并把当前这个平静构型存为新基线 `last_stable`。
- 最后把 `event / delta_added / armed` 补进结果返回。

**`describe(delta_added, top)` —— 把"变了什么"写成人话(L339–L347):**

```python
    @staticmethod
    def describe(delta_added, top) -> str:
        def fmt(m):
            if m[0] == "E": return f"{m[1]}-{m[2]}->{m[3]}"
            if m[0] == "P": return f"{m[1]}-{m[2]}->{m[3]}-{m[4]}->{m[5]}"
            return f"({m[2][0]}-{m[2][1]}->{m[2][2]}) + ({m[3][0]}-{m[3][1]}->{m[3][2]})"
        new = [fmt(m) for m, _ in delta_added] or [fmt(m) for m, _ in top]
        return "new structure: " + "; ".join(new[:4])
```

把那些零件翻译成可读的小字符串(单边写成 `A-关系->B`,路径写成 `A->B->C`,共现写成两条边相加),拼成一句 `new structure: ...`,最多列 4 个。**这句就是给日志看、也是塞进 VLM 提示词的"变化说明"。** 如果没算出 delta 就退而用 top 零件。

**怎么连:** `sidekick` 每拍调这个时间层;它的 `event` 决定要不要叫 `judge`,它的 `delta_added` 被 `judge` 当作"现场变化"的文字依据。

---

### 2.7 文件自测 `__main__`(L350–L376)

直接运行 `python config_surprise.py` 时跑的小演示:
- 先用"工作"构型连喂 8 帧,打印分数**一路下降**(习惯化);
- 再喂一帧"打翻",分数应当**重新蹿高、开火**(同样的节点、不同的组合,被抓到了)。
- 然后演示时间层:`工作×4 → 打翻×4 → 工作×2` 的序列里,那连续 4 帧打翻应当**只产生 1 个事件**(在上升沿),并打印"变了什么"。

这正好把这个文件最得意的两点("能抓新组合""一次转变只报一次")**跑给你看**。

---

# 3. `judge.py` —— VLM 判断脑 + 可改写的 taste

**它在主线里的位置:** 第三棒,而且**只在门控开火后才跑、每个事件只跑一次**。它看**真图**(这是 VLM 的强项),配上门控给的"结构变化说明"当依据,返回:

```
{ worth(值不值得说), why(因为哪些方面), note(一句现场记录), axes(四轴打分) }
```

**关键转变(注释 L11–L19):** 这里的 taste **不再**是旧的 9 个 Berlyne 维度。新颖/惊讶已经是门控的活了;留给 VLM 的问题是 **可报告性(reportability)**——一个**已经是事件**的时刻,值不值得讲给**这个人**听。所以 taste 是一小组**清晰、可编辑**的"可报告性轴",理论上挂靠在叙事学的"可讲性"(Labov 1972;Bruner 1991)和新闻价值(Galtung & Ruge 1965)上。用户可以**实时一句话改这些权重**(`nudge`)——这就是"可编译的口味",也是用户"边看边教"的同一个通道。

**离线模式(`SECONDATTN_OFFLINE=1`):** 返回写死的假分数,让整条流水线**不用 API key 也能端到端跑通**——方便接线测试、也方便你把自己的机器人插进来。

---

### 3.1 导入与模型名(L22–L27)

```python
from __future__ import annotations
import os, re, json, base64, hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional

MODEL = os.environ.get("SECONDATTN_JUDGE_MODEL", "claude-haiku-4-5")
```

- `os`:读环境变量(开关/API key)。`re`:正则,做文字匹配。`json`:解析 VLM 返回的 JSON。`base64`:把图片编码成文本好塞进 API。`hashlib`:离线模式造假分数用。
- `MODEL = os.environ.get(..., "claude-haiku-4-5")`:用哪个 VLM。优先读环境变量 `SECONDATTN_JUDGE_MODEL`,没设就用默认的 `claude-haiku-4-5`(便宜快的小模型)。

---

### 3.2 四个"可报告性轴"和改权重的词表(L34–L48)

```python
AXES = {
    "people":      ("有人 / 社交在场 —— 有人在、参与、互动", 1.0),
    "relevance":   ("和这个人在意的东西 / 他的物品 / 这个空间有多相关", 1.0),
    "consequence": ("后果或麻烦 —— 有点利害关系(打翻、落下、坏了、变了)", 1.0),
    "continuity":  ("是不是之前注意过的事的后续(一条线在延续)", 0.5),
}
```

`AXES` 是四条评判轴,每条配一句**给 VLM 看的说明**和一个**默认权重**。continuity 默认权重 0.5(不如前三条重要)。这四条就是"什么样的时刻值得讲":有人、相关、有后果、是续集。

```python
_AXIS_WORDS = { "people": ["people","person","someone",...], "relevance": [...], ... }
_POS = ["more", "love", "like", "want", "care", "yes", "good", "keep"]
_NEG = ["less", "no", "not", "stop", "ignore", "avoid", "don't", "dont", "fewer", "hate"]
```

- `_AXIS_WORDS`:每条轴对应的**关键词**。用户说话里出现这些词,就知道他在调哪条轴。(注释提到 relevance 故意不收 "care",免得和 "care about X(在意某事)"撞车。)
- `_POS` / `_NEG`:表示"加"和"减"的词。用户说 "more people" → people 轴加;"less clutter" → 减。

---

### 3.3 `ReportabilityTaste` —— 可编辑口味的数据盒子(L51–L88)

```python
    weights: Dict[str, float]   # 四条轴当前的权重(默认取 AXES 里的)
    about: str = ""             # 一句自由文本偏好,如 "the robotics corner"
    lo: float = 0.0             # 权重下限
    hi: float = 2.0             # 权重上限
    lr: float = 0.4             # 每次 nudge 调多少(学习率)
```

`weights` 是四条轴的当前权重;`about` 是一句话的额外偏好;`lo/hi` 把权重限制在 0~2;`lr=0.4` 是"每句话调多大步子"。

**`compose(scores)` —— 把四轴分数合成一个 worth(L59–L62):**

```python
    def compose(self, scores):
        num = sum(self.weights.get(a, 0.0) * scores.get(a, 0.0) for a in AXES)
        den = sum(abs(self.weights.get(a, 0.0)) for a in AXES) or 1.0
        return num / den
```

**加权平均**:每条轴的"VLM 打分 × 该轴权重"加起来,再除以权重总和。结果就是这个时刻对这个人的 **worth(总价值)**。权重越偏向某轴,那轴的分就越主导 worth。

**`why(scores)` —— 主要因为哪两条轴(L64–L67):**

```python
    def why(self, scores):
        ranked = sorted(((self.weights.get(a,0.0)*scores.get(a,0.0), a) for a in AXES), reverse=True)
        return ", ".join(a for _, a in ranked[:2])
```

把四条轴按"加权得分"从高到低排,取**最高的两条**的名字拼成一句解释,比如 `"people, consequence"`。这就是给用户看的"为什么报告这条"。

**`nudge(sentence)` —— 用户一句话实时改权重(L69–L88):**

```python
        toks = re.findall(r"[a-z']+", sentence.lower())
        delta = {}
        for i, tok in enumerate(toks):
            for a, words in _AXIS_WORDS.items():
                if tok in words:
                    val = 1.0
                    for w in reversed(toks[max(0, i - 4):i]):
                        if w in _NEG: val = -1.0; break
                        if w in _POS: val = 1.0; break
                    delta[a] = val
```

- 先把句子拆成小写单词 `toks`。
- 逐词看它是不是某条轴的关键词;是的话,**往前回看最多 4 个词**找方向词:遇到 `_NEG` → 这条轴要减(`val=-1`),遇到 `_POS` → 加(`val=+1`)。比如 "less clutter" 里 "less" 在前面 → 减。
- 把"这条轴该加还是减"记进 `delta`。

```python
        for a, dv in delta.items():
            self.weights[a] = max(self.lo, min(self.hi, self.weights[a] + self.lr * dv))
        m = re.search(r"(?:care about|interested in|watch|about)\s+(.*)", sentence.lower())
        if m and not delta:
            self.about = m.group(1).strip(" .")
        return delta
```

- 按 `delta` 真正改权重:`当前权重 + 学习率×方向`,再用 `max/min` 夹在 0~2 之间(`lr=0.4` 所以一句话不会一下改太猛)。
- 最后:如果句子是 "I care about XXX / interested in XXX" 这种、且没匹配到任何轴关键词,就把 XXX 存进 `about`(自由文本偏好)。
- 返回这次改了哪些轴。

**怎么连:** `sidekick.tell()` 收到用户的话,转给这里的 `nudge`;`judge()` 算 worth 时用这里的 `compose / why`。

---

### 3.4 `relations_text(graph, delta_added)` —— 把结构变成给 VLM 的一句话(L94–L100)

```python
def relations_text(graph, delta_added=None) -> str:
    def fmt(e): return f"{graph.nodes.get(e[0], e[0])} {e[1]} {graph.nodes.get(e[2], e[2])}"
    if delta_added:
        new = "; ".join(fmt(m) for m, _ in delta_added[:6])
        return f"new structure: {new}" if new else ""
    return "; ".join(fmt(e) for e in graph.edges[:10])
```

把场景图(或"新增的变化")写成一句**人话**的关系描述,塞进 VLM 提示词当依据:
- `fmt(e)`:把一条边 `(源, 关系, 目标)` 用**类型名**写成 "laptop on desk" 这样。
- 如果给了 `delta_added`(事件的变化点)→ 只描述**变了什么**(最多 6 条),写成 `new structure: ...`。
- 否则就描述**现在画面里有什么**(最多 10 条边)。

---

### 3.5 `_offline(...)` —— 离线假分数(L106–L109)

```python
def _offline(jpeg, rel, taste) -> dict:
    h = hashlib.md5((rel + taste.about).encode() + (jpeg[:1500] if jpeg else b"")).hexdigest()
    scores = {a: (int(h[i*3:i*3+3], 16) % 1000) / 1000.0 for i, a in enumerate(AXES)}
    return {"axes": scores, "note": f"[offline] {rel[:48]}" or "a quiet moment"}
```

没有 API 时造**可重复**的假分数:
- 用 `md5` 把"关系文字 + 偏好 + 图片前段"哈希成一串十六进制 `h`。
- 从 `h` 里切片当数,折算成 0~1 的四轴分数。同样输入永远得同样分数(可重复,方便测试)。
- `note` 写一句 `[offline] ...`。这一整套让你**没有 key 也能跑完整条链**。

---

### 3.6 `_prompt(rel, taste)` —— 拼给 VLM 的提示词(L112–L127)

```python
    lines = [
        "You are the noticing companion's judgment brain ...",
        "This moment already passed a novelty gate ... do NOT re-judge novelty. Judge how REPORTABLE ...",
    ]
    for a, (rubric, _) in AXES.items():
        lines.append(f"  - {a}: {rubric}")
    if taste.about.strip():
        lines.append(f'The person especially cares about: "{taste.about.strip()}".')
    if rel:
        lines.append(f"\nStructured grounding — {rel}")
    lines.append('\nReturn ONLY JSON: {"axes": {...}, "note": "<one field note, <=16 words>"}')
    return "\n".join(lines)
```

一条条拼出给 VLM 的指令:
- 开头交代角色,并**明确告诉它"别再判断新颖度"**(那是门控干过的),只判断"可报告性"。
- 把四条轴的说明逐条列出。
- 如果用户设过 `about`,加一句"这个人特别在意 XXX"。
- 如果有关系文字 `rel`,作为"结构依据"附上。
- 最后**强制它只返回 JSON**(四轴分数 + 一句 ≤16 词的 note),方便程序解析。
- `"\n".join(lines)`:把这些行拼成完整一段。

---

### 3.7 `judge(...)` —— 核心:判断一个被放行的时刻(L130–L154)

```python
def judge(jpeg, graph, taste, delta_added=None, model=MODEL) -> dict:
    rel = relations_text(graph, delta_added) if graph is not None else ""
    if os.environ.get("SECONDATTN_OFFLINE") == "1" or jpeg is None:
        out = _offline(jpeg, rel, taste)
```

- 先把结构变成文字 `rel`。
- **如果开了离线开关、或根本没有图** → 走 `_offline` 拿假分数。

```python
    else:
        import anthropic
        client = anthropic.Anthropic()
        b64 = base64.standard_b64encode(jpeg).decode()
        msg = client.messages.create(
            model=model, max_tokens=200,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": _prompt(rel, taste)}]}])
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
```

否则**真的叫 VLM**:
- 引入 `anthropic` 库、建客户端。
- 把图片编码成 base64 文本 `b64`。
- 发一条消息,内容是**图片 + 提示词**两部分,`max_tokens=200`(限制回复长度,省钱)。
- 把模型回复里的文字部分拼成 `text`。

```python
        try:
            s, e = text.index("{"), text.rindex("}") + 1
            raw = json.loads(text[s:e])
            out = {"axes": {a: float(raw.get("axes", {}).get(a, 0.0)) for a in AXES},
                   "note": str(raw.get("note", ""))[:120]}
        except Exception:
            out = {"axes": {a: 0.0 for a in AXES}, "note": f"parse-fail: {text[:40]}"}
```

- 从回复里截出 `{...}` 那段,用 `json.loads` 解析成数据。
- 取出四轴分数和 note(note 截到 120 字)。
- `try/except`:万一模型没好好返回 JSON,**不崩溃**,而是给全 0 分 + 一句 "parse-fail"。这是健壮性兜底。

```python
    worth = taste.compose(out["axes"])
    return {"worth": worth, "why": taste.why(out["axes"]), "note": out["note"], "axes": out["axes"]}
```

- 不管分数来自真 VLM 还是离线,都用 `taste.compose` 把四轴合成一个 **worth**,用 `taste.why` 给出"主要因为哪两条轴"。
- 返回 `{worth, why, note, axes}`——这就是交给 `sidekick` 决定"报不报"的最终判断。

**怎么连:** `sidekick.tick()` 在门控 `event` 后调 `judge`,拿 `worth` 和阈值比;`note` 进 feed 给用户看。

---

### 3.8 文件自测 `__main__`(L157–L177)

强制开离线模式后演示:
- 先用默认口味判断一个画面;
- 然后模拟用户说 "more people, less consequence",打印**权重确实变了**,再判断一次;
- 再模拟 "I care about the robotics corner",打印 `about` 被设上了。
这把"口味可被一句话实时改写"这件事**跑给你看**。

---

# 4. `sidekick.py` —— 指挥:把 1–3 串成一拍循环

**它在主线里的位置:** 第四棒,"总指挥"。它本身不做感知/判断,而是**按顺序调用** perceive → 门控 → judge,并加上两个记忆(salience map + 门控里的非冗余),最后把够格的时刻放进 feed。

**设计原则(注释 L11–L16):** 所有跟硬件/模型相关的东西都是**可插拔适配器**(相机 Camera、检测器 Detector、feed)。默认全是"假的"(mock),所以**没有机器人、没有检测器、没有 API key 也能跑通整条循环**。接线方法就是:先用 mock 确认流程对,再在机器人上把真适配器一个个换上(相机=你的 MJPEG 抓帧+云台位姿;检测器=YoloWorldDetector;judge 用你的 key;feed=Discord/网页面板)。**注意:移动(转头看)还没在这里**——相机适配器只负责给 (画面, 位姿),注视策略以后再插。

---

### 4.1 导入(L19–L27)

```python
from perceive import perceive, build_graph, Detection, MockDetector
from config_surprise import ConfigSurpriseGate, TemporalConfigGate
from judge import judge, ReportabilityTaste
```

这三行就是把前面三个文件的成品都拿过来用——`sidekick` 是它们的"组装车间"。前面几行 `import os, math, time ...` 是借标准工具。

---

### 4.2 `Look` —— "一次观察"的数据盒子(L33–L42)

```python
@dataclass
class Look:
    jpeg: Optional[bytes]                 # 这一帧的图片字节(离线测试时是 None)
    dets: List[Detection]                 # 这一帧的检测结果
    pose: Tuple[float, float]             # (pan 水平, tilt 俯仰) 角度 —— 给 salience 和 'up'
    wh: Tuple[int, int] = (1600, 1200)    # 图片宽高
    up: Optional[Tuple[float, float]] = None   # 上方向(有就能算方向关系)
    settled: bool = True                  # 镜头已经稳住了(stillness 门已过)
    changed: bool = True                  # 相比上次看这里,画面有没有变化
```

相机每次交出一个 `Look`,打包"这一眼看到的一切":图、检测、云台朝向、宽高、上方向,以及两个**便宜的预筛标志**——`settled`(画面稳了没,晃动时不处理)和 `changed`(跟上次看同一个朝向比有没有变)。

**`Camera` 协议(L44–L45):** 和检测器一样的"插口":任何有 `look()`、能交出一个 `Look`(或 `None` 表示还没准备好)的东西,都算合格的相机。

---

### 4.3 `SalienceMap` —— 空间记忆:哪些朝向常发生值得注意的事(L51–L75)

```python
    pan_bins: int = 9          # 水平方向分成 9 格
    tilt_bins: int = 3         # 俯仰方向分成 3 格
    pan_range = (-80, 80)      # 水平角度范围
    tilt_range = (-25, 25)     # 俯仰角度范围
    decay: float = 0.997       # 慢慢遗忘
    grid: dict                 # (pan格, tilt格) -> 累计的"价值"
```

把整个可看范围切成 9×3 的网格,记录"哪一格朝向更常出现值得注意的事"。这是关于**地点**的记忆。

**`_bin(pose)`(L60–L66):** 把一个连续角度 `(pan, tilt)` 换算成落在哪一格。里面的 `min/max` 是把结果**夹在 0~格数-1** 之间,防止越界;`+1e-9` 是防除零的小技巧。

**`deposit(pose, worth)`(L68–L71):**

```python
    def deposit(self, pose, worth):
        for k in list(self.grid):
            self.grid[k] *= self.decay   # 所有格子先衰减一点(慢慢忘)
        self.grid[self._bin(pose)] += worth   # 在这次朝向那一格加上这次的价值
```

每报告一次值得注意的事,就在对应朝向的格子里"存"一笔价值,同时让所有格子轻微衰减。久而久之,网格就反映出"这个空间里哪几个方向最值得看"。

**`as_grid()`(L73–L75):** 把网格导出成一个二维表(3 行 × 9 列),四舍五入到 3 位小数,方便打印/可视化。

---

### 4.4 `Sidekick` —— 主体(L81–L118)

```python
    camera: Camera                       # 相机适配器
    taste: ReportabilityTaste            # 可报告性口味
    gate: TemporalConfigGate             # 时间层门控(里面包帧级门控,habituation+max+阈值0.5)
    salience: SalienceMap                # 空间记忆
    worth_threshold: float = 0.45        # worth 超过它才真的报告
    feed: list                           # 报告落到这里(以后换成 Discord/面板)
```

把前面所有部件**组装成一个对象**:相机、口味、门控、空间记忆、报告阈值、feed 列表。`gate` 默认用 habituation 模式 + max 汇总 + 阈值 0.5(和 `FINDINGS.md` 里的最佳配置一致)。

**`tell(sentence)` —— 用户实时教口味(L91–L94):**

```python
    def tell(self, sentence):
        d = self.taste.nudge(sentence)
        return d or {"about": self.taste.about}
```

把用户说的话转给 `taste.nudge` 去改权重;返回改了什么(若只设了 about,就返回 about)。这就是"边看边教"的入口。

**`tick()` —— 核心:一拍循环(L96–L118):**

```python
        look = self.camera.look()
        if look is None or not look.settled:
            return None                       # 还没准备好/镜头没稳 -> 这拍跳过(stillness 门)
```

第一步:拿一眼。没准备好或没稳住就**直接跳过**(便宜的"稳定性"门,晃动时不浪费后面计算)。

```python
        g = build_graph(look.dets, look.wh, up=look.up)
        d = self.gate.step(g.nodes, g.edges)   # 总是:习惯化 + 得到 event/delta
```

第二步:用这帧检测**建场景图**;第三步:**喂给时间层门控**,拿到"是不是事件、变了什么"。注意门控每帧都会习惯化(即使没开火)。

```python
        if not (look.changed or d["event"]):
            return None
```

**双触发**(注释 L102–L108):只要**画面变了**(便宜的像素层)**或**门控判定**新构型**,就算候选;两者都没有就跳过。为什么要两个?
- 画面层能抓到"粗图抓不到的细动"(杯子在桌上滑了一下,场景图还是"杯子在桌上",但像素变了);
- 构型层给出结构、还能压住像素抖动;
- 重复看到一模一样的画面 → `changed=False` → 自动习惯化,白省一次。

```python
        r = judge(look.jpeg, g, self.taste, delta_added=d["delta_added"])
        if r["worth"] < self.worth_threshold:
            return None                       # 是事件,但对这个人不值得报
```

第四步:叫 `judge` 看真图给 worth。worth **不到阈值**就不报(是事件,但对这个人没意思)。

```python
        self.salience.deposit(look.pose, r["worth"])
        report = {"pose": look.pose, "worth": round(r["worth"], 2), "why": r["why"],
                  "note": r["note"], "delta": TemporalConfigGate.describe(d["delta_added"], d["top"])}
        self.feed.append(report)
        return report
```

够格了:在 salience map 对应朝向**存一笔价值**;打包一条报告(朝向、worth、原因、现场记录、变化说明)放进 `feed`,并返回它。**这一拍就走完了整条主线。**

**怎么连:** `tick()` 就是把 perceive / config_surprise / judge 三个文件**按顺序粘起来**的那段;它前面的 `settled`、`changed` 是两道便宜的预筛,把昂贵的 judge 留到最后。

---

### 4.5 `_ScriptedCamera` —— 假相机(端到端演示)(L124–L142)

```python
    def __init__(self):
        base = [Detection("person",...), Detection("laptop",...), Detection("cup",(520,250,640,400)), Detection("desk",...,0.9)]
        spill = [..., Detection("cup",(980,1000,1100,1150)), ...]   # 杯子挪到了笔记本底部
        self.seq = [("base", base)] * 6 + [("spill", spill)] + [("base", base)] * 2
        self.i = 0
        self._prev = None
```

一个"剧本相机":先重复 6 帧桌面基线(应当习惯化),中间插 1 帧"杯子翻到笔记本旁"(应当触发**一个**事件),再回 2 帧基线。`seq` 就是这个剧本。

```python
    def look(self):
        if self.i >= len(self.seq):
            return None
        tag, dets = self.seq[self.i]; self.i += 1
        changed = (dets != self._prev)     # 用"和上一帧检测是否不同"近似像素变化
        self._prev = dets
        return Look(jpeg=None, dets=dets, pose=(20, 0), changed=changed)
```

每次 `look` 吐剧本里的下一帧,顺便算 `changed`(跟上一帧不一样就算变了),包成 `Look` 交出去。剧本放完返回 `None`。

---

### 4.6 文件自测 `__main__`(L145–L166)

直接运行 `python sidekick.py`(自动开离线模式)会:
- 跑那 9 帧剧本,打印每拍是"报告了 ★"还是"——(习惯化/无事件)";结果应当是**6 帧基线习惯化、那 1 帧翻杯报告一次**。
- 打印 salience 网格(看价值落在哪一格)。
- 最后模拟用户说 "I care about the robotics corner" 和 "more people",打印口味确实被改。
这是**整条链一起动**的最直观演示——`CODE_TOUR.md` 推荐你先跑这个。

---

# 5. `viz.py` —— 玻璃箱:把管线状态画在画面上

**它在主线里的位置:** 旁路工具。它不参与判断,但把**系统每一步"想了什么"画在真图上**——检测框、几何关系、哪个大块被当成平面、门控开没开火、VLM 的 worth/why/note。这是项目"可读 / 可解释"的那一面:一屏看尽所有阶段。它**不挑检测器**,你给它图、场景图、和一个小 `state` 字典就行。

> 这个文件用到 `cv2`(OpenCV,画图库)和 `numpy`(数组库)。颜色用 **BGR** 顺序(OpenCV 的习惯,不是常见的 RGB)。

---

### 5.1 颜色表(L20–L29)

```python
REL_COLOR = {
    "near":        (235, 99, 37),    # 蓝   —— 画面上的靠近
    "overlapping": (12, 65, 194),    # 橙   —— 画面重叠(遮挡,不是 3D 接触)
    "inside":      (237, 58, 124),   # 紫   —— 画面包含
    "on":          (110, 118, 15),   # 青   —— 在某个平面区域内(不分深度)
    "above": (160,160,160), "below": (160,160,160),
    "left_of": (160,160,160), "right_of": (160,160,160),
}
_SYMMETRIC = {"near", "overlapping"}
```

给每种关系配一个颜色,画线时好区分。方向关系统一灰色。`_SYMMETRIC` 列出"对称"的关系(a 近 b 等于 b 近 a),画的时候这类只画一条线、不重复。

**`_ctr(b)`(L32–L33):** 算一个框的中心点(画线的端点用)。

---

### 5.2 `draw_overlay(img, g, state, caption)` —— 核心:把状态画上去(L36–L116)

```python
    out = img.copy()
    H, W = out.shape[:2]
    surfaces = set(getattr(g, "surfaces", []))
```

先**复制**原图(不改原图),拿到高宽,取出"哪些是平面"。`getattr(..., [])` 是"没有就给空列表"的安全取法。

```python
    if caption:
        (tw, th), _ = cv2.getTextSize(caption, ...)
        cv2.rectangle(out, (0, 0), (tw + 20, th + 18), (20, 22, 25), -1)
        cv2.putText(out, caption, (10, th + 8), ...)
```

如果传了 `caption`(批处理时用,比如 "5 objects, 8 relations"),在左上角画个深色底块再写字。`getTextSize` 先量字多大好画底块;`rectangle` 最后参数 `-1` 表示**填充**;`putText` 写字。

**① 画平面高亮(L52–L60):**

```python
    for sid in surfaces:
        if sid in g.boxes:
            x1, y1, x2, y2 = map(int, g.boxes[sid])
            layer = out.copy()
            cv2.rectangle(layer, (x1, y1), (x2, y2), (110, 118, 15), -1)
            cv2.addWeighted(layer, 0.10, out, 0.90, 0, out)   # 半透明叠加
            cv2.rectangle(out, (x1, y1), (x2, y2), (110, 118, 15), 2)
            cv2.putText(out, f"{g.nodes.get(sid, sid)} [surface]", ...)
```

对每个平面:在一张副本上画实心矩形,再用 `addWeighted` 以 10% 透明度叠回去 → **淡淡的青色填充**(标出"这是平面");然后描边、写上 "xxx [surface]" 标签。

**② 画关系线 + 标签(L63–L78):**

```python
    drawn = set()
    for (a, rel, b) in g.edges:
        key = (frozenset((a, b)), rel) if rel in _SYMMETRIC else (a, rel, b)
        if key in drawn: continue
        drawn.add(key)
        if a not in g.boxes or b not in g.boxes: continue
        pa, pb = _ctr(g.boxes[a]), _ctr(g.boxes[b])
        col = REL_COLOR.get(rel, (180, 180, 180))
        thick = 1 if rel == "on" else 3
        cv2.line(out, pa, pb, col, thick, ...)
        mx, my = (pa[0] + pb[0]) // 2, (pa[1] + pb[1]) // 2
        ... 在中点画白底 + 写关系名 ...
```

对每条边:
- `drawn` + `key`:**去重**。对称关系用 `frozenset((a,b))` 当键,这样 a-b 和 b-a 只画一次。
- 取两端中心点 `pa, pb`,按关系取颜色,`on` 画细线(1)、其它画粗线(3)。
- 在两点之间连线,在线的**中点**写关系名(先画白底块再写字,保证看得清)。

**③ 画物体框 + 名字(L81–L90):**

```python
    for nid, box in g.boxes.items():
        if nid in surfaces: continue          # 平面已经单独画过了
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(out, (x1,y1),(x2,y2),(40,40,40),2)   # 深灰框
        cv2.circle(out, _ctr(box), 4, (40,40,40), -1)      # 中心点小圆
        cv2.putText(... 名字, 粗白底 ...)                   # 先白色粗字
        cv2.putText(... 名字, 细黑字 ...)                   # 再黑色细字(描边效果,任何背景都看得清)
```

给每个非平面物体画框 + 中心点 + 名字。名字写两遍(先白粗、后黑细)是个常用技巧,做出**描边**效果,在亮/暗背景上都清楚。

**④ 底部 HUD:四个管线阶段(L93–L115):**

```python
    if state is not None:
        bar_h = 150
        ... 在底部画一条半透明深色条 ...
        def ok(v): return "OK" if v else "--"
        ev = state.get("event")
        gate_txt = "EVENT (new configuration)" if ev else "habituated / no new config"
        gate_col = (90,240,120) if ev else (140,140,140)   # 事件用绿色,否则灰
        cv2.putText(... f"(1)stillness {ok(...)}  (2)changed-here {ok(...)}" ...)
        cv2.putText(... f"(3)gate: {gate_txt}" ...)
        w = state.get("worth"); why = state.get("why","")
        if w is not None:
            cv2.putText(... f"(4)judge: worth={w:.2f} why={why}" ...)
        note = state.get("note","")
        if note:
            cv2.putText(... f'"{note[:70]}"' ...)
    return out
```

只有传了 `state` 才画底部仪表盘,把**四个阶段**写出来:(1) 稳了吗 (2) 这里变了吗 (3) 门控:事件还是习惯化(事件绿色) (4) judge 的 worth/why,以及那句 note。这样一张图上就能**肉眼读出系统每一步的判断**。最后返回画好的图。

**`show_live(...)`(L119–L122):** 给真·实时循环用的便利函数:弹个窗口显示叠加图,按 q 退出。

**怎么连:** `sidekick` 的实时循环每拍可以调 `draw_overlay`;`run_perception` 批处理时也调它存图。它读 `SceneGraph` 的 `boxes/edges/surfaces` 和一个 `state` 字典。

**自测 `__main__`(L125–L154):** 读一张真实验室图,用手写框建图、离线 judge 出个样例 state,叠加后存成 `viz_demo_desk.jpg`——就是这个文件夹里那张示例图的来源。

---

# 6. `run_perception.py` —— 整批离线测"感知"(你拍完数据集后用的)

**它在主线里的位置:** 只跑前两步(检测 → 建图 → 叠加存图)的**批处理脚本**。你明天从固定位置拍一批照片后,就用它**一次性**把所有图过一遍,看看感知质量、并把场景图存下来,**以后可以离线重放给门控**(感知最贵,做一次存着反复用)。

---

### 6.1 默认词表(L31–L33)

```python
DEFAULT_VOCAB = ["person", "laptop", "monitor", ... "lamp"]
```

不指定时,YOLO-World 去找的默认物体清单(桌面常见物)。你也可以用 `--vocab` 自己换。

**`_DemoDetector`(L36–L43):** `--mock` 时用的假检测器,按图片大小返回几个比例框,只为**验证批处理流程**(走文件夹、画图、存 JSON)能不能跑,不需要真模型。

**`make_detector(args)`(L46–L54):** 根据命令行参数**决定用真还是假检测器**:带 `--mock` 用假的;否则建 `YoloWorldDetector`,用你给的词表和参数。

---

### 6.2 `main()` —— 主流程(L57–L131)

```python
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, ...)
    ap.add_argument("--out", ...); ap.add_argument("--vocab", ...)
    ... 一堆 --near-frac / --min-score / --surface-frac / --conf / --up / --limit / --device / --mock ...
    args = ap.parse_args()
```

先定义**命令行参数**:必填的 `--images`(图片文件夹),其余都有默认值——它们正好对应 `build_graph` 里那些可调门槛,方便你不改代码就调参。`parse_args()` 把你在命令行打的选项读进来。

```python
    out = args.out or os.path.join(args.images, "_perception")
    os.makedirs(out, exist_ok=True)
    up = tuple(float(x) for x in args.up.split(",")) if args.up else None
    det = make_detector(args)
```

定输出文件夹(默认在图片夹下建 `_perception`)、建好它;把 `--up` 文字 "ux,uy" 解析成数对;按参数造好检测器。

```python
    files = sorted(sum([glob.glob(os.path.join(args.images, e))
                        for e in ("*.jpg","*.jpeg","*.png","*.JPG")], []))
    if args.limit: files = files[:args.limit]
```

**收集**文件夹里所有图片路径(各种扩展名),排序;`--limit` 可只取前 N 张(快速试)。

```python
    records, rel_hist, obj_hist, n_surf = [], Counter(), Counter(), 0
    csv_rows = ["file,n_objects,n_relations,n_surfaces,objects"]
    for i, fp in enumerate(files):
        img = cv2.imread(fp)
        if img is None:
            print("  skip (unreadable):", ...); continue
        H, W = img.shape[:2]
        dets = det.detect(img)
        g = build_graph(dets, (W, H), up=up, near_frac=..., min_score=..., surface_frac=..., surface_min_holds=...)
        cap = f"{len(g.nodes)} objects, {len(g.edges)} relations"
        ann = draw_overlay(img, g, caption=cap)
        name = os.path.splitext(os.path.basename(fp))[0]
        cv2.imwrite(os.path.join(out, name + "_viz.jpg"), ann)
```

这就是**逐张处理的主循环**——对每张图:读图(读不了就跳过)、检测、`build_graph` 建场景图、叠加画框存成 `xxx_viz.jpg`。这一步就是把前两棒(感知)整批跑一遍。

```python
        surfs = getattr(g, "surfaces", [])
        records.append({"file": ..., "wh": [W,H], "nodes": g.nodes, "edges": g.edges, "boxes": g.boxes, "surfaces": surfs})
        objs = sorted(g.nodes.values())
        csv_rows.append(f'{...},{len(g.nodes)},{len(g.edges)},{len(surfs)},{"|".join(objs)}')
        for e in g.edges: rel_hist[e[1]] += 1
        for t in g.nodes.values(): obj_hist[t] += 1
        if surfs: n_surf += 1
        if i % 25 == 0 or i == len(files)-1:
            print(f"  [{i+1}/{len(files)}] {name}: {cap}")
```

同时**做统计**:把每帧场景图存进 `records`(以后离线重放给门控用),往 CSV 加一行,累计"各关系出现几次"(`rel_hist`)、"各物体出现几次"(`obj_hist`)、有平面的帧数。每 25 张打印一次进度。

```python
    n = max(len(records), 1)
    json.dump(records, open(os.path.join(out, "graphs.json"), "w"), indent=1)
    open(os.path.join(out, "per_frame.csv"), "w").write("\n".join(csv_rows))
    summary = {"frames":..., "avg_objects_per_frame":..., "avg_relations_per_frame":...,
               "frames_with_surface":..., "object_frequency":..., "rarest_objects":..., "relation_types":...}
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)
```

全部跑完,**存四样东西**:`graphs.json`(所有场景图,供离线重放)、`per_frame.csv`(每帧一行)、`summary.json`(汇总统计,含最常见/最罕见物体——罕见的正是"不寻常"的候选)。

```python
    print("\n==== SUMMARY ====")
    ... 打印帧数、平均物体/关系数、有平面帧数、关系种类、最常见/最罕见物体、输出位置 ...
```

最后在屏幕上打印汇总,让你**一眼判断感知质量、决定要调哪个参数**。

**`if __name__ == "__main__": main()`(L134–L135):** 直接运行这个脚本时就执行 `main()`。

**怎么连:** 它把 `perceive`(检测+建图)和 `viz`(画图)组合成离线批处理;产出的 `graphs.json` 之后可以喂给 `config_surprise` 的门控做离线评测,而**不用再跑一次昂贵的检测器**。

---

# 7. 脚手架文件(`sim.py` / `eval.py` / `eval_final.py`)—— 略看即可

这三个**不在机器人上跑**,是当初用合成数据**证明"配置新颖度这个想法成不成立"**的验证代码。结论已写在 `FINDINGS.md`,所以代码本身不必逐行精读。简要说明:

- **`sim.py`** —— 造一条"假的一天":因为沙箱里跑不了 GPU 检测器,就**直接模拟感知那一步的输出**(场景图流),用来测真正的贡献——门控。它故意造三种帧:`NORMAL`(日常工作,换实例但同类型,**不该开火**)、`EVENT`(和 NORMAL **共享节点**的真变化,如打翻、交接、新人进来,**该开火**)、`NOISE`(闪烁屏幕,每帧都冒新单边,**不该开火**)。设计上专门给 NOISE 灌很多新单边去"引诱"单边门控,给 EVENT 用和 NORMAL 一样的节点集去"骗"看节点袋的门控——这样能公平检验各种门控。

- **`eval.py`** —— 把**四种门控**摆在这条假数据流上比:`ALWAYS-ON`(每帧都叫 VLM,现状)、`TRIPLET-NOVELTY`(只看单边)、`NODE-EMBEDDING`(只看节点类型袋、丢掉结构)、`CONFIG-SURPRISE`(本项目:motif 构型 + 习惯化 + 噪声抑制)。每种门控都**单独扫出自己的最佳阈值**(保证不偏袒),再比检出率、习惯化、噪声误报、VLM 调用预算。`TripletNovelty` 这类基线是"干净的消融"——和 CONFIG 用**一模一样**的机器,只把表示换成"单边",所以差距纯粹来自"构型表示"这一点。

- **`eval_final.py`** —— 跑出 `FINDINGS.md` 里那张结论表的精简版。

**一句话结论(详见 `FINDINGS.md`):** 在"用熟悉的边重新组合"(reconfiguration)这种事件上,配置门控检出 **100%**,而单边、节点嵌入两个更便宜的基线**检出 0%**、且换任何阈值都救不回来;但在"引入全新关系"的事件上,便宜的单边门控已经够用。所以配置门控**不是处处更好**,而是**对"熟悉元素的重新组合"既必要又唯一够用**——这是个精确、站得住的结论,目前适合做 late-breaking/workshop,要做完整论文还需在真实场景图上重跑。

---

# 8. 词汇表(看到不懂的词翻这里)

- **场景图 / scene graph**:把一帧画面表示成"节点(物体)+ 边(物体间关系)"的结构。本项目里 `nodes` 是"编号→类型",`edges` 是 `(源, 关系, 目标)`。
- **节点 node / 边 edge**:节点=一个物体;边=两个物体之间的一条关系(如"杯子 near 笔记本")。
- **motif(模式片段)**:把场景图拆成的小零件。三种——单边 `E`、长度2路径 `P`、共现 `C`。门控的新颖度就在这袋零件上算。
- **构型 configuration**:很多条边**怎么组合**的整体样子。本项目主张"新颖在构型,而非单条边"。
- **IoU(交并比)**:两个框"重叠区 ÷ 合并区",0=不挨着,1=完全重合。衡量两个框重叠多少。
- **frac_inside(包含比)**:小框有百分之几落在大框里。判断"在……里面/在……上面"。
- **检测器 detector**:把图片变成"物体框 + 类型"的模型(如 YOLO-World)。本项目把它做成可换的"插口"。
- **adapter(适配器)/ Protocol(协议/插口)**:一种"只规定要会做什么、不规定怎么做"的约定,让真/假部件随意替换(相机、检测器、judge 都这么做)。
- **prior(先验)/ HabituatedPrior**:这里指"对各种 motif 看过多少次"的累积记忆。看得多→眼熟→不惊讶。
- **习惯化 habituation**:看得越多越不稀奇。机械实现=每帧把旧记忆乘 decay(遗忘一点),再把这帧加进去。
- **decay(衰减)**:每帧把记忆轻微缩小的系数(如 0.997),实现"缓慢遗忘"。
- **EMA(指数滑动平均)**:一种"新数据占一点、旧数据慢慢淡"的更新方式;习惯化用的就是这种思路。
- **−log p / 自信息 self-information**:概率越小、值越大=越意外。最朴素的"惊讶"。本项目实测发现它会把"罕见但正常"误当新颖,所以改用下面的"习惯化-近因新颖度"。
- **习惯化-近因新颖度 `exp(−次数)`**:衡量"我见没见过这个",而不是"它多罕见"。没见过=1,见多了≈0。**这是最终采用的新颖度**。
- **贝叶斯惊讶 / KL 散度(Itti & Baldi)**:用"看完这帧后信念改变了多少"衡量惊讶。本项目备而不用(实测不如上面)。
- **聚合 aggregation:max / mean / topk**:把袋里很多 motif 的分**汇总成一个总分**的方式。本项目用 **max**(只要有一个零件特别新,整体就算新),避免新组合被一堆眼熟零件平均稀释。
- **噪声抑制 / 学习进度 / IAC(Oudeyer)**:区分"乱但有意义(人)"和"乱且没意义(闪烁屏幕)"。靠**重复率**——会重复出现=可学=可信;每次都新=学不会=噪声。
- **锚点 anchor**:一个 motif 主要"挂在"哪个节点类型上(人/屏幕/…)。重复率按锚点分别统计。
- **可信度 trust(0~1)**:某锚点的重复率;乘到新颖度上,把噪声源打折。
- **阈值 threshold**:分数超过它才"开火"(才花钱叫 VLM)。
- **门控 gate / 开火 fire**:门控=便宜的先筛器;开火=它认为值得叫 VLM。
- **上升沿 rising edge / refractory(不应期)**:时间层只在"从平静跳到新构型那一拍"报一次事件,然后要连续安静若干帧才重新待命——避免一个持续状态被反复报。
- **delta(变化点)/ delta_added**:相对上一个稳定构型,这次**新增了哪些 motif**——就是交给 VLM 的"变了什么"。
- **VLM(视觉语言模型)**:能看图又能讲话的模型(如 Claude Haiku)。本项目里它是**贵但聪明**的"判断脑",只在门控开火后看真图。
- **worth(值不值得说)**:judge 给一个**已经是事件**的时刻打的"对这个人值不值得讲"的总分。
- **可报告性 taste / 四轴**:people / relevance / consequence / continuity 四条"值不值得讲"的轴;用户可一句话实时改权重。
- **nudge(轻推)**:用户说一句话(如 "more people")→ 自动调对应轴的权重。
- **salience map(显著性地图)**:关于**地点**的记忆——哪几个朝向常发生值得注意的事。
- **离线模式 `SECONDATTN_OFFLINE=1`**:不连 API、用写死的假分数,让整条链能在没有 key 时跑通(测试用)。
- **HUD**:画面底部那条状态栏,显示四个阶段的判断。
- **`__main__` / 自测**:每个文件底部"直接运行这个文件时才跑"的小演示,用来把这个文件的能力**跑给你看**。
- **BGR**:OpenCV 表示颜色的顺序(蓝-绿-红),和常见的 RGB 相反。
- **`cv2` / `numpy`**:画图库 / 数组库。
- **mock(假件)**:测试用的假部件(假检测器、假相机),不依赖真硬件/模型。

---

## 附:最快的"亲眼看懂"路径

按这个顺序直接跑,每个都会把自己**打印给你看**(都在 `SecondAttention/config_gate/` 下):

```
python3 perceive.py          # 看"平面规则"砍掉多少无用边
python3 config_surprise.py   # 看习惯化(分数下降)+ 打翻重新开火 + 一次转变一个事件
python3 judge.py             # 看一句话怎么改口味权重(离线,无需 key)
python3 sidekick.py          # 看整条链:6帧习惯化、1帧翻杯报告一次 + salience 网格
```

看不懂某段时,最直观的办法就是在那段里加几行 `print` 跑一遍——用真实中间结果去理解,比读文字快。

# 跑离线检测 —— 明天的操作步骤

拍完同一位置的 dataset 后,在**你自己的电脑**上跑这一个命令即可。

## 1. 装依赖(一次)
```
pip install ultralytics opencv-python
```
首次运行会自动下载 `yolov8s-world.pt`(需要联网)。

## 2. 跑整批
```
cd SecondAttention/config_gate
python run_perception.py --images /你的dataset文件夹 \
    --vocab "person,laptop,cup,chair,desk,monitor,keyboard,book,bag,phone,potted plant,bottle,plant,bookshelf"
```
- `--vocab`:换成你研究室真实有、且你在意的物体(open-vocab,不用训练)。
- 没有 GPU 也能跑(慢一点);想指定:`--device cpu` 或 `--device 0`。
- 只想先试几张:`--limit 20`。

## 3. 看产出(默认在 `你的文件夹/_perception/`)
- `*_viz.jpg` —— 每帧:框 + 关系 + "几个物体/几条关系" 画在真实画面上。**整批翻一遍肉眼判好坏。**
- `per_frame.csv` —— 每帧的物体数/关系数/surface数/物体清单。**可在 Excel 里排序**找最忙/最空的帧。
- `summary.json` —— 物体频率(最常 vs 最罕见)、关系类型分布、平均数。
- `graphs.json` —— 每帧的场景图。**这步最值钱**:detector 只跑这一次,之后测门控/习惯化直接离线吃它,不用再跑检测。

## 4. 翻图时按这几样调旋钮
- 框/标签不准、漏检 → 调 `--conf`(默认 0.25,调低多检、调高更准)、`--min-score`,或往 `--vocab` 里加漏掉的物体。
- `near` 连太多/太少 → 调 `--near-frac`(默认 0.18)。
- 桌子/地板没被判成背景(或误判)→ 调 `--surface-frac`(默认 0.33)、`--surface-min-holds`(默认 3)。
- 画面是歪的、想要 on/above 这类方向关系 → 传 `--up "ux,uy"`(相机朝向大致固定时)。

## 5. 然后
把 `summary.json` 和几张代表性的 `_viz.jpg` 发我 → 我们把 `graphs.json` 当时间序列离线喂门控,看哪些帧会触发、习惯化对不对。

## 常见问题
- `ultralytics 没装` → 按第 1 步装;或先 `--mock` 验证流程(用占位框,不需要 detector)。
- 想换更强(但更慢)的检测器抓长尾物体 → 之后可换 Grounding DINO(藏在同一个 Detector 适配口后面)。

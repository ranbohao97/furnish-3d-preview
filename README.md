# 全屋三维预览 v10

[打开在线预览](https://ranbohao97.github.io/furnish-3d-preview/)

交互式全屋概念模型：厨房无吊柜、CAD 三角洗手台、3230 mm 玄关通顶柜（2470 mm 玄关收纳 + 760 mm 餐边区），以及按用途调整的柜内分区。客厅采用 65 英寸电视与落地支架，取消电视柜与客厅茶几。冰箱 600 mm 档上单门，700 / 800 mm 档上双门，下部均为双抽屉，支持 600 / 700 / 800 mm 宽度与邻柜联动。支持 WASD 第一人称漫游、17 个视角、剖切墙体、CAD 叠合、柜内查看、动线净距、截图与 GLB 下载。

本仓库仅包含预览代码、模型与可复建的几何资料；原始 PDF / DWG、门牌信息、私人文档链接和装修业务资料不公开。

## 预览与构建

需要 Node.js 20 或更高版本：

```sh
npm ci
npm run build
python3 -m http.server 8080
```

打开 `http://localhost:8080`。此网络版本通过 HTTP 按所选宽度加载对应 GLB，请不要直接双击 `index.html`。

- `app.js` / `template.html`：交互与页面源代码。
- `build.mjs`：构建脚本；生成 `index.html` 和 `app.bundle.js`。
- `home-model.glb` / `home-model-600.glb` / `home-model-800.glb`：700 / 600 / 800 mm 完整模型，每档约 16.3 MB，选择时按需加载并缓存。
- `kitchen_config.py` / `kitchen-options.json`：厨房参数化建模与前端档位表；`kitchen-options.test.js` 验证实际 GLB 尺寸、分门、间隙及对应通行图。
- `current-geometry.json`：CAD 提取的局部坐标图元，单位 mm。
- `build_model.py` / `model-data.json` / `union_walls.py`：Blender 建模代码与参数。
- `prepare_assets.py`：重新生成程序木纹和地板数据。
- `verify_geometry.py` / `geometry-checks.json`：模型几何检查及静态净距记录。
- `THREE-LICENSE.txt`：Three.js 0.170.0 及随附插件的 MIT 许可。

## 重建模型

使用 Blender 4.5 与一个安装了 `requirements.txt` 的 Python 环境。保留已提供的 `model-data.json` 可按本版参数重建；`prepare_assets.py` 用于需要重做基础地板与木纹的情况。

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# 700 mm 默认档
MODEL_PYTHON="$PWD/.venv/bin/python" blender -b --python build_model.py
.venv/bin/python verify_geometry.py
.venv/bin/python build_navigation.py
# 600 / 800 mm 配置档
for width in 600 800; do
  FRIDGE_WIDTH_MM="$width" MODEL_FILENAME="home-model-$width.glb" MODEL_PYTHON="$PWD/.venv/bin/python" blender -b --python build_model.py
  .venv/bin/python verify_geometry.py --model "home-model-$width.glb" --output "geometry-checks-$width.json"
  .venv/bin/python build_navigation.py --model "home-model-$width.glb" --output "navigation-$width.json"
done
python3 build_entry_elevation.py
npm test
npm run build
```

会生成 `home-model.glb` 和 `generated/` 中的 Blender 文件及渲染图。默认生成 11 张渲染（另有手工桌与储物柜专用镜头），耗时比网页构建长。

## 第一人称漫游

点击右上角“进入漫游”，从入户以 1.60 m 视高开始。WASD 行走，鼠标拖动转头，方向键也可转头；支持 Pointer Lock 的浏览器另显示“鼠标自由转头”。Esc 暂停，点击继续恢复；切出页面或窗口失焦会暂停并清除按键。手机支持屏幕方向按钮和拖动转头。可快速定位九个房间、回到入户，退出后恢复原来的视角与图层。

默认勾选“穿透物品”：忽略家具、柜体及门板，保留墙体、窗与砌筑包管边界。关闭后恢复完整家具碰撞；如果正在家具内部，自动移动到最近可站位置。两套通行图都从当前 GLB 投影生成，人体半径 0.20 m，网格 4 cm。穿透模式下可从入户进入厨房；完整碰撞模式仍受餐椅摆放影响。固定视高，不模拟楼梯、蹲跳。

- `walkthrough.js`：输入、转头、暂停与模式切换。
- `navigation.js` / `navigation.test.js`：移动及防穿越检查；`npm test` 运行。
- `build_navigation.py` / `navigation*.json`：从各档 GLB 重建通行图。更换模型后必须重建；网页构建会校验模型 SHA-256，拒绝使用过期通行图。
- [Pointer Lock API 说明](https://developer.mozilla.org/en-US/docs/Web/API/Element/requestPointerLock)：通过用户点击启用，不支持时使用拖动转头。

## GitHub Pages

将本目录所有发布文件提交到仓库根目录。在 Settings → Pages 中选 Deploy from a branch、main、/(root)。后续修改源代码后运行 `npm ci && npm run build`，将源文件与生成的 `index.html` / `app.bundle.js` 一起提交，即可更新页面。纯静态站点，无后台、无 CDN 依赖、无付费服务。

## 玄关通顶分区

[查看五段分区与尺寸图](entry-zones.svg)。柜体深 420 mm，门板与把手另占约 46 mm；柜体含 20 mm 顶封板总高 2400 mm，上方 320 mm 局部吊顶接至假定 2720 mm 原顶。按入户向餐桌依次分为 600 mm 日常鞋、600 mm 归家随手位、620 mm 长靴雨伞、650 mm 通勤备品和 760 mm 餐边区。餐边收纳与鞋包分隔；下部移门避免侵占通道，浅抽屉与其他柜门开启时仍占用操作空间。

高度尺度参考 [IKEA PAX 236 cm 成品高柜](https://www.ikea.cn/cn/zh/p/pax-pa-ke-si-yi-gui-kuang-jia-bai-se-40355112/)，本方案取 2400 mm 定制高度，并非鞋柜统一标准。

`entry-storage.json` 为分区参数；`build_entry_elevation.py` 生成对应立面示意 `entry-zones.svg`。

## 客厅电视与支架

65 英寸指有效屏幕对角线；按 16:9 建模，屏幕约 1439 × 809 mm。电视对齐沙发中线，屏幕中心高 1120 mm；取消原电视柜，使用黑色立柱与 540 × 820 mm 的扁平落地底座。原回音壁放到支架连接的小托盘，线缆沿立柱背面走线。增加“65英寸落地电视”专用视角。v6 按业主要求取消客厅茶几及对应碰撞。

支架与边框为概念造型，不对应具体品牌；落地底座单独计入漫游碰撞范围。最终承重、VESA 接口与安装高度按实际电视和支架选型确认。

## v7 布局与管道

- 原家政高柜改为 1280 × 560 mm 手工桌，桌面高 750 mm，上方小吊柜深 280 mm、底高 1550 mm；缝纫机移到此处，台下有收起圆凳。
- 厨房水槽龙头按 CAD 位于餐厅侧的角部，面对厨房操作面。扫地机转移到窗下橱柜，基站按既有选型资料的 450 × 381 × 249 mm 外形建模；洞口净宽 430 mm、高约 315 mm，另设上方检修门。实际接头、检修及前方行走路径需以设备安装说明复核。
- 储物位 CAD 西侧双门线位于 x=6380 / 6420 mm、y=4320..5170 mm；北侧至 y=5170 mm、东侧至 x=7910 mm，围合外包范围 1530 × 850 mm，东南角有原结构凸出。原模型并非整个储藏位变窄，而是架子放在最深处且缺门。本版补两扇柜门，层板沿长边改为 1390 × 320 mm；打开柜内查看可检视。
- 下侧工位只留笔记本，上侧保留显示器；CAD 黄色位置改为暖白装饰隔断，中央透光窗、木饰收口，高 2400 mm 为概念立面。
- `Services` 为烟道和供排水模型；`ServiceEnclosures` 为日常可见包管。显示区与漫游工具栏均有高亮开关，橙色排烟、绿色排水 / 通气、蓝色供水，禁用深度测试实现透视。关闭时恢复原材质。
- 管井位置依据平面符号；管径、立管分工、接入高度、支管走向及楼板内空间均为示意，未取得施工水电图。保留检修、排水坡度、止回与防漏条件供深化确认。

## 方案边界

尺寸对应概念模型的静态摆放，不能替代复尺与施工图。完成面预留 100 mm、净高 2720 mm 均为当前建模假设；柜门及家电开启、设备检修和产品容量需继续核对。原水槽下四设备专项未整体合入；本版机器人独立改至窗下柜，水槽下的净水、软水等设备需另行协调，不能当作统一定稿。

模型图元及页面仅用于本项目的方案讨论。第三方库按各自许可证使用。

## v8 厨房高柜与冰箱配色

冰箱旁原窄抽屉柜及钢台面改为 2400 mm 高柜，柜体宽 230 mm、深 340 mm（门板把手另计），上下分区、可调层板；后方包管保留。新增专用视角。冰箱改为参考东芝大白桃的富士白玻璃面板及银色把手，颜色为近似表现；保留原模型外形与占位，并未替换为厂家精确型号。配色来源：[美的集团官方商城大白桃 GR-RM479WE-PG1B3](https://www.midea.cn/1/1000000000400692349824.html)。

## v9.1 法式冰箱与宽度配置

左侧“冰箱宽度”可选三档，默认 700 mm，浏览器会记住最近一次成功选择。600 mm 上部为一扇整宽冷藏门（单侧把手），700 / 800 mm 上部为两扇冷藏门；下部均为两层整宽冷冻抽屉；延续富士白近似配色和银色把手。切换后保留当前视角与显示选项，导出的 GLB 和漫游通行图同步切换；进入漫游后先退出再修改尺寸。下载失败可重试，有已加载模型时保留原档。

| 冰箱宽度 | 旁侧高柜宽度 | 扫地机柜宽度 |
| --- | --- | --- |
| 600 mm | 230 mm | 740 mm |
| 700 mm | 230 mm | 640 mm |
| 800 mm | 230 mm | 540 mm |

三档共用 CAD 上 1600 mm 的布置区段。冰箱高 1910 mm、箱体深 600 mm；高柜高 2400 mm、深 340 mm。以 700 mm 档为基准，600 / 800 mm 档将窗侧扫地机柜加宽 / 收窄 100 mm，设备及示意支管相应移动 50 mm；左侧高柜位置和宽度固定，430 mm 机器人洞口与基站尺寸保持不变。各档分别重建板件、台面、门板与把手，不缩放设备或固定包管。

冰箱两侧现为 10 / 20 mm 概念间隙。三档用于空间比较，并非某一款东芝产品的可选尺寸；实际散热、开门、抽屉拉出和检修余量应按最终型号深化。

## v9.2 维丁格白色橱柜

厨房原木色柜门、抽屉面、柜体与外露封板统一改为无木纹的柔和白色漆面，参考 [IKEA VEDDINGE 维丁格官方白色柜门](https://www.ikea.cn/cn/zh/p/veddinge-door-white-70274440/)（货号 702.744.40，平滑漆面）。三档冰箱模型均同步；左侧高柜固定、靠窗柜联动的尺寸逻辑不变。保留金属把手、不锈钢台面、冰箱配色和厨房外家具木色。

建模材质 sRGB `#F2F1EC`、粗糙度 0.48、非金属，为官方图片的视觉近似，并非厂家色号或实物校色结果。

## v10 阳台四列外开封窗

按业主提供的立面图：700 / 1600 / 1600 / 700 mm 四列；F1/F2 中央通高固定玻璃，两侧 A1/A2 上部 1300 mm 外开扇、F3/F4 下部 1000 mm 固定玻璃。采用浅灰铝框，两扇按外侧立边为铰轴向室外平开 35°，为静态开启展示。图示 4600×2300 mm；保留 CAD 现有约 4560 mm 宽洞口，横向按比例适配，高度取 2300 mm（底标高 30 mm），上方补收口。两侧纱帘收拢以看清窗扇。洗烘侧窄窗及阳台侧高窗保留原状。

`balcony_window.py` 为可复建几何；新增“阳台四列外开窗”视角。图中 8mm+8mm 标记仅作玻璃示意记录，未据此推断空气层或产品构造；模型不代替门窗复尺深化。

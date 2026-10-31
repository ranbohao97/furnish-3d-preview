# 全屋三维预览 v5

[打开在线预览](https://ranbohao97.github.io/furnish-3d-preview/)

交互式全屋概念模型：厨房无吊柜、CAD 三角洗手台、3230 mm 玄关通顶柜（2470 mm 玄关收纳 + 760 mm 餐边区），以及按用途调整的柜内分区。客厅采用 65 英寸电视与落地支架，取消电视柜。支持 WASD 第一人称漫游、12 个视角、剖切墙体、CAD 叠合、柜内查看、动线净距、截图与 GLB 下载。

本仓库仅包含预览代码、模型与可复建的几何资料；原始 PDF / DWG、门牌信息、私人文档链接和装修业务资料不公开。

## 预览与构建

需要 Node.js 20 或更高版本：

```sh
npm ci
npm run build
python3 -m http.server 8080
```

打开 `http://localhost:8080`。此网络版本通过 HTTP 加载 `home-model.glb`，请不要直接双击 `index.html`。

- `app.js` / `template.html`：交互与页面源代码。
- `build.mjs`：构建脚本；生成 `index.html` 和 `app.bundle.js`。
- `home-model.glb`：完整模型，大小与网格数量见 `geometry-checks.json`；移动网络首次加载可能较慢。
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
MODEL_PYTHON="$PWD/.venv/bin/python" blender -b --python build_model.py
.venv/bin/python verify_geometry.py
.venv/bin/python build_navigation.py
python3 build_entry_elevation.py
npm test
npm run build
```

会生成 `home-model.glb` 和 `generated/` 中的 Blender 文件及渲染图。默认生成 11 张渲染，耗时比网页构建长。

## 第一人称漫游

点击右上角“进入漫游”，从入户以 1.60 m 视高开始。WASD 行走，鼠标拖动转头，方向键也可转头；支持 Pointer Lock 的浏览器另显示“鼠标自由转头”。Esc 暂停，点击继续恢复；切出页面或窗口失焦会暂停并清除按键。手机支持屏幕方向按钮和拖动转头。可快速定位九个房间、回到入户，退出后恢复原来的视角与图层。

碰撞依据当前 GLB 中墙体、柜体、家具等网格的平面投影生成（数量见 `navigation.json`），保留凹墙轮廓；人体半径取 0.20 m，4 cm 网格另留半格对角线裕量。行走高度固定，不模拟楼梯、蹲跳或开门。餐椅当前占位让厨房入口较窄，保守碰撞下不与入户连通，可用房间菜单进入厨房；入户至客厅、卧室、主卫、工位与阳台连通。

- `walkthrough.js`：输入、转头、暂停与模式切换。
- `navigation.js` / `navigation.test.js`：移动及防穿越检查；`npm test` 运行。
- `build_navigation.py` / `navigation.json`：从 GLB 重建通行图。更换模型后必须重建；网页构建会校验模型 SHA-256，拒绝使用过期通行图。
- [Pointer Lock API 说明](https://developer.mozilla.org/en-US/docs/Web/API/Element/requestPointerLock)：通过用户点击启用，不支持时使用拖动转头。

## GitHub Pages

将本目录所有发布文件提交到仓库根目录。在 Settings → Pages 中选 Deploy from a branch、main、/(root)。后续修改源代码后运行 `npm ci && npm run build`，将源文件与生成的 `index.html` / `app.bundle.js` 一起提交，即可更新页面。纯静态站点，无后台、无 CDN 依赖、无付费服务。

## 玄关通顶分区

[查看五段分区与尺寸图](entry-zones.svg)。柜体深 420 mm，门板与把手另占约 46 mm；柜体含 20 mm 顶封板总高 2400 mm，上方 320 mm 局部吊顶接至假定 2720 mm 原顶。按入户向餐桌依次分为 600 mm 日常鞋、600 mm 归家随手位、620 mm 长靴雨伞、650 mm 通勤备品和 760 mm 餐边区。餐边收纳与鞋包分隔；下部移门避免侵占通道，浅抽屉与其他柜门开启时仍占用操作空间。

高度尺度参考 [IKEA PAX 236 cm 成品高柜](https://www.ikea.cn/cn/zh/p/pax-pa-ke-si-yi-gui-kuang-jia-bai-se-40355112/)，本方案取 2400 mm 定制高度，并非鞋柜统一标准。

`entry-storage.json` 为分区参数；`build_entry_elevation.py` 生成对应立面示意 `entry-zones.svg`。

## 客厅电视与支架

65 英寸指有效屏幕对角线；按 16:9 建模，屏幕约 1439 × 809 mm。电视对齐沙发中线，屏幕中心高 1120 mm；取消原电视柜，使用黑色立柱与 540 × 820 mm 的扁平落地底座。原回音壁放到支架连接的小托盘，线缆沿立柱背面走线。增加“65英寸落地电视”专用视角。

支架与边框为概念造型，不对应具体品牌；落地底座单独计入漫游碰撞范围。最终承重、VESA 接口与安装高度按实际电视和支架选型确认。

## 方案边界

尺寸对应概念模型的静态摆放，不能替代复尺与施工图。完成面预留 100 mm、净高 2720 mm 均为当前建模假设；柜门及家电开启、设备检修和产品容量需继续核对。同日水槽下四设备专项尚未合入本模型的水槽分柜与机器人位置，不能当作统一定稿。

模型图元及页面仅用于本项目的方案讨论。第三方库按各自许可证使用。

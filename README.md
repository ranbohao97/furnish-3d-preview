# 全屋三维预览 v2

交互式全屋概念模型：厨房无吊柜、CAD 三角洗手台、低鞋柜与换鞋凳，以及按用途调整的柜内分区。支持 11 个视角、剖切墙体、CAD 叠合、柜内查看、动线净距、截图与 GLB 下载。

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
- `home-model.glb`：完整模型，约 15 MB，2168 个网格；移动网络首次加载可能较慢。
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
npm run build
```

会生成 `home-model.glb` 和 `generated/` 中的 Blender 文件及渲染图。默认生成 9 张渲染，耗时比网页构建长。

## GitHub Pages

将本目录所有发布文件提交到仓库根目录。在 Settings → Pages 中选 Deploy from a branch、main、/(root)。后续修改源代码后运行 `npm ci && npm run build`，将源文件与生成的 `index.html` / `app.bundle.js` 一起提交，即可更新页面。纯静态站点，无后台、无 CDN 依赖、无付费服务。

## 方案边界

尺寸对应概念模型的静态摆放，不能替代复尺与施工图。完成面预留 100 mm、净高 2720 mm 均为当前建模假设；柜门及家电开启、设备检修和产品容量需继续核对。同日水槽下四设备专项尚未合入本模型的水槽分柜与机器人位置，不能当作统一定稿。

模型图元及页面仅用于本项目的方案讨论。第三方库按各自许可证使用。

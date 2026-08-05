# 桌面版 App 的运维细节

> 主文件「环境与 daemon → 3. 桌面版 App」的展开。只在真的碰到这些症状时读。

#### 客户报「打开应用看不到项目了，只能重启」

这是桌面版的已知形态，不是数据丢失。根因是 **UI 与 daemon 是独立进程**：daemon 挂掉或换端口后 UI 仍然活着，于是界面能打开、项目列表却空白（代理还在往已死的旧端口转发，返回 `ECONNREFUSED`）。

诊断与处置：

1. 先按上面的命令探测是否还有活着的 daemon API；没有就是 daemon 掉了。
2. 数据都在磁盘上，**重启 App 即可**，不要试图修复或迁移数据。
3. 检查 `<data>/projects/` 下有没有 0 字节的孤儿目录——那是 daemon 在建项目途中崩溃的残骸
   （目录建了、`app.sqlite` 没写入）。确认为空后可以删。
4. 日志在 `<namespace>/logs/{daemon,desktop,launcher}/`；`launcher/after-quit.log` 反复出现
   `desktop.sock ENOENT` 属于正常的启动时序，不是故障根因。

**因此：任何要长期留存的设计资产都必须有一份在客户自己的 git 仓库里**，桌面版目录只当镜像。

#### 桌面版的项目元数据（HTTP API 之外的必修课）

`app.sqlite` 的 `projects` 表**没有文件清单、也没有 `entryFile` 字段**——文件从磁盘扫描，
而 `entryFile` 埋在 `metadata_json` 里：

```json
{"kind":"prototype","entryFile":"index.html","skipDiscoveryBrief":true}
```

由此产生两个反复踩到的坑：

- `PATCH /api/projects/:id` 传 `{"entryFile":"..."}` 会返回 200，但**不会写进 metadata_json**，
  项目卡片仍是空白预览。
- 直接把文件 `rsync`/`cp` 进项目目录后，卡片同样空白——因为没有 `entryFile` 指明渲染哪个文件。

正确做法：`POST /api/projects` 建项目（`{"id","name"}`，id 必填），把文件放进
`resolvedDir`（`GET /api/projects/:id` 会返回），为每个可渲染文件补一份
`<file>.artifact.json`（照同目录已有产物的格式：`version/kind/title/entry/renderer/status/exports`），
最后确认 `metadata_json.entryFile` 指向入口文件。**改 `app.sqlite` 前先备份，并且只在 App 未在写入时改；改完需要重启 App 才会重新读取。**

#### 删除本地插件要删三处

`DELETE /api/plugins/<id>` 这个路由**不存在**（返回 404）。桌面版跑复刻类
workflow 会在项目内生成本地插件（`sourceKind: local`），删它必须同时清三处，
少一处界面就还显示：

1. 项目内的产物：`<data>/projects/<projectId>/plugin-source/<pluginId>/`
2. 插件安装目录：`<data>/plugins/<pluginId>/`
3. 注册记录：`app.sqlite` 的 `installed_plugins` 表（改前先备份）

删完仍会显示是 daemon 的内存缓存，**重启 App 才消失**。

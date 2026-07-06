# GitHub Release 数据同步设计

## 目标

把 Android 每日数据更新流程，从“手动传 zip、手动导入”改成更稳定的 Release 同步流程：

1. 电脑端生成每日数据更新包。
2. 电脑端把数据包发布到 `635389202/Sequoia-X-app` 的 GitHub Release。
3. Android APP 在数据页检查最新 Release，并一键下载导入。
4. 飞书或企业微信类通知只发送摘要和链接，不负责传输文件。

当前仓库和 Release 资产按公开方式处理。Release 包里不能包含账号凭据、token 或其他不应公开的信息。

## 范围

包含：

- 发布每日增量 zip 到 GitHub Release。
- 生成可机器读取的 `manifest.json`。
- APP 增加检查更新和一键导入 GitHub Release 数据包。
- 保留现有本地文件导入作为备用方式。
- 可选增加飞书通知，通知里包含 Release 链接和更新摘要。
- 后续代码更新继续推送到用户 fork 远端 `fork`。

不包含：

- 自动操作个人微信客户端传文件。
- Android 后台无感定时下载。
- APP 内接入私有 GitHub Release 鉴权。
- 应用商店签名或正式上架流程。

## Release 结构

每日数据 Release 使用：

- 仓库：`635389202/Sequoia-X-app`
- 标签：`data-YYYY-MM-DD`
- 标题：`Sequoia-X Data YYYY-MM-DD`
- 资产：
  - `manifest.json`
  - `sequoia_app_delta_YYYY-MM-DD.zip`
  - 可选首次使用全量包：`sequoia_app_data_latest.zip`

`manifest.json` 格式：

```json
{
  "schema_version": 1,
  "date": "2026-07-06",
  "package_type": "delta",
  "requires_full_package": true,
  "delta_asset": "sequoia_app_delta_2026-07-06.zip",
  "full_asset": "sequoia_app_data_latest.zip",
  "sha256": {
    "sequoia_app_delta_2026-07-06.zip": "...",
    "sequoia_app_data_latest.zip": "..."
  },
  "candidate_count": 110,
  "generated_at": "2026-07-06T19:15:00+08:00"
}
```

## 电脑端发布器

新增脚本，例如 `publish_daily_release.py`，负责完整发布流程：

1. 更新今日行情数据。
2. 执行策略并生成选股结果。
3. 导出 Android 增量包。
4. 生成带 SHA-256 校验值的 `manifest.json`。
5. 创建或更新 `data-YYYY-MM-DD` 对应的 GitHub Release。
6. 上传或替换 Release 资产。
7. 输出发布摘要和 Release 链接。

鉴权优先使用本机已有 GitHub 凭据，或读取 `GITHUB_TOKEN` 环境变量。token 不能写入导出包、日志或文档。

## Android 同步流程

数据页增加第二种导入路径：

- 现有：导入本地数据包。
- 新增：检查 GitHub 更新。

APP 流程：

1. 请求 GitHub 最新 Release 元数据。
2. 下载 `manifest.json`。
3. 对比 manifest 日期和本地最新导入日期。
4. 如果本地没有全量数据，且 manifest 要求全量包，则下载全量包。
5. 否则下载增量包。
6. 导入前校验 SHA-256。
7. 通过现有 zip importer 的事务导入数据库。
8. 在数据页显示成功或失败信息。

网络更新失败时，本地文件导入仍应可用。

## 错误处理

电脑端发布器：

- 数据更新失败：停止发布。
- 数据包导出失败：停止发布。
- Release 已存在：只有在新文件校验值生成成功后，才替换资产。
- 上传失败：保留 `exports/app` 里的本地数据包，并输出可重试命令。

Android APP：

- 无网络：在数据页提示，并保留当前已有数据。
- 最新 Release 缺少 manifest：提示 Release 格式不支持。
- SHA-256 不匹配：删除下载文件，不执行导入。
- 本地没有全量数据但只拿到增量包：提示先导入或下载全量包。
- 导入失败：沿用现有事务回滚机制，避免污染本地数据库。

## 通知策略

飞书适合做通知，不适合承担数据传输。每日通知可以包含：

- 日期。
- 候选数量。
- 主要策略名称。
- GitHub Release 链接。
- APP 操作提示：打开数据页并点击更新。

不建议自动操作个人微信客户端，因为它依赖 GUI 登录状态、窗口焦点和安全确认。需要微信生态通知时，优先考虑企业微信机器人、ServerChan 或 PushPlus 这类 webhook 服务。

## 测试

电脑端：

- 单元测试 manifest 生成和 checksum 计算。
- 单元测试 Release 资产命名。
- dry-run 模式：只生成包和 manifest，不上传。

Android：

- 单元测试 manifest 解析。
- 单元测试更新决策：全量、增量、已经最新。
- 单元测试 checksum 不匹配时拒绝导入。
- 保留现有 importer 测试，继续验证数据库写入。

手动验证：

- 发布一个测试 Release 到 fork。
- 安装 debug APK。
- 在数据页触发 GitHub 更新。
- 确认最新日期、候选数量和列表内容更新正确。

## 已定决策

- Release 发布优先使用 Python 标准库加 `requests`，不强依赖 `gh` CLI，因为当前机器没有安装 `gh`。
- 第一版 APP 同步需要用户手动点击。等手动路径稳定后，再考虑后台自动检查更新。

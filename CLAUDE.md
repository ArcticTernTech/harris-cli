# Harris CLI — 环境配置文档

## 项目概览

harris-cli 是 Harris 电商运营平台的命令行工具，供运营人员和 AI Agent 使用。
公开仓库（**注意：不要在此仓库提交任何敏感信息**）。

相关仓库：
- **harris-backend**：FastAPI 后端 API（私有仓库）→ 完整环境配置见该仓库的 `CLAUDE.md`
- **homebrew-tools**：Homebrew 分发仓库，由 CI/CD 自动更新

---

## 后端连接配置

harris-cli 通过 `~/.config/harris/config.json` 存储登录态和后端地址。

| 环境 | 后端地址 |
|---|---|
| 开发 | `https://dev.rovestep.com` |
| 生产 | `https://api.rovestep.com` |

切换环境：
```bash
harris config set-url https://api.rovestep.com   # 切换到生产
harris config set-url https://dev.rovestep.com   # 切换到开发
```

---

## AI Agent 使用说明

```bash
# 开启 JSON 输出模式（AI Agent 必须设置）
export HARRIS_FORMAT=json

# 获取当前用户上下文（账号列表、角色）
harris context

# 平台参数可选，有歧义时返回结构化错误
harris orders list --store rovestep              # 单平台自动识别
harris orders list --store rovestep --platform coupang  # 多平台时指定

# 错误类型
# {"error": "platform_ambiguous", "platforms": [...]}  → 需要指定 --platform
# {"error": "store_not_found", "available_stores": [...]}  → 店铺名不存在
```

---

## 发布流程

```bash
# 打 tag 触发 GitHub Actions 自动构建 + 更新 Homebrew
git tag v0.x.0 && git push origin v0.x.0
```

CI/CD 会自动：
1. 构建 macOS ARM64 二进制
2. 更新 homebrew-tools 仓库的 Formula
3. 用户通过 `brew upgrade harris-cli` 更新

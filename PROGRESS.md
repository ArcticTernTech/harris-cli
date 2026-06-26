# harris-cli 开发进度

跨境电商多平台运营 CLI 工具，当前支持 Amazon SP-API。

---

## 架构

```
harris/
├── main.py              # 命令注册入口
├── config.py            # ~/.harris/config.toml 读写
├── output.py            # 统一输出：终端表格 / CSV / JSON
├── logger.py            # 日志，写入 ~/.harris/logs/harris.log
├── cli/
│   ├── auth.py          # harris auth —— 账号管理 + OAuth
│   ├── orders.py        # harris orders —— 订单查询
│   ├── inventory.py     # harris inventory —— FBA 库存
│   ├── listings.py      # harris listings —— Listing 管理
│   ├── pricing.py       # harris pricing —— 定价管理
│   └── reports.py       # harris reports —— 报表下载
└── platforms/
    ├── base.py          # 统一数据类型 + 抽象接口
    └── amazon.py        # Amazon SP-API 适配器
```

---

## 命令速查

### auth — 账号管理

```bash
harris auth setup --account store_us_1          # 交互式配置凭证
harris auth token --account store_us_1          # 浏览器 OAuth 获取 Refresh Token
harris auth list                                 # 列出所有账号
harris auth verify --account store_us_1         # 验证连通性
harris auth remove --account store_us_1         # 删除账号
```

### orders — 订单

```bash
harris orders list                               # 所有账号最近 7 天
harris orders list --account store_us_1 --days 30
harris orders list --status unshipped            # 待发货
harris orders list --output orders.csv           # 导出 CSV
harris orders list --output orders.json          # 导出 JSON
harris orders get 114-1234567-8901234 --account store_us_1
```

### inventory — FBA 库存

```bash
harris inventory list                            # 所有账号
harris inventory list --low 20                   # 低于 20 件
harris inventory list --output inventory.csv
harris inventory alert --threshold 30            # 补货预警
```

### listings — Listing 管理

```bash
harris listings list --account store_us_1
harris listings list --account all --status inactive
harris listings list --output listings.csv
```

### pricing — 定价管理

```bash
harris pricing get --sku SKU001 --account store_us_1
harris pricing update --sku SKU001 --price 29.99 --account store_us_1
harris pricing bulk --file prices.csv --account store_us_1
harris pricing bulk --file prices.csv --account store_us_1 --dry-run
```

### reports — 报表

```bash
# 支持类型: settlement / business / inventory / fba_inv / orders / returns
harris reports request --type settlement --start 2026-05-01 --end 2026-05-31 --account store_us_1
harris reports status --report-id XXXXXXXX --account store_us_1
harris reports download --report-id XXXXXXXX --account store_us_1 --output report.csv
```

---

## 配置文件

位置：`~/.harris/config.toml`

```toml
[accounts.store_us_1]
platform = "amazon"
marketplace = "US"
client_id = "amzn1.application-..."
client_secret = "..."
refresh_token = "..."
aws_access_key = "AKIA..."
aws_secret_key = "..."
role_arn = ""          # 可选
```

---

## 安装

```bash
cd harris-cli
pip install -e .
```

---

## 完善记录

### v0.1 — 初始版本
- Amazon SP-API 基础接入（Orders + Inventory）
- 多账号配置管理（`~/.harris/config.toml`）
- `auth setup / list / verify / remove`
- `orders list / get`
- `inventory list / alert`

### v0.2 — 功能完善（当前）

| 模块 | 改进内容 |
|---|---|
| **平台层** | 修复分页（NextToken 翻页），添加限流重试（429 指数退避） |
| **输出格式** | 所有列表命令支持 `--output file.csv / file.json` 导出 |
| **auth token** | 浏览器 OAuth 自动获取 Refresh Token，本地 9090 端口接收回调 |
| **日志** | `~/.harris/logs/harris.log`，RotatingFileHandler，5MB 滚动 |
| **listings** | `harris listings list` 查看 Listing 状态和价格 |
| **pricing** | `harris pricing get/update/bulk` 单个和批量改价 |
| **reports** | `harris reports request/status/download` 异步报表下载 |

---

### v0.3 — 多用户 + 权限管理（进行中）

架构从 `CLI → Amazon` 变为 `CLI → harris-backend → Amazon`。

#### harris-backend（新项目）

位置：`/Users/tandy/Documents/Development/Workspace/harris-backend/`

| 组件 | 内容 |
|---|---|
| 框架 | FastAPI + SQLAlchemy + PostgreSQL |
| 鉴权 | JWT（access token 2h + refresh token 7d） |
| 密码 | bcrypt |
| 凭证加密 | Fernet 对称加密，密钥存 `.env` |
| 权限模型 | RBAC 四角色 + 账号级别授权 |
| 审计 | 所有操作写 audit_logs 表 |

**角色权限：**

| 角色 | 权限 |
|---|---|
| viewer | 查看订单、库存 |
| operator | + 查看 Listing |
| manager | + 改价、下载报表 |
| admin | 全部 + 管理用户和账号 |

**数据库表：** users、platform_accounts、user_accounts、audit_logs

**启动方式：**
```bash
cd harris-backend
docker-compose up -d     # 启动 PostgreSQL
cp .env.example .env     # 配置密钥
pip install -e .
harris-server            # 启动服务（默认 :8000）
```

#### harris-cli 改造

| 新增命令 | 说明 |
|---|---|
| `harris login` | 用户名/密码登录，JWT 存 ~/.harris/session.json |
| `harris logout` | 删除本地 session |
| `harris whoami` | 显示当前登录用户和角色 |
| `harris admin user list/add/set-role/disable` | 用户管理（admin） |
| `harris admin user grant/revoke` | 账号授权（admin） |
| `harris admin account list/add/remove` | 平台账号管理（admin） |
| `harris admin logs` | 审计日志查询（admin） |

所有业务命令（orders/inventory/listings/pricing/reports）不再直连 Amazon，改为调用后端 API。

---

## 待办

- [ ] 账号健康度（Account Health）真实数据接入
- [ ] Coupang WING API 适配器
- [ ] Walmart Marketplace API 适配器
- [ ] FBA 入库货件（Inbound Shipments）
- [ ] 单元测试
- [ ] 跨平台库存联动

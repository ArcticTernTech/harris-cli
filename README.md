# Harris CLI

跨境电商运营工具，支持 Amazon 多账号统一管理——查订单、看库存、改价格、下报表，一条命令搞定。

---

## 安装

### 前置条件：安装 Homebrew

打开终端（Spotlight 搜索「终端」），粘贴以下命令并回车：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

> 安装过程会提示输入 Mac 开机密码，输入时屏幕不显示字符属于正常现象。

### 安装 Harris CLI

```bash
brew tap ArcticTernTech/tools
brew install harris-cli
```

### 升级

```bash
brew upgrade harris-cli
```

---

## 登录

```bash
harris login
```

会自动打开浏览器，用飞书账号授权后即完成登录。

```bash
harris whoami    # 查看当前登录账号
harris logout    # 退出登录
```

---

## 命令速查

```
harris
├── login / logout / whoami      账号管理
├── orders                       订单
│   ├── list                     列出订单
│   └── get <订单号>              查看单个订单
├── inventory                    库存
│   ├── list                     查看 FBA 库存
│   └── alert                    显示需要补货的 SKU
├── listings                     Listing
│   └── list                     查看 Listing 列表
├── pricing                      定价
│   ├── get                      查看当前价格
│   ├── update                   修改单个价格
│   └── bulk                     从 CSV 批量改价
├── reports                      报表
│   ├── request                  请求生成报表
│   ├── status                   查询报表状态
│   └── download                 下载报表内容
└── admin                        管理员功能
    ├── user list/add/...        用户管理
    ├── account list/add/...     店铺账号管理
    └── logs                     操作日志
```

每个命令加 `--help` 可查看详细说明：

```bash
harris orders list --help
```

---

## 订单管理

### 查看最近订单

```bash
# 默认查最近 7 天
harris orders list --account store_us_1

# 查最近 30 天
harris orders list --account store_us_1 --days 30

# 只看待发货订单
harris orders list --account store_us_1 --status Unshipped

# 导出为 CSV
harris orders list --account store_us_1 --days 30 --output orders.csv
```

### 查看单个订单

```bash
harris orders get 114-1234567-1234567 --account store_us_1
```

---

## 库存管理

### 查看 FBA 库存

```bash
harris inventory list --account store_us_1

# 查指定 SKU
harris inventory list --account store_us_1 --sku MY-SKU-001

# 导出 CSV
harris inventory list --account store_us_1 --output inventory.csv
```

### 低库存预警

```bash
# 显示库存低于 20 件的 SKU（默认阈值）
harris inventory alert --account store_us_1

# 自定义阈值
harris inventory alert --account store_us_1 --threshold 50
```

---

## Listing 管理

```bash
# 查看所有 Listing
harris listings list --account store_us_1

# 只看在售
harris listings list --account store_us_1 --status active

# 查指定 SKU
harris listings list --account store_us_1 --sku MY-SKU-001

# 导出
harris listings list --account store_us_1 --output listings.csv
```

---

## 定价管理

### 查看价格

```bash
harris pricing get --account store_us_1 --sku MY-SKU-001
```

### 修改单个价格

```bash
harris pricing update --account store_us_1 --sku MY-SKU-001 --price 29.99
```

### 批量改价（CSV 文件）

CSV 格式（第一行为表头）：

```
sku,price
MY-SKU-001,29.99
MY-SKU-002,49.99
MY-SKU-003,19.99
```

```bash
# 先预演，不实际提交
harris pricing bulk --account store_us_1 --file prices.csv --dry-run

# 确认无误后正式提交
harris pricing bulk --account store_us_1 --file prices.csv
```

---

## 报表管理

报表类型：

| 简写 | 说明 |
|---|---|
| `settlement` | 结算报表 |
| `business` | 业务报告（销量/流量） |
| `inventory` | 库存报表 |
| `fba_inv` | FBA 库存报表 |
| `orders` | 订单报表 |
| `returns` | 退货报表 |

### 请求报表

```bash
harris reports request \
  --account store_us_1 \
  --type settlement \
  --start 2026-06-01 \
  --end 2026-06-30
```

> 命令会返回一个 Report ID，报表由亚马逊异步生成，通常需要几分钟到几十分钟。

### 查询进度

```bash
harris reports status --account store_us_1 --report-id REPORT_1234567890
```

状态说明：
- `IN_QUEUE` — 排队中
- `IN_PROGRESS` — 生成中
- `DONE` — 已完成，可下载
- `FATAL` — 生成失败

### 下载报表

```bash
# 自动等待完成后下载，保存为 CSV
harris reports download \
  --account store_us_1 \
  --report-id REPORT_1234567890 \
  --output settlement_june.csv
```

---

## 管理员功能

> 需要 `admin` 角色

### 用户管理

```bash
# 查看所有团队成员
harris admin user list

# 修改用户角色（viewer / operator / manager / admin）
harris admin user set-role --id 3 --role manager

# 禁用用户
harris admin user disable --id 3

# 授权用户访问某个店铺
harris admin user grant --id 3 --account store_us_1

# 撤销访问
harris admin user revoke --id 3 --account store_us_1
```

### 店铺账号管理

```bash
# 查看所有店铺账号
harris admin account list

# 添加 Amazon 账号
harris admin account add \
  --name store_us_1 \
  --marketplace US \
  --client-id amzn1.application-... \
  --client-secret ... \
  --refresh-token ... \
  --aws-key AKIA... \
  --aws-secret ...

# 删除账号
harris admin account remove --name store_us_1
```

### 操作日志

```bash
# 查看最近 50 条操作记录
harris admin logs

# 按用户筛选
harris admin logs --user zhangsan

# 按操作类型筛选
harris admin logs --action pricing

# 查看更多
harris admin logs --limit 200
```

---

## 权限说明

| 角色 | 可用功能 |
|---|---|
| `viewer` | 查看订单、库存 |
| `operator` | viewer + 查看 Listing |
| `manager` | operator + 改价格、请求/下载报表 |
| `admin` | 全部功能 + 管理用户和账号 |

---

## 常见问题

**提示「未登录」或「Token 已过期」**

重新登录即可：
```bash
harris login
```

**提示「无权限访问该账号」**

联系管理员，确认你的账号已被授权访问对应店铺。

**命令卡住没有响应**

检查网络连接。如果后端服务器地址有变化，可以通过以下方式指定：
```bash
harris login --server https://新地址
```

登录后地址会被记住，后续无需重复指定。

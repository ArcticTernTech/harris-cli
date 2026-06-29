import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from ..client import client

app = typer.Typer(help="管理员操作（需要 admin 角色）")
console = Console()

user_app = typer.Typer(help="用户管理")
account_app = typer.Typer(help="平台账号管理")
app.add_typer(user_app, name="user")
app.add_typer(account_app, name="account")

ROLE_CHOICES = ["viewer", "operator", "manager", "admin"]
MARKETPLACE_CHOICES = ["US", "CA", "MX", "UK", "DE", "FR", "JP", "AU", "SG", "AE"]


# ── 用户管理 ──

@user_app.command("list")
def list_users():
    """列出所有用户"""
    users = client.get("/admin/users")
    table = Table(title="团队成员")
    table.add_column("ID", style="dim")
    table.add_column("用户名", style="bold")
    table.add_column("邮箱", style="dim")
    table.add_column("角色", style="cyan")
    table.add_column("状态")
    for u in users:
        status = "[green]启用[/green]" if u["is_active"] else "[red]禁用[/red]"
        table.add_row(str(u["id"]), u["username"], u["email"], u["role"], status)
    console.print(table)


@user_app.command("add")
def add_user(
    username: str = typer.Option(..., "--username", "-u"),
    email: str = typer.Option(..., "--email", "-e"),
    password: str = typer.Option(..., "--password", "-p"),
    role: str = typer.Option("operator", "--role", "-r"),
):
    """添加团队成员"""
    user = client.post("/admin/users", {"username": username, "email": email, "password": password, "role": role})
    console.print(f"[green]用户 '{user['username']}' 创建成功，角色: {user['role']}[/green]")


@user_app.command("set-role")
def set_role(
    user_id: int = typer.Option(..., "--id"),
    role: str = typer.Option(..., "--role", "-r"),
):
    """修改用户角色"""
    user = client.patch(f"/admin/users/{user_id}", {"role": role})
    console.print(f"[green]{user['username']} 角色已更新为 {user['role']}[/green]")


@user_app.command("disable")
def disable_user(user_id: int = typer.Option(..., "--id")):
    """禁用用户"""
    client.patch(f"/admin/users/{user_id}", {"is_active": False})
    console.print("[green]用户已禁用[/green]")


@user_app.command("grant")
def grant_access(
    user_id: int = typer.Option(..., "--id", help="用户 ID"),
    platform: str = typer.Option(..., "--platform", "-p", help="平台: amazon / coupang / mock"),
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
):
    """授权用户访问某个账号"""
    client.post(f"/admin/users/{user_id}/accounts/{platform}/{store}", {})
    console.print(f"[green]已授权用户 {user_id} 访问 {platform}:{store}[/green]")


@user_app.command("revoke")
def revoke_access(
    user_id: int = typer.Option(..., "--id"),
    platform: str = typer.Option(..., "--platform", "-p", help="平台: amazon / coupang / mock"),
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
):
    """撤销用户对某个账号的访问"""
    client.delete(f"/admin/users/{user_id}/accounts/{platform}/{store}")
    console.print(f"[green]已撤销用户 {user_id} 对 {platform}:{store} 的访问[/green]")


# ── 平台账号管理 ──

@account_app.command("list")
def list_accounts():
    """列出所有平台账号"""
    accounts = client.get("/admin/accounts")
    table = Table(title="平台账号")
    table.add_column("店铺", style="bold cyan")
    table.add_column("平台")
    table.add_column("站点")
    table.add_column("创建时间", style="dim")
    for acc in accounts:
        table.add_row(acc["store"], acc["platform"], acc["marketplace"], acc["created_at"][:10])
    console.print(table)


@account_app.command("add")
def add_account(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    marketplace: str = typer.Option("US", "--marketplace", "-m"),
    client_id: str = typer.Option(..., "--client-id"),
    client_secret: str = typer.Option(..., "--client-secret"),
    refresh_token: str = typer.Option(..., "--refresh-token"),
    aws_access_key: str = typer.Option(..., "--aws-key"),
    aws_secret_key: str = typer.Option(..., "--aws-secret"),
    role_arn: str = typer.Option("", "--role-arn"),
):
    """添加 Amazon 平台账号（凭证加密存储在服务器）"""
    credentials = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "aws_access_key": aws_access_key,
        "aws_secret_key": aws_secret_key,
    }
    if role_arn:
        credentials["role_arn"] = role_arn
    acc = client.post("/admin/accounts", {
        "store": store,
        "platform": "amazon",
        "marketplace": marketplace,
        "credentials": credentials,
    })
    console.print(f"[green]Amazon 账号 '{acc['store']}' ({acc['marketplace']}) 已添加[/green]")


@account_app.command("add-mock")
def add_mock_account(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 test"),
):
    """添加 Mock 测试账号（本地开发用，返回假数据，不调用真实平台 API）"""
    acc = client.post("/admin/accounts", {
        "store": store,
        "platform": "mock",
        "marketplace": "MOCK",
        "credentials": {},
    })
    console.print(f"[green]Mock 账号 '{acc['store']}' 已添加，可用于开发测试[/green]")


@account_app.command("add-coupang")
def add_coupang_account(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    access_key: str = typer.Option(..., "--access-key", help="Coupang Open API Access Key"),
    secret_key: str = typer.Option(..., "--secret-key", help="Coupang Open API Secret Key"),
    vendor_id: str = typer.Option(..., "--vendor-id", help="Vendor ID，如 A00012345"),
    tz_offset: str = typer.Option("+09:00", "--tz", help="时区偏移，韩国 +09:00，台湾 +08:00"),
):
    """添加 Coupang 平台账号（凭证加密存储在服务器）"""
    credentials = {
        "access_key": access_key,
        "secret_key": secret_key,
        "vendor_id": vendor_id,
        "tz_offset": tz_offset,
    }
    acc = client.post("/admin/accounts", {
        "store": store,
        "platform": "coupang",
        "marketplace": "KR",
        "credentials": credentials,
    })
    console.print(f"[green]Coupang 账号 '{acc['store']}' 已添加[/green]")


@account_app.command("remove")
def remove_account(
    platform: str = typer.Option(..., "--platform", "-p", help="平台: amazon / coupang / mock"),
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
):
    """删除平台账号"""
    if not Confirm.ask(f"确认删除账号 '{platform}:{store}'？此操作不可恢复"):
        raise typer.Abort()
    client.delete(f"/admin/accounts/{platform}/{store}")
    console.print(f"[green]账号 '{platform}:{store}' 已删除[/green]")


# ── 审计日志 ──

@app.command("logs")
def audit_logs(
    username: str = typer.Option(None, "--user"),
    action: str = typer.Option(None, "--action"),
    limit: int = typer.Option(50, "--limit"),
):
    """查看操作审计日志"""
    logs = client.get("/audit-logs", username=username, action=action, limit=limit)
    table = Table(title="审计日志", show_lines=False)
    table.add_column("时间", style="dim")
    table.add_column("用户", style="cyan")
    table.add_column("操作", style="bold")
    table.add_column("账号", style="dim")
    table.add_column("状态")
    for log in logs:
        status_style = "green" if log["status"] == "success" else "red"
        table.add_row(
            log["created_at"][:16],
            log["username"],
            log["action"],
            log.get("account_name") or "-",
            f"[{status_style}]{log['status']}[/{status_style}]",
        )
    console.print(table)

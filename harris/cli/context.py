import json
import typer
from rich.console import Console
from rich.table import Table
from ..client import client
from ..config import is_json_mode

app = typer.Typer()
console = Console()


@app.command("context")
def get_context():
    """获取当前用户信息和授权账号列表（AI Agent 初始化上下文专用）。

    返回当前登录用户、角色及所有有权访问的店铺/平台组合。
    AI Agent 应在执行任何操作前先调用此命令以获取可用账号信息。
    """
    ctx = client.get("/context")

    if is_json_mode():
        print(json.dumps(ctx, ensure_ascii=False, indent=2))
        return

    console.print(f"\n[bold]用户:[/bold] {ctx['username']}  [dim]角色: {ctx['role']}[/dim]\n")

    accounts = ctx.get("accounts", [])
    if not accounts:
        console.print("[yellow]当前账号无授权店铺[/yellow]")
        return

    table = Table(title="授权店铺", show_lines=False)
    table.add_column("店铺", style="bold cyan")
    table.add_column("平台")
    table.add_column("站点", style="dim")
    for acc in accounts:
        table.add_row(acc["store"], acc["platform"], acc["marketplace"])
    console.print(table)
    console.print()

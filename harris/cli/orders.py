import typer
from rich.console import Console
from ..client import client
from ..output import output as render_output

app = typer.Typer(help="订单管理")
console = Console()

ORDER_COLUMNS = [
    ("账号",    "account",       "cyan"),
    ("订单号",  "order_id",      "dim"),
    ("状态",    "status",        ""),
    ("下单时间", "purchase_date", "dim"),
    ("金额",    "total_amount",  ""),
    ("币种",    "currency",      "dim"),
    ("件数",    "items_count",   ""),
]

STATUS_STYLE = {"Pending": "yellow", "Unshipped": "blue", "Shipped": "green", "Canceled": "red"}


@app.command("list")
def list_orders(
    platform: str = typer.Option(..., "--platform", "-p", help="平台: amazon / coupang / mock"),
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    days: int = typer.Option(7, "--days", "-d", help="最近 N 天"),
    status: str = typer.Option(None, "--status", help="状态过滤"),
    out: str = typer.Option(None, "--output", "-o", help="导出路径，支持 .csv / .json"),
    fmt: str = typer.Option(None, "--format", "-f", help="输出格式: json（适合 AI Agent）"),
):
    """列出订单"""
    with console.status("获取订单中..."):
        orders = client.get("/orders", platform=platform, store=store, days=days, status=status)
    if not orders:
        console.print("[yellow]没有找到订单[/yellow]")
        return
    render_output(orders, ORDER_COLUMNS, title=f"订单列表（共 {len(orders)} 个）", out=out, fmt=fmt)


@app.command("get")
def get_order(
    order_id: str = typer.Argument(help="订单号"),
    platform: str = typer.Option(..., "--platform", "-p", help="平台: amazon / coupang / mock"),
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
):
    """查看订单详情"""
    with console.status(f"获取订单 {order_id}..."):
        order = client.get(f"/orders/{order_id}", platform=platform, store=store)
    for k, v in order.items():
        console.print(f"[bold]{k}:[/bold] {v}")

import typer
from rich.console import Console
from ..client import client
from ..output import output as render_output

app = typer.Typer(help="Listing 管理")
console = Console()

LISTING_COLUMNS = [
    ("账号",    "account",   "cyan"),
    ("SKU",     "sku",       "bold"),
    ("ASIN",    "asin",      "dim"),
    ("标题",    "title",     ""),
    ("价格",    "price",     ""),
    ("币种",    "currency",  "dim"),
    ("状态",    "status",    ""),
    ("可售库存", "quantity",  ""),
]


@app.command("list")
def list_listings(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    platform: str = typer.Option(None, "--platform", "-p", help="平台: amazon/coupang/mock（多平台时必填）"),
    sku: str = typer.Option(None, "--sku", help="按 SKU 过滤"),
    status: str = typer.Option(None, "--status", help="状态过滤: active/inactive/incomplete"),
    out: str = typer.Option(None, "--output", "-o", help="导出路径 .csv/.json"),
    fmt: str = typer.Option(None, "--format", "-f", help="输出格式: json（适合 AI Agent）"),
):
    """查看商品列表"""
    with console.status("获取商品中..."):
        listings = client.get("/listings", store=store, platform=platform, sku=sku, status=status)
    if not listings:
        console.print("[yellow]没有找到商品[/yellow]")
        return
    render_output(listings, LISTING_COLUMNS, title=f"商品列表（共 {len(listings)} 个）", out=out, fmt=fmt)

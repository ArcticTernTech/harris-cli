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
    account: str = typer.Option(..., "--account", "-a", help="账号别名"),
    sku: str = typer.Option(None, "--sku", help="按 SKU 过滤"),
    status: str = typer.Option(None, "--status", "-s", help="状态过滤: active/inactive/incomplete"),
    out: str = typer.Option(None, "--output", "-o", help="导出路径 .csv/.json"),
):
    """查看 Listing 列表"""
    with console.status("获取 Listing 中..."):
        listings = client.get("/listings", account=account, sku=sku, status=status)
    if not listings:
        console.print("[yellow]没有找到 Listing[/yellow]")
        return
    render_output(listings, LISTING_COLUMNS, title=f"Listing 列表（共 {len(listings)} 个）", out=out)

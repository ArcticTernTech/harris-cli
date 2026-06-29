import typer
from rich.console import Console
from ..client import client
from ..output import output as render_output

app = typer.Typer(help="库存管理")
console = Console()

INVENTORY_COLUMNS = [
    ("账号",  "account",         "cyan"),
    ("SKU",   "sku",             "bold"),
    ("ASIN",  "asin",            "dim"),
    ("可售",  "fulfillable_qty", ""),
    ("在途",  "inbound_qty",     "blue"),
    ("预留",  "reserved_qty",    "dim"),
]


@app.command("list")
def list_inventory(
    platform: str = typer.Option(..., "--platform", "-p", help="平台: amazon / coupang / mock"),
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    sku: str = typer.Option(None, "--sku", help="按 SKU 过滤"),
    low: int = typer.Option(None, "--low", help="只显示库存低于此数量的 SKU"),
    out: str = typer.Option(None, "--output", "-o", help="导出路径，支持 .csv / .json"),
    fmt: str = typer.Option(None, "--format", "-f", help="输出格式: json（适合 AI Agent）"),
):
    """查看库存"""
    with console.status("获取库存中..."):
        items = client.get("/inventory", platform=platform, store=store, sku=sku, low=low)
    if not items:
        console.print("[yellow]没有库存记录[/yellow]")
        return
    render_output(items, INVENTORY_COLUMNS, title=f"库存（共 {len(items)} 个 SKU）", out=out, fmt=fmt)


@app.command("alert")
def alert(
    platform: str = typer.Option(..., "--platform", "-p", help="平台: amazon / coupang / mock"),
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    threshold: int = typer.Option(20, "--threshold", "-t", help="低库存阈值"),
):
    """显示需要补货的 SKU"""
    with console.status("检查库存..."):
        items = client.get("/inventory", platform=platform, store=store, low=threshold)
    if not items:
        console.print(f"[green]所有库存均高于 {threshold}，无需补货。[/green]")
        return
    console.print(f"\n[bold red]以下 {len(items)} 个 SKU 库存不足 {threshold}：[/bold red]\n")
    for item in sorted(items, key=lambda x: x["fulfillable_qty"]):
        console.print(
            f"  [red]•[/red] [bold]{item['sku']}[/bold]  "
            f"可售: [red]{item['fulfillable_qty']}[/red]  在途: {item['inbound_qty']}"
        )

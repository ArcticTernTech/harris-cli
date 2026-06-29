import csv
import typer
from rich.console import Console
from ..client import client

app = typer.Typer(help="定价管理")
console = Console()


@app.command("get")
def get_price(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    platform: str = typer.Option(None, "--platform", "-p", help="平台: amazon/coupang/mock（多平台时必填）"),
    sku: str = typer.Option(..., "--sku", help="SKU"),
):
    """查看当前价格"""
    with console.status(f"获取 {sku} 价格..."):
        listings = client.get("/listings", store=store, platform=platform, sku=sku)
    if not listings:
        console.print(f"[yellow]未找到 SKU: {sku}[/yellow]")
        return
    l = listings[0]
    console.print(
        f"\nSKU:  {l['sku']}\n"
        f"ASIN: {l.get('asin', '-')}\n"
        f"价格: [bold]{l['currency']} {l['price']:.2f}[/bold]\n"
        f"状态: {l['status']}\n"
        f"库存: {l['quantity']}\n"
    )


@app.command("update")
def update_price(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    platform: str = typer.Option(None, "--platform", "-p", help="平台: amazon/coupang/mock（多平台时必填）"),
    sku: str = typer.Option(..., "--sku", help="SKU"),
    price: float = typer.Option(..., "--price", help="新价格"),
    currency: str = typer.Option("USD", "--currency", help="币种"),
):
    """更新单个 SKU 价格"""
    client.put("/pricing", {"store": store, "platform": platform, "sku": sku, "price": price, "currency": currency})
    console.print(f"[green]{sku} 价格已更新为 {currency} {price:.2f}[/green]")


@app.command("bulk")
def bulk_update(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    platform: str = typer.Option(None, "--platform", "-p", help="平台: amazon/coupang/mock（多平台时必填）"),
    file: str = typer.Option(..., "--file", "-f", help="CSV 文件，格式: sku,price"),
    currency: str = typer.Option("USD", "--currency", help="币种"),
    dry_run: bool = typer.Option(False, "--dry-run", help="只验证不实际提交"),
):
    """从 CSV 批量更新价格（格式: sku,price）"""
    rows = []
    with open(file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({"sku": row["sku"].strip(), "price": float(row["price"].strip())})
    if not rows:
        console.print("[yellow]CSV 为空[/yellow]")
        return
    result = client.post("/pricing/bulk", {
        "store": store, "platform": platform,
        "rows": rows, "currency": currency, "dry_run": dry_run,
    })
    if dry_run:
        console.print(f"[dim]Dry run：共 {len(rows)} 条，不实际提交[/dim]")
    else:
        console.print(f"\n[green]成功: {result['success']}[/green]  [red]失败: {len(result['failed'])}[/red]")
        for f in result["failed"]:
            console.print(f"  [red]✗[/red] {f}")

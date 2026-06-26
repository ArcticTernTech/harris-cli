import csv
import typer
from rich.console import Console
from ..client import client

app = typer.Typer(help="定价管理")
console = Console()


@app.command("get")
def get_price(
    account: str = typer.Option(..., "--account", "-a", help="账号别名"),
    sku: str = typer.Option(..., "--sku", help="SKU"),
):
    """查看当前价格"""
    with console.status(f"获取 {sku} 价格..."):
        listings = client.get("/listings", account=account, sku=sku)
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
    account: str = typer.Option(..., "--account", "-a", help="账号别名"),
    sku: str = typer.Option(..., "--sku", help="SKU"),
    price: float = typer.Option(..., "--price", "-p", help="新价格"),
    currency: str = typer.Option("USD", "--currency", help="币种"),
):
    """更新单个 SKU 价格"""
    client.put("/pricing", {"account": account, "sku": sku, "price": price, "currency": currency})
    console.print(f"[green]{sku} 价格已更新为 {currency} {price:.2f}[/green]")


@app.command("bulk")
def bulk_update(
    account: str = typer.Option(..., "--account", "-a", help="账号别名"),
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
    result = client.post("/pricing/bulk", {"account": account, "rows": rows, "currency": currency, "dry_run": dry_run})
    if dry_run:
        console.print(f"[dim]Dry run：共 {len(rows)} 条，不实际提交[/dim]")
    else:
        console.print(f"\n[green]成功: {result['success']}[/green]  [red]失败: {len(result['failed'])}[/red]")
        for f in result["failed"]:
            console.print(f"  [red]✗[/red] {f}")

import json
import typer
from rich.console import Console
from rich.table import Table
from ..client import client

app = typer.Typer(help="结算查询（Coupang）")
console = Console()

SETTLEMENT_COLUMNS = [
    ("结算类型",   "settlement_type"),
    ("结算日",     "settlement_date"),
    ("销售月份",   "revenue_month"),
    ("总销售额",   "total_sale"),
    ("手续费",     "service_fee"),
    ("最终结算额", "final_amount"),
    ("状态",       "status"),
]


@app.command("list")
def list_settlement(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    month: str = typer.Option(..., "--month", "-m", help="销售月份，格式 YYYY-MM，如 2026-06"),
    fmt: str = typer.Option(None, "--format", "-f", help="输出格式: json（适合 AI Agent）"),
):
    """查询 Coupang 结算明细"""
    with console.status(f"获取 {month} 结算数据..."):
        records = client.get("/settlement", platform="coupang", store=store, month=month)

    if not records:
        console.print("[yellow]未找到结算记录[/yellow]")
        return

    if fmt and fmt.lower() == "json":
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Coupang 结算明细 — {month}", show_lines=False)
    for header, _ in SETTLEMENT_COLUMNS:
        table.add_column(header)

    for r in records:
        status_raw = r.get("status") or "-"
        status_display = "[green]已结算[/green]" if status_raw == "DONE" else f"[yellow]{status_raw}[/yellow]"

        def fmt_num(v):
            if v is None:
                return "-"
            return f"{int(v):,}"

        table.add_row(
            r.get("settlement_type") or "-",
            r.get("settlement_date") or "-",
            r.get("revenue_month") or "-",
            fmt_num(r.get("total_sale")),
            fmt_num(r.get("service_fee")),
            fmt_num(r.get("final_amount")),
            status_display,
        )

    console.print(table)

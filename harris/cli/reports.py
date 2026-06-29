import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..client import client

app = typer.Typer(help="报表管理")
console = Console()

REPORT_TYPES = {
    "settlement": "GET_V2_SETTLEMENT_REPORT_DATA_FLAT_FILE",
    "business":   "GET_SALES_AND_TRAFFIC_REPORT",
    "inventory":  "GET_MERCHANT_LISTINGS_ALL_DATA",
    "fba_inv":    "GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA",
    "orders":     "GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL",
    "returns":    "GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA",
}


@app.command("request")
def request_report(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    platform: str = typer.Option(None, "--platform", "-p", help="平台: amazon/coupang/mock（多平台时必填）"),
    type_: str = typer.Option(..., "--type", "-t", help=f"报表类型: {', '.join(REPORT_TYPES.keys())}"),
    start: str = typer.Option(..., "--start", help="开始日期 YYYY-MM-DD"),
    end: str = typer.Option(..., "--end", help="结束日期 YYYY-MM-DD"),
):
    """请求生成报表"""
    with console.status("提交报表请求..."):
        result = client.post("/reports", {"store": store, "platform": platform, "type": type_, "start": start, "end": end})
    report_id = result["report_id"]
    console.print(f"\n[green]报表请求已提交[/green]  Report ID: [bold cyan]{report_id}[/bold cyan]")
    platform_flag = f"--platform {platform} " if platform else ""
    console.print(f"[dim]harris reports status --report-id {report_id} --store {store} {platform_flag}[/dim]")


@app.command("status")
def report_status(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    platform: str = typer.Option(None, "--platform", "-p", help="平台: amazon/coupang/mock（多平台时必填）"),
    report_id: str = typer.Option(..., "--report-id", "-r", help="Report ID"),
):
    """查询报表状态"""
    meta = client.get(f"/reports/{report_id}", store=store, platform=platform)
    style = {"IN_QUEUE": "yellow", "IN_PROGRESS": "blue", "DONE": "green", "FATAL": "red"}.get(meta["status"], "white")
    console.print(f"\nReport ID: {meta['report_id']}\n类型: {meta['report_type']}\n状态: [{style}]{meta['status']}[/{style}]")
    if meta["status"] == "DONE":
        platform_flag = f"--platform {platform} " if platform else ""
        console.print(f"[dim]harris reports download --report-id {report_id} --store {store} {platform_flag}--output report.csv[/dim]")


@app.command("download")
def download_report(
    store: str = typer.Option(..., "--store", "-s", help="店铺名称，如 rovestep"),
    platform: str = typer.Option(None, "--platform", "-p", help="平台: amazon/coupang/mock（多平台时必填）"),
    report_id: str = typer.Option(..., "--report-id", "-r", help="Report ID"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="保存路径，默认输出到终端"),
):
    """等待报表完成并下载"""
    for i in range(20):
        meta = client.get(f"/reports/{report_id}", store=store, platform=platform)
        if meta["status"] == "DONE":
            break
        if meta["status"] == "FATAL":
            console.print("[red]报表生成失败[/red]")
            raise typer.Exit(1)
        console.print(f"[{i+1}/20] {meta['status']}，30 秒后重试...")
        time.sleep(30)
    else:
        console.print("[red]等待超时[/red]")
        raise typer.Exit(1)

    content = client.get_text(f"/reports/{report_id}/download", store=store, platform=platform)
    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(f"[green]已保存到 {output}[/green]")
    else:
        console.print(content)

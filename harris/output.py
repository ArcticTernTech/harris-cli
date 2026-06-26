import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def render_table(rows: list, columns: list[tuple[str, str, str]], title: str = "") -> None:
    """
    columns: list of (header, field_name, style)
    rows: list of dataclass instances
    """
    table = Table(title=title, show_lines=False)
    for header, _, style in columns:
        table.add_column(header, style=style)
    for row in rows:
        d = asdict(row) if hasattr(row, "__dataclass_fields__") else row
        table.add_row(*[str(d.get(field, "")) for _, field, _ in columns])
    console.print(table)


def export_csv(rows: list, columns: list[tuple[str, str, str]], path: str) -> None:
    fields = [f for _, f, _ in columns]
    headers = [h for h, _, _ in columns]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writerow(dict(zip(fields, headers)))
        for row in rows:
            d = asdict(row) if hasattr(row, "__dataclass_fields__") else row
            writer.writerow(d)
    console.print(f"[green]已导出 {len(rows)} 条记录到 {path}[/green]")


def export_json(rows: list, path: str) -> None:
    data = []
    for row in rows:
        d = asdict(row) if hasattr(row, "__dataclass_fields__") else row
        # datetime 序列化
        for k, v in d.items():
            if hasattr(v, "isoformat"):
                d[k] = v.isoformat()
        data.append(d)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    console.print(f"[green]已导出 {len(rows)} 条记录到 {path}[/green]")


def output(rows: list, columns: list[tuple[str, str, str]], title: str = "", out: str | None = None) -> None:
    """统一出口：out=None 打印表格，out=*.csv 导出CSV，out=*.json 导出JSON"""
    if not out:
        render_table(rows, columns, title)
    elif out.endswith(".json"):
        export_json(rows, out)
    else:
        export_csv(rows, columns, out)

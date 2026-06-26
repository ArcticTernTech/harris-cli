import typer
from rich.console import Console

from .cli import auth, orders, inventory, listings, pricing, reports, admin
from .cli.login import login, logout, whoami

app = typer.Typer(
    name="harris",
    help="跨境电商运营 CLI — 多平台、多账号统一管理",
    no_args_is_help=True,
)
console = Console()

app.command("login")(login)
app.command("logout")(logout)
app.command("whoami")(whoami)
app.add_typer(orders.app,    name="orders",    help="订单管理")
app.add_typer(inventory.app, name="inventory", help="库存管理")
app.add_typer(listings.app,  name="listings",  help="Listing 管理")
app.add_typer(pricing.app,   name="pricing",   help="定价管理")
app.add_typer(reports.app,   name="reports",   help="报表管理")
app.add_typer(admin.app,     name="admin",     help="管理员操作")
app.add_typer(auth.app,      name="auth",      help="直连模式（高级）")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-v", is_eager=True),
):
    if version:
        console.print("harris-cli v0.3.0")
        raise typer.Exit()

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from ..config import get_account, save_account, delete_account, list_accounts, load_config
from ..logger import get_logger

logger = get_logger("harris.auth")

app = typer.Typer(help="账号认证管理")
console = Console()

MARKETPLACE_CHOICES = ["US", "CA", "MX", "UK", "DE", "FR", "JP", "AU", "SG", "AE"]


@app.command("setup")
def setup(
    account: str = typer.Option(..., "--account", "-a", help="账号别名，如 store_us_1"),
    platform: str = typer.Option("amazon", "--platform", "-p", help="平台名称"),
):
    """添加或更新一个账号的 API 凭证"""
    console.print(
        Panel(
            f"配置账号 [bold cyan]{account}[/bold cyan] ({platform})\n"
            "请前往卖家后台获取以下信息：\n"
            "- SP-API 应用的 Client ID / Secret\n"
            "- 刷新令牌 (Refresh Token)\n"
            "- AWS IAM 的 Access Key / Secret Key",
            title="账号配置向导",
        )
    )

    if platform == "amazon":
        marketplace = Prompt.ask("站点", choices=MARKETPLACE_CHOICES, default="US")
        client_id = Prompt.ask("Client ID (lwa_app_id)")
        client_secret = Prompt.ask("Client Secret", password=True)
        refresh_token = Prompt.ask("Refresh Token", password=True)
        aws_access_key = Prompt.ask("AWS Access Key ID")
        aws_secret_key = Prompt.ask("AWS Secret Access Key", password=True)
        role_arn = Prompt.ask("Role ARN (可选，直接回车跳过)", default="")

        config: dict = {
            "platform": "amazon",
            "marketplace": marketplace,
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "aws_access_key": aws_access_key,
            "aws_secret_key": aws_secret_key,
        }
        if role_arn:
            config["role_arn"] = role_arn
    else:
        console.print(f"[red]暂不支持平台: {platform}[/red]")
        raise typer.Exit(1)

    save_account(account, config)
    logger.info(f"Account configured: {account} ({platform}/{marketplace})")
    console.print(f"\n[green]账号 '{account}' 配置成功！[/green]")
    console.print(f"可运行 [bold]harris auth verify --account {account}[/bold] 验证连通性")


@app.command("list")
def list_cmd():
    """列出所有已配置的账号"""
    accounts = list_accounts()
    if not accounts:
        console.print("[yellow]尚未配置任何账号，请先运行: harris auth setup[/yellow]")
        return

    config = load_config()
    console.print("\n已配置的账号：\n")
    for name in accounts:
        acc = config["accounts"][name]
        console.print(
            f"  [bold cyan]{name}[/bold cyan]  "
            f"[dim]{acc.get('platform', '?')} / {acc.get('marketplace', '?')}[/dim]"
        )
    console.print()


@app.command("verify")
def verify(
    account: str = typer.Option(..., "--account", "-a", help="账号别名"),
):
    """验证账号凭证是否有效"""
    from ..platforms.amazon import AmazonAdapter

    acc_config = get_account(account)
    console.print(f"正在验证账号 [bold]{account}[/bold] ...")

    try:
        adapter = AmazonAdapter(account, acc_config)
        adapter.get_account_health()
        logger.info(f"Account verified: {account}")
        console.print(f"[green]连接成功！账号 '{account}' 凭证有效。[/green]")
    except Exception as e:
        logger.error(f"Account verification failed: {account}: {e}")
        console.print(f"[red]验证失败: {e}[/red]")
        raise typer.Exit(1)


@app.command("remove")
def remove(
    account: str = typer.Option(..., "--account", "-a", help="账号别名"),
):
    """删除一个账号配置"""
    if not Confirm.ask(f"确认删除账号 '{account}'？"):
        raise typer.Abort()
    delete_account(account)
    console.print(f"[green]账号 '{account}' 已删除。[/green]")


@app.command("token")
def get_token(
    account: str = typer.Option(..., "--account", "-a", help="账号别名（需已配置 client_id/client_secret）"),
):
    """通过浏览器 OAuth 授权自动获取 Refresh Token"""
    import threading
    import webbrowser
    import urllib.parse
    import urllib.request
    import json
    from http.server import HTTPServer, BaseHTTPRequestHandler

    acc_config = get_account(account)
    client_id = acc_config.get("client_id", "")
    client_secret = acc_config.get("client_secret", "")

    if not client_id or not client_secret:
        console.print("[red]请先运行 harris auth setup 配置 client_id 和 client_secret[/red]")
        raise typer.Exit(1)

    REDIRECT_URI = "http://localhost:9090/callback"
    auth_code_holder = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                auth_code_holder["code"] = params["code"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h2>Authorization successful! You can close this tab.</h2>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"<h2>Authorization failed.</h2>")

        def log_message(self, format, *args):
            pass  # 静默 HTTP 日志

    server = HTTPServer(("localhost", 9090), CallbackHandler)

    auth_url = (
        "https://sellercentral.amazon.com/apps/authorize/consent?"
        + urllib.parse.urlencode({
            "application_id": client_id,
            "state": "harris-cli",
            "redirect_uri": REDIRECT_URI,
            "version": "beta",
        })
    )

    console.print(f"\n正在打开浏览器进行 Amazon 授权...\n")
    console.print(f"[dim]如果浏览器未自动打开，请手动访问：\n{auth_url}[/dim]\n")
    webbrowser.open(auth_url)

    console.print("等待授权回调（监听 localhost:9090）...")

    # 在后台线程处理一次请求后关闭
    def serve_once():
        server.handle_request()

    t = threading.Thread(target=serve_once)
    t.start()
    t.join(timeout=120)

    if "code" not in auth_code_holder:
        console.print("[red]等待超时，未收到授权码。[/red]")
        raise typer.Exit(1)

    # 用 code 换取 refresh_token
    token_data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": auth_code_holder["code"],
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode()

    req = urllib.request.Request(
        "https://api.amazon.com/auth/o2/token",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            token_resp = json.loads(resp.read())
    except Exception as e:
        console.print(f"[red]获取 token 失败: {e}[/red]")
        raise typer.Exit(1)

    refresh_token = token_resp.get("refresh_token")
    if not refresh_token:
        console.print(f"[red]响应中没有 refresh_token: {token_resp}[/red]")
        raise typer.Exit(1)

    # 写入配置
    acc_config["refresh_token"] = refresh_token
    save_account(account, acc_config)
    console.print(f"\n[green]Refresh Token 获取成功，已保存到账号 '{account}'[/green]")
    console.print(f"可运行 [bold]harris auth verify --account {account}[/bold] 验证")

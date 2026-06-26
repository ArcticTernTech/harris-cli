import json
import threading
import urllib.parse
import urllib.request
import urllib.error
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import typer
from rich.console import Console

from ..config import get_server_url, save_session, delete_session, load_session

console = Console()

CLI_CALLBACK_PORT = 9091
CLI_CALLBACK_URI = f"http://localhost:{CLI_CALLBACK_PORT}/callback"


def login(
    server: str = typer.Option(None, "--server", help="服务器地址，如 http://your-server:8000"),
):
    """通过飞书 OAuth 登录 Harris 系统"""
    import os
    if server:
        os.environ["HARRIS_SERVER_URL"] = server

    base_url = get_server_url()
    token_holder: dict = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "access_token" in params:
                token_holder["access_token"]  = params["access_token"][0]
                token_holder["refresh_token"] = params["refresh_token"][0]
                token_holder["username"]      = params["username"][0]
                token_holder["role"]          = params["role"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    b"<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                    b"<h2>&#10003; \xe6\x8e\x88\xe6\x9d\x83\xe6\x88\x90\xe5\x8a\x9f\xef\xbc\x81</h2>"
                    b"<p>\xe5\x8f\xaf\xe4\xbb\xa5\xe5\x85\xb3\xe9\x97\xad\xe6\xad\xa4\xe7\xaa\x97\xe5\x8f\xa3\xe3\x80\x82</p>"
                    b"</body></html>"
                )
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"<h2>Authorization failed.</h2>")

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("localhost", CLI_CALLBACK_PORT), CallbackHandler)

    feishu_url = (
        base_url + "/auth/feishu?"
        + urllib.parse.urlencode({"cli_redirect": CLI_CALLBACK_URI})
    )

    console.print(f"\n正在打开浏览器进行飞书授权...\n")
    console.print(f"[dim]如果浏览器未自动打开，请手动访问：\n{feishu_url}[/dim]\n")
    webbrowser.open(feishu_url)
    console.print("等待授权回调（最多 2 分钟）...")

    t = threading.Thread(target=httpd.handle_request)
    t.start()
    t.join(timeout=120)

    if "access_token" not in token_holder:
        console.print("[red]等待超时或授权被取消。[/red]")
        raise typer.Exit(1)

    session = {
        "access_token":  token_holder["access_token"],
        "refresh_token": token_holder["refresh_token"],
        "expires_at":    (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "username":      token_holder["username"],
        "role":          token_holder["role"],
    }
    save_session(session)
    console.print(
        f"\n[green]登录成功！[/green]  "
        f"用户: [bold]{token_holder['username']}[/bold]  "
        f"角色: [cyan]{token_holder['role']}[/cyan]\n"
    )


def logout():
    """退出登录"""
    session = load_session()
    if not session:
        console.print("[yellow]当前未登录[/yellow]")
        return
    delete_session()
    console.print(f"[green]已退出登录（{session.get('username', '')}）[/green]")


def whoami():
    """查看当前登录用户"""
    session = load_session()
    if not session or "username" not in session:
        console.print("[yellow]未登录[/yellow]")
        raise typer.Exit(1)
    console.print(
        f"用户: [bold]{session['username']}[/bold]  "
        f"角色: [cyan]{session['role']}[/cyan]"
    )

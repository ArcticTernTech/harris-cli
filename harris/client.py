import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console

from .config import get_server_url, load_session, save_session, delete_session, is_json_mode

console = Console()


class HarrisClient:
    def __init__(self):
        self.base_url = get_server_url()

    def _session(self) -> dict:
        s = load_session()
        if not s or "access_token" not in s:
            self._output_error({"error": "not_logged_in", "message": "未登录，请先运行: harris login"})
            raise typer.Exit(1)
        return s

    def _access_token(self) -> str:
        s = self._session()
        expires_at = datetime.fromisoformat(s.get("expires_at", "2000-01-01T00:00:00+00:00"))
        if (expires_at - datetime.now(timezone.utc)).total_seconds() < 300:
            try:
                resp = self._raw_post("/auth/refresh", {"refresh_token": s["refresh_token"]}, auth=False)
                from datetime import timedelta
                s["access_token"] = resp["access_token"]
                s["expires_at"] = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
                save_session(s)
                return s["access_token"]
            except Exception:
                self._output_error({"error": "session_expired", "message": "会话已过期，请重新登录: harris login"})
                delete_session()
                raise typer.Exit(1)
        return s["access_token"]

    def _output_error(self, error_obj: dict) -> None:
        """输出错误：JSON 模式输出机器可读 JSON，否则输出人类友好文本。"""
        if is_json_mode():
            print(json.dumps(error_obj, ensure_ascii=False))
            return

        error_type = error_obj.get("error", "")
        msg = error_obj.get("message", str(error_obj))

        if error_type == "platform_ambiguous":
            store = error_obj.get("store", "")
            platforms = error_obj.get("platforms", [])
            console.print(f"\n[yellow]店铺 '{store}' 在多个平台均有账号:[/yellow]")
            for p in platforms:
                console.print(f"  • [cyan]{p}[/cyan]")
            console.print("[dim]请通过 --platform 指定平台，例如: --platform coupang[/dim]\n")
        elif error_type == "store_not_found":
            store = error_obj.get("store", "")
            available = error_obj.get("available_stores", [])
            console.print(f"\n[red]店铺 '{store}' 不存在或无权访问[/red]")
            if available:
                console.print("[dim]您有权访问的店铺:[/dim]")
                for s in available:
                    console.print(f"  • [cyan]{s}[/cyan]")
            console.print()
        elif error_type in ("not_logged_in", "session_expired"):
            console.print(f"[red]{msg}[/red]")
        elif error_type == "access_denied":
            console.print(f"[red]权限不足: {msg}[/red]")
        elif error_type == "not_found":
            console.print(f"[red]资源不存在: {msg}[/red]")
        else:
            console.print(f"[red]{msg}[/red]")

    def _raw_post(self, path: str, body: dict, auth: bool = True) -> dict:
        url = self.base_url + path
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {self._access_token()}"
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read())
            except Exception:
                err = {}
            detail = err.get("detail", str(e))
            msg = detail if isinstance(detail, str) else str(detail)
            self._output_error({"error": "api_error", "code": e.code, "message": msg})
            raise typer.Exit(1)

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict | str:
        url = self.base_url + path
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url += "?" + urllib.parse.urlencode(filtered)
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        else:
            data = None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()
                if "application/json" in content_type:
                    return json.loads(raw)
                return raw.decode()
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read())
            except Exception:
                err = {}
            detail = err.get("detail", {})

            # 结构化错误（409 平台歧义 / 404 店铺不存在）
            if isinstance(detail, dict) and "error" in detail:
                self._output_error(detail)
                raise typer.Exit(1)

            msg = detail if isinstance(detail, str) else str(e)

            if e.code == 401:
                self._output_error({"error": "session_expired", "message": "会话已过期，请重新登录: harris login"})
                delete_session()
            elif e.code == 403:
                self._output_error({"error": "access_denied", "message": msg})
            elif e.code == 404:
                self._output_error({"error": "not_found", "message": msg})
            else:
                self._output_error({"error": "api_error", "code": e.code, "message": msg})
            raise typer.Exit(1)

    def get(self, path: str, **params) -> dict | list:
        return self._request("GET", path, params=params)

    def post(self, path: str, body: dict) -> dict:
        return self._request("POST", path, body=body)

    def put(self, path: str, body: dict) -> dict:
        return self._request("PUT", path, body=body)

    def patch(self, path: str, body: dict) -> dict:
        return self._request("PATCH", path, body=body)

    def delete(self, path: str) -> None:
        self._request("DELETE", path)

    def get_text(self, path: str, **params) -> str:
        return self._request("GET", path, params=params)

    @property
    def current_user_role(self) -> str:
        return self._session().get("role", "viewer")

    @property
    def current_username(self) -> str:
        return self._session().get("username", "")


client = HarrisClient()

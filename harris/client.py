import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console

from .config import get_server_url, load_session, save_session, delete_session

console = Console()


class HarrisClient:
    def __init__(self):
        self.base_url = get_server_url()

    def _session(self) -> dict:
        s = load_session()
        if not s or "access_token" not in s:
            console.print("[red]未登录，请先运行: harris login[/red]")
            raise typer.Exit(1)
        return s

    def _access_token(self) -> str:
        s = self._session()
        # 如果 token 将在 5 分钟内过期，自动刷新
        expires_at = datetime.fromisoformat(s.get("expires_at", "2000-01-01T00:00:00+00:00"))
        if (expires_at - datetime.now(timezone.utc)).total_seconds() < 300:
            try:
                resp = self._raw_post("/auth/refresh", {"refresh_token": s["refresh_token"]}, auth=False)
                new_token = resp["access_token"]
                s["access_token"] = new_token
                # 重新计算过期时间（access token 2 小时）
                from datetime import timedelta
                s["expires_at"] = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
                save_session(s)
                return new_token
            except Exception:
                console.print("[red]会话已过期，请重新登录: harris login[/red]")
                delete_session()
                raise typer.Exit(1)
        return s["access_token"]

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
            err = json.loads(e.read()) if e.headers.get("Content-Type", "").startswith("application/json") else {}
            msg = err.get("detail", str(e))
            if e.code == 403:
                console.print(f"[red]权限不足: {msg}[/red]")
            elif e.code == 401:
                console.print(f"[red]未授权，请重新登录: {msg}[/red]")
                delete_session()
            else:
                console.print(f"[red]请求失败 ({e.code}): {msg}[/red]")
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
            msg = err.get("detail", str(e))
            if e.code == 403:
                console.print(f"[red]权限不足: {msg}[/red]")
            elif e.code == 401:
                console.print(f"[red]会话过期，请重新登录[/red]")
                delete_session()
            elif e.code == 404:
                console.print(f"[red]资源不存在: {msg}[/red]")
            else:
                console.print(f"[red]请求失败 ({e.code}): {msg}[/red]")
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

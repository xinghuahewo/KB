from contextlib import contextmanager
from email.utils import formatdate
from functools import partial
import http.client
import importlib.util
from pathlib import Path
import threading


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY_ROOT / "frontend" / "scripts" / "serve_static_with_proxy.py"


def _load_server_module():
    spec = importlib.util.spec_from_file_location("serve_static_with_proxy", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@contextmanager
def _serve_static_files(root: Path):
    module = _load_server_module()
    handler = partial(module.StaticProxyHandler, directory=str(root))
    server = module.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _request(address, path: str, headers: dict[str, str] | None = None):
    connection = http.client.HTTPConnection(*address, timeout=5)
    connection.request("GET", path, headers=headers or {})
    response = connection.getresponse()
    payload = response.read()
    result = response.status, dict(response.getheaders()), payload
    connection.close()
    return result


def test_html_is_never_reused_across_code_release_switches(tmp_path):
    (tmp_path / "index.html").write_text("current release", encoding="utf-8")

    with _serve_static_files(tmp_path) as address:
        status, headers, payload = _request(address, "/")
        conditional_status, _, conditional_payload = _request(
            address,
            "/index.html",
            {"If-Modified-Since": formatdate(4_102_444_800, usegmt=True)},
        )

    assert status == 200
    assert payload == b"current release"
    assert headers["Cache-Control"] == "no-store, max-age=0, must-revalidate"
    assert headers["Pragma"] == "no-cache"
    assert headers["Expires"] == "0"
    assert conditional_status == 200
    assert conditional_payload == b"current release"


def test_hashed_next_assets_remain_long_lived_and_immutable(tmp_path):
    asset = tmp_path / "_next" / "static" / "css" / "app-release-hash.css"
    asset.parent.mkdir(parents=True)
    asset.write_text("body {}", encoding="utf-8")

    with _serve_static_files(tmp_path) as address:
        status, headers, payload = _request(address, "/_next/static/css/app-release-hash.css")

    assert status == 200
    assert payload == b"body {}"
    assert headers["Cache-Control"] == "public, max-age=31536000, immutable"

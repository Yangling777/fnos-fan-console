# -*- coding: utf-8 -*-
"""web_server 路由本地集成测试(§1.1:带查询参数的入口不再误判 401)

不依赖 sysfs:用假 fan_controller / config_manager / hardware 在随机端口起真实 HTTP 服务。
"""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.join(_HERE, "..", "bin"),          # 资料包布局
              os.path.join(_HERE, "..", "src", "app", "bin")):  # 公开仓库布局
    if os.path.isdir(_cand):
        sys.path.insert(0, _cand)

from web_server import FanControlHTTPServer  # noqa: E402

TOKEN = "test-token-123"


class FakeFanController:
    def get_status(self):
        return {"cpu_temp": 33.0, "hw_detected": True}

    def get_logs(self):
        return [{"time": "t", "level": "info", "message": "m"}]

    def clear_logs(self):
        pass

    def add_log(self, level, message):
        pass

    def set_mode(self, mode, zone_id=None):
        return mode in ("default", "auto", "manual", "full")


class FakeConfigManager:
    def get(self):
        return {"poll_interval": 2}

    def update(self, partial):
        return {"poll_interval": 2, **partial}

    def update_zone(self, zone_id, partial):
        return {"id": zone_id, **partial}


class FakeHardware:
    def get_hardware_info(self):
        return {"chips": []}


class WebServerRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        with open(os.path.join(cls._tmp.name, "auth_token"), "w") as f:
            f.write(TOKEN)
        cls.server = FanControlHTTPServer(
            "127.0.0.1", 0, FakeFanController(), FakeConfigManager(),
            hardware=FakeHardware(), config_dir=cls._tmp.name)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls._tmp.cleanup()

    def _url(self, path):
        return "http://127.0.0.1:{}{}".format(self.port, path)

    def _request(self, method, path, payload=None, token=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(self._url(path), data=data, method=method)
        if payload is not None:
            req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("X-Auth-Token", token)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, resp.read(), resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers.get("Content-Type", "")

    def _get(self, path, token=None):
        return self._request("GET", path, token=token)

    def _post(self, path, payload, token=None):
        return self._request("POST", path, payload=payload, token=token)

    # ── 静态页 / 公共端点:带查询参数不再 401(§1.1)──
    def test_root_with_query_returns_page(self):
        status, body, ctype = self._get("/?cb=1")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertGreater(len(body), 1000)

    def test_index_html_with_query_returns_page(self):
        status, _, ctype = self._get("/index.html?x=1")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)

    def test_favicon_with_query_returns_204(self):
        status, _, _ = self._get("/favicon.ico?v=2")
        self.assertEqual(status, 204)

    def test_auth_status_with_query(self):
        status, body, _ = self._get("/api/auth/status?cb=3")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["auth_enabled"])

    def test_head_root_with_query(self):
        status, _, ctype = self._request("HEAD", "/?cb=4")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)

    # ── API:查询参数不影响认证与路由(§1.1)──
    def test_api_without_token_still_401(self):
        status, _, _ = self._get("/api/status?x=1")
        self.assertEqual(status, 401)

    def test_api_with_token_and_query_ok(self):
        status, body, _ = self._get("/api/status?x=1", token=TOKEN)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["hw_detected"])

    def test_post_mode_with_query(self):
        status, body, _ = self._post("/api/mode?x=1", {"mode": "auto"}, token=TOKEN)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["ok"])

    def test_post_zone_config_with_query(self):
        status, body, _ = self._post("/api/zones/default/config?x=1",
                                     {"temp_source": "gpu"}, token=TOKEN)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["ok"])

    # ── PWA 资源(§2.7)──
    def test_manifest_route(self):
        status, body, ctype = self._get("/manifest.webmanifest?cb=1")
        self.assertEqual(status, 200)
        self.assertIn("manifest", ctype)
        self.assertEqual(json.loads(body)["display"], "standalone")

    def test_icon_routes(self):
        for path in ("/icon-128.png", "/icon-256.png", "/apple-touch-icon.png"):
            status, body, ctype = self._get(path + "?cb=1")
            self.assertEqual(status, 200, path)
            self.assertIn("image/png", ctype)
            self.assertGreater(len(body), 100)


if __name__ == "__main__":
    unittest.main()

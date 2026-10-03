# -*- coding: utf-8 -*-
"""本地 Mock 服务器 v2:支持运行模式状态(用于验证自动/手动/全速模式的界面联动)
v9.2:页面路径改为资料包自包含(源码/index.html),硬件接口加入 system 机器信息
v1.0 批次二:曲线/手动值入库(支持配置导出→导入回滚验证),日志样本含 error 级别
v1.0 批次三:多区域配置存储(区域管理/多区域状态面板)、alert_state 注入(告警通知)、
             alert_webhook 字段、PWA 资源(manifest/图标)本地直出
"""
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # …/源码/ 或公开仓库根
INDEX_HTML = os.path.join(BASE, "index.html")
_STATIC_CANDIDATES = [
    os.path.join(BASE, "应用源码（NAS快照）", "fan-control", "bin", "static"),  # 资料包布局
    os.path.join(BASE, "src", "app", "bin", "static"),                          # 公开仓库布局
]
STATIC_DIR = next((p for p in _STATIC_CANDIDATES if os.path.isdir(p)), _STATIC_CANDIDATES[0])

PWA_FILES = {
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json; charset=utf-8"),
    "/apple-touch-icon.png": ("apple-touch-icon.png", "image/png"),
    "/icon-128.png": ("icon-128.png", "image/png"),
    "/icon-256.png": ("icon-256.png", "image/png"),
}

def load_html():
    return open(INDEX_HTML, encoding="utf-8").read()

DEFAULT_CURVE = [{"temp": 30, "pwm_percent": 20}, {"temp": 40, "pwm_percent": 30}, {"temp": 50, "pwm_percent": 45},
                 {"temp": 60, "pwm_percent": 65}, {"temp": 70, "pwm_percent": 85}, {"temp": 80, "pwm_percent": 100}]

STATE = {"mode": "default", "source": "max", "poll": 2, "min": 20, "gpu": 41.0, "manual": 50,
         "webhook": "", "alert": "ok", "zones": None, "curve": [dict(n) for n in DEFAULT_CURVE]}


def default_zone():
    return {"id": "default", "name": "系统风扇", "channels": ["pwm3", "pwm4"],
            "temp_source": STATE["source"], "mode": STATE["mode"],
            "min_pwm_percent": STATE["min"], "manual_pwm_percent": STATE["manual"],
            "curve": [dict(n) for n in STATE["curve"]]}


def zone_list():
    if STATE["zones"] is None:
        return [default_zone()]
    return STATE["zones"]


def find_zone(zid):
    for z in zone_list():
        if z.get("id") == zid:
            return z
    return None


def sync_legacy_from_zone(z):
    """单区域(legacy)时把区域字段同步回 STATE,兼容 ?source= / ?click= 等注入"""
    if STATE["zones"] is None:
        STATE["source"] = z.get("temp_source", "cpu")
        STATE["mode"] = z.get("mode", "default")
        STATE["min"] = z.get("min_pwm_percent", 20)
        STATE["manual"] = z.get("manual_pwm_percent", 50)
        if isinstance(z.get("curve"), list) and len(z["curve"]) >= 2:
            STATE["curve"] = [dict(n) for n in z["curve"]]


CONFIG = lambda: {"poll_interval": STATE["poll"], "web_port": 9511,
                  "alert_webhook": STATE["webhook"], "zones": zone_list()}


def _zone_temp(z):
    src = z.get("temp_source")
    if src == "gpu":
        return STATE["gpu"] if STATE["gpu"] is not None else 36.0
    return 36.0


def status():
    zs = {}
    for i, z in enumerate(zone_list()):
        m = z.get("mode", "default")
        pwm = 100 if m == "full" else (50 if m == "manual" else 29 + i * 3)
        rpm = 2250 if m == "full" else (1700 if m == "manual" else 1301 + i * 40)
        zs[z["id"]] = {"name": z.get("name", z["id"]), "channels": z.get("channels", []),
                       "temp_source": z.get("temp_source", "cpu"), "temp": _zone_temp(z),
                       "fan_rpm": rpm, "pwm_value": round(pwm * 2.55), "pwm_percent": pwm,
                       "mode": m, "degraded": STATE["alert"] == "degrade",
                       "alert_state": STATE["alert"]}
    ids = list(zs.keys())
    first = zs[ids[0]] if ids else {}
    degraded = STATE["alert"] == "degrade"
    return {"cpu_temp": 33.0, "disk_temps": {"sda": 35.0, "sdb": 32.0, "sdc": 33.0, "sdd": 36.0},
            "gpu_temp": STATE["gpu"], "hw_detected": True, "uptime": 170120, "zones": zs,
            "fan_rpm": first.get("fan_rpm"), "pwm_value": first.get("pwm_value"),
            "pwm_percent": first.get("pwm_percent"), "mode": first.get("mode", "default"),
            "degraded": degraded, "degrade_reason": ("示例:区域已降级" if degraded else "")}


HARDWARE = {"chips": [{"name": "nct6797", "display_name": "NCT6797D", "hwmon_path": "/sys/class/hwmon/hwmon10",
                       "pwm_channels": ["pwm1", "pwm2", "pwm3", "pwm4", "pwm5"], "fan_inputs": ["pwm3", "pwm4"]}],
            "temp_sensors": {"cpu": {"type": "coretemp", "current": 33.0}},
            "system": {"hostname": "fnos-demo", "model": "B760M MORTAR (MS-7D99)"}}


def hardware():
    hw = {"chips": HARDWARE["chips"], "temp_sensors": dict(HARDWARE["temp_sensors"]), "system": HARDWARE["system"]}
    if STATE["gpu"] is not None:
        hw["temp_sensors"]["gpu"] = {"type": "i915", "current": STATE["gpu"]}
    return hw


LOGS = [{"time": "2026-10-03 10:31:02", "level": "info", "message": "服务启动,1 个区域: 系统风扇(pwm3+pwm4)"},
        {"time": "2026-10-03 10:31:04", "level": "info", "message": "所有区域 切换到默认模式"},
        {"time": "2026-10-03 10:32:20", "level": "warn", "message": "区域 '系统风扇' 温控曲线已更新"},
        {"time": "2026-10-03 10:35:47", "level": "error", "message": "示例告警:温度传感器连续读取失败 3 次,全速保护(Mock 数据,仅演示)"}]


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _out(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path, content_type):
        try:
            data = open(path, "rb").read()
        except OSError:
            self._out({"ok": False, "error": "Not Found"}, 404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        p = self.path.split("?")[0]
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if p in PWA_FILES:
            fn, ct = PWA_FILES[p]
            self._file(os.path.join(STATIC_DIR, fn), ct)
            return
        if p in ("/test",):
            if "reset" in qs:
                STATE.update({"mode": "default", "source": "max", "poll": 2, "min": 20, "gpu": 41.0,
                              "manual": 50, "webhook": "", "alert": "ok", "zones": None})
            if "nogpu" in qs:
                STATE["gpu"] = None
            alert = (qs.get("alert") or [""])[0]
            if alert in ("ok", "protect", "degrade"):
                STATE["alert"] = alert
            html = load_html()
            click = (qs.get("click") or [""])[0]
            if click in ("auto", "manual", "full", "default"):
                html = html.replace("</body>", "<script>setTimeout(function(){var b=document.querySelector('#singleModeSection .mode-btn[data-mode=\"" + click + "\"]');if(b)b.click();},400);</script></body>")
            if "wp" in qs:
                html = html.replace("</body>", "<script>setTimeout(function(){var b=document.getElementById('wpBtn');if(b)b.click();},250);</script></body>")
            if "zoneedit" in qs:
                html = html.replace("</body>", "<script>setTimeout(function(){var b=document.getElementById('zoneAddBtn');if(b)b.click();},700);</script></body>")
            if "dirty" in qs:
                html = html.replace("</body>", "<script>setTimeout(function(){try{document.getElementById('curveEditBtn').click();var ins=document.querySelectorAll('#curveInputs input');if(ins.length>=3){ins[2].value=42;ins[2].dispatchEvent(new Event('input',{bubbles:true}));}else if(ins.length){ins[0].dispatchEvent(new Event('input',{bubbles:true}));}}catch(e){}},600);</script></body>")
            if "probe" in qs:
                html = html.replace("</body>", "<script>setTimeout(function(){try{var sb=document.querySelector('.sidebar');document.title='W='+innerWidth+'|MQ='+window.matchMedia('(max-width:880px)').matches+'|side='+getComputedStyle(sb).display+'|appW='+Math.round(document.querySelector('.app').getBoundingClientRect().width)+'|navW='+Math.round(sb.getBoundingClientRect().width)+'|navBottom='+Math.round(sb.getBoundingClientRect().bottom);}catch(e){document.title='ERR '+e.message}},300);</script></body>")
            side = (qs.get("side") or [""])[0]
            if side in ("viewHome", "viewCurve", "viewZones", "viewLogs", "viewSettings", "viewGuide", "viewAbout"):
                html = html.replace("</body>", "<script>(function(){var go=function(){var b=document.querySelector('.side-item[data-view=\"" + side + "\"]');if(b)b.click();};go();setTimeout(go,500);})();</script></body>")
            src = (qs.get("source") or [""])[0]
            if src in ("cpu", "disk", "gpu", "max"):
                html = html.replace("</body>", "<script>setTimeout(function(){var b=document.querySelector('#segSource button[data-v=\"" + src + "\"]');if(b&&!b.disabled)b.click();},1200);</script></body>")
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if p == "/phone":
            # 手机端预览:用固定宽度的 iframe 精确模拟窄屏媒体查询
            inner_qs = urllib.parse.urlencode([(k, v[0]) for k, v in qs.items()])
            inner = "/test?" + inner_qs
            w = int((qs.get("w") or ["390"])[0]); h = int((qs.get("h") or ["844"])[0])
            data = ("<!doctype html><html><head><meta charset='utf-8'><title>phone preview</title>"
                    "<style>html,body{margin:0;min-height:100vh;background:#050a14;display:flex;"
                    "align-items:flex-start;justify-content:center}iframe{width:%dpx;height:%dpx;"
                    "border:0;display:block}</style></head><body><iframe src='%s'></iframe></body></html>"
                    % (w, h, inner)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if p in ("/", "/index.html"):
            data = load_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif p == "/api/auth/status": self._out({"auth_enabled": False, "authenticated": True})
        elif p == "/api/status": self._out(status())
        elif p == "/api/config": self._out(CONFIG())
        elif p == "/api/hardware": self._out(hardware())
        elif p == "/api/logs": self._out(LOGS)
        else: self._out({"ok": False, "error": "Not Found"}, 404)

    def do_POST(self):
        ln = int(self.headers.get("Content-Length", 0) or 0)
        body = {}
        if ln:
            try: body = json.loads(self.rfile.read(ln))
            except Exception: body = {}
        p = self.path.split("?")[0]
        if p == "/api/config":
            if "poll_interval" in body: STATE["poll"] = int(body["poll_interval"])
            if isinstance(body.get("alert_webhook"), str):
                STATE["webhook"] = body["alert_webhook"].strip()
            zones = body.get("zones")
            if isinstance(zones, list) and zones:
                STATE["zones"] = [dict(z) for z in zones if isinstance(z, dict)]
                if len(STATE["zones"]) == 1:
                    sync_legacy_from_zone(STATE["zones"][0])
            self._out({"ok": True, "config": CONFIG()})
        elif p == "/api/mode":
            if body.get("mode") in ("default", "auto", "manual", "full"):
                STATE["mode"] = body["mode"]
                if STATE["zones"] is not None and STATE["zones"]:
                    STATE["zones"][0]["mode"] = body["mode"]
            self._out({"ok": True, "mode": STATE["mode"]})
        elif p.startswith("/api/zones/") and p.endswith("/config"):
            z = find_zone(p.split("/")[3])
            if z is None:
                self._out({"ok": False, "error": "zone not found"}, 404)
            else:
                if "temp_source" in body: z["temp_source"] = body["temp_source"]
                if "min_pwm_percent" in body: z["min_pwm_percent"] = int(body["min_pwm_percent"])
                if "manual_pwm_percent" in body: z["manual_pwm_percent"] = int(body["manual_pwm_percent"])
                if isinstance(body.get("curve"), list) and len(body["curve"]) >= 2:
                    z["curve"] = [dict(n) for n in body["curve"]]
                sync_legacy_from_zone(z)
                self._out({"ok": True, "zone": z})
        elif p.startswith("/api/zones/") and p.endswith("/mode"):
            z = find_zone(p.split("/")[3])
            if z is None:
                self._out({"ok": False, "error": "zone not found"}, 404)
            else:
                if body.get("mode") in ("default", "auto", "manual", "full"):
                    z["mode"] = body["mode"]
                    sync_legacy_from_zone(z)
                self._out({"ok": True})
        elif p == "/api/curve/generate":
            try:
                count = max(2, min(10, int(body.get("count", 6))))
                tmin = max(0, min(119, int(body.get("temp_min", 30))))
                tmax = max(tmin + count, min(120, int(body.get("temp_max", 80))))
                pmin = max(10, min(99, int(body.get("pwm_min", 20))))
                pmax = max(pmin + 1, min(100, int(body.get("pwm_max", 100))))
            except Exception:
                self._out({"ok": False, "error": "Invalid parameters"}, 400); return
            curve = []
            for i in range(count):
                ratio = i / (count - 1) if count > 1 else 1
                temp = round(tmin + (tmax - tmin) * ratio)
                pwm = round(pmin + (pmax - pmin) * (ratio ** 1.3))
                curve.append({"temp": temp, "pwm_percent": max(10, min(100, pwm))})
            self._out({"ok": True, "curve": curve})
        elif p == "/api/logs/clear": self._out({"ok": True, "message": "已清空"})
        elif p == "/api/auth/login": self._out({"ok": True})
        else: self._out({"ok": False, "error": "Not Found"}, 404)

    def log_message(self, *a): pass


if __name__ == "__main__":
    print("mock server v2 on http://127.0.0.1:9377")
    ThreadingHTTPServer(("127.0.0.1", 9377), H).serve_forever()

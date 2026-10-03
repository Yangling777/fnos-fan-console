# -*- coding: utf-8 -*-
"""config_manager 校验逻辑单元测试(不依赖 I/O)"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.join(_HERE, "..", "bin"),          # 资料包布局
              os.path.join(_HERE, "..", "src", "app", "bin")):  # 公开仓库布局
    if os.path.isdir(_cand):
        sys.path.insert(0, _cand)

from config_manager import (  # noqa: E402
    DEFAULT_CONFIG,
    _validate_curve,
    _validate_temp_source,
    _validate_webhook,
    normalize_config,
    validate_config,
)

VALID_CURVE = [
    {"temp": 30, "pwm_percent": 20},
    {"temp": 60, "pwm_percent": 70},
]


class ValidateCurveTests(unittest.TestCase):
    def test_valid_curve_kept(self):
        self.assertEqual(_validate_curve(VALID_CURVE), VALID_CURVE)

    def test_too_few_nodes_falls_back_to_default(self):
        result = _validate_curve([{"temp": 30, "pwm_percent": 20}])
        self.assertEqual(result, DEFAULT_CONFIG["curve"])
        self.assertIsNot(result, DEFAULT_CONFIG["curve"], "应返回深拷贝")

    def test_too_many_nodes_falls_back(self):
        nodes = [{"temp": i * 10, "pwm_percent": 20 + i} for i in range(11)]
        self.assertEqual(_validate_curve(nodes), DEFAULT_CONFIG["curve"])

    def test_temp_out_of_range_falls_back(self):
        self.assertEqual(
            _validate_curve([{"temp": -1, "pwm_percent": 20}, {"temp": 60, "pwm_percent": 70}]),
            DEFAULT_CONFIG["curve"])
        self.assertEqual(
            _validate_curve([{"temp": 30, "pwm_percent": 20}, {"temp": 121, "pwm_percent": 70}]),
            DEFAULT_CONFIG["curve"])

    def test_non_increasing_temp_falls_back(self):
        self.assertEqual(
            _validate_curve([{"temp": 50, "pwm_percent": 20}, {"temp": 50, "pwm_percent": 70}]),
            DEFAULT_CONFIG["curve"])
        self.assertEqual(
            _validate_curve([{"temp": 60, "pwm_percent": 20}, {"temp": 50, "pwm_percent": 70}]),
            DEFAULT_CONFIG["curve"])

    def test_pwm_below_absolute_min_falls_back(self):
        self.assertEqual(
            _validate_curve([{"temp": 30, "pwm_percent": 9}, {"temp": 60, "pwm_percent": 70}]),
            DEFAULT_CONFIG["curve"])
        self.assertEqual(
            _validate_curve([{"temp": 30, "pwm_percent": 20}, {"temp": 60, "pwm_percent": 101}]),
            DEFAULT_CONFIG["curve"])

    def test_non_dict_node_falls_back(self):
        self.assertEqual(_validate_curve(["bad", {"temp": 60, "pwm_percent": 70}]),
                         DEFAULT_CONFIG["curve"])

    def test_missing_fields_fall_back(self):
        self.assertEqual(_validate_curve([{"temp": 30}, {"temp": 60, "pwm_percent": 70}]),
                         DEFAULT_CONFIG["curve"])

    def test_default_not_mutated_after_validation(self):
        before = repr(DEFAULT_CONFIG["curve"])
        _validate_curve([{"temp": 30, "pwm_percent": 20}, {"temp": 60, "pwm_percent": 70}])
        _validate_curve([])
        self.assertEqual(repr(DEFAULT_CONFIG["curve"]), before)


class ValidateTempSourceTests(unittest.TestCase):
    def test_all_valid_sources(self):
        for source in ("cpu", "disk", "gpu", "max"):
            self.assertEqual(_validate_temp_source(source), source)

    def test_invalid_falls_back_to_default(self):
        self.assertEqual(_validate_temp_source("core"), DEFAULT_CONFIG["temp_source"])
        self.assertEqual(_validate_temp_source(None), DEFAULT_CONFIG["temp_source"])
        self.assertEqual(_validate_temp_source(3), DEFAULT_CONFIG["temp_source"])


class ValidateWebhookTests(unittest.TestCase):
    """§2.4:告警 Webhook 校验(空 = 关闭,仅接受 http/https)"""

    def test_empty_means_disabled(self):
        self.assertEqual(_validate_webhook(""), "")
        self.assertEqual(_validate_webhook(None), "")
        self.assertEqual(_validate_webhook("   "), "")

    def test_http_and_https_accepted(self):
        self.assertEqual(_validate_webhook("https://example.com/hook"), "https://example.com/hook")
        self.assertEqual(_validate_webhook("http://192.168.1.5:8080/x"), "http://192.168.1.5:8080/x")
        self.assertEqual(_validate_webhook("  https://trimmed/x  "), "https://trimmed/x")

    def test_invalid_scheme_rejected(self):
        for bad in ("ftp://x", "javascript:alert(1)", "example.com/hook", 123, ["a"]):
            self.assertEqual(_validate_webhook(bad), "")

    def test_validate_config_includes_webhook(self):
        result = validate_config({"poll_interval": 2, "alert_webhook": "https://x/y"})
        self.assertEqual(result["alert_webhook"], "https://x/y")
        result2 = validate_config({"alert_webhook": "ftp://bad"})
        self.assertEqual(result2["alert_webhook"], "")


class ValidateConfigTests(unittest.TestCase):
    def test_flat_config_keeps_user_fields(self):
        raw = {
            "mode": "auto",
            "poll_interval": 5,
            "min_pwm_percent": 30,
            "temp_source": "gpu",
            "manual_pwm_percent": 40,
            "curve": VALID_CURVE,
            "fan_channel": "pwm4",
        }
        result = validate_config(raw)
        self.assertEqual(result["mode"], "auto")
        self.assertEqual(result["poll_interval"], 5)
        self.assertEqual(result["min_pwm_percent"], 30)
        self.assertEqual(result["temp_source"], "gpu")
        self.assertEqual(result["curve"], VALID_CURVE)
        self.assertEqual(result["fan_channel"], "pwm4")

    def test_flat_config_clamps_out_of_range(self):
        result = validate_config({"poll_interval": 999, "web_port": 80, "min_pwm_percent": 101})
        self.assertEqual(result["poll_interval"], DEFAULT_CONFIG["poll_interval"])
        self.assertEqual(result["web_port"], DEFAULT_CONFIG["web_port"])
        self.assertEqual(result["min_pwm_percent"], DEFAULT_CONFIG["min_pwm_percent"])

    def test_zones_config_filters_invalid_channels(self):
        raw = {"zones": [{
            "id": "front", "name": "前面板", "channels": ["pwm3", "bad"],
            "temp_source": "gpu", "mode": "auto",
            "min_pwm_percent": 20, "manual_pwm_percent": 50, "curve": VALID_CURVE,
        }]}
        result = validate_config(raw, available_pwm=["pwm3", "pwm4"])
        self.assertEqual(len(result["zones"]), 1)
        self.assertEqual(result["zones"][0]["channels"], ["pwm3"])
        self.assertEqual(result["zones"][0]["temp_source"], "gpu")

    def test_channel_conflict_drops_second_zone(self):
        def zone(zid, channel):
            return {"id": zid, "name": zid, "channels": [channel],
                    "temp_source": "cpu", "mode": "default",
                    "min_pwm_percent": 20, "manual_pwm_percent": 50, "curve": VALID_CURVE}

        raw = {"zones": [zone("a", "pwm3"), zone("b", "pwm3"), zone("c", "pwm4")]}
        result = validate_config(raw, available_pwm=["pwm3", "pwm4"])
        self.assertEqual([z["id"] for z in result["zones"]], ["a", "c"])

    def test_all_invalid_zones_fall_back_to_default_zone(self):
        raw = {"zones": [{"id": "x", "channels": ["pwm99"]}]}
        result = validate_config(raw, available_pwm=["pwm1"])
        self.assertEqual(len(result["zones"]), 1)
        self.assertEqual(result["zones"][0]["id"], "default")
        self.assertEqual(result["zones"][0]["channels"], ["pwm1"])


class NormalizeConfigTests(unittest.TestCase):
    def test_flat_config_wrapped_into_default_zone(self):
        cfg = {
            "fan_channel": "pwm4", "temp_source": "gpu", "mode": "manual",
            "min_pwm_percent": 25, "manual_pwm_percent": 60, "curve": VALID_CURVE,
        }
        normalized = normalize_config(cfg)
        self.assertIn("zones", normalized)
        self.assertEqual(len(normalized["zones"]), 1)
        zone = normalized["zones"][0]
        self.assertEqual(zone["id"], "default")
        self.assertEqual(zone["channels"], ["pwm4"])
        self.assertEqual(zone["temp_source"], "gpu")
        self.assertEqual(zone["mode"], "manual")
        # 原有扁平字段保留
        self.assertEqual(normalized["fan_channel"], "pwm4")

    def test_zones_config_returned_as_is(self):
        cfg = {"zones": [{"id": "a"}]}
        self.assertIs(normalize_config(cfg), cfg)


if __name__ == "__main__":
    unittest.main()

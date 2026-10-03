# -*- coding: utf-8 -*-
"""fan_controller 核心逻辑单元测试(不依赖 sysfs,可在 Windows 本地运行)

覆盖:
- _interpolate_curve 线性插值
- _get_effective_temp 各温度来源与回退
- 温度读取失败保护(§1.2):按所选来源(cpu/disk/gpu/max)生效
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.join(_HERE, "..", "bin"),          # 资料包布局
              os.path.join(_HERE, "..", "src", "app", "bin")):  # 公开仓库布局
    if os.path.isdir(_cand):
        sys.path.insert(0, _cand)

from fan_controller import (  # noqa: E402
    FanController,
    TEMP_DEGRADE_THRESHOLD,
    TEMP_FULL_SPEED_THRESHOLD,
)


class FakeHardware:
    """无 sysfs 的假硬件:模拟温度读数并记录 PWM 写入"""

    def __init__(self, cpu_temp=40.0, disk_temps=None, gpu_temp=None, gpu_driver="i915"):
        self.cpu_temp = cpu_temp
        self.disk_temps = dict(disk_temps or {})
        self.gpu_temp = gpu_temp
        self.gpu_temp_driver = gpu_driver
        self.read_fail_count = 0
        self.hw_detected = True
        self.writes = []  # [(value, channel, min_percent)]

    def read_cpu_temp(self):
        return self.cpu_temp

    def read_disk_temps(self):
        return dict(self.disk_temps)

    def read_gpu_temp(self):
        return self.gpu_temp

    def write_pwm(self, value, channel="pwm2", min_percent=25):
        self.writes.append((value, channel, min_percent))
        return True

    def set_pwm_mode(self, mode, channel="pwm2"):
        return True

    def read_pwm_enable(self, channel="pwm2"):
        return 1

    def read_pwm(self, channel="pwm2"):
        return 128

    def read_fan_rpm(self, channel="pwm2"):
        return 900

    def reset_read_fail_count(self):
        self.read_fail_count = 0


class FakeConfigManager:
    def __init__(self):
        self.zone_updates = []

    def get(self):
        return {}

    def update_zone(self, zone_id, partial):
        self.zone_updates.append((zone_id, dict(partial)))
        return dict(partial)


def make_zone(source="cpu", mode="auto", channels=("pwm3", "pwm4")):
    return {
        "id": "default",
        "name": "系统风扇",
        "channels": list(channels),
        "temp_source": source,
        "mode": mode,
        "min_pwm_percent": 20,
        "manual_pwm_percent": 50,
        "curve": [
            {"temp": 30, "pwm_percent": 20},
            {"temp": 80, "pwm_percent": 100},
        ],
    }


def make_controller(hw=None):
    hw = hw if hw is not None else FakeHardware()
    cfg = FakeConfigManager()
    fc = FanController(hw, cfg)
    return fc, hw, cfg


class InterpolateCurveTests(unittest.TestCase):
    CURVE = [
        {"temp": 30, "pwm_percent": 20},
        {"temp": 50, "pwm_percent": 60},
        {"temp": 80, "pwm_percent": 100},
    ]

    def test_below_first_node_clamps_to_first(self):
        self.assertEqual(FanController._interpolate_curve(10, self.CURVE), int(255 * 20 / 100))

    def test_above_last_node_clamps_to_last(self):
        self.assertEqual(FanController._interpolate_curve(95, self.CURVE), 255)

    def test_exact_node_values(self):
        self.assertEqual(FanController._interpolate_curve(30, self.CURVE), 51)
        self.assertEqual(FanController._interpolate_curve(50, self.CURVE), 153)
        self.assertEqual(FanController._interpolate_curve(80, self.CURVE), 255)

    def test_linear_interpolation_between_nodes(self):
        # 40°C 位于节点 30(20%) 与 50(60%) 之间 → 40% → int(255*0.4)=102
        self.assertEqual(FanController._interpolate_curve(40, self.CURVE), 102)

    def test_empty_curve_returns_safe_default(self):
        self.assertEqual(FanController._interpolate_curve(50, []), 128)


class EffectiveTempTests(unittest.TestCase):
    def test_cpu_source(self):
        self.assertEqual(FanController._get_effective_temp(42.0, {"sda": 30.0}, 55.0, "cpu"), 42.0)

    def test_disk_source_uses_hottest_disk(self):
        self.assertEqual(
            FanController._get_effective_temp(42.0, {"sda": 31.0, "sdb": 44.0}, 55.0, "disk"), 44.0)

    def test_disk_source_falls_back_to_cpu_when_empty(self):
        self.assertEqual(FanController._get_effective_temp(42.0, {}, 55.0, "disk"), 42.0)

    def test_gpu_source(self):
        self.assertEqual(FanController._get_effective_temp(42.0, {}, 55.0, "gpu"), 55.0)

    def test_gpu_source_falls_back_to_cpu(self):
        self.assertEqual(FanController._get_effective_temp(42.0, {}, None, "gpu"), 42.0)

    def test_max_source_includes_gpu_and_disks(self):
        self.assertEqual(FanController._get_effective_temp(42.0, {"sda": 30.0}, 55.0, "max"), 55.0)
        self.assertEqual(FanController._get_effective_temp(60.0, {"sda": 30.0}, 55.0, "max"), 60.0)

    def test_max_source_with_no_sensors(self):
        self.assertIsNone(FanController._get_effective_temp(None, {}, None, "max"))


class TempFailureCounterTests(unittest.TestCase):
    def test_cpu_and_max_sources_use_cpu_failure_count(self):
        fc, hw, _ = make_controller()
        hw.read_fail_count = 2
        self.assertEqual(fc._zone_temp_fail_count(make_zone("cpu")), 2)
        self.assertEqual(fc._zone_temp_fail_count(make_zone("max")), 2)

    def test_disk_counter_counts_only_when_all_readings_missing(self):
        fc, _, _ = make_controller()
        fc._update_temp_failure_counters({}, 30.0)
        fc._update_temp_failure_counters({}, 30.0)
        self.assertEqual(fc._zone_temp_fail_count(make_zone("disk")), 2)
        # 任意一路硬盘读数恢复 → 计数清零
        fc._update_temp_failure_counters({"sda": 31.0}, 30.0)
        self.assertEqual(fc._zone_temp_fail_count(make_zone("disk")), 0)

    def test_gpu_counter_tracks_missing_raw_reading(self):
        fc, _, _ = make_controller(FakeHardware(gpu_temp=None, gpu_driver="i915"))
        for _ in range(3):
            fc._update_temp_failure_counters({"sda": 30.0}, None)
        self.assertEqual(fc._zone_temp_fail_count(make_zone("gpu")), 3)
        fc._update_temp_failure_counters({"sda": 30.0}, 41.0)
        self.assertEqual(fc._zone_temp_fail_count(make_zone("gpu")), 0)

    def test_gpu_without_sensor_never_counts(self):
        fc, _, _ = make_controller(FakeHardware(gpu_temp=None, gpu_driver=None))
        for _ in range(5):
            fc._update_temp_failure_counters({"sda": 30.0}, None)
        self.assertEqual(fc._zone_temp_fail_count(make_zone("gpu")), 0)


class SourceProtectionTests(unittest.TestCase):
    """§1.2:温度失败保护按所选来源生效"""

    def test_gpu_missing_triggers_full_speed_protection(self):
        fc, hw, _ = make_controller(FakeHardware(cpu_temp=45.0, gpu_temp=None, gpu_driver="i915"))
        zone = make_zone("gpu")

        for _ in range(TEMP_FULL_SPEED_THRESHOLD - 1):
            fc._control_all_zones({"zones": [zone]})
        self.assertTrue(hw.writes)
        self.assertTrue(all(w[0] != 255 for w in hw.writes), "未到阈值不应全速")

        hw.writes.clear()
        fc._control_all_zones({"zones": [zone]})
        self.assertTrue(hw.writes)
        self.assertTrue(all(w[0] == 255 and w[2] == 0 for w in hw.writes), "GPU 缺失达阈值应全速保护")
        self.assertIn("全速保护", fc.get_logs()[-1]["message"])

    def test_disk_empty_triggers_full_speed_protection(self):
        fc, hw, _ = make_controller(FakeHardware(cpu_temp=45.0, disk_temps={}, gpu_driver=None))
        zone = make_zone("disk")
        for _ in range(TEMP_FULL_SPEED_THRESHOLD - 1):
            fc._control_all_zones({"zones": [zone]})
        hw.writes.clear()
        fc._control_all_zones({"zones": [zone]})
        self.assertTrue(all(w[0] == 255 for w in hw.writes))

    def test_sustained_disk_failure_degrades_zone(self):
        fc, hw, cfg = make_controller(FakeHardware(cpu_temp=45.0, disk_temps={}, gpu_driver=None))
        zone = make_zone("disk")
        for _ in range(TEMP_DEGRADE_THRESHOLD):
            fc._control_all_zones({"zones": [zone]})
        self.assertTrue(cfg.zone_updates)
        self.assertEqual(cfg.zone_updates[-1], ("default", {"mode": "default"}))

    def test_cpu_failure_does_not_trigger_disk_zone(self):
        fc, hw, cfg = make_controller(
            FakeHardware(cpu_temp=45.0, disk_temps={"sda": 30.0}, gpu_driver=None))
        hw.read_fail_count = 99  # CPU 温度连续失败,但区域来源是硬盘且硬盘正常
        fc._control_all_zones({"zones": [make_zone("disk")]})
        self.assertTrue(hw.writes)
        self.assertTrue(all(w[0] != 255 for w in hw.writes))
        self.assertFalse(cfg.zone_updates)

    def test_cpu_failure_still_protects_cpu_zone(self):
        fc, hw, _ = make_controller(
            FakeHardware(cpu_temp=45.0, disk_temps={"sda": 30.0}, gpu_driver=None))
        hw.read_fail_count = TEMP_FULL_SPEED_THRESHOLD
        fc._control_all_zones({"zones": [make_zone("cpu")]})
        self.assertTrue(all(w[0] == 255 for w in hw.writes))

    def test_max_source_uses_cpu_failure_count(self):
        fc, hw, _ = make_controller(
            FakeHardware(cpu_temp=45.0, disk_temps={}, gpu_temp=None, gpu_driver="i915"))
        hw.read_fail_count = TEMP_FULL_SPEED_THRESHOLD
        fc._control_all_zones({"zones": [make_zone("max")]})
        self.assertTrue(all(w[0] == 255 for w in hw.writes))


class AlertTransitionTests(unittest.TestCase):
    """§2.4:告警状态迁移(全速保护 → 降级 → 恢复正常)"""

    def _run_sequence(self, counts):
        fc, hw, cfg = make_controller(
            FakeHardware(cpu_temp=45.0, disk_temps={"sda": 30.0}, gpu_driver=None))
        events = []
        fc._send_alert = lambda event, zone, message: events.append(event)
        for count in counts:
            hw.read_fail_count = count
            fc._control_all_zones({"zones": [make_zone("cpu")]})
        return fc, hw, cfg, events

    def test_full_transition_sequence(self):
        _, _, _, events = self._run_sequence([0, 3, 3, 5, 0, 0])
        self.assertEqual(events, ["full_speed", "degraded", "recovered"])

    def test_repeated_same_state_no_duplicate_event(self):
        _, _, _, events = self._run_sequence([3, 3, 3, 3])
        self.assertEqual(events, ["full_speed"])

    def test_recovery_then_relapse(self):
        _, _, _, events = self._run_sequence([3, 0, 4, 0])
        self.assertEqual(events, ["full_speed", "recovered", "full_speed", "recovered"])

    def test_alert_state_exposed_in_status(self):
        fc, hw, _ = make_controller(
            FakeHardware(cpu_temp=45.0, disk_temps={"sda": 30.0}, gpu_driver=None))
        hw.read_fail_count = TEMP_FULL_SPEED_THRESHOLD
        fc._control_all_zones({"zones": [make_zone("cpu")]})
        status = fc.get_status()
        self.assertEqual(status["zones"]["default"]["alert_state"], "protect")

    def test_alert_logged_even_without_webhook(self):
        fc, hw, _ = make_controller(
            FakeHardware(cpu_temp=45.0, disk_temps={"sda": 30.0}, gpu_driver=None))
        hw.read_fail_count = TEMP_FULL_SPEED_THRESHOLD
        fc._control_all_zones({"zones": [make_zone("cpu")]})
        self.assertTrue(any("全速保护" in entry["message"] for entry in fc.get_logs()))


if __name__ == "__main__":
    unittest.main()

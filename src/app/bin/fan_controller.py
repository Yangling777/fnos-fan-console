"""
风扇控制核心 — 温控线程、模式管理、异常降级

支持多风扇区域独立控制。每个区域绑定独立的 PWM 通道、温度来源和温控曲线。
单区域时行为与之前完全一致。

运行模式（每个区域独立）：
- default: 使用保守温控曲线，pwm_enable=1
- auto: 按自定义温控曲线调节 PWM
- manual: 固定 PWM 值
- full: PWM=255 全速
"""

import collections
import json
import logging
import threading
import time
import urllib.request

from hardware import Hardware, PWM_ENABLE_MANUAL
from config_manager import ConfigManager, DEFAULT_SAFE_CURVE, normalize_config

logger = logging.getLogger(__name__)

LOG_BUFFER_SIZE = 100

# 温度读取失败阈值
TEMP_FULL_SPEED_THRESHOLD = 3   # 连续失败 N 次后全速保护
TEMP_DEGRADE_THRESHOLD = 5      # 连续失败 N 次后降级到默认模式
MAX_PWM_WRITE_FAILURES = 3      # PWM 写入连续失败 N 次后降级


class FanController(threading.Thread):
    """风扇控制守护线程，遍历所有区域执行控制周期"""

    MODE_DEFAULT = "default"
    MODE_AUTO = "auto"
    MODE_MANUAL = "manual"
    MODE_FULL = "full"

    def __init__(self, hardware: Hardware, config_manager: ConfigManager):
        super().__init__(daemon=True, name="FanController")
        self._hw = hardware
        self._cfg = config_manager
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        self._start_time: float = time.time()
        self._logs = collections.deque(maxlen=LOG_BUFFER_SIZE)

        # 模式切换时通知守护线程立即执行一次控制周期
        self._mode_changed = threading.Event()

        # 区域级状态
        self._zone_states: dict[str, dict] = {}
        self._degraded_zones: set[str] = set()
        self._write_fail_counts: dict[str, int] = {}

        # 温度来源级连续失败计数(§1.2:保护按所选来源生效)
        self._disk_fail_count: int = 0   # 连续"无任何硬盘读数"的周期数
        self._gpu_fail_count: int = 0    # 连续"GPU 原始读数缺失"的周期数

        # 告警状态机(§2.4):zone_id -> "ok" / "protect" / "degrade"
        # 状态迁移时触发浏览器通知(前端轮询 alert_state)与 Webhook POST
        self._zone_alert_state: dict[str, str] = {}

    def run(self):
        """主控制循环"""
        config = self._cfg.get()
        normalized = normalize_config(config)
        zones = normalized["zones"]

        # 初始化所有区域的 pwm_enable=1（手动模式）
        for zone in zones:
            for ch in zone["channels"]:
                self._hw.set_pwm_mode(PWM_ENABLE_MANUAL, ch)

        logger.info("风扇控制线程启动，区域数: %d", len(zones))
        zone_desc = ", ".join(
            "{}({})".format(z["name"], "+".join(z["channels"])) for z in zones
        )
        self.add_log("info", "服务启动，{} 个区域: {}".format(len(zones), zone_desc))

        while not self._stop_event.is_set():
            try:
                config = self._cfg.get()
                normalized = normalize_config(config)
                self._control_all_zones(normalized)
            except Exception as e:
                logger.error("控制循环异常: %s", e)
                self.add_log("error", "控制循环异常: {}".format(e))

            poll_interval = config.get("poll_interval", 2)
            self._mode_changed.wait(timeout=poll_interval)
            self._mode_changed.clear()

        logger.info("风扇控制线程退出")

    def _control_all_zones(self, config: dict):
        """遍历所有区域执行控制周期(单线程,一次读温多次写 PWM)

        §1.2:温度读取失败保护按"区域所选来源"分别生效——
        cpu/max 看 CPU 连续失败计数,disk 看连续无硬盘读数,GPU 看原始读数缺失;
        各来源互不牵连。
        """
        cpu_temp = self._hw.read_cpu_temp()
        disk_temps = self._hw.read_disk_temps()
        gpu_temp = self._hw.read_gpu_temp()
        self._update_temp_failure_counters(disk_temps, gpu_temp)

        for zone in config["zones"]:
            fail_count = self._zone_temp_fail_count(zone)
            self._notify_zone_transition(zone, fail_count)
            if fail_count >= TEMP_DEGRADE_THRESHOLD:
                # 所选来源连续失败超过降级阈值,该区域降级
                self._degrade_zone(
                    zone, "温度连续读取失败 {} 次".format(fail_count),
                    source=zone.get("temp_source"))
                continue
            if fail_count >= TEMP_FULL_SPEED_THRESHOLD:
                # 达到全速阈值但未降级,该区域全速保护
                msg = "温度读取连续失败 {} 次,全速保护".format(fail_count)
                logger.warning(msg)
                self.add_log("warn", msg)
                for ch in zone["channels"]:
                    self._hw.write_pwm(255, ch, min_percent=0)
                self._update_zone_status(zone, cpu_temp, disk_temps, gpu_temp, 255)
                continue
            self._control_zone(zone, cpu_temp, disk_temps, gpu_temp)

    def _update_temp_failure_counters(self, disk_temps: dict, gpu_temp):
        """按来源统计"连续读取失败"周期数(§1.2)

        - disk:本周期完全没有硬盘读数时 +1,否则清零;
        - gpu:仅在已探测到 GPU 传感器、但原始读数缺失时 +1
          (不能用 _get_effective_temp 回退后的 CPU 值判定);无传感器时保持 0。
        - cpu / max:沿用 Hardware 的 CPU 连续读取失败计数,无需在此统计。
        """
        if disk_temps:
            self._disk_fail_count = 0
        else:
            self._disk_fail_count += 1

        if self._hw.gpu_temp_driver is None:
            self._gpu_fail_count = 0
        elif gpu_temp is None:
            self._gpu_fail_count += 1
        else:
            self._gpu_fail_count = 0

    def _zone_temp_fail_count(self, zone: dict) -> int:
        """返回区域所选温度来源的连续读取失败次数(§1.2)"""
        source = zone.get("temp_source")
        if source == "disk":
            return self._disk_fail_count
        if source == "gpu":
            return self._gpu_fail_count
        return self._hw.read_fail_count

    # ── 告警通知(§2.4)────────────────────────────────────

    def _alert_state_for(self, fail_count: int) -> str:
        """根据连续失败次数映射告警状态"""
        if fail_count >= TEMP_DEGRADE_THRESHOLD:
            return "degrade"
        if fail_count >= TEMP_FULL_SPEED_THRESHOLD:
            return "protect"
        return "ok"

    def _notify_zone_transition(self, zone: dict, fail_count: int):
        """告警状态迁移:全速保护 / 降级 / 恢复正常(§2.4)

        状态存于 _zone_alert_state,并经状态接口的 zones[*].alert_state 暴露给前端,
        前端据此弹浏览器通知;同时(配置了 alert_webhook 时)异步 POST Webhook。
        """
        zone_id = zone["id"]
        state = self._alert_state_for(fail_count)
        prev = self._zone_alert_state.get(zone_id, "ok")
        if state == prev:
            return
        self._zone_alert_state[zone_id] = state
        if state == "protect":
            self._send_alert("full_speed", zone, "温度读取连续失败 {} 次,全速保护".format(fail_count))
        elif state == "degrade":
            self._send_alert("degraded", zone, "温度读取连续失败 {} 次,已降级为默认模式".format(fail_count))
        elif prev in ("protect", "degrade"):
            self._send_alert("recovered", zone, "温度读取恢复正常")

    def _send_alert(self, event: str, zone: dict, message: str):
        """发送告警:记日志 + (可选)异步 POST Webhook;失败仅记日志,不阻塞主循环"""
        self.add_log("warn" if event != "recovered" else "info",
                     "{}:{}".format(zone.get("name", zone.get("id", "?")), message))
        url = ""
        try:
            url = (self._cfg.get() or {}).get("alert_webhook", "") or ""
        except Exception:
            url = ""
        if not url:
            return
        payload = {
            "app": "fan-control",
            "event": event,   # full_speed / degraded / recovered
            "zone": {"id": zone.get("id"), "name": zone.get("name")},
            "message": message,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        threading.Thread(
            target=self._post_webhook, args=(url, payload), daemon=True, name="fc-webhook"
        ).start()

    @staticmethod
    def _post_webhook(url: str, payload: dict):
        """POST 告警 JSON(超时 5s);任何异常只记日志"""
        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, method="POST",
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            logger.info("告警 Webhook 已发送: %s", payload.get("event"))
        except Exception as e:
            logger.warning("告警 Webhook 发送失败: %s", e)

    def _control_zone(self, zone: dict, cpu_temp, disk_temps, gpu_temp):
        """单个区域的控制逻辑"""
        zone_id = zone["id"]
        mode = zone["mode"]
        channels = zone["channels"]

        # 1. 计算有效温度
        effective_temp = self._get_effective_temp(cpu_temp, disk_temps, gpu_temp, zone["temp_source"])

        # 2. 检查 pwm_enable 一致性（自愈）
        for ch in channels:
            current_enable = self._hw.read_pwm_enable(ch)
            if current_enable is not None and current_enable != PWM_ENABLE_MANUAL:
                logger.warning(
                    "区域 '%s' %s pwm_enable=%s，修正为 %d",
                    zone["name"], ch, current_enable, PWM_ENABLE_MANUAL,
                )
                self.add_log("warn", "区域 {} pwm_enable 自动修正".format(zone["name"]))
                if not self._hw.set_pwm_mode(PWM_ENABLE_MANUAL, ch):
                    self._degrade_zone(zone, "无法恢复 PWM 手动模式")
                    return

        # 3. 计算目标 PWM（温度失败检测已在 _control_all_zones 统一处理）
        target_pwm = self._calculate_target_pwm(mode, effective_temp, zone)

        # 5. 写入所有绑定通道
        if target_pwm is not None:
            for ch in channels:
                ok = self._hw.write_pwm(target_pwm, ch, zone["min_pwm_percent"])
                if not ok:
                    count = self._write_fail_counts.get(zone_id, 0) + 1
                    self._write_fail_counts[zone_id] = count
                    self.add_log("warn", "区域 {} PWM 写入失败 (连续 {} 次)".format(
                        zone["name"], count))
                    if count >= MAX_PWM_WRITE_FAILURES:
                        self._degrade_zone(zone, "PWM 连续写入失败 {} 次".format(count))
                        return
                else:
                    self._write_fail_counts[zone_id] = 0

        # 6. 更新区域状态
        actual_pwm = self._hw.read_pwm(channels[0]) if channels else None
        self._update_zone_status(zone, cpu_temp, disk_temps, gpu_temp, actual_pwm)

    @staticmethod
    def _get_effective_temp(cpu_temp, disk_temps, gpu_temp, source):
        """根据温度来源获取有效温度

        - cpu / disk / gpu:对应传感器温度(disk 无数据时回退 CPU;gpu 无数据时回退 CPU)
        - max:所有可用传感器中的最高值(含 GPU,探测到才参与)

        纯函数,便于单元测试(§2.1)。
        """
        if source == "cpu":
            return cpu_temp
        elif source == "disk":
            return max(disk_temps.values()) if disk_temps else cpu_temp
        elif source == "gpu":
            return gpu_temp if gpu_temp is not None else cpu_temp
        elif source == "max":
            temps = []
            if cpu_temp is not None:
                temps.append(cpu_temp)
            if gpu_temp is not None:
                temps.append(gpu_temp)
            temps.extend(disk_temps.values())
            return max(temps) if temps else None
        return cpu_temp

    def _calculate_target_pwm(self, mode, temp, zone):
        """根据模式计算目标 PWM 值"""
        if mode == self.MODE_DEFAULT:
            if temp is None:
                return None
            return self._interpolate_curve(temp, DEFAULT_SAFE_CURVE)
        if mode == self.MODE_FULL:
            return 255
        if mode == self.MODE_MANUAL:
            return int(255 * zone["manual_pwm_percent"] / 100)
        if mode == self.MODE_AUTO:
            if temp is None:
                return None
            return self._interpolate_curve(temp, zone["curve"])
        return None

    @staticmethod
    def _interpolate_curve(temp, curve):
        """线性插值计算温控曲线对应的 PWM 值"""
        if not curve:
            return 128

        if temp <= curve[0]["temp"]:
            return int(255 * curve[0]["pwm_percent"] / 100)

        if temp >= curve[-1]["temp"]:
            return int(255 * curve[-1]["pwm_percent"] / 100)

        for i in range(len(curve) - 1):
            t1, p1 = curve[i]["temp"], curve[i]["pwm_percent"]
            t2, p2 = curve[i + 1]["temp"], curve[i + 1]["pwm_percent"]
            if t1 <= temp <= t2:
                if t2 == t1:
                    return int(255 * p1 / 100)
                ratio = (temp - t1) / (t2 - t1)
                pwm_percent = p1 + (p2 - p1) * ratio
                return int(255 * pwm_percent / 100)

        return int(255 * curve[-1]["pwm_percent"] / 100)

    def _degrade_zone(self, zone: dict, reason: str, source: str | None = None):
        """区域级异常降级:恢复该区域为默认模式(保守曲线)

        Args:
            source: 触发降级的温度来源;仅重置对应来源的连续失败计数,
                    避免持续失败时反复触发保护(§1.2)。
        """
        zone_id = zone["id"]
        logger.error("区域 '%s' 异常降级: %s", zone["name"], reason)

        if source == "disk":
            self._disk_fail_count = 0
        elif source == "gpu":
            self._gpu_fail_count = 0
        else:
            self._hw.reset_read_fail_count()

        with self._lock:
            self._degraded_zones.add(zone_id)
            self._write_fail_counts[zone_id] = 0

        self.add_log("error", "区域 {} 降级: {}".format(zone["name"], reason))
        self._cfg.update_zone(zone_id, {"mode": "default"})

    def _update_zone_status(self, zone: dict, cpu_temp, disk_temps, gpu_temp, pwm_value):
        """更新指定区域的状态快照"""
        zone_id = zone["id"]
        channels = zone["channels"]
        rpm = self._hw.read_fan_rpm(channels[0]) if channels else None
        pwm_percent = round(pwm_value / 255 * 100) if pwm_value is not None else None

        zone_status = {
            "name": zone["name"],
            "channels": channels,
            "temp_source": zone["temp_source"],
            "temp": self._get_effective_temp(cpu_temp, disk_temps, gpu_temp, zone["temp_source"]),
            "fan_rpm": rpm,
            "pwm_value": pwm_value,
            "pwm_percent": pwm_percent,
            "mode": zone["mode"],
            "degraded": zone_id in self._degraded_zones,
            "alert_state": self._zone_alert_state.get(zone_id, "ok"),
        }

        with self._lock:
            self._zone_states[zone_id] = zone_status

    def add_log(self, level, message):
        """记录事件日志（操作、告警、错误）"""
        entry = {
            "time": time.strftime("%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
        }
        with self._lock:
            self._logs.append(entry)

    # ── 公共接口（Web API 调用）──────────────────────────

    def set_mode(self, mode: str, zone_id: str | None = None) -> bool:
        """切换运行模式（线程安全）

        Args:
            mode: 目标模式
            zone_id: 指定区域 ID，None 表示所有区域
        """
        if mode not in (self.MODE_DEFAULT, self.MODE_AUTO, self.MODE_MANUAL, self.MODE_FULL):
            logger.warning("无效模式: %s", mode)
            return False

        if not self._hw.hw_detected and mode != self.MODE_DEFAULT:
            logger.warning("硬件未探测到，仅允许默认模式")
            return False

        config = self._cfg.get()
        normalized = normalize_config(config)

        target_zones = normalized["zones"]
        if zone_id is not None:
            target_zones = [z for z in target_zones if z["id"] == zone_id]
            if not target_zones:
                logger.warning("区域 %s 不存在", zone_id)
                return False

        # 一次性读取温度（所有区域共享）
        cpu_temp = self._hw.read_cpu_temp()
        disk_temps = self._hw.read_disk_temps()
        gpu_temp = self._hw.read_gpu_temp()

        for zone in target_zones:
            # 设置 pwm_enable=1
            for ch in zone["channels"]:
                if not self._hw.set_pwm_mode(PWM_ENABLE_MANUAL, ch):
                    logger.error("set_pwm_mode 失败，模式切换中止")
                    return False

            # 立即写入对应 PWM
            effective_temp = self._get_effective_temp(
                cpu_temp, disk_temps, gpu_temp, zone["temp_source"])

            if mode == self.MODE_DEFAULT and effective_temp is not None:
                pwm_val = self._interpolate_curve(effective_temp, DEFAULT_SAFE_CURVE)
                for ch in zone["channels"]:
                    self._hw.write_pwm(pwm_val, ch, zone["min_pwm_percent"])
            elif mode == self.MODE_FULL:
                for ch in zone["channels"]:
                    self._hw.write_pwm(255, ch, min_percent=0)
            elif mode == self.MODE_MANUAL:
                pwm_val = int(255 * zone["manual_pwm_percent"] / 100)
                for ch in zone["channels"]:
                    self._hw.write_pwm(pwm_val, ch, zone["min_pwm_percent"])
            elif mode == self.MODE_AUTO and effective_temp is not None:
                pwm_val = self._interpolate_curve(effective_temp, zone["curve"])
                for ch in zone["channels"]:
                    self._hw.write_pwm(pwm_val, ch, zone["min_pwm_percent"])

            # 更新配置
            self._cfg.update_zone(zone["id"], {"mode": mode})

            # 清除降级状态
            with self._lock:
                self._degraded_zones.discard(zone["id"])
                self._write_fail_counts[zone["id"]] = 0
                self._zone_alert_state[zone["id"]] = "ok"

        self._hw.reset_read_fail_count()

        names = {"default": "默认模式", "auto": "自动模式", "manual": "手动模式", "full": "全速模式"}
        scope = "区域 {}".format(zone_id) if zone_id else "所有区域"
        self.add_log("info", "{} 切换到{}".format(scope, names.get(mode, mode)))
        logger.info("%s 切换到 %s", scope, mode)

        self._mode_changed.set()
        return True

    def get_status(self):
        """获取状态快照（兼容单区域和多区域）"""
        with self._lock:
            zone_states = dict(self._zone_states)
            degraded_zones = set(self._degraded_zones)

        cpu_temp = self._hw.read_cpu_temp()
        disk_temps = self._hw.read_disk_temps()
        gpu_temp = self._hw.read_gpu_temp()

        status = {
            "cpu_temp": cpu_temp,
            "disk_temps": disk_temps or {},
            "gpu_temp": gpu_temp,
            "hw_detected": self._hw.hw_detected,
            "uptime": int(time.time() - self._start_time),
            "zones": zone_states,
        }

        # 兼容单区域：提取第一个区域的字段到顶层
        if zone_states:
            first = next(iter(zone_states.values()))
            status["fan_rpm"] = first.get("fan_rpm")
            status["pwm_value"] = first.get("pwm_value")
            status["pwm_percent"] = first.get("pwm_percent")
            status["mode"] = first.get("mode", "default")
            status["degraded"] = bool(degraded_zones)
            status["degrade_reason"] = ""
            if degraded_zones:
                status["degrade_reason"] = "{} 个区域已降级".format(len(degraded_zones))
        else:
            status.update({
                "fan_rpm": None, "pwm_value": None, "pwm_percent": None,
                "mode": "default", "degraded": False, "degrade_reason": "",
            })

        return status

    def get_logs(self, count=20):
        """获取最近的运行日志"""
        with self._lock:
            return list(self._logs)[-count:]

    def clear_logs(self):
        """清空运行日志"""
        with self._lock:
            self._logs.clear()
        logger.info("运行日志已清空")

    def cleanup(self):
        """退出清理：恢复所有 PWM 为安全状态"""
        logger.info("执行退出清理...")
        self._hw.restore_safe_state()

    def stop(self):
        """停止控制线程"""
        self._stop_event.set()
        self._mode_changed.set()
        self.join(timeout=10)
        self.cleanup()

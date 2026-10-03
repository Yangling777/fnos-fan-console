# -*- coding: utf-8 -*-
"""hardware 纯函数单元测试(不依赖 sysfs;仅覆盖 safe_pwm_value 下限保护边界)"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.join(_HERE, "..", "bin"),          # 资料包布局
              os.path.join(_HERE, "..", "src", "app", "bin")):  # 公开仓库布局
    if os.path.isdir(_cand):
        sys.path.insert(0, _cand)

from hardware import ABSOLUTE_MIN_PWM, CHIP_DISPLAY_NAMES, safe_pwm_value  # noqa: E402


class ChipDisplayNameTests(unittest.TestCase):
    """§1.5:常见芯片应有友好显示名"""

    def test_nct6797_display_name(self):
        self.assertEqual(CHIP_DISPLAY_NAMES.get("nct6797"), "Nuvoton NCT6797D")

    def test_common_chips_covered(self):
        for name in ("nct6795", "nct6796", "nct6798", "it8688", "f71882fg"):
            self.assertIn(name, CHIP_DISPLAY_NAMES)


class SafePwmValueTests(unittest.TestCase):
    def test_target_above_both_minimums_kept(self):
        self.assertEqual(safe_pwm_value(200, 20), 200)

    def test_target_below_user_minimum_raised(self):
        self.assertEqual(safe_pwm_value(10, 20), int(255 * 20 / 100))

    def test_target_below_absolute_minimum_raised(self):
        self.assertEqual(safe_pwm_value(0, 0), ABSOLUTE_MIN_PWM)
        self.assertEqual(safe_pwm_value(5, 1), ABSOLUTE_MIN_PWM)

    def test_user_min_100_forces_max(self):
        self.assertEqual(safe_pwm_value(0, 100), 255)

    def test_bounds_within_valid_range(self):
        for target in (-50, 0, 10, 26, 100, 255):
            for min_percent in (0, 10, 20, 50, 100):
                value = safe_pwm_value(target, min_percent)
                self.assertGreaterEqual(value, ABSOLUTE_MIN_PWM)
                self.assertLessEqual(value, 255)

    def test_absolute_min_constant_is_about_ten_percent(self):
        # 26/255 ≈ 10.2%,与 config_manager.ABSOLUTE_MIN_PERCENT 的语义一致
        self.assertEqual(ABSOLUTE_MIN_PWM, 26)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""风扇控制器界面组装脚本(当前 v1.0)
- 基线:原始基线/index-original-v1.1.1.html(不可动,原版 v1.1.1 页面)
- 样式:样式/style-liquid-glass.css(玻璃基底) + 样式/layout-legion.css(布局补丁)
- 产物:源码/index.html(直接可部署)
- HTML 版式重组:左侧栏 + 仪表盘英雄卡 + 快捷卡片区(指针追光/壁纸/Legion 适配/曲线增强)
- 路径以本脚本所在位置自动推导,资料包整体搬移后无需改路径
"""
import os
import re

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # …/源码/
BASE = os.path.join(SRC, "原始基线", "index-original-v1.1.1.html")
C_BASE = os.path.join(SRC, "样式", "style-liquid-glass.css")
C_PATCH = os.path.join(SRC, "样式", "layout-legion.css")
OUT = os.path.join(SRC, "index.html")

html = open(BASE, encoding="utf-8").read()
css_base = open(C_BASE, encoding="utf-8").read()
css_patch = open(C_PATCH, encoding="utf-8").read()

# ══════ 0) 图标库(python 里定义,用于静态 HTML) ══════
I = {
"fan": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="12" r="2.1"/><path d="M12 9.9c0-3.6-1-6.1-3-6.1-1.6 0-2.7 1.5-2.7 3.1 0 2.2 2.2 3.5 5.7 3"/><path d="M14.1 12c3.6 0 6.1-1 6.1-3 0-1.6-1.5-2.7-3.1-2.7-2.2 0-3.5 2.2-3 5.7"/><path d="M12 14.1c0 3.6 1 6.1 3 6.1 1.6 0 2.7-1.5 2.7-3.1 0-2.2-2.2-3.5-5.7-3"/></svg>',
"home": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 10.5 12 4l8 6.5V20h-5.6v-5.2h-4.8V20H4z"/></svg>',
"chart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5h16"/><path d="M4.5 15.5l4.3-5 3.4 2.8 5.3-6.8"/></svg>',
"list": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.6" cy="6" r="1.1" fill="currentColor" stroke="none"/><circle cx="4.6" cy="12" r="1.1" fill="currentColor" stroke="none"/><circle cx="4.6" cy="18" r="1.1" fill="currentColor" stroke="none"/></svg>',
"sliders": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 4v16M12 4v16M18 4v16"/><circle cx="6" cy="9" r="2.1"/><circle cx="12" cy="15" r="2.1"/><circle cx="18" cy="7.5" r="2.1"/></svg>',
"book": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M5 5a2 2 0 0 1 2-2h12v15H7a2 2 0 0 0-2 2z"/><path d="M5 19.5a2 2 0 0 1 2-2h12"/></svg>',
"chev": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 6 8.5 12l6 6"/></svg>',
"thermo": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13.6V5.2a2 2 0 1 1 4 0v8.4a4.2 4.2 0 1 1-4 0z"/><circle cx="12" cy="17.6" r="1.3" fill="currentColor" stroke="none"/></svg>',
"bolt": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M13 3 5.5 13.5h5L9.5 21l7.5-10.5h-5z"/></svg>',
"clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="8.4"/><path d="M12 7.6V12l3 2"/></svg>',
"shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3.2l7 2.8v5.4c0 4.5-2.9 7.6-7 9.4-4.1-1.8-7-4.9-7-9.4V6z"/><path d="M9 11.6l2.1 2.1 4-4.3" stroke-linecap="round"/></svg>',
"manual": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M7.5 4v16M16.5 4v16"/><circle cx="7.5" cy="9.5" r="2.2"/><circle cx="16.5" cy="14.5" r="2.2"/></svg>',
"down": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 4v10.2M8 10.6l4 4 4-4"/><path d="M5 19.5h14"/></svg>',
"img": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/></svg>',
"grid": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="4" y="4" width="7" height="7" rx="1.6"/><rect x="13" y="4" width="7" height="7" rx="1.6"/><rect x="4" y="13" width="7" height="7" rx="1.6"/><rect x="13" y="13" width="7" height="7" rx="1.6"/></svg>',
"info": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 11.2V16"/><circle cx="12" cy="7.9" r="1.05" fill="currentColor" stroke="none"/></svg>',
"gpu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="7" y="7" width="10" height="10" rx="2"/><path d="M10 3.5v3M14 3.5v3M10 17.5v3M14 17.5v3M3.5 10h3M3.5 14h3M17.5 10h3M17.5 14h3"/></svg>',
"fanSm": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="2"/><path d="M12 10c0-3.4-.9-5.8-2.9-5.8-1.5 0-2.6 1.4-2.6 3 0 2.1 2.1 3.3 5.5 2.8"/><path d="M14 12c3.4 0 5.8-.9 5.8-2.9 0-1.5-1.4-2.6-3-2.6-2.1 0-3.3 2.1-2.8 5.5"/><path d="M12 14c0 3.4.9 5.8 2.9 5.8 1.5 0 2.6-1.4 2.6-3 0-2.1-2.1-3.3-5.5-2.8"/></svg>',
}

# ══════ 1) 组装 CSS(玻璃基底 → 顶栏命名替换 → 追加布局补丁) ══════
css = css_base
old_s = ".header,.card,.section,.zone-panel,.login-box{"
assert css.count(old_s) == 1
css = css.replace(old_s, ".topbar,.card,.section,.zone-panel,.login-box{")
old_s = ".header::after,.card::after,.section::after,.zone-panel::after,.login-box::after{"
assert css.count(old_s) == 1
css = css.replace(old_s, ".topbar::after,.card::after,.section::after,.zone-panel::after,.login-box::after{")
old_s = ".header{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;margin-bottom:16px}"
assert css.count(old_s) == 1
css = css.replace(old_s, ".topbar{display:flex;justify-content:space-between;align-items:center;flex:none}")
css = css + "\n" + css_patch

i = html.index("<style>")
j = html.index("</style>") + len("</style>")
html = html[:i] + "<style>\n" + css + "</style>" + html[j:]

# ══════ 1.5) 视口:补 viewport-fit=cover(iPhone 安全区,配合 v9.2 手机端适配) ══════
old_viewport = '<meta name="viewport" content="width=device-width,initial-scale=1">'
assert html.count(old_viewport) == 1, "viewport 标签未找到"
html = html.replace(old_viewport, '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">')

# ══════ 1.6) 版本号 v1.0(meta + 文件头注释,§2.10) ══════
old_vp = '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
assert html.count(old_vp) == 1, "viewport-fit 标签未找到"
html = html.replace(old_vp, old_vp + '\n<meta name="app-version" content="v1.0">')
# PWA(§2.7):manifest / 图标 / 主题色 / iOS 独立窗口
old_meta_v = '<meta name="app-version" content="v1.0">'
assert html.count(old_meta_v) == 1
html = html.replace(old_meta_v, old_meta_v +
    '\n<link rel="manifest" href="/manifest.webmanifest">'
    '\n<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
    '\n<meta name="theme-color" content="#0b1220">'
    '\n<meta name="mobile-web-app-capable" content="yes">'
    '\n<meta name="apple-mobile-web-app-capable" content="yes">'
    '\n<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
    '\n<meta name="apple-mobile-web-app-title" content="风扇控制器">')
old_doctype = "<!DOCTYPE html>\n"
assert html.count(old_doctype) == 1, "DOCTYPE 未找到"
html = html.replace(old_doctype, old_doctype + "<!-- 风扇控制器 v1.0 · 组装产物(请勿手改):源头 = 原始基线 + 样式 + 构建脚本/fc-assemble-legion.py -->\n", 1)

# ══════ 2) <body> 后插入壁纸层与折射滤镜 ══════
bg = """
<!-- 液态玻璃:壁纸层 + 折射滤镜 -->
<div class="bg" aria-hidden="true"><div class="bg-img" id="bgImg"></div><div class="orb orb-a"></div><div class="orb orb-b"></div><div class="orb orb-c"></div><div class="bg-vignette"></div><div class="bg-grain"></div></div>
<svg class="svg-defs" width="0" height="0" aria-hidden="true" focusable="false"><defs><filter id="lg-distort" x="-30%" y="-30%" width="160%" height="160%"><feTurbulence type="fractalNoise" baseFrequency="0.012 0.012" numOctaves="2" seed="92" result="noise"/><feGaussianBlur in="noise" stdDeviation="1.4" result="soft"/><feDisplacementMap in="SourceGraphic" in2="soft" scale="14" xChannelSelector="R" yChannelSelector="G"/></filter></defs></svg>
"""
assert html.count("<body>") == 1
html = html.replace("<body>", "<body>" + bg, 1)

# ══════ 3) 模式按钮:白色 SVG 图标(替换 emoji,含区域面板 JS 模板) ══════
SVG_DEFAULT = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5.2c0 4.4-2.9 7.3-7 8.8-4.1-1.5-7-4.4-7-8.8V6z"/><path d="M9 11.6l2.1 2.1 3.9-4.2"/></svg>'
SVG_AUTO = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19h16"/><path d="M5.5 14.5l4.2-4.8 3.4 2.6 5.4-6"/></svg>'
SVG_MANUAL = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4v16M17 4v16"/><circle cx="7" cy="9.5" r="2.4"/><circle cx="17" cy="14.5" r="2.4"/></svg>'
SVG_FULL = '<svg viewBox="0 0 24 24" fill="#fff" stroke="none"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
for old, new, expect in [
    ('<div class="m-icon">🔄</div>', '<div class="m-icon">' + SVG_DEFAULT + '</div>', 2),
    ('<div class="m-icon">📈</div>', '<div class="m-icon">' + SVG_AUTO + '</div>', 2),
    ('<div class="m-icon">🎚</div>', '<div class="m-icon">' + SVG_MANUAL + '</div>', 2),
    ('<div class="m-icon">🚀</div>', '<div class="m-icon">' + SVG_FULL + '</div>', 2),
]:
    assert html.count(old) == expect, f"m-icon 匹配异常: {old[:30]}"
    html = html.replace(old, new)

# ══════ 4) 曲线底部按钮:次要动作在左、主操作在右;恢复默认改文字样式 ══════
old_curve = """        <button class="btn" id="curveSaveBtn" onclick="saveCurve()">保存曲线</button>
        <button class="btn btn-secondary" onclick="resetCurve()">恢复默认</button>"""
new_curve = """        <button class="btn btn-ghost" onclick="resetCurve()">恢复默认</button>
        <button class="btn" id="curveSaveBtn" onclick="saveCurve()">保存曲线</button>"""
assert html.count(old_curve) == 1
html = html.replace(old_curve, new_curve)
old_reset = '<button class="btn btn-secondary" onclick="resetSettings()">恢复默认</button>'
new_reset = '<button class="btn btn-ghost" onclick="resetSettings()">恢复默认</button>'
assert html.count(old_reset) == 1
html = html.replace(old_reset, new_reset)

# ══════ 4.5) 曲线:未保存提醒(标题行常显提示;保存按钮由 JS 加高亮) ══════
old_edit_head = '''      <div class="section-title" style="margin-bottom:0"><span class="s-icon">📊</span> 温控曲线</div>
      <button class="btn btn-sm btn-secondary" id="curveEditBtn" onclick="toggleCurveEdit()">编辑曲线</button>'''
new_edit_head = '''      <div class="section-title" style="margin-bottom:0"><span class="s-icon">📊</span> 温控曲线</div>
      <span class="curve-dirty-note" id="curveDirtyNote">有未保存的修改</span>
      <button class="btn btn-sm btn-secondary" id="curveEditBtn" onclick="toggleCurveEdit()">编辑曲线</button>'''
assert html.count(old_edit_head) == 1, "曲线标题行未找到"
html = html.replace(old_edit_head, new_edit_head)

# ══════ 4.6) 温度来源:加入 GPU 选项(设置页单选) ══════
old_src_radio = '          <label><input type="radio" name="tempSource" value="disk"> 硬盘</label>\n'
new_src_radio = old_src_radio + '          <label><input type="radio" name="tempSource" value="gpu"> GPU</label>\n'
assert html.count(old_src_radio) == 1, "温度来源单选行未找到"
html = html.replace(old_src_radio, new_src_radio)

# ══════ 4.7) 使用说明:橙色虚线文案 + 新增"温度来源"小节(§1.3) ══════
old_guide_cpu = "<li>橙色虚线表示当前 CPU 温度位置。</li>"
assert html.count(old_guide_cpu) == 1, "guide 橙色虚线文案未找到"
html = html.replace(old_guide_cpu, "<li>橙色虚线表示当前温度位置(跟随所选温度来源)。</li>")

old_guide_sec = """        <div class="guide-section">
          <h3>安全机制</h3>"""
new_guide_sec = """        <div class="guide-section">
          <h3>温度来源</h3>
          <ul>
            <li><b>CPU</b> — 以处理器温度(Intel coretemp / AMD k10temp 等)为调速依据。</li>
            <li><b>硬盘</b> — 以所有硬盘(drivetemp)中的最高温度为依据,适合散热重点在硬盘仓的机器。</li>
            <li><b>GPU</b> — 以显卡温度(amdgpu / nvidia / i915 等,含 nvidia-smi 回退)为依据;未检测到传感器时该选项自动置灰。</li>
            <li><b>最高值</b> — 取所有可用传感器(CPU、硬盘、GPU)中的最高温度,任何一路偏热都会及时提高转速,最稳妥。</li>
            <li>可在首页“温度来源”卡片或“高级设置”中切换;曲线图上的橙色虚线跟随所选来源显示当前温度。</li>
          </ul>
        </div>
        <div class="guide-section">
          <h3>区域管理(多风扇)</h3>
          <ul>
            <li>侧栏「区域管理」可为每个风扇区域绑定独立的 PWM 通道、温度来源、最低转速与温控曲线,适合机箱有多路风扇的机器;</li>
            <li>新增 / 编辑:勾选 PWM 通道(同一通道不可被多个区域占用)、选择来源、设置下限、调整 2–10 节点曲线;</li>
            <li>区域超过 1 个时,首页会自动切换为“每个区域一张状态卡”(含独立模式切换);单区域用户无需使用本页;</li>
            <li>最后一个区域不可删除;保存后立即生效,可在首页查看各区域的温度 / 转速 / PWM。</li>
          </ul>
        </div>
        <div class="guide-section">
          <h3>温度趋势与日志</h3>
          <ul>
            <li>首页仪表盘下方为“温度趋势”小图:按轮询间隔采样,保留最近约 2 分钟(60 个点)的 CPU / GPU / 硬盘温度曲线;</li>
            <li>「运行日志」页进入后每 5 秒自动刷新,离开页面即停止;支持按 全部 / 信息 / 警告 / 错误 筛选;</li>
            <li>「导出」把当前日志保存为 .log 文本;「清空」清除应用内运行日志(不影响主机系统日志)。</li>
          </ul>
        </div>
        <div class="guide-section">
          <h3>通知与告警</h3>
          <ul>
            <li>「高级设置 → 告警通知」可开启浏览器通知(需授权):出现<b>全速保护 / 高温降级 / 恢复正常</b>时按区域提醒;</li>
            <li>「告警 Webhook」填写一个 http(s) 地址(留空关闭),应用会以 JSON 形式 POST 告警事件(事件类型、区域、原因、时间),Bark / 钉钉可直接填 URL;</li>
            <li>Webhook 发送失败只记入运行日志,不影响风扇控制。</li>
          </ul>
        </div>
        <div class="guide-section">
          <h3>备份与恢复</h3>
          <ul>
            <li>「高级设置 → 配置备份」可将当前配置(曲线、来源、下限、区域等)导出为 JSON 文件;</li>
            <li>导入时先做格式校验并二次确认,成功后一键还原;运行模式与端口不在导入范围内(保持当前值);</li>
            <li>壁纸图片仅保存在本机浏览器(localStorage),不会上传服务器;清理浏览器数据会丢失,重新选择即可。</li>
          </ul>
        </div>
        <div class="guide-section">
          <h3>安全机制</h3>"""
assert html.count(old_guide_sec) == 1, "guide 安全机制锚点未找到"
html = html.replace(old_guide_sec, new_guide_sec)

# ══════ 4.8) 使用说明:手机端与添加到主屏(§2.7) ══════
old_guide_uninstall = """        <div class="guide-section">
          <h3>卸载与重装</h3>"""
new_guide_uninstall = """        <div class="guide-section">
          <h3>手机端与添加到主屏</h3>
          <ul>
            <li>手机浏览器访问本页面会自动切换为窄屏布局(底部导航 + 单列卡片);</li>
            <li>支持“添加到主屏”:iPhone 用 Safari「分享 → 添加到主屏幕」;安卓用 Chrome 菜单「添加到主屏幕」,打开后为独立窗口样式(PWA);</li>
            <li>局域网 HTTP 环境下,部分安卓机型仅生成快捷方式形态,不影响使用。</li>
          </ul>
        </div>
        <div class="guide-section">
          <h3>卸载与重装</h3>"""
assert html.count(old_guide_uninstall) == 1, "guide 卸载锚点未找到"
html = html.replace(old_guide_uninstall, new_guide_uninstall)

# ══════ 5) 版式重组:抽出单区域模式块 → 删除旧头部 → 替换状态卡片为新布局 ══════
i1 = html.index("  <!-- 运行模式（单区域时使用） -->")
i2 = html.index("  <!-- 温控曲线 -->")
single_block = html[i1:i2]
html = html[:i1] + html[i2:]

h1 = html.index("  <!-- 顶部 -->")
h2 = html.index("  <!-- 告警 -->")
html = html[:h1] + html[h2:]

GRIDS = """  <!-- 温控仪表盘(英雄卡) + 快捷卡片 -->
  <div class="top-grid">
    <div class="card hero">
      <div class="hero-head">
        <div class="hero-title">系统风扇 · 温控仪表盘 <div class="status-badge ok" id="statusBadge"><div class="pulse ok" id="statusDot"></div><span id="statusText">运行中</span></div></div>
        <div class="hw-chip" id="hwChip">硬件检测中…</div>
      </div>
      <div class="hero-body">
        <div class="gauge-col">
          <div class="card c-cpu" id="cardCpu">
            <div class="gauge" id="gaugeCpu">
              <div class="g-center">
                <div class="g-label">@@THERMO@@ CPU 温度</div>
                <div class="g-num"><span class="card-value temp-safe" id="cpuTemp">--<span class="card-unit">°C</span></span></div>
              </div>
            </div>
          </div>
          <div class="gauge-stats">
            <div class="stat">@@FANSM@@<b class="card-value" id="fanRpm">--<span class="card-unit"> RPM</span></b></div>
            <div class="stat">@@CLOCK@@<b class="card-value" id="heroPoll">2.0</b><span style="font-size:11px;color:var(--text2)">s 轮询</span></div>
            <div class="stat" id="gpuStat" style="display:none">@@GPU@@ GPU <b class="card-value" id="gpuTemp">--</b><span class="card-unit">°C</span></div>
            <span id="cardFan" hidden></span>
          </div>
        </div>
        <div class="center-col">
          <div class="tag-heat">散热</div>
          <span class="tag-side tag-cpu">CPU</span>
          <span class="tag-side tag-gpu">SYS</span>
          <div class="pentagon" id="pentagon"></div>
          <div class="gauge gauge--mini" id="gaugePwm">
            <div class="g-center">
              <div class="g-label" style="margin-bottom:0">@@BOLT@@ PWM</div>
              <div class="g-num"><span class="card-value" id="pwmPercent">--<span class="card-unit">%</span></span></div>
            </div>
          </div>
          <div class="progress-bar"><div class="progress-fill" id="pwmBar" style="width:0"></div></div>
        </div>
        <div class="gauge-col">
          <div class="card c-disk" id="cardDisk">
            <div class="gauge" id="gaugeDisk">
              <div class="g-center">
                <div class="g-label">@@THERMO@@ 硬盘温度</div>
                <div class="g-num"><span class="card-value" id="diskTemp">--<span class="card-unit">°C</span></span></div>
              </div>
            </div>
          </div>
          <div class="gauge-stats">
            <div class="stat" style="font-size:11.5px">🌡 来源 <b class="card-value" id="heroSource" style="font-size:12.5px">最高值</b></div>
          </div>
          <div class="card-sub hero-disk-detail" id="diskDetail"></div>
        </div>
      </div>
      <div class="spark-wrap" id="sparkWrap">
        <div class="spark-head">
          <span class="spark-title">温度趋势 · 最近 2 分钟</span>
          <span class="spark-legend" id="sparkLegend"></span>
        </div>
        <svg class="spark-svg" id="sparkSvg" viewBox="0 0 640 128" role="img" aria-label="温度趋势小图"></svg>
      </div>
@@SINGLE_MODE@@
    </div>

    <div class="mini-grid">
      <div class="card mini-card">
        <span class="m-icon">@@SHIELD@@</span>
        <h3>运行状态</h3>
        <p>看门狗守护正常,异常时自动恢复安全状态</p>
        <div class="m-foot">
          <span class="dot-ok"><i></i><span id="stateText">运行中</span></span>
          <span class="m-state" id="upTimeText">—</span>
        </div>
      </div>
      <div class="card mini-card promo promo--red" data-act="full" style="cursor:pointer">
        <h3 class="big">紧急散热</h3>
        <p class="sub">全速 100% 转速<br>适用于高温场景</p>
        <span class="link">立即启动 ›</span>
        <span class="glyph">FULL</span>
      </div>
      <div class="card mini-card">
        <span class="m-icon">@@MANUAL@@</span>
        <h3>手动模式</h3>
        <p>固定转速运行,适合调试与特殊场景</p>
        <div class="m-foot">
          <span class="m-state" id="manualState">未启用</span>
          <label class="switch"><input type="checkbox" id="swManualUI"><i></i></label>
        </div>
      </div>
      <div class="card mini-card promo promo--blue" data-act="curve" style="cursor:pointer">
        <h3 class="big">温控曲线</h3>
        <p class="sub">2–10 节点自定义<br>低温安静 · 高温积极</p>
        <span class="link">编辑曲线 ›</span>
        <span class="glyph">CURVE</span>
      </div>
    </div>
  </div>

  <div class="bottom-grid">
    <div class="card sm-card">
      <span class="m-icon">@@THERMO@@</span>
      <h3>温度来源</h3>
      <p>风扇依据哪一路温度调速</p>
      <div class="m-foot">
        <div class="seg" id="segSource">
          <button data-v="cpu">CPU</button>
          <button data-v="disk">硬盘</button>
          <button data-v="gpu">GPU</button>
          <button data-v="max" class="active">最高值</button>
        </div>
      </div>
    </div>
    <div class="card sm-card">
      <span class="m-icon">@@DOWN@@</span>
      <h3>最低转速</h3>
      <p>转速下限,防止风扇停转</p>
      <div class="m-foot" style="flex-direction:column;align-items:stretch;gap:8px">
        <div class="foot-row"><span>下限</span><span class="v" id="uiMinPwmVal">20%</span></div>
        <input type="range" id="uiMinPwm" min="10" max="100" value="20" style="--fill:11%">
      </div>
    </div>
    <div class="card sm-card">
      <span class="m-icon">@@CLOCK@@</span>
      <h3>轮询间隔</h3>
      <p>刷新温度与转速的频率</p>
      <div class="m-foot">
        <div class="seg" id="segPoll">
          <button data-v="1">1s</button>
          <button data-v="2" class="active">2s</button>
          <button data-v="5">5s</button>
        </div>
      </div>
    </div>
  </div>

"""
for k, v in {"THERMO": I["thermo"], "FANSM": I["fanSm"], "CLOCK": I["clock"], "BOLT": I["bolt"],
             "SHIELD": I["shield"], "MANUAL": I["manual"], "DOWN": I["down"], "LIST": I["list"],
             "BOOK": I["book"], "IMG": I["img"], "GPU": I["gpu"]}.items():
    GRIDS = GRIDS.replace("@@" + k + "@@", v)

c1 = html.index("  <!-- 状态卡片 -->")
c2 = html.index("  <!-- 多区域面板容器")
html = html[:c1] + GRIDS + "\n" + html[c2:]

# ══════ 6) 容器 → 应用外框(侧栏 + 主区 + 玻璃顶栏 + 内容滚动区) ══════
WP_PANEL = """      <div class="wp-panel" id="wpPanel">
        <div class="wp-panel__title">壁纸</div>
        <div class="wp-grid">
          <button class="wp-item" type="button" data-wp="blue"><span class="wp-thumb wp-thumb--blue"></span><span class="wp-name">深空蓝</span></button>
          <button class="wp-item" type="button" data-wp="dusk"><span class="wp-thumb wp-thumb--dusk"></span><span class="wp-name">暮紫</span></button>
          <button class="wp-item" type="button" data-wp="mint"><span class="wp-thumb wp-thumb--mint"></span><span class="wp-name">青珀</span></button>
          <button class="wp-item" type="button" data-wp="obsidian"><span class="wp-thumb wp-thumb--obsidian"></span><span class="wp-name">曜石</span></button>
        </div>
        <div class="wp-custom">
          <button class="wp-item wp-item--custom" type="button" data-wp="custom" id="wpCustomApply">
            <span class="wp-thumb wp-thumb--custom" id="wpCustomThumb"></span>
            <span class="wp-name" id="wpCustomName">自定义图片</span>
          </button>
          <div class="wp-custom-actions">
            <button class="wp-mini" type="button" id="wpCustomPick">选择本地图片</button>
            <button class="wp-mini wp-mini--danger" type="button" id="wpCustomClear" hidden>移除</button>
          </div>
          <input type="file" id="wpFile" accept="image/*" hidden>
        </div>
      </div>"""
OPENING = """<div class="app" id="app">
  <aside class="sidebar">
    <div class="brand">
      <span class="b-icon">@@FAN@@</span>
      <div class="b-text"><div class="b-name">FAN CONSOLE</div><div class="b-sub">风扇控制器</div></div>
    </div>
    <nav class="side-nav" id="sideNav">
      <button class="side-item active" data-view="viewHome">@@HOME@@<span>首页</span></button>
      <button class="side-item" data-view="viewCurve">@@CHART@@<span>温控曲线</span><i class="s-dot" id="navCurveDirty" title="温控曲线有未保存的修改"></i><span class="s-badge" id="navCurveBadge">自动模式</span></button>
      <button class="side-item" data-view="viewZones">@@GRID@@<span>区域管理</span></button>
      <button class="side-item" data-view="viewLogs">@@LIST@@<span>运行日志</span></button>
      <button class="side-item" data-view="viewSettings">@@SLIDERS@@<span>高级设置</span></button>
      <button class="side-item" data-view="viewGuide">@@BOOK@@<span>使用说明</span></button>
      <button class="side-item" data-view="viewAbout">@@INFO@@<span>关于</span></button>
    </nav>
    <div class="side-foot">
      <button class="collapse-btn" id="btnCollapse" title="收起/展开侧栏">@@CHEV@@</button>
      <span class="sys" id="sysInfo" title="设备信息">…</span>
    </div>
  </aside>
  <main class="main">
    <div class="content" id="mainContainer">"""
for k, v in {"FAN": I["fan"], "HOME": I["home"], "CHART": I["chart"], "LIST": I["list"], "SLIDERS": I["sliders"],
             "BOOK": I["book"], "INFO": I["info"], "CHEV": I["chev"], "GRID": I["grid"]}.items():
    OPENING = OPENING.replace("@@" + k + "@@", v)

old_open = '<div class="container" id="mainContainer">'
assert html.count(old_open) == 1
html = html.replace(old_open, OPENING, 1)

# 各区块加 id(侧栏滚动定位)
html = html.replace('  <!-- 高级设置 -->\n  <div class="section">', '  <!-- 高级设置 -->\n  <div class="section" id="settingsSection">', 1)
html = html.replace('  <!-- 日志（默认折叠，点击展开） -->\n  <div class="section">', '  <!-- 日志（默认折叠，点击展开） -->\n  <div class="section" id="logsSection">', 1)
html = html.replace('  <!-- 使用说明 -->\n  <div class="section">', '  <!-- 使用说明 -->\n  <div class="section" id="guideSection">', 1)

# 壁纸入口:放入高级设置页(更换壁纸按钮 + 面板)
anchor_row = '          <label><input type="radio" name="tempSource" value="max"> 最高值</label>\n        </div>\n      </div>\n'
assert html.count(anchor_row) == 1, "温度来源行未找到"
wall_row = anchor_row + """      <div class="setting-row">
        <label>壁纸</label>
        <div class="wp-anchor">
          <button class="btn btn-secondary" id="wpBtn" type="button" title="更换壁纸">更换壁纸</button>
          @@WP_PANEL@@
        </div>
      </div>
      <div class="setting-row">
        <label>配置备份</label>
        <div class="cfg-actions">
          <button class="btn btn-secondary" id="cfgExportBtn" type="button" title="导出当前配置为 JSON 文件">导出配置</button>
          <button class="btn btn-secondary" id="cfgImportBtn" type="button" title="从 JSON 文件导入配置(覆盖当前,需二次确认)">导入配置</button>
          <input type="file" id="cfgFile" accept=".json,application/json" hidden>
        </div>
      </div>
      <div class="setting-row">
        <label>告警通知</label>
        <div class="notify-inline">
          <label class="switch"><input type="checkbox" id="notifyToggle"><i></i></label>
          <span class="hint">浏览器通知:全速保护 / 降级时提醒(需授权,仅当前设备)</span>
        </div>
      </div>
      <div class="setting-row">
        <label>告警 Webhook</label>
        <div class="webhook-inline">
          <input type="text" id="webhookInput" placeholder="https://…(留空关闭;Bark / 钉钉可直接填 URL)">
          <button class="btn btn-secondary" id="webhookSaveBtn" type="button">保存</button>
        </div>
      </div>
"""
html = html.replace(anchor_row, wall_row, 1)

# 替换壁纸面板占位符(高级设置内的壁纸入口)
assert html.count("@@WP_PANEL@@") == 1
html = html.replace("@@WP_PANEL@@", WP_PANEL)

# 容器收尾 → 关闭 guide视图/关于视图/content/main/app
old_tail = "\n</div>\n\n<script>"
assert html.count(old_tail) == 1
ABOUT_VIEW = """
  <div class="view" id="viewAbout" style="display:none">
  <div class="section">
    <div class="section-title"><span class="s-icon">ℹ️</span> 关于</div>
    <div class="guide">
      <div class="guide-section">
        <h3>关于</h3>
        <ul>
          <li>当前版本:<b>v1.0</b>(公开发布版,2026-10-03)。</li>
          <li>本项目基于开源项目 <b>fnos-fan-control</b>(飞牛 NAS 风扇控制器 · MIT License · 作者 AriesOxO)进行的<b>二次开发</b>。</li>
          <li>原仓库:<a href="https://github.com/AriesOxO/fnos-fan-control" target="_blank" rel="noopener">github.com/AriesOxO/fnos-fan-control</a></li>
        </ul>
      </div>
      <div class="guide-section">
        <h3>我做了哪些开发</h3>
        <ul>
          <li><b>Liquid Glass 液态玻璃外观</b> — 深空壁纸、玻璃面板、镜面描边与指针追光,并完成性能优化(移除实时背景模糊 / 位移折射 / 壁纸动画,低配设备也顺滑)。</li>
          <li><b>拯救者(Legion)风格布局</b> — 左侧导航栏、温控仪表盘(温度刻度环 / 五边形模式徽章 / PWM 迷你表)、快捷卡片区,以及各菜单独立分页切换。</li>
          <li><b>壁纸系统</b> — 4 套预设壁纸 + 自定义图片上传(自动压缩,浏览器本地存储)。</li>
          <li><b>温控曲线增强</b> — 大尺寸自适应图表,支持直接拖拽节点调节“温度 → 转速”映射;修改未保存会提醒,离开页面时二次确认。</li>
          <li><b>GPU 温度来源</b> — 支持 AMD / NVIDIA / Intel 显卡温度(amdgpu / nvidia / nouveau / i915 / nvidia-smi / thermal zone),可作为风扇调速依据。</li>
          <li><b>温度趋势与安全</b> — 首页温度趋势小图(最近约 2 分钟);温度读取失败保护按所选来源分别生效,避免误伤其他来源。</li>
          <li><b>多区域管理</b> — 多风扇时可为每个区域绑定独立的 PWM 通道、温度来源与温控曲线,首页自动显示各区域状态面板。</li>
          <li><b>告警通知</b> — 浏览器通知 + 告警 Webhook(Bark / 钉钉可直接填 URL):全速保护 / 高温降级 / 恢复正常时按区域提醒。</li>
          <li><b>日志与配置备份</b> — 运行日志 5s 自动刷新、级别筛选与导出;配置一键导出 / 导入(含二次确认)。</li>
          <li><b>手机与安装</b> — 手机端布局适配、底部导航、设备信息自动读取;支持“添加到主屏”(PWA 独立窗口)。</li>
          <li><b>公开发布 v1.0</b> — 带查询参数访问等修复、68 例单元测试与一键部署脚本,版本号统一为 v1.0。</li>
          <li><b>若干修复与细节</b> — 曲线 / 设置保存写入区域接口(多通道配置)、桌面启动地址修复、按钮与交互调整等。</li>
        </ul>
      </div>
      <div class="guide-section">
        <h3>说明</h3>
        <ul>
          <li>二次开发<b>以前端为主,另含少量后端增强</b>(GPU 温度来源、机器信息接口、温度失败保护按来源生效等),风扇控制核心逻辑保持原项目实现;</li>
          <li>全部改造版本记录与技术文档保存在应用数据目录 <b>manual-backup-20260930</b>(含原版与各版本页面文件、文档 01–04,可随时回退)。</li>
        </ul>
      </div>
    </div>
  </div>
  </div>
"""
html = html.replace(old_tail, "\n  </div>\n" + ABOUT_VIEW + "    </div>\n  </main>\n</div>\n\n<script>", 1)

# ══════ 5.5) 视图切换:五个页面包裹 + 相关修正 ══════
# 曲线区块初始 display:none 移除(改由视图系统控制)
old_curve_style = '<div class="section" id="curveSection" style="display:none">'
assert html.count(old_curve_style) == 1
html = html.replace(old_curve_style, '<div class="section" id="curveSection">', 1)

# 应用 JS:曲线不再随运行模式自动显隐(视图系统接管)
old_line = "  document.getElementById('curveSection').style.display=mode==='auto'?'':'none';\n"
assert html.count(old_line) == 1, "updateModeUI 曲线行未找到"
html = html.replace(old_line, "")

# 应用 JS:GPU 温度来源(多区域标签 + 曲线"当前温度"改为区域有效温度,与温控取值一致)
old_src_label = "const srcLabel={cpu:'CPU',disk:'硬盘',max:'最高值'};"
assert html.count(old_src_label) == 1, "srcLabel 未找到"
html = html.replace(old_src_label, "const srcLabel={cpu:'CPU',disk:'硬盘',gpu:'GPU',max:'最高值'};")
old_ct = "currentTemp=s.cpu_temp;"
assert html.count(old_ct) == 1, "currentTemp 赋值未找到"
html = html.replace(old_ct, "currentTemp=(s.zones&&s.zones.default&&s.zones.default.temp!=null)?s.zones.default.temp:s.cpu_temp;")

# 应用 JS:日志不再随状态轮询抓取(改由"运行日志"视图的 5s 专用轮询,§2.3)
old_log_poll = """  const logPanel=document.querySelector('.log-header .collapsible');
  if(logPanel&&logPanel.classList.contains('open')) fetchLogs();
"""
assert html.count(old_log_poll) == 1, "状态轮询内 fetchLogs 未找到"
html = html.replace(old_log_poll, "")

# 应用 JS:多区域模式下不再隐藏曲线区块(视图系统接管,§2.5 启用 multiZone 展示路径)
old_mz = "document.getElementById('singleModeSection').style.display='none';document.getElementById('curveSection').style.display='none'"
assert html.count(old_mz) == 1, "multiZone 隐藏曲线行未找到"
html = html.replace(old_mz, "document.getElementById('singleModeSection').style.display='none'")

# 设置/日志/说明三个折叠块默认展开(独立页面直接可见)
for old, new in [
    ('<div class="section-title collapsible" data-target="settingsBody"', '<div class="section-title collapsible open" data-target="settingsBody"'),
    ('<div class="collapse-body" id="settingsBody">', '<div class="collapse-body open" id="settingsBody">'),
    ('<div class="section-title collapsible" data-target="logCollapseBody"', '<div class="section-title collapsible open" data-target="logCollapseBody"'),
    ('<div class="collapse-body" id="logCollapseBody">', '<div class="collapse-body open" id="logCollapseBody">'),
    ('<div class="section-title collapsible" data-target="guideBody"', '<div class="section-title collapsible open" data-target="guideBody"'),
    ('<div class="collapse-body" id="guideBody">', '<div class="collapse-body open" id="guideBody">'),
]:
    assert html.count(old) == 1, f"折叠替换失败: {old[:60]}"
    html = html.replace(old, new)

# ══════ 5.6) 折叠容器:scrollHeight 测量 + transitionend 清内联高度(§1.6,修复 2000px 裁切) ══════
old_collapse_fn = """function toggleCollapse(el){
  el.classList.toggle('open');
  var targetId=el.getAttribute('data-target');
  var body=targetId?document.getElementById(targetId):null;
  if(!body){body=el.nextElementSibling}
  if(!body||!body.classList.contains('collapse-body')){body=el.parentElement.nextElementSibling}
  if(body&&body.classList.contains('collapse-body')){body.classList.toggle('open')}
  if(el.classList.contains('open')&&el.closest('.log-header')){fetchLogs()}
}"""
new_collapse_fn = """function toggleCollapse(el){
  el.classList.toggle('open');
  var targetId=el.getAttribute('data-target');
  var body=targetId?document.getElementById(targetId):null;
  if(!body){body=el.nextElementSibling}
  if(!body||!body.classList.contains('collapse-body')){body=el.parentElement.nextElementSibling}
  if(!body||!body.classList.contains('collapse-body'))return;
  var opening=el.classList.contains('open');
  /* 清理上一次未完成的过渡 */
  if(body._fcCollapseEnd){body.removeEventListener('transitionend',body._fcCollapseEnd);body._fcCollapseEnd=null}
  if(body._fcCollapseTimer){clearTimeout(body._fcCollapseTimer);body._fcCollapseTimer=null}
  function settle(){body.style.maxHeight='';body._fcCollapseTimer=null}
  if(opening){
    /* 按实际内容高度测量过渡,结束后交还 CSS(max-height:none),不再受 2000px 上限限制 */
    body.classList.add('open');
    body.style.maxHeight=body.scrollHeight+'px';
  }else{
    if(!body.style.maxHeight||body.style.maxHeight==='none'){body.style.maxHeight=body.scrollHeight+'px'}
    void body.offsetHeight; /* 强制回流,让高度从像素值过渡到 0 */
    body.classList.remove('open');
    body.style.maxHeight='0px';
  }
  body._fcCollapseEnd=function(ev){if(ev.target!==body||ev.propertyName!=='max-height')return;settle()};
  body.addEventListener('transitionend',body._fcCollapseEnd);
  body._fcCollapseTimer=setTimeout(settle,450); /* transitionend 未触发时的兜底 */
  if(opening&&el.closest('.log-header')){fetchLogs()}
}"""
assert html.count(old_collapse_fn) == 1, "toggleCollapse 函数未找到"
html = html.replace(old_collapse_fn, new_collapse_fn)

# ══════ 5.7) 日志页增强:级别筛选 + 导出按钮(§2.3) ══════
old_log_clear = '      <button class="btn btn-danger" onclick="clearLogs()">清空</button>\n'
new_log_tools = '''      <div class="log-actions">
        <div class="log-filter" id="logFilter">
          <button type="button" data-v="all" class="active">全部</button>
          <button type="button" data-v="info">信息</button>
          <button type="button" data-v="warn">警告</button>
          <button type="button" data-v="error">错误</button>
        </div>
        <button class="btn btn-sm btn-secondary" id="logExportBtn" type="button">导出</button>
        <button class="btn btn-sm btn-danger" onclick="clearLogs()">清空</button>
      </div>
'''
assert html.count(old_log_clear) == 1, "日志清空按钮未找到"
html = html.replace(old_log_clear, new_log_tools)

# ══════ 5.8) 区域管理视图(§2.5)DOM ══════
ZONES_VIEW = """  <div class="view" id="viewZones" style="display:none">
  <div class="section" id="zonesSection">
    <div class="section-title"><span class="s-icon">@@GRID@@</span> 区域管理</div>
    <div class="zones-intro">多风扇 / 多区域时,可为每个区域绑定独立的 PWM 通道、温度来源与温控曲线;单区域用户可忽略本页。真机默认单区域不受影响。</div>
    <div class="zones-list" id="zonesList"><div class="zones-empty">正在加载…</div></div>
    <div class="zones-actions">
      <button class="btn btn-sm" id="zoneAddBtn" type="button">+ 新增区域</button>
      <button class="btn btn-sm btn-ghost" id="zoneReloadBtn" type="button">重新加载</button>
    </div>
    <div class="zone-editor" id="zoneEditor" hidden>
      <div class="zone-editor-title" id="zoneEditorTitle">新增区域</div>
      <div class="zone-form">
        <div class="zone-field"><label>名称</label><input type="text" id="zfName" maxlength="24" placeholder="如: 前面板"></div>
        <div class="zone-field"><label>PWM 通道</label><div class="zf-channels" id="zfChannels"></div></div>
        <div class="zone-field"><label>温度来源</label><select id="zfSource"><option value="cpu">CPU</option><option value="disk">硬盘</option><option value="gpu">GPU</option><option value="max">最高值</option></select></div>
        <div class="zone-field"><label>最低转速(%)</label><input type="number" id="zfMin" min="10" max="100" value="20"></div>
        <div class="zone-field zone-field--wide"><label>温控曲线(2–10 节点,温度递增)</label>
          <div class="zf-curve" id="zfCurve"></div>
          <div class="zf-curve-actions">
            <button class="btn btn-sm btn-secondary" id="zfAddNode" type="button">+ 添加节点</button>
            <button class="btn btn-sm btn-ghost" id="zfDelNode" type="button">- 删除末尾</button>
          </div>
        </div>
      </div>
      <div class="zone-editor-actions">
        <button class="btn btn-sm btn-ghost" id="zoneCancelBtn" type="button">取消</button>
        <button class="btn btn-sm" id="zoneSaveBtn" type="button">保存</button>
      </div>
    </div>
  </div>
  </div>
"""
ZONES_VIEW = ZONES_VIEW.replace("@@GRID@@", I["grid"])

# 用 view 容器包裹六个页面(区域管理插在温控曲线之前)
for old, new in [
    ('  <!-- 温控仪表盘(英雄卡) + 快捷卡片 -->', '<div class="view" id="viewHome">\n  <!-- 温控仪表盘(英雄卡) + 快捷卡片 -->'),
    ('  <!-- 温控曲线 -->', '</div>\n\n' + ZONES_VIEW + '\n  <div class="view" id="viewCurve" style="display:none">\n  <!-- 温控曲线 -->'),
    ('  <!-- 高级设置 -->', '</div>\n\n  <div class="view" id="viewSettings" style="display:none">\n  <!-- 高级设置 -->'),
    ('  <!-- 日志（默认折叠，点击展开） -->', '</div>\n\n  <div class="view" id="viewLogs" style="display:none">\n  <!-- 日志（默认折叠，点击展开） -->'),
    ('  <!-- 使用说明 -->', '</div>\n\n  <div class="view" id="viewGuide" style="display:none">\n  <!-- 使用说明 -->'),
]:
    assert html.count(old) == 1, f"视图锚点失败: {old[:40]}"
    html = html.replace(old, new)

# 把单区域模式块放进英雄卡底部
assert html.count("@@SINGLE_MODE@@") == 1
html = html.replace("@@SINGLE_MODE@@", single_block, 1)

# ══════ 7) 脚本:指针追光 + 壁纸切换 + Legion 布局适配 ══════
MODE_JS = ('{"default":{en:"DEFAULT MODE",icon:\'' + SVG_DEFAULT + '\'},'
           '"auto":{en:"AUTO MODE",icon:\'' + SVG_AUTO + '\'},'
           '"manual":{en:"MANUAL MODE",icon:\'' + SVG_MANUAL + '\'},'
           '"full":{en:"FULL SPEED",icon:\'' + SVG_FULL + '\'}}')

SCRIPTS = """
<script>
/* Liquid Glass:镜面高光跟随指针(rAF 节流) */
(function () {
  var sel = '.topbar,.card,.section,.zone-panel,.login-box';
  var raf = null, ev = null;
  document.addEventListener('pointermove', function (e) {
    ev = e;
    if (raf) return;
    raf = requestAnimationFrame(function () {
      raf = null;
      if (!ev) return;
      var el = ev.target && ev.target.closest ? ev.target.closest(sel) : null;
      if (!el) return;
      var r = el.getBoundingClientRect();
      var x = ((ev.clientX - r.left) / r.width * 100).toFixed(1) + '%';
      var y = ((ev.clientY - r.top) / r.height * 100).toFixed(1) + '%';
      if (el.style.getPropertyValue('--mx') === x && el.style.getPropertyValue('--my') === y) return;
      el.style.setProperty('--mx', x);
      el.style.setProperty('--my', y);
    });
  }, { passive: true });
})();

/* 壁纸切换(预设 + 自定义图片) */
(function () {
  var KEY = 'fc-wallpaper', CKEY = 'fc-wallpaper-custom', NKEY = 'fc-wallpaper-custom-name';
  var root = document.documentElement;
  var items = document.querySelectorAll('.wp-item');
  var bgImg = document.getElementById('bgImg');
  var applyBtn = document.getElementById('wpCustomApply');
  var thumb = document.getElementById('wpCustomThumb');
  var nameEl = document.getElementById('wpCustomName');
  var clearBtn = document.getElementById('wpCustomClear');
  var pickBtn = document.getElementById('wpCustomPick');
  var fileInput = document.getElementById('wpFile');
  var btn = document.getElementById('wpBtn');
  var panel = document.getElementById('wpPanel');

  function store(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); return true; } catch (e) { return false; } }
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function closePanel() { if (panel) panel.classList.remove('open'); }
  function toast(msg, type) { try { if (typeof showToast === 'function') showToast(msg, type || 'success'); } catch (e) {} }

  var VALID = /^(blue|dusk|mint|obsidian|custom)$/;

  function syncCustomUI() {
    var data = get(CKEY), has = !!data;
    if (has) { thumb.style.backgroundImage = 'url("' + data + '")'; } else { thumb.style.backgroundImage = 'none'; }
    applyBtn.classList.toggle('has-img', has);
    clearBtn.hidden = !has;
    nameEl.textContent = has ? (get(NKEY) || '自定义图片') : '自定义图片';
  }
  function apply(v) {
    if (v === 'custom') {
      var data = get(CKEY);
      if (!data) return false;
      bgImg.style.backgroundImage = 'url("' + data + '")';
    }
    root.setAttribute('data-wallpaper', v);
    items.forEach(function (b) { b.classList.toggle('active', b.dataset.wp === v); });
    return true;
  }
  var saved = get(KEY);
  if (!saved || !VALID.test(saved)) saved = 'blue';
  if (saved === 'custom' && !get(CKEY)) saved = 'blue';
  apply(saved);
  syncCustomUI();

  function saveImage(img, name) {
    var sizes = [2560, 1920, 1280, 960];
    for (var i = 0; i < sizes.length; i++) {
      var s = Math.min(1, sizes[i] / Math.max(img.width, img.height));
      var c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(img.width * s));
      c.height = Math.max(1, Math.round(img.height * s));
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      var data = c.toDataURL('image/jpeg', i === 0 ? 0.82 : 0.78);
      if (store(CKEY, data)) { store(NKEY, name || ''); return true; }
    }
    return false;
  }
  function pick() { if (fileInput) fileInput.click(); }

  if (applyBtn) applyBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    if (get(CKEY)) { if (apply('custom')) { store(KEY, 'custom'); closePanel(); } }
    else pick();
  });
  if (pickBtn) pickBtn.addEventListener('click', function (e) { e.stopPropagation(); pick(); });
  if (clearBtn) clearBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    store(CKEY, null); store(NKEY, null);
    if (root.getAttribute('data-wallpaper') === 'custom') { apply('blue'); store(KEY, 'blue'); }
    syncCustomUI();
    toast('已移除自定义壁纸');
  });
  if (fileInput) fileInput.addEventListener('change', function () {
    var f = this.files && this.files[0];
    this.value = '';
    if (!f) return;
    if (!/^image\\//.test(f.type)) { toast('请选择图片文件', 'fail'); return; }
    var url = URL.createObjectURL(f);
    var img = new Image();
    img.onload = function () {
      URL.revokeObjectURL(url);
      if (saveImage(img, f.name)) {
        syncCustomUI();
        if (apply('custom')) { store(KEY, 'custom'); closePanel(); toast('自定义壁纸已应用'); }
      } else { toast('图片过大,请换一张更小的', 'fail'); }
    };
    img.onerror = function () { URL.revokeObjectURL(url); toast('图片读取失败', 'fail'); };
    img.src = url;
  });
  if (btn && panel) {
    btn.addEventListener('click', function (e) { e.stopPropagation(); panel.classList.toggle('open'); });
    panel.addEventListener('click', function (e) {
      var item = e.target.closest('.wp-item');
      if (!item) return;
      var wp = item.dataset.wp;
      if (wp === 'custom') return;
      if (apply(wp)) { store(KEY, wp); closePanel(); }
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('#wpPanel') && !e.target.closest('#wpBtn')) closePanel();
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closePanel(); });
  }
})();

/* Legion 布局适配:仪表盘 / 五边形 / 侧栏 / 快捷卡片 */
(function () {
  "use strict";
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };

  /* —— 仪表盘 —— */
  function polar(cx, cy, r, deg) { var a = deg * Math.PI / 180; return [+(cx + r * Math.cos(a)).toFixed(2), +(cy + r * Math.sin(a)).toFixed(2)]; }
  function buildArc(container, opts) {
    if (!container) return { set: function () {} };
    opts = opts || {};
    var cx = 120, cy = 120, r = opts.mini ? 96 : 90;
    var A1 = 135, A2 = 405, n = opts.mini ? 30 : 52, every = opts.mini ? 5 : 4.5;
    var p1 = polar(cx, cy, r, A1), p2 = polar(cx, cy, r, A2);
    var arc = "M" + p1[0] + " " + p1[1] + "A" + r + " " + r + " 0 1 1 " + p2[0] + " " + p2[1];
    var ticks = "";
    for (var i = 0; i <= n; i++) {
      var a = A1 + (A2 - A1) * i / n, major = i % every === 0;
      var t1 = polar(cx, cy, r + 13, a), t2 = polar(cx, cy, r + (major ? 25 : 19), a);
      ticks += '<line x1="' + t1[0] + '" y1="' + t1[1] + '" x2="' + t2[0] + '" y2="' + t2[1] + '" stroke="' + (major ? "rgba(255,255,255,.35)" : "rgba(255,255,255,.14)") + '" stroke-width="' + (major ? 2 : 1.2) + '" stroke-linecap="round"/>';
    }
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 240 240");
    svg.innerHTML = ticks + '<path class="g-track" d="' + arc + '"/><path class="g-value" d="' + arc + '" pathLength="100" stroke-dasharray="0 100"/>';
    container.insertBefore(svg, container.firstChild);
    var val = svg.querySelector(".g-value");
    var last = -1;
    return {
      set: function (v) {
        if (v == null || isNaN(v)) return;
        v = Math.max(0, Math.min(100, v));
        if (v === last) return;
        last = v;
        val.setAttribute("stroke-dasharray", v.toFixed(1) + " " + (100 - v).toFixed(1));
      }
    };
  }
  var gCpu = buildArc($("#gaugeCpu"), {});
  var gDisk = buildArc($("#gaugeDisk"), {});
  var gPwm = buildArc($("#gaugePwm"), { mini: true });
  function numOf(id) { var el = document.getElementById(id); if (!el) return null; var v = parseFloat(el.textContent); return isNaN(v) ? null : v; }
  function syncGauges() { gCpu.set(numOf("cpuTemp")); gDisk.set(numOf("diskTemp")); gPwm.set(numOf("pwmPercent")); }
  ["cpuTemp", "diskTemp", "pwmPercent", "fanRpm"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) new MutationObserver(syncGauges).observe(el, { childList: true, subtree: true, characterData: true });
  });
  syncGauges();

  /* —— 五边形模式徽章 —— */
  var MODES = __MODES_JS__;
  (function () {
    var pent = $("#pentagon"); if (!pent) return;
    var pts = [];
    for (var i = 0; i < 5; i++) { var a = (-90 + i * 72) * Math.PI / 180; pts.push((75 + 68 * Math.cos(a)).toFixed(2) + "," + (70 + 68 * Math.sin(a)).toFixed(2)); }
    pent.innerHTML = '<svg viewBox="0 0 150 150"><polygon points="' + pts.join(" ") + '" fill="rgba(255,255,255,.02)" stroke="rgba(255,255,255,.3)" stroke-width="1.5" stroke-linejoin="round"/><polygon points="' + pts.join(" ") + '" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="6" stroke-linejoin="round" transform="scale(.92) translate(6.5 5.6)"/></svg><span class="p-icon" id="pIcon"></span><span class="p-mode" id="pModeText">DEFAULT MODE</span>';
  })();
  function currentMode() { var b = $("#singleModeSection .mode-btn.active"); return b ? b.dataset.mode : "default"; }
  function syncModeUI() {
    var m = currentMode(), d = MODES[m] || MODES["default"];
    var ic = $("#pIcon"), tx = $("#pModeText");
    if (ic) ic.innerHTML = d.icon;
    if (tx) tx.textContent = d.en;
    var sw = $("#swManualUI"), st = $("#manualState");
    if (sw) sw.checked = (m === "manual");
    if (st) st.textContent = (m === "manual" ? "已启用" : "未启用");
    var nb = $("#navCurveBadge"); if (nb) nb.textContent = (m === "auto" ? "编辑中" : "自动模式");
  }
  $$("#singleModeSection .mode-btn").forEach(function (b) {
    new MutationObserver(syncModeUI).observe(b, { attributes: true, attributeFilter: ["class"] });
  });
  syncModeUI();

  /* —— 侧栏与视图切换(点菜单只显示对应页面) —— */
  var app = $("#app");
  var colBtn = $("#btnCollapse");
  if (colBtn) colBtn.addEventListener("click", function () { app.classList.toggle("collapsed"); });
  var VIEWS = ["viewHome", "viewCurve", "viewZones", "viewLogs", "viewSettings", "viewGuide", "viewAbout"];
  function activateNav(v) {
    $$(".side-item").forEach(function (x) { x.classList.toggle("active", x.dataset.view === v); });
  }
  /* 进入“运行日志”视图时启动 5s 专用轮询,离开即停止(§2.3) */
  var logPollTimer = null;
  function setLogPolling(on) {
    if (on) {
      if (!logPollTimer) {
        try { fetchLogs(); } catch (e) {}
        logPollTimer = setInterval(function () { try { fetchLogs(); } catch (e) {} }, 5000);
      }
    } else if (logPollTimer) {
      clearInterval(logPollTimer);
      logPollTimer = null;
    }
    window.__fcLogPolling = !!logPollTimer; /* 自动化检查探针 */
  }
  function showView(v) {
    if (VIEWS.indexOf(v) < 0) v = "viewHome";
    VIEWS.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.style.display = (id === v) ? "" : "none";
    });
    activateNav(v);
    var c = $(".content"); if (c) c.scrollTop = 0;
    setLogPolling(v === "viewLogs");
  }
  $$(".side-item").forEach(function (b) {
    b.addEventListener("click", function () { showView(b.dataset.view); });
  });

  /* —— 快捷卡片 —— */
  $$("[data-act]").forEach(function (el) {
    el.addEventListener("click", function () {
      var a = el.dataset.act;
      if (a === "full") { try { switchMode("full"); } catch (e) {} }
      else if (a === "curve") { showView("viewCurve"); }
      else if (a === "help") { showView("viewGuide"); }
    });
  });
  var swM = $("#swManualUI");
  if (swM) swM.addEventListener("change", function () { try { switchMode(this.checked ? "manual" : "default"); } catch (e) {} });

  /* —— 温控曲线:自适应大尺寸 + 节点拖拽调节 —— */
  (function () {
    var svg = document.getElementById("curveSvg");
    if (!svg) return;
    function draw() {
      var rect = svg.getBoundingClientRect();
      var W = Math.max(560, Math.round(rect.width || 900));
      var H = Math.max(260, Math.round(rect.height || 340));
      svg.setAttribute("viewBox", "0 0 " + W + " " + H);
      var PX = 54, PY = 30, PB = Math.round(H * 0.11), PR = 26;
      var gW = W - PX - PR, gH = H - PY - PB;
      window.__curveDisp = { W: W, H: H, PX: PX, PY: PY, PB: PB, gW: gW, gH: gH };
      var lw = Math.max(2.5, Math.min(4, W * 0.0021));
      var rr = Math.max(5, Math.min(9, W * 0.004));
      svg.style.setProperty("--curve-lw", lw.toFixed(2) + "px");
      svg.style.setProperty("--curve-r", rr.toFixed(1) + "px");
      var fs = Math.max(11, Math.round(H * 0.042));
      var html = '<defs><linearGradient id="curveGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(34,193,224,.25)"/><stop offset="100%" stop-color="rgba(34,193,224,0)"/></linearGradient></defs>';
      var t, x, p, y;
      for (t = 0; t <= 120; t += 20) {
        x = PX + (t / 120) * gW;
        html += '<line class="curve-grid" x1="' + x + '" y1="' + PY + '" x2="' + x + '" y2="' + (H - PB) + '"/><text class="curve-label" style="font-size:' + fs + 'px" x="' + x + '" y="' + (H - 10) + '" text-anchor="middle">' + t + '°</text>';
      }
      for (p = 0; p <= 100; p += 25) {
        y = H - PB - (p / 100) * gH;
        html += '<line class="curve-grid" x1="' + PX + '" y1="' + y + '" x2="' + (W - PR) + '" y2="' + y + '"/><text class="curve-label" style="font-size:' + fs + 'px" x="' + (PX - 8) + '" y="' + (y + 4) + '" text-anchor="end">' + p + '%</text>';
      }
      if (curveData && curveData.length >= 2) {
        var pts = curveData.map(function (n) { return { x: PX + (n.temp / 120) * gW, y: H - PB - (n.pwm_percent / 100) * gH }; });
        html += '<path class="curve-area" d="M' + pts.map(function (q) { return q.x + "," + q.y; }).join("L") + "L" + pts[pts.length - 1].x + "," + (H - PB) + "L" + pts[0].x + "," + (H - PB) + 'Z"/>';
        html += '<polyline class="curve-line" points="' + pts.map(function (q) { return q.x + "," + q.y; }).join(" ") + '"/>';
        pts.forEach(function (q, i) {
          html += '<circle class="curve-hit" data-i="' + i + '" cx="' + q.x + '" cy="' + q.y + '" r="' + (rr * 2.4).toFixed(1) + '"/>';
          html += '<circle class="curve-dot" data-i="' + i + '" cx="' + q.x + '" cy="' + q.y + '"/>';
        });
      }
      if (currentTemp != null) {
        var tx = PX + (currentTemp / 120) * gW;
        html += '<line class="curve-temp-line" x1="' + tx + '" y1="' + PY + '" x2="' + tx + '" y2="' + (H - PB) + '"/><text fill="rgba(245,176,62,.9)" style="font-size:' + fs + 'px" x="' + tx + '" y="' + (PY - 6) + '" text-anchor="middle">' + currentTemp.toFixed(0) + '°C</text>';
      }
      svg.innerHTML = html;
    }
    window.drawCurve = draw;

    var dragIdx = -1;
    svg.addEventListener("pointerdown", function (e) {
      var hit = e.target && e.target.closest ? e.target.closest(".curve-hit,.curve-dot") : null;
      if (!hit) return;
      dragIdx = parseInt(hit.getAttribute("data-i"), 10);
      try { svg.setPointerCapture(e.pointerId); } catch (err) {}
      svg.classList.add("dragging");
      e.preventDefault();
    });
    svg.addEventListener("pointermove", function (e) {
      if (dragIdx < 0) return;
      var d = window.__curveDisp;
      if (!d) return;
      var rect = svg.getBoundingClientRect();
      var vb = svg.viewBox.baseVal;
      var x = (e.clientX - rect.left) / rect.width * vb.width;
      var y = (e.clientY - rect.top) / rect.height * vb.height;
      var temp = Math.round((x - d.PX) / d.gW * 120);
      var pwm = Math.round((d.H - d.PB - y) / d.gH * 100);
      var lo = dragIdx > 0 ? curveData[dragIdx - 1].temp + 1 : 0;
      var hi = dragIdx < curveData.length - 1 ? curveData[dragIdx + 1].temp - 1 : 120;
      temp = Math.max(lo, Math.min(hi, temp));
      pwm = Math.max(10, Math.min(100, pwm));
      curveData[dragIdx].temp = temp;
      curveData[dragIdx].pwm_percent = pwm;
      draw();
      var rows = document.querySelectorAll("#curveInputs .curve-node");
      if (rows[dragIdx]) {
        var ins = rows[dragIdx].querySelectorAll("input");
        if (ins[0]) ins[0].value = temp;
        if (ins[1]) ins[1].value = pwm;
      }
    });
    function endDrag() {
      if (dragIdx < 0) return;
      dragIdx = -1;
      svg.classList.remove("dragging");
      try { updateCurveSummary(); } catch (e) {}
      try { window.__curveDirtyRefresh && window.__curveDirtyRefresh(); } catch (e) {}
    }
    svg.addEventListener("pointerup", endDrag);
    svg.addEventListener("pointercancel", endDrag);

    var rzT = null;
    window.addEventListener("resize", function () {
      clearTimeout(rzT);
      rzT = setTimeout(function () { try { draw(); } catch (e) {} }, 180);
    });
    try { draw(); } catch (e) {}
  })();

  /* —— 温控曲线:未保存提醒 —— */
  (function () {
    var note = document.getElementById("curveDirtyNote");
    var saveBtn = document.getElementById("curveSaveBtn");
    var navDot = document.getElementById("navCurveDirty");
    var lastSaved = null;
    var isDirty = false;
    function snap() { try { return JSON.stringify(curveData); } catch (e) { return null; } }
    function refresh() {
      isDirty = lastSaved !== null && snap() !== lastSaved;
      if (note) note.classList.toggle("on", isDirty);
      if (saveBtn) saveBtn.classList.toggle("is-dirty", isDirty);
      if (navDot) navDot.classList.toggle("on", isDirty);
      return isDirty;
    }
    window.__curveDirtyRefresh = refresh;

    /* §2.9:存在未保存修改时,关闭/刷新页面弹出浏览器原生确认;保存或恢复默认后自动解除 */
    window.addEventListener("beforeunload", function (e) {
      if (!isDirty) return;
      e.preventDefault();
      e.returnValue = "";
      return "";
    });

    /* 节点输入框修改(含键盘输入,事件冒泡到 document) */
    document.addEventListener("input", function (e) {
      if (e.target && e.target.closest && e.target.closest("#curveInputs")) refresh();
    });
    document.addEventListener("change", function (e) {
      if (e.target && e.target.closest && e.target.closest("#curveInputs")) refresh();
    });

    /* 服务器数据装载(初始加载/重载)→ 作为已保存基线 */
    if (typeof window.loadConfig === "function") {
      var _load = window.loadConfig;
      window.loadConfig = function () {
        var r = _load.apply(this, arguments);
        lastSaved = snap(); refresh();
        return r;
      };
    }
    /* 保存成功(请求体含 curve 且返回 ok)→ 更新已保存基线 */
    if (typeof window.api === "function") {
      var _api = window.api;
      window.api = function (path, method, body) {
        var p = _api.apply(this, arguments);
        if (body && body.curve && p && typeof p.then === "function") {
          return p.then(function (r) { if (r && r.ok) { lastSaved = snap(); refresh(); } return r; });
        }
        return p;
      };
    }
    /* 结构性操作(恢复默认/自动生成/增删节点)之后刷新 */
    ["resetCurve", "generateCurve", "addNode", "removeNode"].forEach(function (name) {
      var orig = window[name];
      if (typeof orig !== "function") return;
      window[name] = function () {
        var r = orig.apply(this, arguments);
        Promise.resolve(r).then(refresh);
        return r;
      };
    });
  })();

  /* —— 温度来源 —— */
  var segS = $("#segSource");
  var SRC_NAME = { cpu: "CPU", disk: "硬盘", gpu: "GPU", max: "最高值" };
  function syncSourceSeg() {
    if (!segS) return;
    var r = document.querySelector("input[name=tempSource]:checked");
    if (!r) return;
    $$("button", segS).forEach(function (b) { b.classList.toggle("active", b.dataset.v === r.value); });
    var hs = $("#heroSource"); if (hs) hs.textContent = SRC_NAME[r.value] || r.value;
  }
  if (segS) segS.addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    var r = document.querySelector("input[name=tempSource][value=" + b.dataset.v + "]");
    if (r) { r.checked = true; try { saveSettings(); } catch (err) {} syncSourceSeg(); }
  });
  syncSourceSeg();

  /* —— GPU 温度(状态同步 + 无传感器时禁用来源选项) —— */
  (function () {
    var gpuStat = $("#gpuStat");
    var gpuVal = $("#gpuTemp");
    var radio = document.querySelector("input[name=tempSource][value=gpu]");
    var segBtn = document.querySelector('#segSource button[data-v="gpu"]');
    function setGpu(t) {
      var has = (t != null && !isNaN(t));
      if (gpuStat) gpuStat.style.display = has ? "flex" : "none";
      if (gpuVal && has) gpuVal.textContent = (+t).toFixed(1);
      [radio, segBtn].forEach(function (el) {
        if (!el) return;
        el.disabled = !has;
        el.title = has ? "" : "未检测到 GPU 温度传感器";
      });
    }
    if (typeof window.updateStatusCards === "function") {
      var _u = window.updateStatusCards;
      window.updateStatusCards = function (s) {
        var r = _u.apply(this, arguments);
        try { setGpu(s && s.gpu_temp); } catch (e) {}
        return r;
      };
    }
    setGpu(null); /* 首个状态到达前先置灰,避免误选无数据的来源 */
  })();

  /* —— 轮询间隔 —— */
  var segP = $("#segPoll");
  function syncPollSeg() {
    var p = document.getElementById("pollInterval");
    if (!p || !segP) return;
    $$("button", segP).forEach(function (b) { b.classList.toggle("active", +b.dataset.v === +p.value); });
    var hp = $("#heroPoll"); if (hp) hp.textContent = (+p.value).toFixed(1);
  }
  if (segP) segP.addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    var p = document.getElementById("pollInterval");
    if (p) { p.value = b.dataset.v; try { saveSettings(); } catch (err) {} syncPollSeg(); }
  });
  syncPollSeg();

  /* —— 最低转速 —— */
  var sMin = $("#uiMinPwm"), vMin = $("#uiMinPwmVal");
  function fillFor(v) { return Math.max(0, Math.min(100, (v - 10) / 90 * 100)).toFixed(0) + "%"; }
  function syncMin() {
    var real = document.getElementById("minPwm");
    if (!real) return;
    var v = +real.value || 20;
    if (sMin && +sMin.value !== v) { sMin.value = v; sMin.style.setProperty("--fill", fillFor(v)); }
    if (vMin) vMin.textContent = v + "%";
  }
  if (sMin) {
    sMin.addEventListener("input", function () {
      var v = +this.value;
      this.style.setProperty("--fill", fillFor(v));
      if (vMin) vMin.textContent = v + "%";
      var real = document.getElementById("minPwm"); if (real) real.value = v;
    });
    sMin.addEventListener("change", function () { try { saveSettings(); } catch (e) {} });
  }
  syncMin();

  /* —— 日志 / 使用说明 / 硬件信息 —— */
  var ll = $("#linkLogs");
  if (ll) ll.addEventListener("click", function () { var el = document.getElementById("logsSection"); if (el) el.scrollIntoView({ behavior: "smooth" }); });
  var lc = $("#linkClearLogs");
  if (lc) lc.addEventListener("click", function () { try { clearLogs(); } catch (e) {} });
  function syncMeta() {
    try {
      api("status").then(function (s) {
        var el = $("#upTimeText");
        if (el && s && s.uptime != null) el.textContent = "已运行 " + Math.max(1, Math.round(s.uptime / 86400)) + " 天";
      });
      api("hardware").then(function (h) {
        var hasChips = !!(h && h.chips && h.chips.length);
        var chip = $("#hwChip");
        if (chip) {
          if (hasChips) {
            var c = h.chips[0];
            chip.textContent = (c.display_name || c.name) + " · " + ((c.pwm_channels || []).length) + " 路 PWM";
          } else { chip.textContent = "仅监控模式"; }
        }
        var sys = $("#sysInfo");
        if (sys) {
          var si = (h && h.system) || {};
          var host = si.hostname || location.hostname || "";
          var model = (si.model || "").replace(/\\s*\\([^)]*\\)\\s*$/, "");
          sys.textContent = model ? host + " · " + model : host;
          sys.title = (si.hostname && si.model) ? si.hostname + " · " + si.model : (host || "设备信息");
        }
        /* 拿到有效硬件数据(或旧后端无 system 字段)即算成功,否则留给重试 */
        if (hasChips || (h && h.system)) metaLoaded = true;
      });
    } catch (e) {}
  }
  var metaLoaded = false, metaTries = 0;
  if (typeof api === "function") {
    syncMeta();
    /* 登录成功后再补拉一次(首屏未认证时硬件请求会是 401,设备信息需要刷新) */
    if (typeof window.doLogin === "function") {
      var _login = window.doLogin;
      window.doLogin = function () {
        var p = _login.apply(this, arguments);
        if (p && typeof p.then === "function") return p.then(function (r) { syncMeta(); return r; });
        syncMeta();
        return p;
      };
    }
  }

  /* —— 低频同步(兜底:loadConfig / 轮询引起的值变化;含设备信息未拉到时重试) —— */
  setInterval(function () {
    syncMin(); syncPollSeg(); syncSourceSeg();
    if (!metaLoaded && metaTries < 40) { metaTries++; syncMeta(); }
  }, 2500);
})();

/* —— 日志增强:级别筛选 + 导出(§2.3) —— */
(function () {
  "use strict";
  var filterBox = document.getElementById("logFilter");
  var exportBtn = document.getElementById("logExportBtn");
  var body = document.getElementById("logBody");
  var active = "all";
  window.__fcLogs = window.__fcLogs || [];

  function levelOf(el) {
    var badge = el.querySelector(".log-badge");
    if (!badge) return "info";
    if (/\\berror\\b/.test(badge.className)) return "error";
    if (/\\bwarn\\b/.test(badge.className)) return "warn";
    return "info";
  }
  function applyFilter() {
    if (!body) return;
    var items = body.querySelectorAll(".log-item");
    for (var i = 0; i < items.length; i++) {
      items[i].style.display = (active === "all" || levelOf(items[i]) === active) ? "" : "none";
    }
  }

  /* 包装 updateLogs:记录原始数据 + 给条目补 data-level 供筛选 */
  if (typeof window.updateLogs === "function") {
    var _ul = window.updateLogs;
    window.updateLogs = function (logs) {
      window.__fcLogs = Array.isArray(logs) ? logs.slice() : [];
      var r = _ul.apply(this, arguments);
      try {
        var items = body ? body.querySelectorAll(".log-item") : [];
        for (var i = 0; i < items.length; i++) items[i].setAttribute("data-level", levelOf(items[i]));
        applyFilter();
      } catch (e) {}
      return r;
    };
  }
  /* 清空后同步导出缓存(否则立即导出会残留旧日志) */
  if (typeof window.clearLogs === "function") {
    var _cl = window.clearLogs;
    window.clearLogs = function () {
      var p = _cl.apply(this, arguments);
      Promise.resolve(p).then(function () { window.__fcLogs = []; });
      return p;
    };
  }

  if (filterBox) {
    filterBox.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest("button") : null;
      if (!b) return;
      active = b.dataset.v || "all";
      var btns = filterBox.querySelectorAll("button");
      for (var i = 0; i < btns.length; i++) btns[i].classList.toggle("active", btns[i] === b);
      applyFilter();
    });
  }

  /* 导出为 .log 文本;__fcBuildLogText 供自动化检查 */
  window.__fcBuildLogText = function () {
    var lines = (window.__fcLogs || []).map(function (l) {
      return "[" + (l.time || "") + "] [" + (l.level || "info").toUpperCase() + "] " + (l.message || "");
    });
    return "风扇控制器 运行日志(导出时间 " + new Date().toLocaleString() + ")\\n" +
           "共 " + lines.length + " 条\\n" + lines.join("\\n") + "\\n";
  };
  if (exportBtn) exportBtn.addEventListener("click", function () {
    var blob = new Blob([window.__fcBuildLogText()], { type: "text/plain;charset=utf-8" });
    var a = document.createElement("a");
    var d = new Date();
    function p(v) { return (v < 10 ? "0" : "") + v; }
    a.href = URL.createObjectURL(blob);
    a.download = "fan-control-logs-" + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) +
                 "-" + p(d.getHours()) + p(d.getMinutes()) + ".log";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    try { showToast("日志已导出"); } catch (e) {}
  });
})();

/* —— 温度趋势 sparkline:60 点环形缓冲 + 无动画 SVG(§2.6) —— */
(function () {
  "use strict";
  var svg = document.getElementById("sparkSvg");
  var wrap = document.getElementById("sparkWrap");
  var legend = document.getElementById("sparkLegend");
  if (!svg || !wrap) return;
  var MAX = 60, W = 640, H = 128, P = 12;
  var SERIES = [
    { key: "cpu", color: "#34d399", label: "CPU" },
    { key: "gpu", color: "#c084fc", label: "GPU" },
    { key: "disk", color: "#22d3ee", label: "硬盘" }
  ];
  var buf = { cpu: [], gpu: [], disk: [] };

  function push(k, v) {
    buf[k].push(v == null || isNaN(v) ? null : +v);
    if (buf[k].length > MAX) buf[k].shift();
  }
  function lastOf(arr) {
    for (var i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return arr[i];
    return null;
  }
  function draw() {
    var all = [];
    SERIES.forEach(function (se) { buf[se.key].forEach(function (v) { if (v != null) all.push(v); }); });
    if (all.length < 2) return;
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    if (hi - lo < 8) { var mid = (hi + lo) / 2; lo = mid - 4; hi = mid + 4; }
    lo -= 2; hi += 2;
    var len = 0;
    SERIES.forEach(function (se) { len = Math.max(len, buf[se.key].length); });
    var offset = MAX - len;
    function x(i) { return P + (offset + i) / (MAX - 1) * (W - P * 2); }
    function y(v) { return H - P - (v - lo) / (hi - lo) * (H - P * 2); }
    var html = '<text class="spark-txt" x="' + (P + 2) + '" y="' + (P + 10) + '">' + hi.toFixed(0) + '°</text>';
    html += '<text class="spark-txt" x="' + (P + 2) + '" y="' + (H - P - 2) + '">' + lo.toFixed(0) + '°</text>';
    SERIES.forEach(function (se) {
      var pts = [];
      for (var i = 0; i < buf[se.key].length; i++) {
        var v = buf[se.key][i];
        if (v != null) pts.push(x(i).toFixed(1) + "," + y(v).toFixed(1));
      }
      if (pts.length >= 2) {
        html += '<polyline class="spark-line" stroke="' + se.color + '" points="' + pts.join(" ") + '"/>';
      }
      var last = lastOf(buf[se.key]);
      if (last != null && pts.length) {
        html += '<circle class="spark-dot" cx="' + x(buf[se.key].length - 1).toFixed(1) +
                '" cy="' + y(last).toFixed(1) + '" r="2.6" fill="' + se.color + '"/>';
      }
    });
    svg.innerHTML = html;
    if (legend) {
      legend.innerHTML = SERIES.map(function (se) {
        var last = lastOf(buf[se.key]);
        if (last == null) return "";
        return '<span class="spark-item"><i style="background:' + se.color + '"></i>' +
               se.label + " " + last.toFixed(1) + "°</span>";
      }).join("");
    }
  }
  function sample(s) {
    if (!s) return;
    push("cpu", s.cpu_temp);
    push("gpu", s.gpu_temp);
    var d = s.disk_temps || {}, vals = [];
    Object.keys(d).forEach(function (k) { vals.push(d[k]); });
    push("disk", vals.length ? Math.max.apply(null, vals) : null);
    draw();
  }
  if (typeof window.updateStatusCards === "function") {
    var _u = window.updateStatusCards;
    window.updateStatusCards = function (s) {
      var r = _u.apply(this, arguments);
      try { sample(s); } catch (e) {}
      return r;
    };
  }
  window.__fcSparkSample = sample; /* 自动化检查探针 */
})();

/* —— 配置导出 / 导入(§2.8) —— */
(function () {
  "use strict";
  var exportBtn = document.getElementById("cfgExportBtn");
  var importBtn = document.getElementById("cfgImportBtn");
  var fileInput = document.getElementById("cfgFile");
  if (!exportBtn || !importBtn || !fileInput) return;

  function stamp() {
    var d = new Date();
    function p(v) { return (v < 10 ? "0" : "") + v; }
    return "" + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate());
  }
  exportBtn.addEventListener("click", function () {
    api("config").then(function (cfg) {
      if (!cfg || typeof cfg !== "object") { showToast("读取配置失败", "fail"); return; }
      var blob = new Blob([JSON.stringify(cfg, null, 2)], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "fan-control-config-" + stamp() + ".json";
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
      showToast("配置已导出");
    });
  });
  importBtn.addEventListener("click", function () { fileInput.click(); });
  fileInput.addEventListener("change", function () {
    var f = this.files && this.files[0];
    this.value = "";
    if (!f) return;
    var reader = new FileReader();
    reader.onload = function () {
      var cfg = null;
      try { cfg = JSON.parse(String(reader.result)); } catch (e) {}
      if (!cfg || typeof cfg !== "object" || Array.isArray(cfg)) { showToast("文件不是有效的配置 JSON", "fail"); return; }
      if (!("zones" in cfg) && !("curve" in cfg) && !("poll_interval" in cfg)) { showToast("缺少配置字段,已取消", "fail"); return; }
      if (!window.confirm("导入将覆盖当前配置(运行模式与端口保持不变)。确定继续?")) return;
      delete cfg.mode; delete cfg.web_port; /* 后端也会忽略,前端先清理 */
      api("config", "POST", cfg).then(function (r) {
        if (r && r.ok) {
          if (r.config) { loadConfig(r.config); startPolling(config.poll_interval || 2); }
          showToast("配置已导入");
        } else { showToast("导入失败", "fail"); }
      });
    };
    reader.onerror = function () { showToast("文件读取失败", "fail"); };
    reader.readAsText(f, "utf-8");
  });
})();

/* —— 告警通知:浏览器通知(§2.4) —— */
(function () {
  "use strict";
  var KEY = "fc-notify";
  var toggle = document.getElementById("notifyToggle");
  var prev = {};
  function enabled() { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } }
  function notify(title, body) {
    if (!enabled()) return;
    try {
      if (typeof Notification === "undefined" || Notification.permission !== "granted") return;
      new Notification(title, { body: body, tag: "fc-alert" });
    } catch (e) {}
  }
  function check(s) {
    if (!s || !s.zones) return;
    Object.keys(s.zones).forEach(function (id) {
      var z = s.zones[id] || {};
      var st = z.alert_state || "ok";
      var old = prev[id] || "ok";
      if (st === old) return;
      prev[id] = st;
      var name = z.name || id;
      if (st === "protect") notify("⚠ 全速保护", name + ":温度读取连续失败,已全速保护");
      else if (st === "degrade") notify("⛔ 高温降级", name + ":已降级为默认模式");
      else if (old !== "ok") notify("✅ 已恢复正常", name + ":温度读取恢复正常");
    });
  }
  if (toggle) {
    toggle.checked = enabled();
    toggle.addEventListener("change", function () {
      if (!this.checked) {
        try { localStorage.setItem(KEY, "0"); } catch (e) {}
        toastSafe("已关闭浏览器通知");
        return;
      }
      if (typeof Notification === "undefined") {
        this.checked = false;
        toastSafe("当前浏览器不支持通知", "fail");
        return;
      }
      var self = this;
      Notification.requestPermission().then(function (p) {
        if (p === "granted") {
          try { localStorage.setItem(KEY, "1"); } catch (e) {}
          toastSafe("已开启浏览器通知");
        } else {
          self.checked = false;
          toastSafe("通知权限被拒绝", "fail");
        }
      });
    });
  }
  function toastSafe(m, t) { try { showToast(m, t || "success"); } catch (e) {} }
  if (typeof window.updateStatusCards === "function") {
    var _u = window.updateStatusCards;
    window.updateStatusCards = function (s) {
      var r = _u.apply(this, arguments);
      try { check(s); } catch (e) {}
      return r;
    };
  }
  window.__fcNotifyCheck = check; /* 测试探针 */
})();

/* —— 告警 Webhook 设置(§2.4) —— */
(function () {
  "use strict";
  var input = document.getElementById("webhookInput");
  var btn = document.getElementById("webhookSaveBtn");
  if (!input || !btn) return;
  function refresh() {
    api("config").then(function (cfg) {
      if (cfg && typeof cfg.alert_webhook === "string") input.value = cfg.alert_webhook;
    });
  }
  refresh();
  btn.addEventListener("click", function () {
    var v = input.value.trim();
    if (v && !/^https?:\\/\\//i.test(v)) { showToast("地址需以 http:// 或 https:// 开头", "fail"); return; }
    api("config", "POST", { alert_webhook: v }).then(function (r) {
      if (r && r.ok) {
        if (r.config && typeof r.config.alert_webhook === "string") input.value = r.config.alert_webhook;
        showToast(v ? "Webhook 已保存" : "Webhook 已关闭");
      } else showToast("保存失败", "fail");
    });
  });
  var navSet = document.querySelector('.side-item[data-view="viewSettings"]');
  if (navSet) navSet.addEventListener("click", refresh);
  if (typeof window.doLogin === "function") {
    var _l = window.doLogin;
    window.doLogin = function () {
      var p = _l.apply(this, arguments);
      if (p && typeof p.then === "function") return p.then(function (r) { refresh(); return r; });
      refresh();
      return p;
    };
  }
})();

/* —— 区域管理:列表 / 新增 / 编辑 / 删除(§2.5) —— */
(function () {
  "use strict";
  var listEl = document.getElementById("zonesList");
  var editor = document.getElementById("zoneEditor");
  if (!listEl || !editor) return;
  var addBtn = document.getElementById("zoneAddBtn");
  var reloadBtn = document.getElementById("zoneReloadBtn");
  var cancelBtn = document.getElementById("zoneCancelBtn");
  var saveBtn = document.getElementById("zoneSaveBtn");
  var titleEl = document.getElementById("zoneEditorTitle");
  var nameIn = document.getElementById("zfName");
  var chBox = document.getElementById("zfChannels");
  var srcSel = document.getElementById("zfSource");
  var minIn = document.getElementById("zfMin");
  var curveBox = document.getElementById("zfCurve");
  var addNodeBtn = document.getElementById("zfAddNode");
  var delNodeBtn = document.getElementById("zfDelNode");

  var zones = [];
  var editingId = null;
  var draft = null;
  var channelNames = [];
  var gpuChecked = false;
  var optionsLoaded = false;

  var SRC_LABEL = { cpu: "CPU", disk: "硬盘", gpu: "GPU", max: "最高值" };
  var MODE_LABEL = { default: "默认", auto: "自动", manual: "手动", full: "全速" };

  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function toast(m, t) { try { showToast(m, t || "success"); } catch (e) {} }

  function loadOptions() {
    if (optionsLoaded) return Promise.resolve();
    return api("hardware").then(function (h) {
      channelNames = [];
      ((h && h.chips) || []).forEach(function (chip) {
        (chip.pwm_channels || []).forEach(function (ch) {
          if (channelNames.indexOf(ch) < 0) channelNames.push(ch);
        });
      });
      gpuChecked = !!(h && h.temp_sensors && h.temp_sensors.gpu);
      var gpuOpt = srcSel.querySelector('option[value="gpu"]');
      if (gpuOpt) gpuOpt.disabled = !gpuChecked;
      optionsLoaded = true;
    });
  }
  function fallbackZones(cfg) {
    if (cfg && cfg.curve && !cfg.zones) {
      return [{
        id: "default", name: "系统风扇", channels: [cfg.fan_channel || "pwm2"],
        temp_source: cfg.temp_source || "cpu", mode: cfg.mode || "default",
        min_pwm_percent: cfg.min_pwm_percent || 20,
        manual_pwm_percent: cfg.manual_pwm_percent || 50, curve: clone(cfg.curve)
      }];
    }
    return [];
  }
  function loadZones() {
    return api("config").then(function (cfg) {
      zones = (cfg && cfg.zones) || fallbackZones(cfg);
      renderList();
      return zones;
    });
  }
  function renderList() {
    listEl.innerHTML = "";
    if (!zones.length) {
      listEl.innerHTML = '<div class="zones-empty">未读取到区域配置</div>';
      return;
    }
    zones.forEach(function (z) {
      var row = document.createElement("div");
      row.className = "zone-row";
      row.innerHTML =
        '<div class="zone-row-main"><div class="zone-row-name"></div><div class="zone-row-meta"></div></div>' +
        '<div class="zone-row-btns">' +
        '<button class="btn btn-sm btn-secondary z-edit" type="button">编辑</button>' +
        '<button class="btn btn-sm btn-danger z-del" type="button">删除</button></div>';
      row.querySelector(".zone-row-name").textContent = z.name || z.id;
      row.querySelector(".zone-row-meta").textContent =
        (z.channels || []).join(" + ") + " · 来源 " + (SRC_LABEL[z.temp_source] || z.temp_source) +
        " · 模式 " + (MODE_LABEL[z.mode] || z.mode) + " · 最低 " + z.min_pwm_percent + "% · 曲线 " +
        ((z.curve || []).length) + " 节点";
      row.querySelector(".z-edit").addEventListener("click", function () { openEditor(z.id); });
      var delBtn = row.querySelector(".z-del");
      delBtn.disabled = zones.length <= 1;
      delBtn.title = delBtn.disabled ? "至少保留一个区域" : "删除该区域";
      delBtn.addEventListener("click", function () { if (!delBtn.disabled) removeZone(z.id); });
      listEl.appendChild(row);
    });
  }
  function renderChannels() {
    var names = channelNames.slice();
    (draft.channels || []).forEach(function (ch) { if (names.indexOf(ch) < 0) names.push(ch); });
    chBox.innerHTML = "";
    if (!names.length) { chBox.innerHTML = '<span class="hint">未探测到 PWM 通道</span>'; return; }
    names.forEach(function (name) {
      var label = document.createElement("label");
      label.className = "zf-ch";
      var cb = document.createElement("input");
      cb.type = "checkbox";
      cb.value = name;
      cb.checked = (draft.channels || []).indexOf(name) >= 0;
      cb.addEventListener("change", function () { draft.channels = readChannels(); });
      label.appendChild(cb);
      label.appendChild(document.createTextNode(" " + name));
      chBox.appendChild(label);
    });
  }
  function readChannels() {
    var out = [];
    Array.prototype.forEach.call(chBox.querySelectorAll("input:checked"), function (cb) { out.push(cb.value); });
    return out;
  }
  function renderCurve() {
    curveBox.innerHTML = "";
    draft.curve.forEach(function (node, i) {
      var row = document.createElement("div");
      row.className = "zf-node";
      row.innerHTML =
        '<span class="zf-node-label">节点' + (i + 1) + '</span>' +
        '<input type="number" min="0" max="120" value="' + node.temp + '"><span class="zf-unit">°C</span>' +
        '<span class="zf-arrow">→</span>' +
        '<input type="number" min="10" max="100" value="' + node.pwm_percent + '"><span class="zf-unit">%</span>';
      var ins = row.querySelectorAll("input");
      ins[0].addEventListener("input", function () { draft.curve[i].temp = parseInt(this.value, 10); });
      ins[1].addEventListener("input", function () { draft.curve[i].pwm_percent = parseInt(this.value, 10); });
      curveBox.appendChild(row);
    });
  }
  function validCurve() {
    var c = draft.curve;
    if (!Array.isArray(c) || c.length < 2 || c.length > 10) return "曲线需 2–10 个节点";
    var prev = -1;
    for (var i = 0; i < c.length; i++) {
      var t = c[i].temp, p = c[i].pwm_percent;
      if (!(t >= 0 && t <= 120)) return "节点 " + (i + 1) + " 温度需在 0–120°C";
      if (!(p >= 10 && p <= 100)) return "节点 " + (i + 1) + " 转速需在 10–100%";
      if (t <= prev) return "节点 " + (i + 1) + " 温度需大于前一节点";
      prev = t;
    }
    return "";
  }
  function findZone(id) {
    for (var i = 0; i < zones.length; i++) if (zones[i].id === id) return zones[i];
    return null;
  }
  function openEditor(zoneId) {
    loadOptions().then(function () {
      editingId = zoneId || null;
      var base = zoneId ? findZone(zoneId) : null;
      draft = base ? clone(base) : {
        id: "zone_" + Date.now().toString(36),
        name: "新区域",
        channels: [],
        temp_source: "cpu",
        mode: "default",
        min_pwm_percent: 20,
        manual_pwm_percent: 50,
        curve: clone(DEFAULT_CURVE)
      };
      titleEl.textContent = zoneId ? "编辑区域:" + ((base && base.name) || zoneId) : "新增区域";
      nameIn.value = draft.name || "";
      if (!gpuChecked) {
        var gpuOpt = srcSel.querySelector('option[value="gpu"]');
        srcSel.value = (gpuOpt && gpuOpt.disabled && draft.temp_source === "gpu") ? "cpu" : (draft.temp_source || "cpu");
      } else {
        srcSel.value = draft.temp_source || "cpu";
      }
      minIn.value = draft.min_pwm_percent || 20;
      renderChannels();
      renderCurve();
      editor.hidden = false;
      try { editor.scrollIntoView({ behavior: "smooth", block: "nearest" }); } catch (e) {}
    });
  }
  function closeEditor() { editor.hidden = true; editingId = null; draft = null; }
  function submitZones(nextZones, okMsg) {
    return api("config", "POST", { zones: nextZones }).then(function (r) {
      if (r && r.ok && r.config) {
        zones = r.config.zones || [];
        renderList();
        loadConfig(r.config);
        try { fetchStatus(); } catch (e) {}
        toast(okMsg);
        return true;
      }
      toast("保存失败", "fail");
      return false;
    });
  }
  if (addBtn) addBtn.addEventListener("click", function () {
    loadOptions().then(function () {
      if (!channelNames.length) { toast("未探测到 PWM 通道,无法新增区域", "fail"); return; }
      openEditor(null);
    });
  });
  if (reloadBtn) reloadBtn.addEventListener("click", function () { loadZones(); toast("已重新加载"); });
  if (cancelBtn) cancelBtn.addEventListener("click", closeEditor);
  if (addNodeBtn) addNodeBtn.addEventListener("click", function () {
    if (!draft) return;
    if (draft.curve.length >= 10) { toast("最多 10 个节点", "fail"); return; }
    var last = draft.curve[draft.curve.length - 1] || { temp: 30, pwm_percent: 20 };
    draft.curve.push({
      temp: Math.min(120, (last.temp || 30) + 10),
      pwm_percent: Math.min(100, (last.pwm_percent || 20) + 10)
    });
    renderCurve();
  });
  if (delNodeBtn) delNodeBtn.addEventListener("click", function () {
    if (!draft) return;
    if (draft.curve.length <= 2) { toast("至少保留 2 个节点", "fail"); return; }
    draft.curve.pop();
    renderCurve();
  });
  if (saveBtn) saveBtn.addEventListener("click", function () {
    if (!draft) return;
    var err = validCurve();
    if (err) { toast(err, "fail"); return; }
    var channels = readChannels();
    if (!channels.length) { toast("请至少选择一个 PWM 通道", "fail"); return; }
    var conflict = null;
    zones.forEach(function (z) {
      if (z.id === editingId) return;
      (z.channels || []).forEach(function (ch) { if (channels.indexOf(ch) >= 0) conflict = ch; });
    });
    if (conflict) { toast("通道 " + conflict + " 已被其他区域占用", "fail"); return; }
    var baseZone = editingId ? findZone(editingId) : null;
    var zone = {
      id: editingId || draft.id,
      name: (nameIn.value || "").trim() || "风扇区域",
      channels: channels,
      temp_source: srcSel.value,
      mode: (baseZone && baseZone.mode) || "default",
      min_pwm_percent: Math.max(10, Math.min(100, parseInt(minIn.value, 10) || 20)),
      manual_pwm_percent: draft.manual_pwm_percent || 50,
      curve: clone(draft.curve)
    };
    var next = zones.map(function (z) { return z.id === editingId ? zone : z; });
    if (!editingId) next.push(zone);
    var wantId = zone.id;
    submitZones(next, editingId ? "区域已更新" : "区域已创建").then(function (ok) {
      if (!ok) return;
      if (!findZone(wantId)) { toast("该区域因通道冲突或校验未通过,未保存", "fail"); return; }
      closeEditor();
    });
  });
  function removeZone(zoneId) {
    var z = findZone(zoneId) || {};
    if (!window.confirm("删除区域“" + (z.name || zoneId) + "”?该区域的 PWM 通道将不再由本应用控制。")) return;
    var next = zones.filter(function (z2) { return z2.id !== zoneId; });
    submitZones(next, "区域已删除").then(function (ok) {
      if (ok && editingId === zoneId) closeEditor();
    });
  }
  var navBtn = document.querySelector('.side-item[data-view="viewZones"]');
  if (navBtn) navBtn.addEventListener("click", function () { loadOptions().then(loadZones); });
  window.__fcZones = { loadZones: loadZones, openEditor: openEditor, getDraft: function () { return draft; } }; /* 测试探针 */
})();
</script>
"""
SCRIPTS = SCRIPTS.replace("__MODES_JS__", MODE_JS)
assert html.count("</body>") == 1
html = html.replace("</body>", SCRIPTS + "</body>", 1)

open(OUT, "w", encoding="utf-8", newline="").write(html)
print("legion assembly OK:", len(html))
checks = ["top-grid", "bottom-grid", "sidebar", "FAN CONSOLE", "pentagon", "gaugeCpu", "gaugePwm",
          "swManualUI", "segSource", "segPoll", "uiMinPwm", "wpPanel", "wpCustomApply", "hwChip",
          "singleModeSection", "settingsSection", "logsSection", "guideSection", "Legion 布局适配",
          "curveDirtyNote", "navCurveDirty", "sysInfo", "viewport-fit=cover", "curve-dirty-note",
          "gpuStat", "gpuTemp", 'value="gpu"',
          'app-version" content="v1.0"', "当前版本:<b>v1.0</b>", "跟随所选温度来源",
          "_fcCollapseEnd", "beforeunload", "<h3>温度来源</h3>",
          "log-actions", "spark-wrap", "cfg-actions", "__fcBuildLogText", "setLogPolling", "sparkLegend",
          "viewZones", "zoneAddBtn", "zfCurve", "notifyToggle", "webhookInput", "webhookSaveBtn",
          'rel="manifest"', "apple-touch-icon", "区域管理",
          "区域管理(多风扇)", "温度趋势与日志", "通知与告警", "备份与恢复", "手机端与添加到主屏"]
for m in checks:
    print("  -", m, "->", "OK" if m in html else "MISSING")

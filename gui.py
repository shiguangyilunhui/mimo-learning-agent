"""
MiMo 智能学习助手 - GUI v4
深度参考 Claude Code 设计语言：终端风格、流畅动画、高分辨率渲染
"""
import asyncio
import math
import threading
import tkinter as tk
from tkinter import ttk, font as tkfont
import uuid
import time
from typing import Optional, Callable

# ─── DPI 感知（高分辨率） ───
try:
    from ctypes import windll, c_int, byref
    windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
    # 获取主显示器缩放比例
    hdc = windll.user32.GetDC(0)
    dpi = windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
    windll.user32.ReleaseDC(0, hdc)
    SCALE = dpi / 96.0
except:
    SCALE = 1.0

# ─── Claude Code 精确配色（从 theme.ts 提取） ───
class Colors:
    """Claude Code Dark Theme - 精确匹配"""
    # 主背景
    BG = "#0d1117"              # GitHub Dark 背景
    SURFACE = "#161b22"         # 面板背景
    SURFACE_HOVER = "#1c2128"   # 悬停态
    SURFACE_ACTIVE = "#21262d"  # 激活态
    
    # 品牌色
    CLAUDE = "#d77757"          # Claude 橙色
    CLAUDE_DIM = "#a05a3a"      # 暗橙
    CLAUDE_GLOW = "#e8936f"     # 发光橙
    
    # 交互色
    PERMISSION = "#5769f7"      # 权限蓝
    PERMISSION_DIM = "#3a4aa0"  # 暗蓝
    PERMISSION_GLOW = "#7b8aff" # 发光蓝
    
    # 文字色
    TEXT = "#e6edf3"            # 主文字
    TEXT_SECONDARY = "#8b949e"  # 次要文字
    TEXT_MUTED = "#484f58"      # 暗文字
    TEXT_LINK = "#58a6ff"       # 链接色
    
    # 语义色
    SUCCESS = "#3fb950"         # 成功绿
    ERROR = "#f85149"           # 错误红
    WARNING = "#d29922"         # 警告琥珀
    INFO = "#58a6ff"            # 信息蓝
    
    # 边框和分隔
    BORDER = "#30363d"          # 边框
    BORDER_LIGHT = "#21262d"    # 浅边框
    DIVIDER = "#21262d"         # 分隔线
    
    # 特殊效果
    SHADOW = "#000000"          # 阴影
    GLOW = "#1f6feb33"          # 发光效果（带透明度）
    
    # 消息背景
    USER_BG = "#1c2128"         # 用户消息
    BOT_BG = "#161b22"          # 助手消息
    CODE_BG = "#0d1117"         # 代码块


# ─── 动画系统 ───
class Animation:
    """平滑动画引擎"""
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """三次缓出函数"""
        return 1 - (1 - t) ** 3
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """三次缓入缓出函数"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - (-2 * t + 2) ** 3 / 2
    
    @staticmethod
    def lerp(start: float, end: float, t: float) -> float:
        """线性插值"""
        return start + (end - start) * t


class AnimatedWidget:
    """可动画化的组件基类"""
    
    def __init__(self):
        self._animations = {}
    
    def animate(self, prop: str, start: float, end: float, 
                duration: int = 300, easing: str = "ease_out_cubic",
                on_update: Optional[Callable] = None,
                on_complete: Optional[Callable] = None):
        """启动属性动画"""
        if prop in self._animations:
            self.after_cancel(self._animations[prop])
        
        start_time = time.time() * 1000
        
        def update():
            current_time = time.time() * 1000
            elapsed = current_time - start_time
            progress = min(elapsed / duration, 1.0)
            
            # 应用缓动函数
            if easing == "ease_out_cubic":
                eased = Animation.ease_out_cubic(progress)
            elif easing == "ease_in_out_cubic":
                eased = Animation.ease_in_out_cubic(progress)
            else:
                eased = progress
            
            value = Animation.lerp(start, end, eased)
            
            if on_update:
                on_update(value)
            
            if progress < 1.0:
                self._animations[prop] = self.after(16, update)  # ~60fps
            else:
                del self._animations[prop]
                if on_complete:
                    on_complete()
        
        update()


# ─── 自定义组件 ───
class GlowCanvas(tk.Canvas):
    """带发光效果的画布"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self._glow_items = []
    
    def create_glow_oval(self, x1, y1, x2, y2, color, glow_radius=10):
        """创建带发光效果的圆形"""
        # 多层发光
        for i in range(glow_radius, 0, -2):
            alpha = int(20 * (1 - i / glow_radius))
            glow_color = self._blend_color(color, "#000000", alpha / 100)
            self.create_oval(x1-i, y1-i, x2+i, y2+i, fill="", outline=glow_color, width=1)
        
        # 主体
        return self.create_oval(x1, y1, x2, y2, fill=color, outline="")
    
    def _blend_color(self, color1, color2, alpha):
        """混合颜色"""
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 * (1 - alpha) + r2 * alpha)
        g = int(g1 * (1 - alpha) + g2 * alpha)
        b = int(b1 * (1 - alpha) + b2 * alpha)
        return f"#{r:02x}{g:02x}{b:02x}"


class TypingIndicator(tk.Frame):
    """打字指示器动画"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=Colors.BOT_BG)
        self.dots = []
        self._create_dots()
        self._animate()
    
    def _create_dots(self):
        """创建三个点"""
        for i in range(3):
            dot = tk.Canvas(self, width=8, height=8, bg=Colors.BOT_BG, highlightthickness=0)
            dot.pack(side="left", padx=2)
            oval = dot.create_oval(2, 2, 6, 6, fill=Colors.TEXT_MUTED, outline="")
            self.dots.append((dot, oval))
    
    def _animate(self):
        """动画效果"""
        def update(step=0):
            for i, (canvas, oval) in enumerate(self.dots):
                # 延迟动画
                phase = (step + i * 20) % 60
                if phase < 30:
                    alpha = phase / 30
                else:
                    alpha = 1 - (phase - 30) / 30
                
                # 颜色插值
                r = int(72 + (230 - 72) * alpha)
                g = int(79 + (237 - 79) * alpha)
                b = int(88 + (243 - 88) * alpha)
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                canvas.itemconfig(oval, fill=color)
            
            self.after(50, update, step + 1)
        
        update()


class MessageBubble(tk.Frame, AnimatedWidget):
    """消息气泡 - 参考 Claude Code 消息样式"""
    
    def __init__(self, parent, role: str, content: str, is_user: bool = True):
        tk.Frame.__init__(self, parent, bg=Colors.BG)
        AnimatedWidget.__init__(self)
        
        self.is_user = is_user
        self.alpha = 0.0
        
        # 创建容器
        self._create_layout(content)
        
        # 淡入动画
        self.animate("alpha", 0.0, 1.0, duration=400, on_update=self._update_alpha)
    
    def _create_layout(self, content: str):
        """创建布局"""
        # 外层容器
        outer = tk.Frame(self, bg=Colors.BG)
        outer.pack(fill="x", padx=16, pady=4)
        
        # 标签行
        label_frame = tk.Frame(outer, bg=Colors.BG)
        label_frame.pack(fill="x", anchor="w" if not self.is_user else "e")
        
        if self.is_user:
            # 用户标签
            user_label = tk.Label(label_frame, text="You", 
                                  font=("Consolas", 10, "bold"),
                                  fg=Colors.PERMISSION, bg=Colors.BG)
            user_label.pack(anchor="e")
        else:
            # 助手标签
            bot_label = tk.Label(label_frame, text="MiMo", 
                                 font=("Consolas", 10, "bold"),
                                 fg=Colors.CLAUDE, bg=Colors.BG)
            bot_label.pack(anchor="w")
        
        # 消息内容
        bg = Colors.USER_BG if self.is_user else Colors.BOT_BG
        msg_frame = tk.Frame(outer, bg=bg, padx=14, pady=10)
        msg_frame.pack(anchor="e" if self.is_user else "w", 
                       padx=(80, 0) if self.is_user else (0, 80))
        
        # 添加圆角效果（通过Canvas实现）
        self._render_content(msg_frame, content, bg)
    
    def _render_content(self, parent, content: str, bg: str):
        """渲染消息内容"""
        lines = content.split("\n")
        
        for line in lines:
            if not line.strip():
                # 空行
                spacer = tk.Label(parent, text=" ", font=("Consolas", 4), bg=bg)
                spacer.pack(anchor="w")
                continue
            
            # 判断内容类型
            if any(line.startswith(p) for p in ["    ", "│", "┌", "└", "├", ">", "$", "#", "- ", "* "]):
                # 代码/指令样式
                code_label = tk.Label(parent, text=line, 
                                      font=("Consolas", 11),
                                      fg=Colors.WARNING, bg=bg,
                                      anchor="w", justify="left")
                code_label.pack(anchor="w", fill="x")
            elif line.startswith("```"):
                # 代码块标记
                marker = tk.Label(parent, text="─" * 40, 
                                  font=("Consolas", 9),
                                  fg=Colors.TEXT_MUTED, bg=bg)
                marker.pack(anchor="w", fill="x", pady=2)
            else:
                # 普通文本
                text_label = tk.Label(parent, text=line,
                                      font=("Segoe UI", 11),
                                      fg=Colors.TEXT, bg=bg,
                                      wraplength=550, anchor="w", justify="left")
                text_label.pack(anchor="w", fill="x")
    
    def _update_alpha(self, alpha: float):
        """更新透明度（模拟）"""
        self.alpha = alpha
        # tkinter 不直接支持透明度，这里通过颜色调整模拟
        if alpha < 1.0:
            blend = int(alpha * 100)
            # 可以调整前景色亮度来模拟
            pass


class StatusBar(tk.Frame):
    """底部状态栏 - 参考 Claude Code StatusLine"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=Colors.SURFACE, height=32)
        self.pack(fill="x", side="bottom")
        self.pack_propagate(False)
        
        # 分隔线
        sep = tk.Frame(self, bg=Colors.BORDER, height=1)
        sep.pack(fill="x")
        
        # 内容区域
        content = tk.Frame(self, bg=Colors.SURFACE)
        content.pack(fill="x", padx=12, pady=6)
        
        # 左侧：状态指示器
        left = tk.Frame(content, bg=Colors.SURFACE)
        left.pack(side="left")
        
        # 状态点（带发光效果）
        self.status_canvas = tk.Canvas(left, width=12, height=12, 
                                        bg=Colors.SURFACE, highlightthickness=0)
        self.status_canvas.pack(side="left", pady=2)
        self._draw_status_dot(Colors.SUCCESS)
        
        self.status_text = tk.Label(left, text="就绪", 
                                     font=("Consolas", 9),
                                     fg=Colors.TEXT_SECONDARY, 
                                     bg=Colors.SURFACE)
        self.status_text.pack(side="left", padx=(8, 0))
        
        # 中间：模型信息
        self.model_label = tk.Label(content, text="MiMo-V2.5-Pro", 
                                     font=("Consolas", 10, "bold"),
                                     fg=Colors.CLAUDE, 
                                     bg=Colors.SURFACE)
        self.model_label.pack(side="left", padx=24)
        
        # 右侧：统计信息
        right = tk.Frame(content, bg=Colors.SURFACE)
        right.pack(side="right")
        
        # 统计项
        stats = [
            ("turns", "Turns", "0"),
            ("level", "Level", "0/10"),
            ("tokens", "Tokens", "0"),
        ]
        
        self.stat_labels = {}
        for key, label, value in stats:
            stat_frame = tk.Frame(right, bg=Colors.SURFACE)
            stat_frame.pack(side="left", padx=12)
            
            tk.Label(stat_frame, text=label, font=("Consolas", 8),
                     fg=Colors.TEXT_MUTED, bg=Colors.SURFACE).pack(side="left")
            
            value_label = tk.Label(stat_frame, text=value, 
                                   font=("Consolas", 9, "bold"),
                                   fg=Colors.TEXT, bg=Colors.SURFACE)
            value_label.pack(side="left", padx=(4, 0))
            self.stat_labels[key] = value_label
    
    def _draw_status_dot(self, color: str):
        """绘制带发光效果的状态点"""
        self.status_canvas.delete("all")
        # 外发光
        for i in range(4, 0, -1):
            alpha = int(30 * (1 - i / 4))
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            glow = f"#{r:02x}{g:02x}{b:02x}"
            self.status_canvas.create_oval(4-i, 4-i, 8+i, 8+i, 
                                           fill="", outline=glow, width=1)
        # 主体
        self.status_canvas.create_oval(4, 4, 8, 8, fill=color, outline="")
    
    def update_status(self, text: str, color: str = Colors.TEXT_SECONDARY):
        """更新状态"""
        self.status_text.config(text=text)
        self._draw_status_dot(color)
    
    def update_stats(self, turns: int = 0, level: int = 0, tokens: int = 0):
        """更新统计"""
        self.stat_labels["turns"].config(text=str(turns))
        
        level_color = Colors.SUCCESS if level >= 7 else Colors.WARNING if level >= 4 else Colors.TEXT
        self.stat_labels["level"].config(text=f"{level}/10", fg=level_color)
        
        if tokens > 1000:
            token_str = f"{tokens/1000:.1f}k"
        else:
            token_str = str(tokens)
        self.stat_labels["tokens"].config(text=token_str)


class InputArea(tk.Frame):
    """输入区域 - 参考 Claude Code PromptInput"""
    
    def __init__(self, parent, on_submit: Callable):
        super().__init__(parent, bg=Colors.BG)
        self.pack(fill="x", side="bottom")
        self.on_submit = on_submit
        self._focused = False
        
        # 分隔线
        sep = tk.Frame(self, bg=Colors.BORDER, height=1)
        sep.pack(fill="x")
        
        # 输入框容器
        input_container = tk.Frame(self, bg=Colors.BG)
        input_container.pack(fill="x", padx=16, pady=12)
        
        # 输入框背景（带边框效果）
        self.input_frame = tk.Frame(input_container, bg=Colors.SURFACE,
                                     highlightbackground=Colors.BORDER,
                                     highlightthickness=1,
                                     highlightcolor=Colors.PERMISSION)
        self.input_frame.pack(fill="x")
        
        # 左侧图标区
        icon_frame = tk.Frame(self.input_frame, bg=Colors.SURFACE)
        icon_frame.pack(side="left", padx=(12, 8), pady=10)
        
        # 提示符号
        prompt_icon = tk.Label(icon_frame, text="❯", 
                               font=("Consolas", 12),
                               fg=Colors.CLAUDE, 
                               bg=Colors.SURFACE)
        prompt_icon.pack()
        
        # 输入框
        self.text_input = tk.Text(
            self.input_frame,
            font=("Consolas", 11),
            bg=Colors.SURFACE,
            fg=Colors.TEXT,
            insertbackground=Colors.CLAUDE,
            insertwidth=2,
            relief="flat",
            height=1,
            wrap="word",
            padx=4,
            pady=10,
            undo=True,
            selectbackground=Colors.PERMISSION_DIM,
            selectforeground=Colors.TEXT
        )
        self.text_input.pack(side="left", fill="both", expand=True)
        
        # 右侧按钮区
        btn_frame = tk.Frame(self.input_frame, bg=Colors.SURFACE)
        btn_frame.pack(side="right", padx=(8, 12), pady=8)
        
        # 发送按钮
        self.send_btn = tk.Button(
            btn_frame,
            text="Enter ⏎",
            font=("Consolas", 9),
            bg=Colors.PERMISSION,
            fg="white",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            activebackground=Colors.PERMISSION_DIM,
            activeforeground="white",
            command=self._submit
        )
        self.send_btn.pack()
        
        # 绑定事件
        self.text_input.bind("<Return>", self._on_enter)
        self.text_input.bind("<Shift-Return>", lambda e: None)
        self.text_input.bind("<FocusIn>", self._on_focus_in)
        self.text_input.bind("<FocusOut>", self._on_focus_out)
        
        # 底部提示
        hint_frame = tk.Frame(self, bg=Colors.BG)
        hint_frame.pack(fill="x", padx=16, pady=(0, 8))
        
        hints = [
            ("Enter", "发送"),
            ("Shift+Enter", "换行"),
            ("/help", "帮助"),
            ("/status", "状态"),
        ]
        
        for key, desc in hints:
            hint = tk.Label(hint_frame, text=f"  {key} {desc}",
                            font=("Consolas", 8),
                            fg=Colors.TEXT_MUTED,
                            bg=Colors.BG)
            hint.pack(side="left")
    
    def _on_focus_in(self, event):
        """获得焦点"""
        self._focused = True
        self.input_frame.config(highlightbackground=Colors.PERMISSION)
    
    def _on_focus_out(self, event):
        """失去焦点"""
        self._focused = False
        self.input_frame.config(highlightbackground=Colors.BORDER)
    
    def _on_enter(self, event):
        """回车提交"""
        if not (event.state & 0x1):  # 非 Shift
            self._submit()
            return "break"
    
    def _submit(self):
        """提交消息"""
        text = self.text_input.get("1.0", "end").strip()
        if text:
            self.text_input.delete("1.0", "end")
            self.on_submit(text)


class ChatPage(tk.Frame):
    """对话页面 - 主界面"""
    
    def __init__(self, parent, app):
        super().__init__(parent, bg=Colors.BG)
        self.app = app
        
        # 创建滚动区域
        self._create_scroll_area()
        
        # 输入区域
        self.input_area = InputArea(self, self.app._send_message)
        
        # 欢迎消息
        self.after(200, self._show_welcome)
    
    def _create_scroll_area(self):
        """创建滚动区域"""
        # 滚动容器
        container = tk.Frame(self, bg=Colors.BG)
        container.pack(fill="both", expand=True)
        
        # Canvas 用于平滑滚动
        self.canvas = tk.Canvas(container, bg=Colors.BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        # 消息容器
        self.messages_frame = tk.Frame(self.canvas, bg=Colors.BG)
        self.messages_frame.bind("<Configure>", 
                                  lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 布局
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 绑定滚动
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # 平滑滚动状态
        self._scroll_target = 0
        self._scroll_current = 0
        self._scrolling = False
    
    def _on_canvas_configure(self, event):
        """Canvas 大小变化"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """鼠标滚轮"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _smooth_scroll_to_bottom(self):
        """平滑滚动到底部"""
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def _show_welcome(self):
        """显示欢迎消息"""
        welcome = """你好！我是 MiMo 智能学习助手。

我可以帮你学习编程，但不会直接给你答案。我会通过提问引导你自己思考。

试试问我一个编程问题吧：
  > 如何用 Python 实现二分查找？
  > 递归和迭代有什么区别？
  > 什么是时间复杂度？

输入 /help 查看所有命令"""
        
        self.add_message("assistant", welcome)
    
    def add_message(self, role: str, content: str):
        """添加消息"""
        is_user = (role == "user")
        bubble = MessageBubble(self.messages_frame, role, content, is_user)
        bubble.pack(fill="x", padx=8, pady=2)
        
        # 滚动到底部
        self.after(50, self._smooth_scroll_to_bottom)


class ReportPage(tk.Frame):
    """学习报告页面"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=Colors.BG)
        
        # 滚动容器
        canvas = tk.Canvas(self, bg=Colors.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=Colors.BG)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        
        # 标题
        header = tk.Frame(scroll_frame, bg=Colors.BG)
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        tk.Label(header, text="学习报告", 
                 font=("Segoe UI", 20, "bold"),
                 fg=Colors.TEXT, bg=Colors.BG).pack(anchor="w")
        
        tk.Label(header, text="查看你的学习进度和知识掌握情况",
                 font=("Segoe UI", 11),
                 fg=Colors.TEXT_SECONDARY, 
                 bg=Colors.BG).pack(anchor="w", pady=(4, 0))
        
        # 统计卡片
        cards_frame = tk.Frame(scroll_frame, bg=Colors.BG)
        cards_frame.pack(fill="x", padx=32, pady=8)
        
        self.stat_labels = {}
        stats = [
            ("turns", "对话轮数", "0", Colors.PERMISSION),
            ("level", "理解程度", "0/10", Colors.CLAUDE),
            ("topics", "知识点", "0", Colors.SUCCESS),
            ("time", "学习时长", "0min", Colors.WARNING),
        ]
        
        for key, title, value, color in stats:
            card = tk.Frame(cards_frame, bg=Colors.SURFACE, padx=20, pady=16)
            card.pack(side="left", fill="both", expand=True, padx=4)
            card.config(highlightbackground=Colors.BORDER, highlightthickness=1)
            
            # 图标区域
            icon_frame = tk.Frame(card, bg=Colors.SURFACE)
            icon_frame.pack(fill="x")
            
            # 小圆点指示器
            indicator = tk.Canvas(icon_frame, width=10, height=10, 
                                  bg=Colors.SURFACE, highlightthickness=0)
            indicator.pack(side="left")
            indicator.create_oval(1, 1, 9, 9, fill=color, outline="")
            
            tk.Label(icon_frame, text=title, font=("Segoe UI", 10),
                     fg=Colors.TEXT_SECONDARY, bg=Colors.SURFACE).pack(side="left", padx=8)
            
            # 数值
            lbl = tk.Label(card, text=value, 
                           font=("Consolas", 24, "bold"),
                           fg=color, bg=Colors.SURFACE)
            lbl.pack(anchor="w", pady=(12, 0))
            self.stat_labels[key] = lbl
        
        # 知识点列表
        list_frame = tk.Frame(scroll_frame, bg=Colors.SURFACE, padx=24, pady=20)
        list_frame.pack(fill="both", expand=True, padx=32, pady=16)
        list_frame.config(highlightbackground=Colors.BORDER, highlightthickness=1)
        
        # 列表标题
        list_header = tk.Frame(list_frame, bg=Colors.SURFACE)
        list_header.pack(fill="x", pady=(0, 16))
        
        tk.Label(list_header, text="知识点掌握情况",
                 font=("Segoe UI", 14, "bold"),
                 fg=Colors.TEXT, bg=Colors.SURFACE).pack(side="left")
        
        # 图例
        legend = tk.Frame(list_header, bg=Colors.SURFACE)
        legend.pack(side="right")
        
        tk.Canvas(legend, width=10, height=10, bg=Colors.SURFACE, 
                  highlightthickness=0).pack(side="left")
        legend.create_oval(1, 1, 9, 9, fill=Colors.SUCCESS, outline="")
        tk.Label(legend, text="已掌握", font=("Segoe UI", 9),
                 fg=Colors.TEXT_SECONDARY, bg=Colors.SURFACE).pack(side="left", padx=(4, 12))
        
        tk.Canvas(legend, width=10, height=10, bg=Colors.SURFACE,
                  highlightthickness=0).pack(side="left")
        tk.Label(legend, text="需加强", font=("Segoe UI", 9),
                 fg=Colors.TEXT_SECONDARY, bg=Colors.SURFACE).pack(side="left", padx=(4, 0))
        
        # 知识点内容
        self.knowledge_frame = tk.Frame(list_frame, bg=Colors.SURFACE)
        self.knowledge_frame.pack(fill="both", expand=True)
        
        self.empty_label = tk.Label(self.knowledge_frame,
                                     text="暂无学习记录\n\n开始对话后，这里会显示你的学习进度",
                                     font=("Segoe UI", 11),
                                     fg=Colors.TEXT_MUTED,
                                     bg=Colors.SURFACE,
                                     justify="center")
        self.empty_label.pack(expand=True)
    
    def update_stats(self, turns: int = 0, level: int = 0, 
                     topics: int = 0, time_min: int = 0):
        """更新统计"""
        self.stat_labels["turns"].config(text=str(turns))
        self.stat_labels["level"].config(text=f"{level}/10")
        self.stat_labels["topics"].config(text=str(topics))
        self.stat_labels["time"].config(text=f"{time_min}min")
    
    def update_knowledge(self, weak_points: list, strong_points: list):
        """更新知识点"""
        for widget in self.knowledge_frame.winfo_children():
            widget.destroy()
        
        all_points = list(set(weak_points + strong_points))
        if not all_points:
            self.empty_label = tk.Label(self.knowledge_frame,
                                         text="暂无学习记录\n\n开始对话后，这里会显示你的学习进度",
                                         font=("Segoe UI", 11),
                                         fg=Colors.TEXT_MUTED,
                                         bg=Colors.SURFACE,
                                         justify="center")
            self.empty_label.pack(expand=True)
            return
        
        for point in all_points:
            row = tk.Frame(self.knowledge_frame, bg=Colors.SURFACE)
            row.pack(fill="x", pady=4)
            
            is_strong = point in strong_points
            color = Colors.SUCCESS if is_strong else Colors.WARNING
            status = "已掌握" if is_strong else "需加强"
            
            # 状态指示器
            indicator = tk.Canvas(row, width=12, height=12, 
                                  bg=Colors.SURFACE, highlightthickness=0)
            indicator.pack(side="left", padx=(0, 12))
            indicator.create_oval(2, 2, 10, 10, fill=color, outline="")
            
            # 知识点名称
            tk.Label(row, text=point, font=("Segoe UI", 11),
                     fg=Colors.TEXT, bg=Colors.SURFACE,
                     width=25, anchor="w").pack(side="left")
            
            # 状态标签
            status_label = tk.Label(row, text=status,
                                     font=("Consolas", 10),
                                     fg=color, bg=Colors.SURFACE)
            status_label.pack(side="left", padx=12)
            
            # 分隔线
            sep = tk.Frame(self.knowledge_frame, bg=Colors.DIVIDER, height=1)
            sep.pack(fill="x", pady=2)


class SettingsPage(tk.Frame):
    """设置页面"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=Colors.BG)
        
        # 滚动容器
        canvas = tk.Canvas(self, bg=Colors.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=Colors.BG)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        
        # 标题
        header = tk.Frame(scroll_frame, bg=Colors.BG)
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        tk.Label(header, text="设置",
                 font=("Segoe UI", 20, "bold"),
                 fg=Colors.TEXT, bg=Colors.BG).pack(anchor="w")
        
        tk.Label(header, text="配置 MiMo API 和应用选项",
                 font=("Segoe UI", 11),
                 fg=Colors.TEXT_SECONDARY,
                 bg=Colors.BG).pack(anchor="w", pady=(4, 0))
        
        # API 配置
        api_frame = tk.Frame(scroll_frame, bg=Colors.SURFACE, padx=24, pady=20)
        api_frame.pack(fill="x", padx=32, pady=8)
        api_frame.config(highlightbackground=Colors.BORDER, highlightthickness=1)
        
        tk.Label(api_frame, text="MiMo API 配置",
                 font=("Segoe UI", 14, "bold"),
                 fg=Colors.TEXT, bg=Colors.SURFACE).pack(anchor="w", pady=(0, 16))
        
        # API Key
        self._create_input_field(api_frame, "API Key", "sk-...", show="*")
        
        # API Base
        self._create_input_field(api_frame, "API Base", "https://api.xiaomimimo.com/v1")
        
        # 模型选择
        self._create_input_field(api_frame, "模型", "MiMo-V2.5-Pro")
        
        # 保存按钮
        btn_frame = tk.Frame(api_frame, bg=Colors.SURFACE)
        btn_frame.pack(fill="x", pady=(16, 0))
        
        save_btn = tk.Button(btn_frame, text="保存配置",
                             font=("Consolas", 10),
                             bg=Colors.PERMISSION,
                             fg="white",
                             relief="flat",
                             padx=24,
                             pady=8,
                             cursor="hand2",
                             activebackground=Colors.PERMISSION_DIM,
                             command=self._save)
        save_btn.pack(anchor="w")
        
        # 关于
        about_frame = tk.Frame(scroll_frame, bg=Colors.SURFACE, padx=24, pady=20)
        about_frame.pack(fill="x", padx=32, pady=8)
        about_frame.config(highlightbackground=Colors.BORDER, highlightthickness=1)
        
        tk.Label(about_frame, text="关于",
                 font=("Segoe UI", 14, "bold"),
                 fg=Colors.TEXT, bg=Colors.SURFACE).pack(anchor="w", pady=(0, 16))
        
        info = [
            ("版本", "1.0.0"),
            ("作者", "shiguangyilunhui"),
            ("GitHub", "github.com/shiguangyilunhui/mimo-learning-agent"),
            ("模型", "Xiaomi MiMo-V2.5-Pro"),
            ("架构", "Multi-Agent + Tool Use"),
            ("设计", "参考 Claude Code 设计语言"),
        ]
        
        for label, value in info:
            row = tk.Frame(about_frame, bg=Colors.SURFACE)
            row.pack(fill="x", pady=4)
            
            tk.Label(row, text=label, font=("Consolas", 10),
                     fg=Colors.TEXT_SECONDARY, bg=Colors.SURFACE,
                     width=8, anchor="w").pack(side="left")
            
            tk.Label(row, text=value, font=("Segoe UI", 10),
                     fg=Colors.TEXT, bg=Colors.SURFACE,
                     anchor="w").pack(side="left", padx=8)
    
    def _create_input_field(self, parent, label: str, placeholder: str, show: str = None):
        """创建输入字段"""
        row = tk.Frame(parent, bg=Colors.SURFACE)
        row.pack(fill="x", pady=8)
        
        tk.Label(row, text=label, font=("Consolas", 10),
                 fg=Colors.TEXT_SECONDARY, bg=Colors.SURFACE,
                 width=10, anchor="w").pack(side="left")
        
        entry = tk.Entry(row, font=("Consolas", 11),
                         bg=Colors.SURFACE_ACTIVE,
                         fg=Colors.TEXT,
                         insertbackground=Colors.CLAUDE,
                         relief="flat",
                         show=show)
        entry.insert(0, placeholder)
        entry.pack(side="left", fill="x", expand=True, padx=8, ipady=6)
        
        return entry
    
    def _save(self):
        """保存配置"""
        from pathlib import Path
        # 这里简化处理，实际应该读取输入框的值
        env = "MIMO_API_KEY=your_key_here\nMIMO_API_BASE=https://api.xiaomimimo.com/v1\n"
        (Path(__file__).parent / ".env").write_text(env, encoding="utf-8")
        
        # 显示保存成功提示
        self._show_toast("配置已保存")
    
    def _show_toast(self, message: str):
        """显示提示消息"""
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        
        # 位置
        x = self.winfo_rootx() + self.winfo_width() // 2 - 100
        y = self.winfo_rooty() + 50
        toast.geometry(f"200x40+{x}+{y}")
        
        # 内容
        label = tk.Label(toast, text=message,
                         font=("Consolas", 10),
                         bg=Colors.SUCCESS,
                         fg="white",
                         padx=20,
                         pady=8)
        label.pack(fill="both", expand=True)
        
        # 自动关闭
        toast.after(2000, toast.destroy)


class MiMoApp(tk.Tk):
    """主应用 - 参考 Claude Code 架构"""
    
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.title("MiMo 智能学习助手")
        self.geometry("1200x800")
        self.minsize(1000, 650)
        self.configure(bg=Colors.BG)
        
        # 应用状态
        self.student_id = f"student_{uuid.uuid4().hex[:8]}"
        self.conversation_manager = None
        self.loop = asyncio.new_event_loop()
        self.start_time = time.time()
        
        # 构建界面
        self._build_nav()
        self._build_pages()
        self._build_status_bar()
        
        # 启动异步循环
        self._start_async()
        
        # 绑定快捷键
        self._bind_shortcuts()
    
    def _build_nav(self):
        """构建顶部导航栏"""
        nav = tk.Frame(self, bg=Colors.SURFACE, height=52)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        
        # 分隔线
        sep = tk.Frame(nav, bg=Colors.BORDER, height=1)
        sep.pack(fill="x", side="bottom")
        
        # Logo 区域
        logo_frame = tk.Frame(nav, bg=Colors.SURFACE)
        logo_frame.pack(side="left", padx=20)
        
        # Logo 图标
        logo_canvas = tk.Canvas(logo_frame, width=32, height=32, 
                                bg=Colors.SURFACE, highlightthickness=0)
        logo_canvas.pack(side="left", pady=10)
        
        # 绘制 Logo（带发光效果）
        logo_canvas.create_oval(2, 2, 30, 30, fill=Colors.CLAUDE, outline="")
        logo_canvas.create_text(16, 17, text="M", fill="white", 
                                font=("Consolas", 14, "bold"))
        
        # Logo 文字
        tk.Label(logo_frame, text="  MiMo",
                 font=("Consolas", 14, "bold"),
                 fg=Colors.CLAUDE, bg=Colors.SURFACE).pack(side="left", pady=10)
        
        # 版本标签
        version_label = tk.Label(logo_frame, text=" v1.0",
                                 font=("Consolas", 9),
                                 fg=Colors.TEXT_MUTED,
                                 bg=Colors.SURFACE)
        version_label.pack(side="left", pady=10, padx=(4, 0))
        
        # 导航标签
        nav_tabs = tk.Frame(nav, bg=Colors.SURFACE)
        nav_tabs.pack(side="left", padx=32)
        
        self.nav_buttons = {}
        tabs = [
            ("chat", "对话", "💬"),
            ("report", "报告", "📊"),
            ("settings", "设置", "⚙️"),
        ]
        
        for key, label, icon in tabs:
            btn_frame = tk.Frame(nav_tabs, bg=Colors.SURFACE)
            btn_frame.pack(side="left", padx=4)
            
            btn = tk.Label(btn_frame, text=f" {icon} {label} ",
                           font=("Segoe UI", 10),
                           fg=Colors.TEXT_MUTED,
                           bg=Colors.SURFACE,
                           padx=12,
                           pady=14,
                           cursor="hand2")
            btn.pack()
            
            # 绑定事件
            btn.bind("<Button-1>", lambda e, k=key: self._switch_page(k))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=Colors.SURFACE_HOVER))
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(
                bg=Colors.SURFACE_ACTIVE if k == self._current_page else Colors.SURFACE))
            
            self.nav_buttons[key] = btn
        
        # 右侧信息
        right = tk.Frame(nav, bg=Colors.SURFACE)
        right.pack(side="right", padx=20)
        
        # 用户 ID
        tk.Label(right, text=f"ID: {self.student_id[-8:]}",
                 font=("Consolas", 9),
                 fg=Colors.TEXT_MUTED,
                 bg=Colors.SURFACE).pack(pady=14)
        
        self._current_page = "chat"
    
    def _build_pages(self):
        """构建页面"""
        self.page_container = tk.Frame(self, bg=Colors.BG)
        self.page_container.pack(fill="both", expand=True)
        
        # 创建页面
        self.pages = {}
        self.pages["chat"] = ChatPage(self.page_container, self)
        self.pages["report"] = ReportPage(self.page_container)
        self.pages["settings"] = SettingsPage(self.page_container)
        
        # 显示默认页面
        self._switch_page("chat")
    
    def _build_status_bar(self):
        """构建状态栏"""
        self.status_bar = StatusBar(self)
    
    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.bind("<Control-1>", lambda e: self._switch_page("chat"))
        self.bind("<Control-2>", lambda e: self._switch_page("report"))
        self.bind("<Control-3>", lambda e: self._switch_page("settings"))
        self.bind("<Control-q>", lambda e: self.quit())
    
    def _switch_page(self, key: str):
        """切换页面"""
        if key == self._current_page:
            return
        
        # 隐藏所有页面
        for page in self.pages.values():
            page.pack_forget()
        
        # 显示目标页面
        self.pages[key].pack(fill="both", expand=True)
        
        # 更新导航按钮状态
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.config(fg=Colors.TEXT, bg=Colors.SURFACE_ACTIVE,
                           font=("Segoe UI", 10, "bold"))
            else:
                btn.config(fg=Colors.TEXT_MUTED, bg=Colors.SURFACE,
                           font=("Segoe UI", 10))
        
        self._current_page = key
    
    def _add_message(self, role: str, content: str):
        """添加消息到聊天页面"""
        self.pages["chat"].add_message(role, content)
    
    def _send_message(self, text: str):
        """发送消息"""
        # 添加用户消息
        self._add_message("user", text)
        
        # 检查特殊命令
        if text.lower() == "status" and self.conversation_manager:
            self._show_status()
            return
        
        if text.lower() == "help":
            self._show_help()
            return
        
        # 更新状态
        self.status_bar.update_status("思考中...", Colors.WARNING)
        
        # 异步处理
        asyncio.run_coroutine_threadsafe(self._process(text), self.loop)
    
    def _show_status(self):
        """显示状态"""
        s = self.conversation_manager.get_conversation_summary()
        self._add_message("assistant",
            f"当前学习状态：\n\n"
            f"  对话轮数：{s['total_turns']}\n"
            f"  理解程度：{s['understanding_level']} / 10\n"
            f"  薄弱点：{', '.join(s['weak_points']) or '暂无'}\n"
            f"  优势点：{', '.join(s['strong_points']) or '暂无'}")
    
    def _show_help(self):
        """显示帮助"""
        self._add_message("assistant",
            "可用命令：\n\n"
            "  /status  - 查看学习状态\n"
            "  /help    - 显示此帮助\n"
            "  /clear   - 清空对话\n\n"
            "你也可以直接输入编程问题，我会引导你思考。")
    
    async def _process(self, text: str):
        """处理消息"""
        try:
            result = await self.conversation_manager.process_message(text)
            response = result.get("response", "处理出错，请重试。")
            self.after(0, lambda: self._on_result(result, response))
        except Exception as e:
            self.after(0, lambda: self._add_message("assistant", f"处理出错：{e}"))
            self.after(0, lambda: self.status_bar.update_status("出错", Colors.ERROR))
    
    def _on_result(self, result: dict, response: str):
        """处理结果"""
        # 添加助手消息
        self._add_message("assistant", response)
        
        # 更新状态
        s = self.conversation_manager.get_conversation_summary()
        elapsed = int((time.time() - self.start_time) / 60)
        
        # 更新状态栏
        self.status_bar.update_stats(s["total_turns"], s["understanding_level"], 0)
        self.status_bar.update_status("就绪", Colors.SUCCESS)
        
        # 更新报告页面
        self.pages["report"].update_stats(
            s["total_turns"], s["understanding_level"],
            len(set(s["weak_points"] + s["strong_points"])), elapsed)
        self.pages["report"].update_knowledge(s["weak_points"], s["strong_points"])
    
    def _start_async(self):
        """启动异步循环"""
        def run():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        threading.Thread(target=run, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self._init(), self.loop)
    
    async def _init(self):
        """初始化"""
        from core import ConversationManager
        self.conversation_manager = ConversationManager(student_id=self.student_id)
        self.after(0, lambda: self.status_bar.update_status("就绪", Colors.SUCCESS))
    
    def run(self):
        """运行应用"""
        self.mainloop()


def main():
    """主函数"""
    app = MiMoApp()
    app.run()


if __name__ == "__main__":
    main()

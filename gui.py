"""
MiMo 智能学习助手 - GUI 前端
现代聊天界面设计，参考 Claude Code 的交互风格
"""
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, font as tkfont
import uuid
import time

# ─── 配色方案 ───
C = {
    "bg": "#0f0f1a",
    "surface": "#1a1a2e",
    "surface2": "#252540",
    "surface3": "#2e2e50",
    "accent": "#6c5ce7",
    "accent_hover": "#7c6cf7",
    "accent_dim": "#4a3db0",
    "text": "#e8e8f0",
    "text_secondary": "#9090b0",
    "text_muted": "#606080",
    "success": "#00d2a0",
    "warning": "#ffb347",
    "error": "#ff6b6b",
    "border": "#303055",
    "input_bg": "#1e1e38",
    "scrollbar": "#3a3a60",
    "user_bg": "#2a2a55",
    "bot_bg": "#1a1a35",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MiMo 智能学习助手")
        self.geometry("1000x700")
        self.minsize(800, 550)
        self.configure(bg=C["bg"])
        self.student_id = f"student_{uuid.uuid4().hex[:8]}"
        self.conversation_manager = None
        self.loop = asyncio.new_event_loop()
        self._msg_widgets = []
        self._build()
        self._start_async()

    # ─── UI 构建 ───
    def _build(self):
        # 顶部栏
        top = tk.Frame(self, bg=C["surface"], height=56)
        top.pack(fill="x")
        top.pack_propagate(False)

        # Logo区域
        logo_frame = tk.Frame(top, bg=C["surface"])
        logo_frame.pack(side="left", padx=20)

        # 圆形logo
        logo_canvas = tk.Canvas(logo_frame, width=32, height=32, bg=C["surface"], highlightthickness=0)
        logo_canvas.pack(side="left", pady=12)
        logo_canvas.create_oval(2, 2, 30, 30, fill=C["accent"], outline="")
        logo_canvas.create_text(16, 16, text="M", fill="white", font=("Segoe UI", 12, "bold"))

        tk.Label(logo_frame, text="  MiMo 智能学习助手", font=("Segoe UI", 14, "bold"),
                 fg=C["text"], bg=C["surface"]).pack(side="left", pady=12)

        # 右侧状态
        right_frame = tk.Frame(top, bg=C["surface"])
        right_frame.pack(side="right", padx=20)

        self.status_indicator = tk.Canvas(right_frame, width=10, height=10, bg=C["surface"], highlightthickness=0)
        self.status_indicator.pack(side="left", pady=23)
        self.status_indicator.create_oval(1, 1, 9, 9, fill=C["success"], outline="")

        self.status_text = tk.Label(right_frame, text="就绪", font=("Segoe UI", 10),
                                     fg=C["text_secondary"], bg=C["surface"])
        self.status_text.pack(side="left", padx=(6, 0), pady=23)

        # 主体区域
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        # 聊天区域（中间）
        chat_container = tk.Frame(body, bg=C["bg"])
        chat_container.pack(side="left", fill="both", expand=True)

        # 聊天画布
        self.canvas = tk.Canvas(chat_container, bg=C["bg"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(chat_container, orient="vertical", command=self.canvas.yview)
        self.chat_frame = tk.Frame(self.canvas, bg=C["bg"])

        self.chat_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.chat_frame, anchor="nw", tags="chat_win")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 绑定滚轮和窗口大小变化
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # 右侧面板
        self.side_panel = self._build_side_panel(body)

        # 底部输入区域
        self._build_input()

        # 欢迎消息
        self._add_bot_msg(
            "你好！我是 MiMo 智能学习助手。\n\n"
            "我可以帮你学习编程，但不会直接给你答案。"
            "我会通过提问引导你自己思考。\n\n"
            "试试问我一个编程问题吧！比如：\n"
            "  - 如何用 Python 实现二分查找？\n"
            "  - 递归和迭代有什么区别？\n"
            "  - 什么是时间复杂度？"
        )

    def _build_side_panel(self, parent):
        panel = tk.Frame(parent, bg=C["surface"], width=240)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        # 标题
        header = tk.Frame(panel, bg=C["surface"])
        header.pack(fill="x", pady=(20, 10), padx=15)
        tk.Label(header, text="学习面板", font=("Segoe UI", 13, "bold"),
                 fg=C["accent"], bg=C["surface"]).pack(anchor="w")

        # 理解程度
        self._build_panel_section(panel, "理解程度", "progress")
        # 当前知识点
        self._build_panel_section(panel, "当前知识点", "topic")
        # 薄弱环节
        self._build_panel_section(panel, "薄弱环节", "weak")
        # 已掌握
        self._build_panel_section(panel, "已掌握", "strong")

        return panel

    def _build_panel_section(self, parent, title, key):
        frame = tk.Frame(parent, bg=C["surface2"], padx=12, pady=10)
        frame.pack(fill="x", padx=12, pady=4)

        tk.Label(frame, text=title, font=("Segoe UI", 9, "bold"),
                 fg=C["text_secondary"], bg=C["surface2"]).pack(anchor="w")

        if key == "progress":
            # 进度条
            bar_frame = tk.Frame(frame, bg=C["surface3"], height=8)
            bar_frame.pack(fill="x", pady=(8, 4))
            bar_frame.pack_propagate(False)

            self.progress_bar = tk.Frame(bar_frame, bg=C["accent"], width=0, height=8)
            self.progress_bar.place(x=0, y=0, relheight=1.0)

            self.progress_label = tk.Label(frame, text="0 / 10", font=("Segoe UI", 11, "bold"),
                                            fg=C["text"], bg=C["surface2"])
            self.progress_label.pack(anchor="w")
        else:
            label = tk.Label(frame, text="暂无", font=("Segoe UI", 10),
                             fg=C["text_muted"], bg=C["surface2"], wraplength=200, anchor="w", justify="left")
            label.pack(anchor="w", pady=(4, 0))
            setattr(self, f"{key}_label", label)

    def _build_input(self):
        # 输入区域容器
        input_outer = tk.Frame(self, bg=C["bg"])
        input_outer.pack(fill="x", side="bottom")

        # 分隔线
        tk.Frame(input_outer, bg=C["border"], height=1).pack(fill="x")

        input_container = tk.Frame(input_outer, bg=C["bg"])
        input_container.pack(fill="x", padx=20, pady=16)

        # 输入框背景
        input_bg = tk.Frame(input_container, bg=C["input_bg"], padx=4, pady=4,
                             highlightbackground=C["border"], highlightthickness=1)
        input_bg.pack(fill="x")

        # 输入框
        self.input_text = tk.Text(
            input_bg, font=("Segoe UI", 11), bg=C["input_bg"], fg=C["text"],
            insertbackground=C["accent"], relief="flat", height=1, wrap="word",
            padx=12, pady=10, undo=True, autoseparators=True, maxundo=-1
        )
        self.input_text.pack(side="left", fill="both", expand=True)

        # 发送按钮
        self.send_btn = tk.Button(
            input_bg, text="发送", font=("Segoe UI", 10, "bold"),
            bg=C["accent"], fg="white", relief="flat", padx=16, pady=6,
            cursor="hand2", activebackground=C["accent_hover"], activeforeground="white",
            command=self._send
        )
        self.send_btn.pack(side="right", padx=(8, 4))

        # 绑定事件
        self.input_text.bind("<Return>", self._on_enter)
        self.input_text.bind("<Shift-Return>", lambda e: None)  # Shift+Enter换行

        # 底部提示
        hint_frame = tk.Frame(input_outer, bg=C["bg"])
        hint_frame.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(hint_frame, text="Enter 发送 · Shift+Enter 换行 · 输入 status 查看学习状态",
                 font=("Segoe UI", 8), fg=C["text_muted"], bg=C["bg"]).pack(anchor="w")

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig("chat_win", width=event.width)

    # ─── 消息显示 ───
    def _add_user_msg(self, text):
        container = tk.Frame(self.chat_frame, bg=C["bg"])
        container.pack(fill="x", padx=20, pady=6)

        # 用户消息靠右
        bubble = tk.Frame(container, bg=C["user_bg"], padx=14, pady=10,
                          highlightbackground=C["border"], highlightthickness=1)
        bubble.pack(anchor="e", padx=(80, 0))

        # 头像标签
        header = tk.Frame(bubble, bg=C["user_bg"])
        header.pack(fill="x", anchor="e")
        tk.Label(header, text="你", font=("Segoe UI", 9, "bold"),
                 fg=C["accent"], bg=C["user_bg"]).pack(anchor="e")

        # 消息内容
        msg = tk.Label(bubble, text=text, font=("Segoe UI", 11), fg=C["text"],
                       bg=C["user_bg"], wraplength=500, justify="left", anchor="w")
        msg.pack(anchor="w", pady=(4, 0))

        self._msg_widgets.append(container)
        self._scroll_bottom()

    def _add_bot_msg(self, text):
        container = tk.Frame(self.chat_frame, bg=C["bg"])
        container.pack(fill="x", padx=20, pady=6)

        # 助手消息靠左
        bubble = tk.Frame(container, bg=C["bot_bg"], padx=14, pady=10,
                          highlightbackground=C["border"], highlightthickness=1)
        bubble.pack(anchor="w", padx=(0, 80))

        # 头像标签
        header = tk.Frame(bubble, bg=C["bot_bg"])
        header.pack(fill="x")
        tk.Label(header, text="MiMo 助手", font=("Segoe UI", 9, "bold"),
                 fg=C["success"], bg=C["bot_bg"]).pack(anchor="w")

        # 消息内容（支持多行）
        lines = text.split("\n")
        for line in lines:
            if not line.strip():
                tk.Label(bubble, text="", font=("Segoe UI", 4), bg=C["bot_bg"]).pack(anchor="w")
                continue
            # 检查是否是代码块
            if line.startswith("    ") or line.startswith("│") or line.startswith("┌") or line.startswith("└"):
                lbl = tk.Label(bubble, text=line, font=("Consolas", 10), fg=C["warning"],
                               bg=C["bot_bg"], anchor="w", justify="left")
            else:
                lbl = tk.Label(bubble, text=line, font=("Segoe UI", 11), fg=C["text"],
                               bg=C["bot_bg"], anchor="w", justify="left", wraplength=500)
            lbl.pack(anchor="w", fill="x")

        self._msg_widgets.append(container)
        self._scroll_bottom()

    def _add_system_msg(self, text):
        container = tk.Frame(self.chat_frame, bg=C["bg"])
        container.pack(fill="x", padx=20, pady=4)
        tk.Label(container, text=text, font=("Segoe UI", 9), fg=C["text_muted"],
                 bg=C["bg"]).pack(anchor="center")
        self._msg_widgets.append(container)
        self._scroll_bottom()

    def _scroll_bottom(self):
        self.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # ─── 事件处理 ───
    def _on_enter(self, event):
        if not (event.state & 0x1):  # 没按Shift
            self._send()
            return "break"

    def _send(self):
        msg = self.input_text.get("1.0", "end").strip()
        if not msg:
            return
        self.input_text.delete("1.0", "end")
        self._add_user_msg(msg)

        # 特殊命令
        if msg.lower() == "status" and self.conversation_manager:
            s = self.conversation_manager.get_conversation_summary()
            self._add_bot_msg(
                f"当前学习状态：\n\n"
                f"  对话轮数：{s['total_turns']}\n"
                f"  理解程度：{s['understanding_level']} / 10\n"
                f"  薄弱点：{', '.join(s['weak_points']) if s['weak_points'] else '暂无'}\n"
                f"  优势点：{', '.join(s['strong_points']) if s['strong_points'] else '暂无'}"
            )
            return

        # 设置状态为思考中
        self._set_status("思考中...", C["warning"])
        asyncio.run_coroutine_threadsafe(self._process(msg), self.loop)

    async def _process(self, msg):
        try:
            result = await self.conversation_manager.process_message(msg)
            response = result.get("response", "处理出错，请重试。")
            self.after(0, lambda: self._on_result(result, response))
        except Exception as e:
            self.after(0, lambda: self._add_bot_msg(f"处理出错：{e}"))
            self.after(0, lambda: self._set_status("出错", C["error"]))

    def _on_result(self, result, response):
        self._add_bot_msg(response)
        s = self.conversation_manager.get_conversation_summary()
        self._update_panel(s)
        self._set_status("就绪", C["success"])

    def _set_status(self, text, color=None):
        self.status_text.config(text=text)
        if color:
            self.status_indicator.delete("all")
            self.status_indicator.create_oval(1, 1, 9, 9, fill=color, outline="")

    def _update_panel(self, summary):
        level = summary["understanding_level"]
        # 进度条
        bar_width = int(level / 10 * 216)  # 216 = panel width - padding
        self.progress_bar.config(width=max(bar_width, 0))
        self.progress_label.config(text=f"{level} / 10")

        # 颜色
        if level >= 7:
            color = C["success"]
        elif level >= 4:
            color = C["warning"]
        else:
            color = C["accent"]
        self.progress_bar.config(bg=color)

        # 知识点
        topic = self.conversation_manager.context.current_topic
        self.topic_label.config(text=topic or "暂无", fg=C["text"] if topic else C["text_muted"])

        # 薄弱点
        weak = summary["weak_points"]
        self.weak_label.config(text=", ".join(weak) if weak else "暂无",
                                fg=C["error"] if weak else C["text_muted"])

        # 已掌握
        strong = summary["strong_points"]
        self.strong_label.config(text=", ".join(strong) if strong else "暂无",
                                  fg=C["success"] if strong else C["text_muted"])

    # ─── 异步循环 ───
    def _start_async(self):
        def run():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        threading.Thread(target=run, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self._init(), self.loop)

    async def _init(self):
        from core import ConversationManager
        self.conversation_manager = ConversationManager(student_id=self.student_id)
        self.after(0, lambda: self._set_status("就绪", C["success"]))

    def run(self):
        self.mainloop()


def main():
    App().run()

if __name__ == "__main__":
    main()

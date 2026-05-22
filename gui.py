"""
MiMo 智能学习助手 - GUI v3
参考 Claude Code 设计语言：终端风格、信息密度高、配色专业
"""
import asyncio
import threading
import tkinter as tk
from tkinter import ttk
import uuid
import time

# ─── DPI 感知 ───
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# ─── Claude Code 风格配色 ───
C = {
    # 主色调（参考 Claude Code dark theme）
    "bg": "#0a0a0f",              # 深黑背景
    "surface": "#111118",          # 面板背景
    "surface2": "#1a1a24",         # 次级面板
    "surface3": "#222230",         # 三级面板
    # 品牌色
    "claude": "#d77757",           # Claude 橙色（品牌色）
    "claude_dim": "#a05a3a",       # 暗橙色
    "permission": "#5769f7",       # 权限蓝（Claude Code 蓝）
    "permission_dim": "#3a4aa0",   # 暗蓝
    # 文字
    "text": "#e0e0e8",             # 主文字
    "text_secondary": "#8888a0",   # 次要文字
    "text_muted": "#505068",       # 暗文字
    # 语义色
    "success": "#2c7a39",          # 成功绿
    "error": "#ab2b3f",            # 错误红
    "warning": "#966c1e",          # 警告琥珀
    # 边框和分隔
    "border": "#2a2a3a",           # 边框
    "divider": "#1e1e2e",          # 分隔线
    # 用户消息背景
    "user_bg": "#14141e",          # 用户消息背景
    "bot_bg": "#0f0f18",           # 助手消息背景
}


class StatusBar(tk.Frame):
    """底部状态栏 - 参考 Claude Code StatusLine"""

    def __init__(self, parent):
        super().__init__(parent, bg=C["surface"], height=28)
        self.pack(fill="x", side="bottom")
        self.pack_propagate(False)

        # 左侧：状态指示器
        left = tk.Frame(self, bg=C["surface"])
        left.pack(side="left", padx=12)

        self.dot = tk.Canvas(left, width=8, height=8, bg=C["surface"], highlightthickness=0)
        self.dot.pack(side="left", pady=10)
        self.dot.create_oval(1, 1, 7, 7, fill=C["success"], outline="")

        self.status_text = tk.Label(left, text="就绪", font=("Consolas", 9),
                                     fg=C["text_secondary"], bg=C["surface"])
        self.status_text.pack(side="left", padx=(6, 0))

        # 中间：模型信息
        self.model_label = tk.Label(self, text="MiMo-V2.5-Pro", font=("Consolas", 9),
                                     fg=C["claude"], bg=C["surface"])
        self.model_label.pack(side="left", padx=20)

        # 右侧：统计信息
        right = tk.Frame(self, bg=C["surface"])
        right.pack(side="right", padx=12)

        self.tokens_label = tk.Label(right, text="Tokens: 0", font=("Consolas", 9),
                                      fg=C["text_muted"], bg=C["surface"])
        self.tokens_label.pack(side="left", padx=8)

        self.turns_label = tk.Label(right, text="Turns: 0", font=("Consolas", 9),
                                     fg=C["text_muted"], bg=C["surface"])
        self.turns_label.pack(side="left", padx=8)

        self.level_label = tk.Label(right, text="Level: 0/10", font=("Consolas", 9),
                                     fg=C["text_muted"], bg=C["surface"])
        self.level_label.pack(side="left", padx=8)

    def update_status(self, text, color=None):
        self.status_text.config(text=text)
        if color:
            self.dot.delete("all")
            self.dot.create_oval(1, 1, 7, 7, fill=color, outline="")

    def update_stats(self, turns=0, level=0, tokens=0):
        self.turns_label.config(text=f"Turns: {turns}")
        color = C["success"] if level >= 7 else C["warning"] if level >= 4 else C["text_muted"]
        self.level_label.config(text=f"Level: {level}/10", fg=color)
        self.tokens_label.config(text=f"Tokens: {tokens}")


class MessageBubble(tk.Frame):
    """消息气泡 - 参考 Claude Code 消息样式"""

    def __init__(self, parent, role, content, is_user=True):
        super().__init__(parent, bg=C["bg"])

        # 容器
        container = tk.Frame(self, bg=C["bg"])
        container.pack(fill="x", padx=16, pady=4)

        # 标签行
        label_frame = tk.Frame(container, bg=C["bg"])
        label_frame.pack(fill="x", anchor="w" if not is_user else "e")

        if is_user:
            tk.Label(label_frame, text="You", font=("Consolas", 9, "bold"),
                     fg=C["permission"], bg=C["bg"]).pack(anchor="e")
        else:
            tk.Label(label_frame, text="MiMo", font=("Consolas", 9, "bold"),
                     fg=C["claude"], bg=C["bg"]).pack(anchor="w")

        # 消息内容
        bg = C["user_bg"] if is_user else C["bot_bg"]
        msg_frame = tk.Frame(container, bg=bg, padx=12, pady=8)
        msg_frame.pack(anchor="e" if is_user else "w", padx=(60, 0) if is_user else (0, 60))

        for line in content.split("\n"):
            if not line.strip():
                tk.Label(msg_frame, text=" ", font=("Consolas", 3), bg=bg).pack(anchor="w")
                continue
            # 判断是否是代码/指令
            if any(line.startswith(p) for p in ["    ", "│", "┌", "└", "├", ">", "$", "#"]):
                tk.Label(msg_frame, text=line, font=("Consolas", 10), fg=C["warning"],
                         bg=bg, anchor="w", justify="left").pack(anchor="w", fill="x")
            else:
                tk.Label(msg_frame, text=line, font=("Segoe UI", 11), fg=C["text"],
                         bg=bg, wraplength=500, anchor="w", justify="left").pack(anchor="w", fill="x")


class InputArea(tk.Frame):
    """输入区域 - 参考 Claude Code PromptInput"""

    def __init__(self, parent, on_submit):
        super().__init__(parent, bg=C["bg"])
        self.pack(fill="x", side="bottom")
        self.on_submit = on_submit

        # 分隔线
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # 输入框容器
        input_container = tk.Frame(self, bg=C["bg"])
        input_container.pack(fill="x", padx=16, pady=12)

        # 输入框背景
        input_bg = tk.Frame(input_container, bg=C["surface2"], highlightbackground=C["border"], highlightthickness=1)
        input_bg.pack(fill="x")

        # 输入框
        self.text_input = tk.Text(
            input_bg, font=("Consolas", 11), bg=C["surface2"], fg=C["text"],
            insertbackground=C["claude"], relief="flat", height=1, wrap="word",
            padx=12, pady=10, undo=True
        )
        self.text_input.pack(side="left", fill="both", expand=True)

        # 发送按钮
        btn_frame = tk.Frame(input_bg, bg=C["surface2"])
        btn_frame.pack(side="right", padx=(8, 12))

        self.send_btn = tk.Button(
            btn_frame, text="Enter", font=("Consolas", 9), bg=C["permission"],
            fg="white", relief="flat", padx=16, pady=6, cursor="hand2",
            activebackground=C["permission_dim"], activeforeground="white",
            command=self._submit
        )
        self.send_btn.pack()

        # 绑定事件
        self.text_input.bind("<Return>", self._on_enter)
        self.text_input.bind("<Shift-Return>", lambda e: None)

        # 底部提示
        hint_frame = tk.Frame(self, bg=C["bg"])
        hint_frame.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(hint_frame, text="Enter 发送 · Shift+Enter 换行 · /help 查看帮助",
                 font=("Consolas", 8), fg=C["text_muted"], bg=C["bg"]).pack(anchor="w")

    def _on_enter(self, event):
        if not (event.state & 0x1):
            self._submit()
            return "break"

    def _submit(self):
        text = self.text_input.get("1.0", "end").strip()
        if text:
            self.text_input.delete("1.0", "end")
            self.on_submit(text)


class ChatPage(tk.Frame):
    """对话页面 - 主界面"""

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app

        # 聊天区域
        self.chat_canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.chat_canvas.yview)
        self.chat_frame = tk.Frame(self.chat_canvas, bg=C["bg"])

        self.chat_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw", tags="chat_win")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)

        self.chat_canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", before=self.chat_canvas)
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig("chat_win", width=e.width))
        self.chat_canvas.bind_all("<MouseWheel>", lambda e: self.chat_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 输入区域
        self.input_area = InputArea(self, self.app._send_message)

    def add_message(self, role, content):
        is_user = (role == "user")
        bubble = MessageBubble(self.chat_frame, role, content, is_user)
        bubble.pack(fill="x", padx=8, pady=2)
        self.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)


class ReportPage(tk.Frame):
    """学习报告页面"""

    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"])

        # 标题
        header = tk.Frame(self, bg=C["bg"])
        header.pack(fill="x", padx=32, pady=(24, 16))
        tk.Label(header, text="学习报告", font=("Segoe UI", 18, "bold"),
                 fg=C["text"], bg=C["bg"]).pack(anchor="w")
        tk.Label(header, text="查看你的学习进度和知识掌握情况", font=("Segoe UI", 10),
                 fg=C["text_secondary"], bg=C["bg"]).pack(anchor="w", pady=(4, 0))

        # 统计卡片
        cards_frame = tk.Frame(self, bg=C["bg"])
        cards_frame.pack(fill="x", padx=32, pady=8)

        self.stat_labels = {}
        stats = [
            ("turns", "对话轮数", "0", C["permission"]),
            ("level", "理解程度", "0/10", C["claude"]),
            ("topics", "知识点", "0", C["success"]),
            ("time", "学习时长", "0min", C["warning"]),
        ]
        for key, title, value, color in stats:
            card = tk.Frame(cards_frame, bg=C["surface"], padx=20, pady=16)
            card.pack(side="left", fill="both", expand=True, padx=4)
            card.config(highlightbackground=C["border"], highlightthickness=1)
            tk.Label(card, text=title, font=("Segoe UI", 9), fg=C["text_secondary"],
                     bg=C["surface"]).pack(anchor="w")
            lbl = tk.Label(card, text=value, font=("Consolas", 22, "bold"), fg=color, bg=C["surface"])
            lbl.pack(anchor="w", pady=(6, 0))
            self.stat_labels[key] = lbl

        # 知识点列表
        list_frame = tk.Frame(self, bg=C["surface"], padx=20, pady=16)
        list_frame.pack(fill="both", expand=True, padx=32, pady=16)
        list_frame.config(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(list_frame, text="知识点掌握情况", font=("Segoe UI", 12, "bold"),
                 fg=C["text"], bg=C["surface"]).pack(anchor="w", pady=(0, 12))

        self.knowledge_frame = tk.Frame(list_frame, bg=C["surface"])
        self.knowledge_frame.pack(fill="both", expand=True)

        self.empty_label = tk.Label(self.knowledge_frame, text="暂无学习记录\n开始对话后，这里会显示你的学习进度",
                                     font=("Segoe UI", 11), fg=C["text_muted"], bg=C["surface"],
                                     justify="center")
        self.empty_label.pack(expand=True)

    def update_stats(self, turns=0, level=0, topics=0, time_min=0):
        self.stat_labels["turns"].config(text=str(turns))
        self.stat_labels["level"].config(text=f"{level}/10")
        self.stat_labels["topics"].config(text=str(topics))
        self.stat_labels["time"].config(text=f"{time_min}min")

    def update_knowledge(self, weak_points, strong_points):
        for widget in self.knowledge_frame.winfo_children():
            widget.destroy()

        all_points = list(set(weak_points + strong_points))
        if not all_points:
            tk.Label(self.knowledge_frame, text="暂无学习记录", font=("Segoe UI", 11),
                     fg=C["text_muted"], bg=C["surface"]).pack(expand=True)
            return

        for point in all_points:
            row = tk.Frame(self.knowledge_frame, bg=C["surface"])
            row.pack(fill="x", pady=3)

            is_strong = point in strong_points
            status = "已掌握" if is_strong else "需加强"
            color = C["success"] if is_strong else C["warning"]

            # 状态指示器
            indicator = tk.Canvas(row, width=10, height=10, bg=C["surface"], highlightthickness=0)
            indicator.pack(side="left", padx=(0, 8))
            indicator.create_oval(1, 1, 9, 9, fill=color, outline="")

            tk.Label(row, text=point, font=("Segoe UI", 11), fg=C["text"],
                     bg=C["surface"], width=20, anchor="w").pack(side="left")
            tk.Label(row, text=status, font=("Consolas", 10), fg=color,
                     bg=C["surface"]).pack(side="left", padx=12)


class SettingsPage(tk.Frame):
    """设置页面"""

    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"])

        header = tk.Frame(self, bg=C["bg"])
        header.pack(fill="x", padx=32, pady=(24, 16))
        tk.Label(header, text="设置", font=("Segoe UI", 18, "bold"),
                 fg=C["text"], bg=C["bg"]).pack(anchor="w")
        tk.Label(header, text="配置 MiMo API 和应用选项", font=("Segoe UI", 10),
                 fg=C["text_secondary"], bg=C["bg"]).pack(anchor="w", pady=(4, 0))

        # API 配置
        api_frame = tk.Frame(self, bg=C["surface"], padx=20, pady=16)
        api_frame.pack(fill="x", padx=32, pady=8)
        api_frame.config(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(api_frame, text="MiMo API 配置", font=("Segoe UI", 12, "bold"),
                 fg=C["text"], bg=C["surface"]).pack(anchor="w", pady=(0, 12))

        # API Key
        row = tk.Frame(api_frame, bg=C["surface"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text="API Key", font=("Consolas", 10), fg=C["text_secondary"],
                 bg=C["surface"], width=10, anchor="w").pack(side="left")
        self.api_key = tk.Entry(row, font=("Consolas", 11), bg=C["surface2"], fg=C["text"],
                                 insertbackground=C["text"], relief="flat", show="*", width=40)
        self.api_key.pack(side="left", padx=8, ipady=4)

        # API Base
        row = tk.Frame(api_frame, bg=C["surface"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text="API Base", font=("Consolas", 10), fg=C["text_secondary"],
                 bg=C["surface"], width=10, anchor="w").pack(side="left")
        self.api_base = tk.Entry(row, font=("Consolas", 11), bg=C["surface2"], fg=C["text"],
                                  insertbackground=C["text"], relief="flat", width=40)
        self.api_base.insert(0, "https://api.xiaomimimo.com/v1")
        self.api_base.pack(side="left", padx=8, ipady=4)

        # 保存按钮
        tk.Button(api_frame, text="保存配置", font=("Consolas", 10), bg=C["permission"],
                  fg="white", relief="flat", padx=20, pady=6, cursor="hand2",
                  command=self._save).pack(anchor="w", pady=(12, 0))

        # 关于
        about_frame = tk.Frame(self, bg=C["surface"], padx=20, pady=16)
        about_frame.pack(fill="x", padx=32, pady=8)
        about_frame.config(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(about_frame, text="关于", font=("Segoe UI", 12, "bold"),
                 fg=C["text"], bg=C["surface"]).pack(anchor="w", pady=(0, 12))

        info = [
            ("版本", "1.0.0"),
            ("作者", "shiguangyilunhui"),
            ("GitHub", "github.com/shiguangyilunhui/mimo-learning-agent"),
            ("模型", "Xiaomi MiMo-V2.5-Pro"),
            ("架构", "Multi-Agent + Tool Use"),
        ]
        for label, value in info:
            row = tk.Frame(about_frame, bg=C["surface"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, font=("Consolas", 10), fg=C["text_secondary"],
                     bg=C["surface"], width=8, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=("Segoe UI", 10), fg=C["text"],
                     bg=C["surface"], anchor="w").pack(side="left", padx=8)

    def _save(self):
        from pathlib import Path
        env = f"MIMO_API_KEY={self.api_key.get().strip()}\nMIMO_API_BASE={self.api_base.get().strip()}\n"
        (Path(__file__).parent / ".env").write_text(env, encoding="utf-8")
        tk.messagebox.showinfo("保存成功", "配置已保存，重启后生效。")


class MiMoApp(tk.Tk):
    """主应用 - 参考 Claude Code 架构"""

    def __init__(self):
        super().__init__()
        self.title("MiMo 智能学习助手")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg=C["bg"])
        self.student_id = f"student_{uuid.uuid4().hex[:8]}"
        self.conversation_manager = None
        self.loop = asyncio.new_event_loop()
        self.start_time = time.time()

        self._build_nav()
        self._build_pages()
        self._build_status_bar()
        self._start_async()

        # 欢迎消息
        self.after(100, lambda: self._add_message("assistant",
            "你好！我是 MiMo 智能学习助手。\n\n"
            "我可以帮你学习编程，但不会直接给你答案。\n"
            "我会通过提问引导你自己思考。\n\n"
            "试试问我一个编程问题吧！\n"
            "  > 如何用 Python 实现二分查找？\n"
            "  > 递归和迭代有什么区别？\n"
            "  > 什么是时间复杂度？"))

    def _build_nav(self):
        """顶部导航栏"""
        nav = tk.Frame(self, bg=C["surface"], height=48)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(nav, bg=C["surface"])
        logo_frame.pack(side="left", padx=16)

        canvas = tk.Canvas(logo_frame, width=28, height=28, bg=C["surface"], highlightthickness=0)
        canvas.pack(side="left", pady=10)
        canvas.create_oval(2, 2, 26, 26, fill=C["claude"], outline="")
        canvas.create_text(14, 15, text="M", fill="white", font=("Consolas", 11, "bold"))

        tk.Label(logo_frame, text="  MiMo", font=("Consolas", 12, "bold"),
                 fg=C["claude"], bg=C["surface"]).pack(side="left", pady=10)

        # 导航标签
        nav_tabs = tk.Frame(nav, bg=C["surface"])
        nav_tabs.pack(side="left", padx=24)

        self.nav_buttons = {}
        for key, label in [("chat", "对话"), ("report", "报告"), ("settings", "设置")]:
            btn = tk.Label(nav_tabs, text=label, font=("Consolas", 10),
                           fg=C["text_muted"], bg=C["surface"], padx=14, pady=14, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_page(k))
            self.nav_buttons[key] = btn

        # 右侧信息
        right = tk.Frame(nav, bg=C["surface"])
        right.pack(side="right", padx=16)

        tk.Label(right, text=f"ID: {self.student_id[-8:]}", font=("Consolas", 8),
                 fg=C["text_muted"], bg=C["surface"]).pack(pady=14)

    def _build_pages(self):
        """构建页面"""
        self.page_container = tk.Frame(self, bg=C["bg"])
        self.page_container.pack(fill="both", expand=True)

        self.pages = {}
        self.pages["chat"] = ChatPage(self.page_container, self)
        self.pages["report"] = ReportPage(self.page_container)
        self.pages["settings"] = SettingsPage(self.page_container)

        self._switch_page("chat")

    def _build_status_bar(self):
        """底部状态栏"""
        self.status_bar = StatusBar(self)

    def _switch_page(self, key):
        for k, page in self.pages.items():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.config(fg=C["claude"], font=("Consolas", 10, "bold"))
            else:
                btn.config(fg=C["text_muted"], font=("Consolas", 10))

    def _add_message(self, role, content):
        self.pages["chat"].add_message(role, content)

    def _send_message(self, text):
        self._add_message("user", text)

        if text.lower() == "status" and self.conversation_manager:
            s = self.conversation_manager.get_conversation_summary()
            self._add_message("assistant",
                f"当前学习状态：\n\n"
                f"  对话轮数：{s['total_turns']}\n"
                f"  理解程度：{s['understanding_level']} / 10\n"
                f"  薄弱点：{', '.join(s['weak_points']) or '暂无'}\n"
                f"  优势点：{', '.join(s['strong_points']) or '暂无'}")
            return

        self.status_bar.update_status("思考中...", C["warning"])
        asyncio.run_coroutine_threadsafe(self._process(text), self.loop)

    async def _process(self, text):
        try:
            result = await self.conversation_manager.process_message(text)
            response = result.get("response", "处理出错，请重试。")
            self.after(0, lambda: self._on_result(result, response))
        except Exception as e:
            self.after(0, lambda: self._add_message("assistant", f"处理出错：{e}"))
            self.after(0, lambda: self.status_bar.update_status("出错", C["error"]))

    def _on_result(self, result, response):
        self._add_message("assistant", response)

        s = self.conversation_manager.get_conversation_summary()
        elapsed = int((time.time() - self.start_time) / 60)

        # 更新状态栏
        self.status_bar.update_stats(s["total_turns"], s["understanding_level"], 0)
        self.status_bar.update_status("就绪", C["success"])

        # 更新报告页
        self.pages["report"].update_stats(s["total_turns"], s["understanding_level"],
                                           len(set(s["weak_points"] + s["strong_points"])), elapsed)
        self.pages["report"].update_knowledge(s["weak_points"], s["strong_points"])

    def _start_async(self):
        def run():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        threading.Thread(target=run, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self._init(), self.loop)

    async def _init(self):
        from core import ConversationManager
        self.conversation_manager = ConversationManager(student_id=self.student_id)
        self.after(0, lambda: self.status_bar.update_status("就绪", C["success"]))

    def run(self):
        self.mainloop()


def main():
    MiMoApp().run()

if __name__ == "__main__":
    main()

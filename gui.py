"""
MiMo 智能学习助手 - GUI 前端 v2
多页面现代界面，高DPI支持
"""
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import json
from pathlib import Path

# ─── DPI 感知 ───
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# ─── 配色方案 ───
C = {
    "bg": "#0d1117",
    "surface": "#161b22",
    "surface2": "#21262d",
    "surface3": "#30363d",
    "accent": "#7c3aed",
    "accent_light": "#a78bfa",
    "accent_dim": "#5b21b6",
    "text": "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted": "#484f58",
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f85149",
    "border": "#30363d",
    "input_bg": "#0d1117",
    "user_bg": "#1c1f26",
    "bot_bg": "#161b22",
    "chart_bg": "#21262d",
    "header_bg": "#010409",
}


class MiMoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MiMo 智能学习助手")
        self.geometry("1200x800")
        self.minsize(1000, 650)
        self.configure(bg=C["bg"])
        self.student_id = f"student_{uuid.uuid4().hex[:8]}"
        self.conversation_manager = None
        self.loop = asyncio.new_event_loop()
        self.chat_history = []

        self._build_header()
        self._build_body()
        self._start_async()

    # ═══════════════════════════════════════
    #  顶部导航栏
    # ═══════════════════════════════════════
    def _build_header(self):
        header = tk.Frame(self, bg=C["header_bg"], height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(header, bg=C["header_bg"])
        logo_frame.pack(side="left", padx=24)

        canvas = tk.Canvas(logo_frame, width=36, height=36, bg=C["header_bg"], highlightthickness=0)
        canvas.pack(side="left", pady=14)
        canvas.create_oval(2, 2, 34, 34, fill=C["accent"], outline="")
        canvas.create_text(18, 19, text="M", fill="white", font=("Segoe UI", 14, "bold"))

        tk.Label(logo_frame, text="  MiMo 智能学习助手", font=("Segoe UI", 16, "bold"),
                 fg=C["text"], bg=C["header_bg"]).pack(side="left", pady=14)

        # 导航标签
        nav_frame = tk.Frame(header, bg=C["header_bg"])
        nav_frame.pack(side="left", padx=40)

        self.nav_buttons = {}
        pages = [("chat", "对话"), ("report", "学习报告"), ("settings", "设置")]
        for key, label in pages:
            btn = tk.Label(
                nav_frame, text=label, font=("Segoe UI", 11),
                fg=C["text_secondary"], bg=C["header_bg"], padx=16, pady=20, cursor="hand2"
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_page(k))
            self.nav_buttons[key] = btn

        # 右侧状态
        right = tk.Frame(header, bg=C["header_bg"])
        right.pack(side="right", padx=24)

        self.status_dot = tk.Canvas(right, width=12, height=12, bg=C["header_bg"], highlightthickness=0)
        self.status_dot.pack(side="left", pady=26)
        self.status_dot.create_oval(2, 2, 10, 10, fill=C["success"], outline="")

        self.status_label = tk.Label(right, text="就绪", font=("Segoe UI", 10),
                                      fg=C["text_secondary"], bg=C["header_bg"])
        self.status_label.pack(side="left", padx=(6, 0), pady=26)

        # 学生ID
        tk.Label(right, text=f"ID: {self.student_id}", font=("Segoe UI", 9),
                 fg=C["text_muted"], bg=C["header_bg"]).pack(side="left", padx=12, pady=26)

    # ═══════════════════════════════════════
    #  主体区域（多页面）
    # ═══════════════════════════════════════
    def _build_body(self):
        self.body = tk.Frame(self, bg=C["bg"])
        self.body.pack(fill="both", expand=True)

        self.pages = {}
        self._build_chat_page()
        self._build_report_page()
        self._build_settings_page()

        self._switch_page("chat")

    def _switch_page(self, key):
        for k, page in self.pages.items():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.config(fg=C["accent_light"])
                # 下划线效果
                btn.config(font=("Segoe UI", 11, "bold"))
            else:
                btn.config(fg=C["text_secondary"])
                btn.config(font=("Segoe UI", 11))

    # ═══════════════════════════════════════
    #  页面1: 对话
    # ═══════════════════════════════════════
    def _build_chat_page(self):
        page = tk.Frame(self.body, bg=C["bg"])
        self.pages["chat"] = page

        # 主容器
        main = tk.Frame(page, bg=C["bg"])
        main.pack(fill="both", expand=True)

        # 聊天区域
        chat_area = tk.Frame(main, bg=C["bg"])
        chat_area.pack(side="left", fill="both", expand=True)

        # 聊天画布
        self.chat_canvas = tk.Canvas(chat_area, bg=C["bg"], highlightthickness=0)
        self.chat_scrollbar = tk.Scrollbar(chat_area, orient="vertical", command=self.chat_canvas.yview)
        self.chat_frame = tk.Frame(self.chat_canvas, bg=C["bg"])

        self.chat_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw", tags="chat_win")
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_canvas.pack(side="left", fill="both", expand=True)
        self.chat_scrollbar.pack(side="right", fill="y")
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig("chat_win", width=e.width))
        self.chat_canvas.bind_all("<MouseWheel>", lambda e: self.chat_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 右侧面板
        side = tk.Frame(main, bg=C["surface"], width=260)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)

        # 面板内容
        tk.Label(side, text="学习面板", font=("Segoe UI", 14, "bold"),
                 fg=C["accent_light"], bg=C["surface"]).pack(anchor="w", padx=20, pady=(24, 16))

        # 理解程度卡片
        self._build_card(side, "理解程度", "progress")
        self._build_card(side, "当前知识点", "topic")
        self._build_card(side, "薄弱环节", "weak")
        self._build_card(side, "已掌握", "strong")

        # 底部输入
        self._build_chat_input(page)

        # 欢迎消息
        self._add_bot(
            "你好！我是 MiMo 智能学习助手。\n\n"
            "我可以帮你学习编程，但不会直接给你答案。"
            "我会通过提问引导你自己思考。\n\n"
            "试试问我一个编程问题吧！"
        )

    def _build_card(self, parent, title, key):
        frame = tk.Frame(parent, bg=C["surface2"], padx=16, pady=12)
        frame.pack(fill="x", padx=16, pady=4)

        tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"),
                 fg=C["text_secondary"], bg=C["surface2"]).pack(anchor="w")

        if key == "progress":
            bar_outer = tk.Frame(frame, bg=C["surface3"], height=10)
            bar_outer.pack(fill="x", pady=(10, 6))
            bar_outer.pack_propagate(False)
            self.progress_inner = tk.Frame(bar_outer, bg=C["accent"], width=0, height=10)
            self.progress_inner.place(x=0, y=0, relheight=1.0)
            self.progress_text = tk.Label(frame, text="0 / 10", font=("Segoe UI", 12, "bold"),
                                           fg=C["text"], bg=C["surface2"])
            self.progress_text.pack(anchor="w")
        else:
            lbl = tk.Label(frame, text="暂无", font=("Segoe UI", 11), fg=C["text_muted"],
                           bg=C["surface2"], wraplength=220, anchor="w", justify="left")
            lbl.pack(anchor="w", pady=(6, 0))
            setattr(self, f"{key}_label", lbl)

    def _build_chat_input(self, parent):
        outer = tk.Frame(parent, bg=C["bg"])
        outer.pack(fill="x", side="bottom")
        tk.Frame(outer, bg=C["border"], height=1).pack(fill="x")

        container = tk.Frame(outer, bg=C["bg"])
        container.pack(fill="x", padx=24, pady=16)

        bg = tk.Frame(container, bg=C["surface2"], highlightbackground=C["border"], highlightthickness=1)
        bg.pack(fill="x")

        self.input_text = tk.Text(
            bg, font=("Segoe UI", 12), bg=C["surface2"], fg=C["text"],
            insertbackground=C["accent"], relief="flat", height=1, wrap="word",
            padx=16, pady=12, undo=True
        )
        self.input_text.pack(side="left", fill="both", expand=True)

        btn_frame = tk.Frame(bg, bg=C["surface2"])
        btn_frame.pack(side="right", padx=(8, 12))

        self.send_btn = tk.Button(
            btn_frame, text="发送", font=("Segoe UI", 10, "bold"),
            bg=C["accent"], fg="white", relief="flat", padx=20, pady=8,
            cursor="hand2", activebackground=C["accent_light"], activeforeground="white",
            command=self._send
        )
        self.send_btn.pack()

        self.input_text.bind("<Return>", self._on_enter)

        hint = tk.Frame(outer, bg=C["bg"])
        hint.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(hint, text="Enter 发送 · Shift+Enter 换行 · 输入 status 查看学习状态",
                 font=("Segoe UI", 9), fg=C["text_muted"], bg=C["bg"]).pack(anchor="w")

    # ═══════════════════════════════════════
    #  页面2: 学习报告
    # ═══════════════════════════════════════
    def _build_report_page(self):
        page = tk.Frame(self.body, bg=C["bg"])
        self.pages["report"] = page

        # 标题
        tk.Label(page, text="学习报告", font=("Segoe UI", 20, "bold"),
                 fg=C["text"], bg=C["bg"]).pack(anchor="w", padx=40, pady=(32, 8))
        tk.Label(page, text="查看你的学习进度和知识掌握情况", font=("Segoe UI", 11),
                 fg=C["text_secondary"], bg=C["bg"]).pack(anchor="w", padx=40, pady=(0, 24))

        # 统计卡片行
        cards_frame = tk.Frame(page, bg=C["bg"])
        cards_frame.pack(fill="x", padx=40, pady=8)

        self.stat_cards = {}
        stats = [
            ("total_turns", "对话轮数", "0", C["accent"]),
            ("understanding", "理解程度", "0/10", C["success"]),
            ("topics_covered", "涉及知识点", "0", C["warning"]),
            ("session_time", "学习时长", "0分钟", C["error"]),
        ]
        for key, title, value, color in stats:
            card = tk.Frame(cards_frame, bg=C["surface"], padx=24, pady=20)
            card.pack(side="left", fill="both", expand=True, padx=6)
            card.config(highlightbackground=C["border"], highlightthickness=1)

            tk.Label(card, text=title, font=("Segoe UI", 10),
                     fg=C["text_secondary"], bg=C["surface"]).pack(anchor="w")

            val_label = tk.Label(card, text=value, font=("Segoe UI", 24, "bold"),
                                  fg=color, bg=C["surface"])
            val_label.pack(anchor="w", pady=(8, 0))
            self.stat_cards[key] = val_label

        # 知识点掌握情况
        knowledge_frame = tk.Frame(page, bg=C["surface"], padx=24, pady=20)
        knowledge_frame.pack(fill="both", expand=True, padx=40, pady=16)
        knowledge_frame.config(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(knowledge_frame, text="知识点掌握情况", font=("Segoe UI", 13, "bold"),
                 fg=C["text"], bg=C["surface"]).pack(anchor="w", pady=(0, 12))

        # 知识点列表
        self.knowledge_list = tk.Frame(knowledge_frame, bg=C["surface"])
        self.knowledge_list.pack(fill="both", expand=True)

        # 空状态
        self.empty_state = tk.Label(self.knowledge_list, text="暂无学习记录\n开始对话后，这里会显示你的学习进度",
                                     font=("Segoe UI", 12), fg=C["text_muted"], bg=C["surface"],
                                     justify="center")
        self.empty_state.pack(expand=True)

    # ═══════════════════════════════════════
    #  页面3: 设置
    # ═══════════════════════════════════════
    def _build_settings_page(self):
        page = tk.Frame(self.body, bg=C["bg"])
        self.pages["settings"] = page

        tk.Label(page, text="设置", font=("Segoe UI", 20, "bold"),
                 fg=C["text"], bg=C["bg"]).pack(anchor="w", padx=40, pady=(32, 8))
        tk.Label(page, text="配置 MiMo API 和应用选项", font=("Segoe UI", 11),
                 fg=C["text_secondary"], bg=C["bg"]).pack(anchor="w", padx=40, pady=(0, 24))

        # API 配置
        api_frame = tk.Frame(page, bg=C["surface"], padx=24, pady=20)
        api_frame.pack(fill="x", padx=40, pady=8)
        api_frame.config(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(api_frame, text="MiMo API 配置", font=("Segoe UI", 13, "bold"),
                 fg=C["text"], bg=C["surface"]).pack(anchor="w", pady=(0, 16))

        # API Key
        key_frame = tk.Frame(api_frame, bg=C["surface"])
        key_frame.pack(fill="x", pady=6)
        tk.Label(key_frame, text="API Key", font=("Segoe UI", 10), fg=C["text_secondary"],
                 bg=C["surface"], width=12, anchor="w").pack(side="left")
        self.api_key_entry = tk.Entry(key_frame, font=("Segoe UI", 11), bg=C["surface2"],
                                       fg=C["text"], insertbackground=C["text"], relief="flat",
                                       show="*", width=40)
        self.api_key_entry.pack(side="left", padx=8, ipady=6)

        # API Base
        base_frame = tk.Frame(api_frame, bg=C["surface"])
        base_frame.pack(fill="x", pady=6)
        tk.Label(base_frame, text="API 地址", font=("Segoe UI", 10), fg=C["text_secondary"],
                 bg=C["surface"], width=12, anchor="w").pack(side="left")
        self.api_base_entry = tk.Entry(base_frame, font=("Segoe UI", 11), bg=C["surface2"],
                                        fg=C["text"], insertbackground=C["text"], relief="flat", width=40)
        self.api_base_entry.insert(0, "https://api.xiaomimimo.com/v1")
        self.api_base_entry.pack(side="left", padx=8, ipady=6)

        # 模型选择
        model_frame = tk.Frame(api_frame, bg=C["surface"])
        model_frame.pack(fill="x", pady=6)
        tk.Label(model_frame, text="模型", font=("Segoe UI", 10), fg=C["text_secondary"],
                 bg=C["surface"], width=12, anchor="w").pack(side="left")
        self.model_var = tk.StringVar(value="MiMo-V2.5-Pro")
        model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, state="readonly",
                                    values=["MiMo-V2.5-Pro", "MiMo-V2.5", "MiMo-V2-Pro"], width=37)
        model_combo.pack(side="left", padx=8, ipady=4)

        # 保存按钮
        save_btn = tk.Button(api_frame, text="保存配置", font=("Segoe UI", 10, "bold"),
                              bg=C["accent"], fg="white", relief="flat", padx=24, pady=8,
                              cursor="hand2", command=self._save_settings)
        save_btn.pack(anchor="w", pady=(16, 0))

        # 应用信息
        info_frame = tk.Frame(page, bg=C["surface"], padx=24, pady=20)
        info_frame.pack(fill="x", padx=40, pady=8)
        info_frame.config(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(info_frame, text="关于", font=("Segoe UI", 13, "bold"),
                 fg=C["text"], bg=C["surface"]).pack(anchor="w", pady=(0, 12))

        info_items = [
            ("版本", "1.0.0"),
            ("作者", "shiguangyilunhui"),
            ("GitHub", "github.com/shiguangyilunhui/mimo-learning-agent"),
            ("许可证", "MIT"),
            ("技术栈", "Python + tkinter + MiMo-V2.5-Pro"),
        ]
        for label, value in info_items:
            row = tk.Frame(info_frame, bg=C["surface"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, font=("Segoe UI", 10), fg=C["text_secondary"],
                     bg=C["surface"], width=10, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=("Segoe UI", 10), fg=C["text"],
                     bg=C["surface"], anchor="w").pack(side="left", padx=8)

    def _save_settings(self):
        api_key = self.api_key_entry.get().strip()
        api_base = self.api_base_entry.get().strip()
        model = self.model_var.get()

        env_content = f"MIMO_API_KEY={api_key}\nMIMO_API_BASE={api_base}\nMIMO_MODEL={model}\n"
        env_path = Path(__file__).parent / ".env"
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)

        messagebox.showinfo("保存成功", "配置已保存。重启应用后生效。")

    # ═══════════════════════════════════════
    #  消息显示
    # ═══════════════════════════════════════
    def _add_user(self, text):
        container = tk.Frame(self.chat_frame, bg=C["bg"])
        container.pack(fill="x", padx=24, pady=8)

        bubble = tk.Frame(container, bg=C["user_bg"], padx=16, pady=12,
                          highlightbackground=C["border"], highlightthickness=1)
        bubble.pack(anchor="e", padx=(100, 0))

        tk.Label(bubble, text="你", font=("Segoe UI", 9, "bold"),
                 fg=C["accent_light"], bg=C["user_bg"]).pack(anchor="e")

        for line in text.split("\n"):
            tk.Label(bubble, text=line or " ", font=("Segoe UI", 12), fg=C["text"],
                     bg=C["user_bg"], wraplength=550, justify="left", anchor="w").pack(anchor="w", fill="x")

        self.chat_history.append({"role": "user", "content": text})
        self._scroll()

    def _add_bot(self, text):
        container = tk.Frame(self.chat_frame, bg=C["bg"])
        container.pack(fill="x", padx=24, pady=8)

        bubble = tk.Frame(container, bg=C["bot_bg"], padx=16, pady=12,
                          highlightbackground=C["border"], highlightthickness=1)
        bubble.pack(anchor="w", padx=(0, 100))

        tk.Label(bubble, text="MiMo 助手", font=("Segoe UI", 9, "bold"),
                 fg=C["success"], bg=C["bot_bg"]).pack(anchor="w")

        for line in text.split("\n"):
            if not line.strip():
                tk.Label(bubble, text=" ", font=("Segoe UI", 4), bg=C["bot_bg"]).pack(anchor="w")
                continue
            tk.Label(bubble, text=line, font=("Segoe UI", 12), fg=C["text"],
                     bg=C["bot_bg"], wraplength=550, justify="left", anchor="w").pack(anchor="w", fill="x")

        self.chat_history.append({"role": "assistant", "content": text})
        self._scroll()

    def _scroll(self):
        self.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ═══════════════════════════════════════
    #  事件处理
    # ═══════════════════════════════════════
    def _on_enter(self, event):
        if not (event.state & 0x1):
            self._send()
            return "break"

    def _send(self):
        msg = self.input_text.get("1.0", "end").strip()
        if not msg:
            return
        self.input_text.delete("1.0", "end")
        self._add_user(msg)

        if msg.lower() == "status" and self.conversation_manager:
            s = self.conversation_manager.get_conversation_summary()
            self._add_bot(
                f"当前学习状态：\n\n"
                f"  对话轮数：{s['total_turns']}\n"
                f"  理解程度：{s['understanding_level']} / 10\n"
                f"  薄弱点：{', '.join(s['weak_points']) or '暂无'}\n"
                f"  优势点：{', '.join(s['strong_points']) or '暂无'}"
            )
            self._update_report(s)
            return

        self._set_status("思考中...", C["warning"])
        asyncio.run_coroutine_threadsafe(self._process(msg), self.loop)

    async def _process(self, msg):
        try:
            result = await self.conversation_manager.process_message(msg)
            response = result.get("response", "处理出错，请重试。")
            self.after(0, lambda: self._on_result(result, response))
        except Exception as e:
            self.after(0, lambda: self._add_bot(f"处理出错：{e}"))
            self.after(0, lambda: self._set_status("出错", C["error"]))

    def _on_result(self, result, response):
        self._add_bot(response)
        summary = self.conversation_manager.get_conversation_summary()
        self._update_panel(summary)
        self._update_report(summary)
        self._set_status("就绪", C["success"])

    def _set_status(self, text, color=None):
        self.status_label.config(text=text)
        if color:
            self.status_dot.delete("all")
            self.status_dot.create_oval(2, 2, 10, 10, fill=color, outline="")

    def _update_panel(self, s):
        level = s["understanding_level"]
        bar_w = int(level / 10 * 228)
        self.progress_inner.config(width=max(bar_w, 0), bg=C["success"] if level >= 7 else C["warning"] if level >= 4 else C["accent"])
        self.progress_text.config(text=f"{level} / 10")

        topic = self.conversation_manager.context.current_topic
        self.topic_label.config(text=topic or "暂无", fg=C["text"] if topic else C["text_muted"])

        weak = s["weak_points"]
        self.weak_label.config(text=", ".join(weak) if weak else "暂无", fg=C["error"] if weak else C["text_muted"])

        strong = s["strong_points"]
        self.strong_label.config(text=", ".join(strong) if strong else "暂无", fg=C["success"] if strong else C["text_muted"])

    def _update_report(self, s):
        # 统计卡片
        self.stat_cards["total_turns"].config(text=str(s["total_turns"]))
        self.stat_cards["understanding"].config(text=f"{s['understanding_level']}/10")
        topics = set()
        for h in s.get("history", []):
            if h.get("input"):
                topics.add(h["input"][:20])
        self.stat_cards["topics_covered"].config(text=str(len(topics)))

        # 清空知识点列表
        for widget in self.knowledge_list.winfo_children():
            widget.destroy()

        if s["total_turns"] > 0:
            # 显示知识点进度
            all_points = list(set(s["weak_points"] + s["strong_points"]))
            if all_points:
                for point in all_points:
                    row = tk.Frame(self.knowledge_list, bg=C["surface"])
                    row.pack(fill="x", pady=4)

                    tk.Label(row, text=point, font=("Segoe UI", 11), fg=C["text"],
                             bg=C["surface"], width=20, anchor="w").pack(side="left")

                    status = "已掌握" if point in s["strong_points"] else "需加强"
                    color = C["success"] if point in s["strong_points"] else C["warning"]
                    tk.Label(row, text=status, font=("Segoe UI", 10), fg=color,
                             bg=C["surface"]).pack(side="left", padx=12)
            else:
                tk.Label(self.knowledge_list, text="继续对话，系统会自动追踪你的知识掌握情况",
                         font=("Segoe UI", 11), fg=C["text_muted"], bg=C["surface"]).pack(expand=True)
        else:
            self.empty_state = tk.Label(self.knowledge_list, text="暂无学习记录\n开始对话后，这里会显示你的学习进度",
                                         font=("Segoe UI", 12), fg=C["text_muted"], bg=C["surface"],
                                         justify="center")
            self.empty_state.pack(expand=True)

    # ═══════════════════════════════════════
    #  异步循环
    # ═══════════════════════════════════════
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
    MiMoApp().run()

if __name__ == "__main__":
    main()

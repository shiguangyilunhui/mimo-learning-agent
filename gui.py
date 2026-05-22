"""
MiMo 智能学习助手 - GUI 前端
基于 tkinter 构建的桌面客户端
"""
import asyncio
import threading
import tkinter as tk
from tkinter import ttk
import uuid

THEME = {
    "bg": "#1e1e2e", "surface": "#2d2d44", "surface2": "#383858",
    "accent": "#7c3aed", "accent_light": "#a78bfa", "text": "#e0e0e0",
    "text_dim": "#8888a0", "success": "#4ade80", "warning": "#fbbf24",
    "user_bubble": "#3b3b6b", "bot_bubble": "#2a2a4a", "border": "#4a4a6a",
}


class ChatBubble(tk.Frame):
    def __init__(self, parent, sender, message, is_user=True):
        super().__init__(parent, bg=THEME["bg"])
        bg = THEME["user_bubble"] if is_user else THEME["bot_bubble"]
        bubble = tk.Frame(self, bg=bg, padx=12, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
        tk.Label(bubble, text=sender, font=("Microsoft YaHei UI", 9, "bold"),
                 fg=THEME["accent_light"] if is_user else THEME["success"], bg=bg, anchor="e" if is_user else "w").pack(fill="x", anchor="e" if is_user else "w")
        tk.Label(bubble, text=message, font=("Microsoft YaHei UI", 10), fg=THEME["text"], bg=bg,
                 wraplength=400, justify="left", anchor="w").pack(fill="x", anchor="w")
        bubble.pack(anchor="e" if is_user else "w", padx=(60, 10) if is_user else (10, 60), pady=4)


class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["surface"], height=30)
        self.status_label = tk.Label(self, text="就绪", font=("Microsoft YaHei UI", 9), fg=THEME["text_dim"], bg=THEME["surface"])
        self.status_label.pack(side="left", padx=10)
        self.turn_label = tk.Label(self, text="对话轮数: 0", font=("Microsoft YaHei UI", 9), fg=THEME["text_dim"], bg=THEME["surface"])
        self.turn_label.pack(side="right", padx=10)
        self.level_label = tk.Label(self, text="理解程度: 0/10", font=("Microsoft YaHei UI", 9), fg=THEME["text_dim"], bg=THEME["surface"])
        self.level_label.pack(side="right", padx=10)

    def update_status(self, text):
        self.status_label.config(text=text)

    def update_stats(self, turns, level):
        self.turn_label.config(text=f"对话轮数: {turns}")
        color = THEME["success"] if level >= 7 else THEME["warning"] if level >= 4 else THEME["text_dim"]
        self.level_label.config(text=f"理解程度: {level}/10", fg=color)


class SidePanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["surface"], width=220)
        tk.Label(self, text="学习面板", font=("Microsoft YaHei UI", 12, "bold"),
                 fg=THEME["accent_light"], bg=THEME["surface"]).pack(pady=(15, 10), padx=10, anchor="w")

        pf = tk.LabelFrame(self, text=" 理解程度 ", font=("Microsoft YaHei UI", 9), fg=THEME["text_dim"], bg=THEME["surface"], bd=1, relief="groove")
        pf.pack(fill="x", padx=10, pady=5)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("C.Horizontal.TProgressbar", troughcolor=THEME["surface2"], background=THEME["accent"], thickness=18)
        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(pf, variable=self.progress_var, maximum=100, style="C.Horizontal.TProgressbar").pack(fill="x", padx=8, pady=8)
        self.progress_text = tk.Label(pf, text="0 / 10", font=("Microsoft YaHei UI", 11, "bold"), fg=THEME["text"], bg=THEME["surface"])
        self.progress_text.pack(pady=(0, 8))

        kf = tk.LabelFrame(self, text=" 当前知识点 ", font=("Microsoft YaHei UI", 9), fg=THEME["text_dim"], bg=THEME["surface"], bd=1, relief="groove")
        kf.pack(fill="x", padx=10, pady=5)
        self.knowledge_label = tk.Label(kf, text="暂无", font=("Microsoft YaHei UI", 10), fg=THEME["text"], bg=THEME["surface"], wraplength=190, anchor="w", justify="left")
        self.knowledge_label.pack(padx=8, pady=8, anchor="w")

        wf = tk.LabelFrame(self, text=" 薄弱环节 ", font=("Microsoft YaHei UI", 9), fg=THEME["text_dim"], bg=THEME["surface"], bd=1, relief="groove")
        wf.pack(fill="x", padx=10, pady=5)
        self.weak_label = tk.Label(wf, text="暂无", font=("Microsoft YaHei UI", 10), fg=THEME["text"], bg=THEME["surface"], wraplength=190, anchor="w", justify="left")
        self.weak_label.pack(padx=8, pady=8, anchor="w")

        sf = tk.LabelFrame(self, text=" 已掌握 ", font=("Microsoft YaHei UI", 9), fg=THEME["text_dim"], bg=THEME["surface"], bd=1, relief="groove")
        sf.pack(fill="x", padx=10, pady=5)
        self.strong_label = tk.Label(sf, text="暂无", font=("Microsoft YaHei UI", 10), fg=THEME["text"], bg=THEME["surface"], wraplength=190, anchor="w", justify="left")
        self.strong_label.pack(padx=8, pady=8, anchor="w")

    def update_panel(self, level, topic, weak, strong):
        self.progress_var.set(level * 10)
        self.progress_text.config(text=f"{level} / 10")
        self.knowledge_label.config(text=topic or "暂无")
        self.weak_label.config(text=", ".join(weak) if weak else "暂无")
        self.strong_label.config(text=", ".join(strong) if strong else "暂无")


class MiMoLearningApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MiMo 智能学习助手")
        self.root.geometry("960x640")
        self.root.minsize(800, 500)
        self.root.configure(bg=THEME["bg"])
        self.student_id = f"student_{uuid.uuid4().hex[:8]}"
        self.conversation_manager = None
        self.loop = asyncio.new_event_loop()
        self._build_ui()
        self._start_async_loop()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=THEME["accent"], height=48)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text="MiMo 智能学习助手", font=("Microsoft YaHei UI", 14, "bold"), fg="white", bg=THEME["accent"]).pack(side="left", padx=15)
        tk.Label(header, text=f"ID: {self.student_id}", font=("Microsoft YaHei UI", 9), fg="#d0d0ff", bg=THEME["accent"]).pack(side="right", padx=15)

        main_frame = tk.Frame(self.root, bg=THEME["bg"])
        main_frame.pack(fill="both", expand=True)

        chat_frame = tk.Frame(main_frame, bg=THEME["bg"])
        chat_frame.pack(side="left", fill="both", expand=True)
        self.chat_canvas = tk.Canvas(chat_frame, bg=THEME["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_canvas.yview)
        self.chat_inner = tk.Frame(self.chat_canvas, bg=THEME["bg"])
        self.chat_inner.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.create_window((0, 0), window=self.chat_inner, anchor="nw")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.chat_canvas.bind_all("<MouseWheel>", lambda e: self.chat_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        input_frame = tk.Frame(chat_frame, bg=THEME["surface"], height=60)
        input_frame.pack(fill="x", side="bottom"); input_frame.pack_propagate(False)
        self.input_field = tk.Text(input_frame, font=("Microsoft YaHei UI", 11), bg=THEME["surface2"], fg=THEME["text"],
            insertbackground=THEME["text"], relief="flat", height=2, wrap="word")
        self.input_field.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        self.input_field.bind("<Return>", self._on_enter)
        tk.Button(input_frame, text="发送", font=("Microsoft YaHei UI", 10, "bold"), bg=THEME["accent"], fg="white",
            relief="flat", padx=20, command=self._send_message).pack(side="right", padx=(5, 10), pady=10)

        self.side_panel = SidePanel(main_frame)
        self.side_panel.pack(side="right", fill="y")

        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill="x", side="bottom")

        self._add_bot_message("欢迎使用 MiMo 智能学习助手！\n\n我可以帮你学习编程，但不会直接给你答案。\n我会通过提问引导你自己思考。\n\n试试问我一个编程问题吧！")

    def _on_enter(self, event):
        if not event.state & 0x1:
            self._send_message()
            return "break"

    def _add_user_message(self, msg):
        ChatBubble(self.chat_inner, "你", msg, True).pack(fill="x", padx=5)
        self.root.after(50, lambda: self.chat_canvas.yview_moveto(1.0))

    def _add_bot_message(self, msg):
        ChatBubble(self.chat_inner, "MiMo 助手", msg, False).pack(fill="x", padx=5)
        self.root.after(50, lambda: self.chat_canvas.yview_moveto(1.0))

    def _start_async_loop(self):
        def run():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        threading.Thread(target=run, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self._init_manager(), self.loop)

    async def _init_manager(self):
        from core import ConversationManager
        self.conversation_manager = ConversationManager(student_id=self.student_id)
        self.root.after(0, lambda: self.status_bar.update_status("就绪 - 请输入你的编程问题"))

    def _send_message(self):
        msg = self.input_field.get("1.0", "end").strip()
        if not msg: return
        self.input_field.delete("1.0", "end")
        self._add_user_message(msg)
        if msg.lower() == "status" and self.conversation_manager:
            s = self.conversation_manager.get_conversation_summary()
            self._add_bot_message(f"对话轮数: {s['total_turns']}\n理解程度: {s['understanding_level']}/10")
            return
        self.status_bar.update_status("思考中...")
        asyncio.run_coroutine_threadsafe(self._process(msg), self.loop)

    async def _process(self, msg):
        try:
            result = await self.conversation_manager.process_message(msg)
            response = result.get("response", "处理出错")
            self.root.after(0, lambda: self._on_result(result, response))
        except Exception as e:
            self.root.after(0, lambda: self._add_bot_message(f"处理出错: {e}"))
            self.root.after(0, lambda: self.status_bar.update_status("出错"))

    def _on_result(self, result, response):
        self._add_bot_message(response)
        s = self.conversation_manager.get_conversation_summary()
        self.status_bar.update_stats(s["total_turns"], s["understanding_level"])
        self.status_bar.update_status("就绪")
        self.side_panel.update_panel(s["understanding_level"], self.conversation_manager.context.current_topic, s["weak_points"], s["strong_points"])

    def run(self):
        self.root.mainloop()


def main():
    MiMoLearningApp().run()

if __name__ == "__main__":
    main()

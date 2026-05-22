"""
MiMo 智能学习助手 - 入口文件
基于 Xiaomi MiMo-V2.5-Pro 构建的多 Agent 协作式编程辅导系统
"""
import asyncio
import uuid
from typing import Optional
from core import ConversationManager
from utils import Config, get_logger

logger = get_logger(__name__)

async def interactive_mode(student_id=None):
    if not student_id:
        student_id = f"student_{uuid.uuid4().hex[:8]}"
    print("=" * 60)
    print("           MiMo 智能学习助手 - 交互式编程辅导")
    print("=" * 60)
    print(f"  学生ID: {student_id}")
    print("  输入 'exit' 退出, 'status' 查看状态")
    print("=" * 60)
    manager = ConversationManager(student_id=student_id)
    try:
        while True:
            try:
                user_input = input("\n[你] ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！"); break
            if not user_input: continue
            if user_input.lower() in ("exit", "quit"):
                print("\n再见！继续保持学习的热情！"); break
            if user_input.lower() == "status":
                s = manager.get_conversation_summary()
                print(f"\n[学习状态] 对话轮数: {s['total_turns']}, 理解程度: {s['understanding_level']}/10")
                continue
            print("\n[助手思考中...]")
            try:
                result = await manager.process_message(user_input)
                print(f"\n[助手] {result.get('response', '处理出错')}")
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\n[错误] 处理出错，请重试。")
    finally:
        s = manager.get_conversation_summary()
        print(f"\n[总结] 对话轮数: {s['total_turns']}, 理解程度: {s['understanding_level']}/10")
        print("感谢使用 MiMo 智能学习助手！")

async def demo_mode():
    print("=" * 60)
    print("              MiMo 智能学习助手 - 功能演示")
    print("=" * 60)
    manager = ConversationManager(student_id="demo_student")
    questions = ["如何用 Python 实现一个二分查找？", "我想用递归的方法来解决", "递归的终止条件应该怎么设置？"]
    for i, q in enumerate(questions, 1):
        print(f"\n--- 演示 {i}/{len(questions)} ---")
        print(f"[学生] {q}")
        print("[助手思考中...]")
        try:
            result = await manager.process_message(q)
            print(f"[助手] {result.get('response', '处理出错')}")
        except Exception as e:
            print(f"[错误] {e}")
    s = manager.get_conversation_summary()
    print(f"\n[演示结束] 对话轮数: {s['total_turns']}, 理解程度: {s['understanding_level']}/10")

def main():
    import sys
    try:
        config = Config.from_env()
        if not config.validate():
            print("[WARNING] MIMO_API_KEY not set. Running in demo mode without API.")
        else:
            logger.info(f"Config loaded, using model: {config.mimo_model}")
    except Exception as e:
        logger.warning(f"Config warning: {e}")
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        asyncio.run(demo_mode())
    else:
        print("启动交互模式...")
        asyncio.run(interactive_mode())

if __name__ == "__main__":
    main()

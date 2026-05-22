"""
打包脚本 - 将项目打包为 exe 可执行文件
使用方法: pip install pyinstaller && python build.py
"""
import subprocess
import sys
import os

def build_exe():
    project_root = os.path.dirname(os.path.abspath(__file__))
    sep = ";" if sys.platform == "win32" else ":"
    modules = ["agents", "core", "planning", "permissions", "hooks", "recovery", "tools", "utils"]
    cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "--name=MiMo智能学习助手", "--clean"]
    for mod in modules:
        mod_path = os.path.join(project_root, mod)
        if os.path.exists(mod_path):
            cmd.append(f"--add-data={mod_path}{sep}{mod}")
    env_path = os.path.join(project_root, ".env.example")
    if os.path.exists(env_path):
        cmd.append(f"--add-data={env_path}{sep}.")
    cmd.append(os.path.join(project_root, "gui.py"))
    print("=" * 50)
    print("  MiMo 智能学习助手 - 打包中...")
    print("=" * 50)
    subprocess.check_call(cmd, cwd=project_root)
    print()
    print(f"打包完成！exe 位于: {os.path.join(project_root, 'dist')}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        import PyInstaller
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    build_exe()

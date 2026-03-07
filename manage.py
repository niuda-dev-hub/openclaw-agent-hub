#!/usr/bin/env python3
import os
import subprocess
import sys
import platform
import threading

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_command(command, cwd):
    """运行命令并在当前窗口显示输出"""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    
    process.stdout.close()
    process.wait()

def start_backend():
    print("--- 正在启动后端 (Port: 8000) ---")
    backend_dir = os.path.join(ROOT_DIR, "src")
    # 检查 uvicorn 是否可用
    cmd = "uvicorn agent_hub.main:app --host 127.0.0.1 --port 8000 --reload"
    run_command(cmd, backend_dir)

def start_frontend():
    print("--- 正在启动前端 (Port: 5173) ---")
    frontend_dir = os.path.join(ROOT_DIR, "frontend")
    # 检查 .env 是否存在
    env_file = os.path.join(frontend_dir, ".env")
    if not os.path.exists(env_file):
        example_env = os.path.join(frontend_dir, ".env.example")
        if os.path.exists(example_env):
            import shutil
            shutil.copy(example_env, env_file)
            print("已从 .env.example 创建 .env")
    
    cmd = "npm run dev"
    run_command(cmd, frontend_dir)

def show_menu():
    print("\n" + "="*30)
    print("   OpenClaw Agent Hub 管理器")
    print("="*30)
    print("1) 同时启动前后端 (并行执行)")
    print("2) 仅启动后端 (API)")
    print("3) 仅启动前端 (Web)")
    print("q) 退出")
    print("-" * 30)
    choice = input("请选择 [1-3, q]: ").strip().lower()
    return choice

def main():
    choice = show_menu()
    
    if choice == '1':
        t1 = threading.Thread(target=start_backend)
        t2 = threading.Thread(target=start_frontend)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    elif choice == '2':
        start_backend()
    elif choice == '3':
        start_frontend()
    elif choice == 'q':
        sys.exit(0)
    else:
        print("无效选择")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n服务已由用户停止")
        sys.exit(0)

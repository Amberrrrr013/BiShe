"""
Flask 服务器交互式入口
支持在命令行窗口中输入命令查看进度
"""

import os
import sys
import threading
import time
import signal
from datetime import datetime
from typing import Optional, Dict, Any, List


# 全局任务状态管理器
class TaskStatusManager:
    """全局任务状态管理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks = {}
                    cls._instance._current_task_id = None
                    cls._instance._server_ready = False
                    cls._instance._server_start_time = None
        return cls._instance

    def set_server_ready(self, ready: bool):
        with self._lock:
            self._server_ready = ready
            if ready and self._server_start_time is None:
                self._server_start_time = time.time()

    def is_server_ready(self) -> bool:
        return self._server_ready

    def get_uptime(self) -> float:
        if self._server_start_time:
            return time.time() - self._server_start_time
        return 0

    def add_task(self, task_id: str, info: Dict[str, Any]):
        with self._lock:
            info["task_id"] = task_id
            info["start_time"] = time.time()
            info["last_update"] = time.time()
            self._tasks[task_id] = info
            self._current_task_id = task_id

    def update_task(self, task_id: str, **kwargs):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].update(kwargs)
                self._tasks[task_id]["last_update"] = time.time()
                self._current_task_id = task_id

    def complete_task(self, task_id: str, success: bool = True):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["completed"] = True
                self._tasks[task_id]["success"] = success
                self._tasks[task_id]["end_time"] = time.time()
                self._tasks[task_id]["duration"] = (
                    time.time() - self._tasks[task_id]["start_time"]
                )
                if self._current_task_id == task_id:
                    self._current_task_id = None

    def remove_task(self, task_id: str):
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._tasks.get(task_id)

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self._current_task_id and self._current_task_id in self._tasks:
                return self._tasks[self._current_task_id]
            return None

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._tasks.values())

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [t for t in self._tasks.values() if not t.get("completed", False)]

    def clear_completed_tasks(self):
        with self._lock:
            self._tasks = {
                k: v for k, v in self._tasks.items() if not v.get("completed", False)
            }


# 全局实例
task_manager = TaskStatusManager()


# ===================== 命令行界面 =====================


def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}分钟"
    else:
        return f"{seconds / 3600:.1f}小时"


def format_uptime(seconds: float) -> str:
    """格式化运行时间"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}分{s}秒"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}小时{m}分钟"


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 60)
    print("  AI 英语演讲视频生成系统 - 交互式控制台")
    print("=" * 60)
    print(f"  服务器: http://127.0.0.1:5000/frontend")
    print(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()


def print_help():
    """打印帮助信息"""
    print("\n" + "-" * 40)
    print("可用命令:")
    print("-" * 40)
    print("  status, s     - 显示所有任务状态")
    print("  current, c    - 显示当前任务详情")
    print("  progress, p   - 显示任务进度条")
    print("  tasks, t     - 列出所有任务")
    print("  clear, cl     - 清除已完成任务")
    print("  server, sv    - 显示服务器状态")
    print("  uptime, u    - 显示运行时间")
    print("  help, h, ?   - 显示此帮助")
    print("  exit, quit, q - 退出服务器")
    print("-" * 40)


def cmd_status():
    """显示任务状态"""
    current = task_manager.get_current_task()
    active = task_manager.get_active_tasks()
    completed = [t for t in task_manager.get_all_tasks() if t.get("completed", False)]

    print("\n" + "=" * 50)
    print("  任务状态概览")
    print("=" * 50)

    if not active and not completed:
        print("  暂无任务")
    else:
        print(f"  活跃任务: {len(active)} 个")
        print(f"  已完成: {len(completed)} 个")

    print("-" * 50)

    # 显示当前任务
    if current:
        print(f"\n  当前任务: {current.get('task_id', 'N/A')}")
        print(f"  类型: {current.get('type', 'N/A')}")
        print(f"  状态: {current.get('step', 'N/A')}")
        progress = current.get("progress", 0)
        print(f"  进度: {progress}%")
        elapsed = time.time() - current.get("start_time", time.time())
        print(f"  已运行: {format_duration(elapsed)}")
        if current.get("message"):
            print(f"  消息: {current.get('message')[:50]}...")
    else:
        print("\n  无进行中的任务")

    print("=" * 50)


def cmd_current():
    """显示当前任务详情"""
    current = task_manager.get_current_task()

    print("\n" + "=" * 50)
    print("  当前任务详情")
    print("=" * 50)

    if not current:
        print("  无进行中的任务")
        print("=" * 50)
        return

    print(f"  任务ID: {current.get('task_id', 'N/A')}")
    print(f"  类型: {current.get('type', 'N/A')}")
    print(f"  步骤: {current.get('step', 'N/A')}")
    print(f"  进度: {current.get('progress', 0)}%")
    print(
        f"  开始时间: {datetime.fromtimestamp(current.get('start_time', 0)).strftime('%H:%M:%S')}"
    )
    elapsed = time.time() - current.get("start_time", time.time())
    print(f"  已运行时长: {format_duration(elapsed)}")

    # 详细步骤信息
    if "steps" in current:
        print("\n  步骤详情:")
        for step_name, step_info in current["steps"].items():
            status = step_info.get("status", "pending")
            step_progress = step_info.get("progress", 0)
            status_icon = (
                "✓" if status == "complete" else "○" if status == "pending" else "⟳"
            )
            print(f"    {status_icon} {step_name}: {step_progress}%")

    # 消息
    if current.get("message"):
        print(f"\n  最新消息: {current.get('message')}")

    # 预估剩余时间
    if current.get("progress", 0) > 0:
        elapsed = time.time() - current.get("start_time", time.time())
        progress = current.get("progress", 1)
        estimated_total = elapsed / (progress / 100)
        remaining = estimated_total - elapsed
        print(f"  预估剩余: {format_duration(remaining)}")

    print("=" * 50)


def cmd_progress():
    """显示进度条"""
    current = task_manager.get_current_task()

    print("\n" + "=" * 50)

    if not current:
        print("  无进行中的任务")
        print("=" * 50)
        return

    task_id = current.get("task_id", "N/A")
    task_type = current.get("type", "N/A")
    progress = current.get("progress", 0)
    step = current.get("step", "N/A")

    # 进度条
    bar_length = 40
    filled = int(bar_length * progress / 100)
    bar = "█" * filled + "░" * (bar_length - filled)

    print(f"  任务: {task_id}")
    print(f"  类型: {task_type}")
    print(f"  当前步骤: {step}")
    print()
    print(f"  [{bar}] {progress}%")
    print()

    # 预估剩余时间
    if progress > 0:
        elapsed = time.time() - current.get("start_time", time.time())
        estimated_total = elapsed / (progress / 100)
        remaining = estimated_total - elapsed
        print(f"  预估剩余时间: {format_duration(remaining)}")

    print("=" * 50)


def cmd_tasks():
    """列出所有任务"""
    all_tasks = task_manager.get_all_tasks()
    active = task_manager.get_active_tasks()
    completed = [t for t in all_tasks if t.get("completed", False)]

    print("\n" + "=" * 50)
    print(f"  所有任务 ({len(all_tasks)} 个)")
    print("=" * 50)

    if not all_tasks:
        print("  暂无任务")
    else:
        print(f"\n  进行中 ({len(active)} 个):")
        for t in active:
            task_id = t.get("task_id", "N/A")[:20]
            step = t.get("step", "N/A")
            prog = t.get("progress", 0)
            print(f"    • {task_id:20} | {step:15} | {prog:3}%")

        print(f"\n  已完成 ({len(completed)} 个):")
        for t in completed[:10]:  # 只显示最近10个
            task_id = t.get("task_id", "N/A")[:20]
            step = t.get("step", "N/A")
            success = "✓" if t.get("success") else "✗"
            dur = format_duration(t.get("duration", 0))
            print(f"    {success} {task_id:20} | {step:15} | {dur}")

        if len(completed) > 10:
            print(f"    ... 还有 {len(completed) - 10} 个任务")

    print("=" * 50)


def cmd_server():
    """显示服务器状态"""
    uptime = task_manager.get_uptime()
    ready = task_manager.is_server_ready()
    active = task_manager.get_active_tasks()

    print("\n" + "=" * 50)
    print("  服务器状态")
    print("=" * 50)
    print(f"  状态: {'✓ 运行中' if ready else '✗ 未就绪'}")
    print(f"  运行时间: {format_uptime(uptime)}")
    print(f"  监听端口: 5000")
    print(f"  前端地址: http://127.0.0.1:5000/frontend")
    print(f"  进行中任务: {len(active)} 个")
    print("=" * 50)


def cmd_uptime():
    """显示运行时间"""
    uptime = task_manager.get_uptime()
    start = datetime.now()
    if task_manager._server_start_time:
        start = datetime.fromtimestamp(task_manager._server_start_time)

    print("\n" + "=" * 50)
    print("  运行时间信息")
    print("=" * 50)
    print(f"  已运行: {format_uptime(uptime)} ({uptime:.1f}秒)")
    print(f"  启动时间: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)


def command_loop():
    """命令行主循环"""
    print_banner()
    print_help()

    while True:
        try:
            # 使用原始输入，不阻塞
            print("\n> ", end="", flush=True)
            cmd = input()

            if not cmd.strip():
                continue

            # 解析命令
            cmd_lower = cmd.strip().lower()

            if cmd_lower in ["status", "s"]:
                cmd_status()
            elif cmd_lower in ["current", "c"]:
                cmd_current()
            elif cmd_lower in ["progress", "p", "prog"]:
                cmd_progress()
            elif cmd_lower in ["tasks", "t", "list"]:
                cmd_tasks()
            elif cmd_lower in ["clear", "cl", "cleanup"]:
                task_manager.clear_completed_tasks()
                print("已清除已完成任务")
            elif cmd_lower in ["server", "sv", "info"]:
                cmd_server()
            elif cmd_lower in ["uptime", "u", "time"]:
                cmd_uptime()
            elif cmd_lower in ["help", "h", "?", "?"]:
                print_help()
            elif cmd_lower in ["exit", "quit", "q", "x"]:
                print("\n正在停止服务器...")
                # 发送停止信号
                os.kill(os.getpid(), signal.SIGTERM)
                break
            else:
                print(f"未知命令: {cmd}")
                print("输入 'help' 查看可用命令")

        except EOFError:
            print("\n输入结束，服务器继续运行...")
            break
        except KeyboardInterrupt:
            print("\n\n检测到 Ctrl+C，要退出服务器吗？(y/n): ", end="")
            try:
                confirm = input().strip().lower()
                if confirm == "y":
                    print("正在停止服务器...")
                    os.kill(os.getpid(), signal.SIGTERM)
                    break
            except:
                print("\n继续运行...")
        except Exception as e:
            print(f"命令执行错误: {e}")


# ===================== 服务器启动 =====================


def run_flask_app():
    """在独立线程中运行Flask应用"""
    from server import app

    task_manager.set_server_ready(True)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)


def signal_handler(signum, frame):
    """处理退出信号"""
    print("\n\n收到停止信号，正在关闭服务器...")
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动Flask服务器线程
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    # 等待服务器启动
    time.sleep(1)

    # 启动命令行循环
    command_loop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
三次每日调度的脚本：每天在 09:30、14:00、19:00 启动 `deliSignup.py`。

行为：
 - 脚本将持续运行（守护式），并在每天以上三个时间点各启动一次 `deliSignup.py`。
 - 使用当前 Python 解释器启动子进程，捕获并记录 stdout/stderr 到日志中。
 - 日志文件位于项目的 `log/` 目录，文件名例如 `scheduler_2025-11-06.txt`。

时间为 09:30、14:00、19:00（本地 24 小时制）。
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os
import subprocess
import sys
import time
import random


def setup_logging(log_dir: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    log_path = os.path.join(log_dir, f"scheduler_{today}.txt")
    logger = logging.getLogger("scheduler")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger


def get_next_schedule_time(now: datetime.datetime, schedule_times: list[tuple[int, int]], jitter_minutes: int = 15) -> datetime.datetime:
    """获取下一个调度时间，确保每个基准时间每天只执行一次"""
    today = now.date()
    
    # 为每个基准时间生成今天的随机时间
    scheduled_times = []
    for hour, minute in schedule_times:
        base_time = datetime.datetime.combine(today, datetime.time(hour, minute))
        # 生成随机偏移（秒）
        jitter_seconds = random.randint(-jitter_minutes * 60, jitter_minutes * 60)
        scheduled_time = base_time + datetime.timedelta(seconds=jitter_seconds)
        scheduled_times.append(scheduled_time)
    
    # 找到下一个未过期的调度时间
    future_times = [t for t in scheduled_times if t > now]
    
    if future_times:
        return min(future_times)
    else:
        # 如果今天的所有调度时间都已过，返回明天第一个调度时间
        tomorrow = today + datetime.timedelta(days=1)
        first_schedule = schedule_times[0]
        base_time = datetime.datetime.combine(tomorrow, datetime.time(first_schedule[0], first_schedule[1]))
        jitter_seconds = random.randint(-jitter_minutes * 60, jitter_minutes * 60)
        return base_time + datetime.timedelta(seconds=jitter_seconds)


def run_deli_signup(script_path: str, logger: logging.Logger) -> int:
    logger.info(f"启动子进程: {script_path}")
    try:
        proc = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        logger.info(f"子进程退出，返回码={proc.returncode}")
        if proc.stdout:
            logger.info("--- 子进程 stdout ---")
            logger.info(proc.stdout)
        if proc.stderr:
            logger.warning("--- 子进程 stderr ---")
            logger.warning(proc.stderr)
        return proc.returncode
    except Exception as e:
        logger.exception(f"启动 deliSignup.py 失败: {e}")
        return -1


def main() -> int:
    parser = argparse.ArgumentParser(description="三次每日调度：每天在 09:30、14:00、19:00 启动 deliSignup.py")
    parser.add_argument("--once", action="store_true", help="仅执行下一次调度后退出（用于调试）")
    args = parser.parse_args()

    here = os.path.abspath(os.path.dirname(__file__))
    deli_path = os.path.join(here, "deliSignup.py")

    logger = setup_logging(os.path.join(here, "log"))
    logger.info("调度器启动（固定三次：09:30、14:00、19:00）")

    if not os.path.isfile(deli_path):
        logger.error(f"找不到 deliSignup.py：{deli_path}")
        return 2

    # 固定调度时间基准（24 小时制）
    SCHEDULE_TIMES = [(9, 30), (14, 0), (19, 0)]
    JITTER_MINUTES = 15
    
    # 跟踪今天的执行情况
    today_executed = set()
    current_day = datetime.date.today()

    # 主循环
    while True:
        now = datetime.datetime.now()
        
        # 检查是否是新的一天
        if now.date() != current_day:
            today_executed.clear()
            current_day = now.date()
            logger.info(f"新的一天开始: {current_day}，重置执行记录")
        
        # 获取下一个调度时间
        target = get_next_schedule_time(now, SCHEDULE_TIMES, JITTER_MINUTES)
        wait_seconds = (target - now).total_seconds()
        
        logger.info(f"下一次运行时间: {target.strftime('%Y-%m-%d %H:%M:%S')}，还需等待 {int(wait_seconds)} 秒")

        # 等待到目标时间
        while True:
            now = datetime.datetime.now()
            remaining = (target - now).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(60, remaining))

        # 检查这个调度时间是否已经执行过
        schedule_key = (target.date(), target.hour, target.minute // 30)  # 按半小时分组
        if schedule_key in today_executed:
            logger.warning(f"跳过已执行的调度: {target.strftime('%H:%M')}")
            continue
            
        # 执行打卡
        logger.info(f"执行打卡任务，时间: {target.strftime('%H:%M')}")
        rc = run_deli_signup(deli_path, logger)
        
        # 标记为已执行
        today_executed.add(schedule_key)
        logger.info(f"今日已执行调度: {len(today_executed)}/3")

        if args.once:
            logger.info("--once 模式：已执行一次，调度器退出。")
            return rc

        logger.info("等待下一个调度点...")


if __name__ == "__main__":
    raise SystemExit(main())
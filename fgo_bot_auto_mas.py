#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FGO自动化脚本 - AUTO-MAS适配版
功能：连接ADB -> 启动FGO -> 执行自动操作 -> 关闭游戏
说明：模拟器管理由AUTO-MAS负责，本脚本只负责游戏操作
"""

import subprocess
import configparser
import os
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.ini"
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    return config


def get_adb_path():
    """获取adb路径，直接使用adb\adb.exe"""
    adb_path = os.path.join(os.path.dirname(__file__), 'adb', 'adb.exe')
    return f'"{adb_path}"'


def run_command(cmd, description="", check_output=False):
    """执行系统命令"""
    if description:
        print(f"[执行] {description}")
    print(f"  命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if result.returncode != 0 and result.stderr:
        print(f"  警告: {result.stderr}")
    if check_output:
        return result
    return result.returncode == 0


def tap_screen(adb_device, x, y, description=""):
    """点击屏幕指定坐标"""
    adb = get_adb_path()
    cmd = f"{adb} -s {adb_device} shell input tap {x} {y}"
    return run_command(cmd, description)


def key_event(adb_device, keycode, description=""):
    """发送按键事件"""
    adb = get_adb_path()
    cmd = f"{adb} -s {adb_device} shell input keyevent {keycode}"
    return run_command(cmd, description)


def connect_adb(adb_device, timeout=60, interval=5):
    """连接ADB设备"""
    adb = get_adb_path()
    logger = logging.getLogger(__name__)
    
    logger.info(f"尝试连接ADB设备: {adb_device}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        cmd = f"{adb} connect {adb_device}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if "connected" in result.stdout or "already connected" in result.stdout:
            logger.info(f"ADB连接成功: {adb_device}")
            return True
        
        logger.info(f"ADB连接中... ({int(time.time() - start_time)}/{timeout}秒)")
        time.sleep(interval)
    
    logger.error(f"ADB连接超时: {adb_device}")
    return False


def launch_fgo(config, adb_device):
    """启动FGO"""
    adb = get_adb_path()
    logger = logging.getLogger(__name__)
    
    package = "com.bilibili.fatego"
    activity = ".UnityPlayerNativeActivity"
    
    cmd = f'{adb} -s {adb_device} shell am start -n {package}/{activity}'
    logger.info(f"启动FGO: {package}/{activity}")
    
    result = run_command(cmd, "启动FGO")
    return result


def stop_fgo(config, adb_device):
    """停止FGO"""
    adb = get_adb_path()
    logger = logging.getLogger(__name__)
    
    package = "com.bilibili.fatego"
    cmd = f'{adb} -s {adb_device} shell am force-stop {package}'
    logger.info(f"停止FGO: {package}")
    
    result = run_command(cmd, "停止FGO")
    return result


def parse_tap_config(config_str):
    """解析点击配置: x,y,count"""
    parts = config_str.split(',')
    if len(parts) >= 3:
        try:
            x = int(parts[0].strip())
            y = int(parts[1].strip())
            count = int(parts[2].strip())
            return x, y, count, parts[3] if len(parts) > 3 else ""
        except ValueError:
            pass
    return None


def parse_key_config(config_str):
    """解析按键配置: keycode,count"""
    parts = config_str.split(',')
    if len(parts) >= 2:
        try:
            keycode = parts[0].strip()
            count = int(parts[1].strip())
            return keycode, count, parts[2] if len(parts) > 2 else ""
        except ValueError:
            pass
    return None


def execute_tap_steps(config, adb_device):
    """执行点击步骤"""
    logger = logging.getLogger(__name__)
    
    click_interval = config.getfloat('Delays', 'click_interval', fallback=1)
    step_base = config.getfloat('Delays', 'step_base', fallback=5)
    enter_login_interval = config.getfloat('Delays', 'enter_login_interval', fallback=20)
    
    steps = [
        ('tap_enter_game', '进入游戏'),
        ('tap_login', '登录点击'),
        ('tap_back', '返回键'),
        ('tap_side', '侧边栏防护'),
        ('tap_energy', '点击体力条'),
        ('tap_plant', '点击种树'),
        ('tap_plus', '点击加号'),
        ('tap_swap_btn', '点击交换按钮'),
        ('tap_close_swap', '关闭交换'),
        ('tap_back_main', '返回主界面'),
    ]
    
    for i, (key, desc) in enumerate(steps):
        value = config.get('Steps', key, fallback='').strip()
        if not value:
            logger.info(f"跳过 {desc} (未配置)")
            continue
        
        if value.startswith('KEYCODE_'):
            parsed = parse_key_config(value)
            if parsed:
                keycode, count, _ = parsed
                for j in range(count):
                    key_event(adb_device, keycode, f"{desc} ({j+1}/{count})")
                    if j < count - 1:
                        print(f"[信息] 点击间隔等待 {click_interval} 秒")
                        time.sleep(click_interval)
        else:
            parsed = parse_tap_config(value)
            if parsed:
                x, y, count, _ = parsed
                for j in range(count):
                    tap_screen(adb_device, x, y, f"{desc} ({j+1}/{count})")
                    if j < count - 1:
                        print(f"[信息] 点击间隔等待 {click_interval} 秒")
                        time.sleep(click_interval)
        
        if i < len(steps) - 1:
            if key == 'tap_enter_game' and steps[i+1][0] == 'tap_login':
                print(f"[信息] 进入游戏与登录之间等待 {enter_login_interval} 秒")
                time.sleep(enter_login_interval)
            elif key == 'tap_login' and steps[i+1][0] == 'tap_back':
                print(f"[信息] 登录到返回键之间等待 {enter_login_interval} 秒")
                time.sleep(enter_login_interval)
            else:
                print(f"[信息] 步骤间等待 {step_base} 秒")
                time.sleep(step_base)


def setup_logging():
    """设置日志系统"""
    log_file = "fgo_bot_log.txt"
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except Exception as e:
            print(f"[警告] 无法删除旧日志文件: {e}")
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"FGO自动化脚本日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
    except Exception as e:
        print(f"[警告] 无法创建日志文件: {e}")
    
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    """主流程"""
    parser = argparse.ArgumentParser(description='FGO自动化脚本 - AUTO-MAS适配版')
    parser.add_argument('--device', type=str, help='ADB设备地址 (例如: 127.0.0.1:5555)')
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("FGO自动化脚本启动 (AUTO-MAS适配版)")
    logger.info("=" * 50)
    
    config = load_config()
    
    post_launch = config.getfloat('Delays', 'post_launch', fallback=30)
    
    try:
        adb_device = args.device or config.get('Emulator', 'ip_port', fallback='127.0.0.1:5555')
        logger.info(f"使用ADB设备: {adb_device}")
        
        if not connect_adb(adb_device):
            logger.error("ADB连接失败，任务终止")
            logger.info("[AUTO-MAS] 任务失败")
            return
        
        logger.info("\n[阶段1] 启动FGO")
        if launch_fgo(config, adb_device):
            logger.info(f"等待游戏加载... ({post_launch}秒)")
            time.sleep(post_launch)
        
        logger.info("\n[阶段2] 执行自动操作")
        execute_tap_steps(config, adb_device)
        
        logger.info("\n[阶段3] 关闭FGO")
        stop_fgo(config, adb_device)
        time.sleep(2)
        
        logger.info("\n" + "=" * 50)
        logger.info("任务完成！")
        logger.info("[AUTO-MAS] 任务成功")
        logger.info("=" * 50)
        
    except KeyboardInterrupt:
        logger.info("\n\n用户中断，正在清理...")
        logger.info("[AUTO-MAS] 任务失败")
        return
    except Exception as e:
        logger.error(f"\n发生错误: {e}")
        logger.info("[AUTO-MAS] 任务失败")
        return


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FGO自动化脚本
功能：启动模拟器 -> 启动FGO -> 执行自动操作 -> 关闭游戏 -> 关闭模拟器
"""

import subprocess
import time
import configparser
import os
import json
from pathlib import Path


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.ini"
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    return config


def get_adb_path(config):
    """获取adb路径，优先使用配置的路径，否则使用系统adb"""
    adb_path = config.get('Paths', 'adb_path', fallback='')
    if adb_path and os.path.exists(adb_path):
        return f'"{adb_path}"'
    return "adb"


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
    config = load_config()
    adb = get_adb_path(config)
    cmd = f"{adb} -s {adb_device} shell input tap {x} {y}"
    return run_command(cmd, description)


def key_event(adb_device, keycode, description=""):
    """发送按键事件"""
    config = load_config()
    adb = get_adb_path(config)
    cmd = f"{adb} -s {adb_device} shell input keyevent {keycode}"
    return run_command(cmd, description)


def get_emulator_instance(config):
    """根据模拟器名称获取实例编号"""
    muemu_path = config.get('Paths', 'muemu_manager')
    target_name = config.get('Emulator', 'name', fallback='').strip()
    
    if not target_name:
        print("[错误] 配置文件未设置模拟器名称")
        return None
    
    # 检查文件是否存在
    if not os.path.exists(muemu_path):
        print(f"[错误] MuMuManager.exe 不存在: {muemu_path}")
        print("[提示] 请检查 config.ini 中的 muemu_manager 路径配置")
        return None
    
    # 查询所有模拟器信息
    cmd = f'"{muemu_path}" info -v all'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode != 0:
        print(f"[错误] 无法获取模拟器列表，返回码: {result.returncode}")
        return None
    
    # 解析JSON输出
    try:
        emulators = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"[错误] 解析模拟器信息失败: {e}")
        print(f"[调试] 原始输出: {result.stdout[:200]}")
        return None
    
    # 查找匹配的模拟器
    for idx, info in emulators.items():
        emulator_name = info.get('name', '')
        if target_name.lower() in emulator_name.lower() or emulator_name.lower() in target_name.lower():
            instance_id = info.get('index', idx)
            print(f"[信息] 找到模拟器: {emulator_name} (索引: {instance_id})")
            return instance_id
    
    # 未找到，输出可用列表
    print(f"[错误] 未找到名称为 '{target_name}' 的模拟器")
    print("[提示] 可用模拟器列表:")
    for idx, info in emulators.items():
        print(f"       索引 {info.get('index', idx)}: {info.get('name', '未知')}")
    return None


def connect_adb(adb_device, timeout=60, interval=5):
    """连接ADB设备并等待设备就绪"""
    print(f"  尝试连接ADB设备: {adb_device} (超时{timeout}秒)")
    
    config = load_config()
    adb = get_adb_path(config)
    
    # 先尝试直接连接
    subprocess.run(f"{adb} connect {adb_device}", shell=True, capture_output=True)
    
    start_time = time.time()
    attempt = 1
    while time.time() - start_time < timeout:
        print(f"    第{attempt}次尝试连接...")
        # 检查设备列表
        result = subprocess.run(f"{adb} devices", shell=True, capture_output=True, text=True)
        
        # 检查设备是否在线（不是offline/unauthorized）
        for line in result.stdout.strip().split('\n'):
            if adb_device in line and 'device' in line and 'offline' not in line:
                # 再验证设备真正可用
                test_result = subprocess.run(f"{adb} -s {adb_device} shell echo ready", 
                                            shell=True, capture_output=True, text=True)
                if test_result.returncode == 0 and "ready" in test_result.stdout:
                    print(f"  ADB设备已就绪")
                    return True
        
        time.sleep(interval)
        attempt += 1
    
    print(f"  [错误] ADB设备连接超时，停止任务")
    print(f"  [调试] 当前设备列表:\n{result.stdout}")
    return False


def launch_emulator(config):
    """启动模拟器"""
    muemu_path = config.get('Paths', 'muemu_manager')
    instance = get_emulator_instance(config)
    
    if instance is None:
        print("[错误] 无法获取模拟器实例编号，启动失败")
        return False
    
    cmd = f'"{muemu_path}" control -v {instance} launch'
    success = run_command(cmd, "启动模拟器")
    if not success:
        print("[错误] 启动模拟器命令执行失败")
    return success


def shutdown_emulator(config):
    """关闭模拟器"""
    muemu_path = config.get('Paths', 'muemu_manager')
    instance = get_emulator_instance(config)
    
    if instance is None:
        return False
    
    cmd = f'"{muemu_path}" control -v {instance} shutdown'
    return run_command(cmd, "关闭模拟器")


def launch_fgo(config):
    """启动FGO游戏"""
    adb = get_adb_path(config)
    adb_device = config.get('Emulator', 'ip_port')
    package = config.get('Game', 'package', fallback='com.bilibili.fatego')
    activity = config.get('Game', 'activity', fallback='.UnityPlayerNativeActivity')
    cmd = f"{adb} -s {adb_device} shell am start -n {package}/{activity}"
    return run_command(cmd, "启动FGO")


def stop_fgo(config):
    """强制停止FGO"""
    adb = get_adb_path(config)
    adb_device = config.get('Emulator', 'ip_port')
    package = config.get('Game', 'package', fallback='com.bilibili.fatego')
    cmd = f"{adb} -s {adb_device} shell am force-stop {package}"
    return run_command(cmd, "关闭FGO")


def parse_tap_config(value):
    """
    解析点击配置
    格式: x坐标 y坐标 [点击次数] [延迟秒]
    返回: (x, y, count, delay)
    """
    parts = value.strip().split()
    if len(parts) < 2:
        return None
    
    x = int(parts[0])
    y = int(parts[1])
    count = int(parts[2]) if len(parts) > 2 else 1
    delay = float(parts[3]) if len(parts) > 3 else 1.0
    
    return (x, y, count, delay)


def parse_key_config(value):
    """
    解析按键配置
    格式: KEYCODE_XXX [按键次数] [延迟秒]
    返回: (keycode, count, delay)
    """
    parts = value.strip().split()
    if len(parts) < 1:
        return None
    
    keycode = parts[0]
    count = int(parts[1]) if len(parts) > 1 else 1
    delay = float(parts[2]) if len(parts) > 2 else 1.0
    
    return (keycode, count, delay)


def execute_tap_steps(config):
    """执行所有点击步骤"""
    adb_device = config.get('Emulator', 'ip_port')
    
    # 定义步骤顺序
    steps = [
        ('tap_enter_game', '进入游戏点击'),
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
    
    for key, desc in steps:
        if not config.has_option('Steps', key):
            continue
            
        value = config.get('Steps', key)
        
        # 判断是点击还是按键
        if value.strip().startswith('KEYCODE_'):
            parsed = parse_key_config(value)
            if parsed:
                keycode, count, delay = parsed
                for i in range(count):
                    key_event(adb_device, keycode, f"{desc} ({i+1}/{count})")
                    if i < count - 1 or delay > 0:
                        time.sleep(delay)
        else:
            parsed = parse_tap_config(value)
            if parsed:
                x, y, count, delay = parsed
                for i in range(count):
                    tap_screen(adb_device, x, y, f"{desc} ({i+1}/{count})")
                    if i < count - 1 or delay > 0:
                        time.sleep(delay)


def main():
    """主流程"""
    print("=" * 50)
    print("FGO自动化脚本启动")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 获取延迟配置
    adb_timeout = config.getfloat('Delays', 'adb_timeout', fallback=60)
    adb_interval = config.getfloat('Delays', 'adb_interval', fallback=5)
    post_launch = config.getfloat('Delays', 'post_launch', fallback=5)
    step_base = config.getfloat('Delays', 'step_base', fallback=1)
    
    try:
        # 1. 启动模拟器并等待ADB连接
        print("\n[阶段1] 启动模拟器")
        if not launch_emulator(config):
            print("[错误] 模拟器启动失败，终止任务")
            return
        
        # 等待ADB连接（动态检测，无需固定等待）
        adb_device = config.get('Emulator', 'ip_port')
        if not connect_adb(adb_device, timeout=adb_timeout, interval=adb_interval):
            return
        
        # 2. 启动FGO
        print("\n[阶段2] 启动FGO")
        if launch_fgo(config):
            print(f"  等待游戏加载... ({post_launch}秒)")
            time.sleep(post_launch)
        
        # 3. 执行自动操作
        print("\n[阶段3] 执行自动操作")
        execute_tap_steps(config)
        
        # 4. 关闭FGO
        print("\n[阶段4] 关闭FGO")
        stop_fgo(config)
        time.sleep(2)
        
        # 5. 关闭模拟器
        print("\n[阶段5] 关闭模拟器")
        shutdown_emulator(config)
        
        print("\n" + "=" * 50)
        print("任务完成！")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n用户中断，正在清理...")
        stop_fgo(config)
        shutdown_emulator(config)
    except Exception as e:
        print(f"\n[错误] {e}")
        raise


if __name__ == "__main__":
    main()

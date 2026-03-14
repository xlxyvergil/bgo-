#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FGO自动化脚本
功能：启动模拟器 -> 启动FGO -> 执行自动操作 -> 关闭游戏 -> 关闭模拟器
"""

import subprocess
import json
import configparser
import os
import time
import logging
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


def get_emulator_instance(config):
    """根据模拟器名称获取实例编号"""
    logger = logging.getLogger(__name__)
    muemu_path = config.get('Paths', 'muemu_manager')
    target_name = config.get('Emulator', 'name', fallback='').strip()
    
    if not target_name:
        logger.error("配置文件未设置模拟器名称")
        return None
    
    # 检查文件是否存在
    if not os.path.exists(muemu_path):
        logger.error(f"MuMuManager.exe 不存在: {muemu_path}")
        logger.info("请检查 config.ini 中的 muemu_manager 路径配置")
        return None
    
    # 查询所有模拟器信息
    cmd = f'"{muemu_path}" info -v all'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode != 0:
        logger.error(f"无法获取模拟器列表，返回码: {result.returncode}")
        return None
    
    # 解析JSON输出
    try:
        emulators = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        logger.error(f"解析模拟器信息失败: {e}")
        logger.debug(f"原始输出: {result.stdout[:200]}")
        return None
    
    # 查找匹配的模拟器
    for idx, info in emulators.items():
        emulator_name = info.get('name', '')
        if target_name.lower() in emulator_name.lower() or emulator_name.lower() in target_name.lower():
            instance_id = info.get('index', idx)
            logger.info(f"找到模拟器: {emulator_name} (索引: {instance_id})")
            return instance_id
    
    # 未找到，输出可用列表
    logger.error(f"未找到名称为 '{target_name}' 的模拟器")
    logger.info("可用模拟器列表:")
    for idx, info in emulators.items():
        logger.info(f"       索引 {info.get('index', idx)}: {info.get('name', '未知')}")
    return None


def get_emulator_adb_port(config):
    """获取模拟器ADB端口，仅从配置文件读取"""
    # 从配置文件读取
    adb_ip_port = config.get('Emulator', 'ip_port', fallback='')
    if adb_ip_port:
        # 提取端口部分
        if ':' in adb_ip_port:
            adb_port = adb_ip_port.split(':')[-1]
            if adb_port.isdigit():
                print(f"[信息] 从配置文件获取ADB端口: {adb_port}")
                return adb_port
            else:
                print(f"[错误] 配置文件中的端口格式无效: {adb_ip_port}")
                return None
        else:
            print(f"[错误] 配置文件中的ip_port格式无效，缺少端口: {adb_ip_port}")
            return None
    else:
        print("[错误] 配置文件中未设置ip_port")
        return None


def connect_adb(adb_device, timeout=60, interval=5):
    """连接ADB设备并等待设备就绪"""
    print(f"  尝试连接ADB设备: {adb_device} (超时{timeout}秒)")
    
    adb = get_adb_path()
    
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


def launch_emulator(config, instance_id=None):
    """启动模拟器"""
    muemu_path = config.get('Paths', 'muemu_manager')
    
    # 如果没有提供实例ID，则获取
    if instance_id is None:
        instance_id = get_emulator_instance(config)
        if instance_id is None:
            print("[错误] 无法获取模拟器实例编号，启动失败")
            return False
    
    cmd = f'"{muemu_path}" control -v {instance_id} launch'
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


def launch_fgo(config, adb_device=None):
    """启动FGO游戏"""
    adb = get_adb_path()
    if adb_device is None:
        adb_device = config.get('Emulator', 'ip_port')
    package = 'com.bilibili.fatego'
    activity = '.UnityPlayerNativeActivity'
    cmd = f"{adb} -s {adb_device} shell am start -n {package}/{activity}"
    return run_command(cmd, "启动FGO")


def stop_fgo(config, adb_device=None):
    """强制停止FGO"""
    adb = get_adb_path()
    if adb_device is None:
        adb_device = config.get('Emulator', 'ip_port')
    package = 'com.bilibili.fatego'
    cmd = f"{adb} -s {adb_device} shell am force-stop {package}"
    return run_command(cmd, "关闭FGO")


def parse_tap_config(value):
    """
    解析点击配置
    格式: x坐标 y坐标 [点击次数]
    返回: (x, y, count, delay)
    """
    parts = value.strip().split()
    if len(parts) < 2:
        return None
    
    x = int(parts[0])
    y = int(parts[1])
    count = int(parts[2]) if len(parts) > 2 else 1
    delay = 0.0  # 不再使用配置中的延迟值，由click_interval控制
    
    return (x, y, count, delay)


def parse_key_config(value):
    """
    解析按键配置
    格式: KEYCODE_XXX [按键次数]
    返回: (keycode, count, delay)
    """
    parts = value.strip().split()
    if len(parts) < 1:
        return None
    
    keycode = parts[0]
    count = int(parts[1]) if len(parts) > 1 else 1
    delay = 0.0  # 不再使用配置中的延迟值，由click_interval控制
    
    return (keycode, count, delay)


def execute_tap_steps(config, adb_device=None):
    """执行所有点击步骤"""
    if adb_device is None:
        adb_device = config.get('Emulator', 'ip_port')
    
    # 获取各种延迟配置
    step_base = config.getfloat('Delays', 'step_base', fallback=5)
    click_interval = config.getfloat('Delays', 'click_interval', fallback=0.5)
    enter_login_interval = config.getfloat('Delays', 'enter_login_interval', fallback=20)
    
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
    
    for i, (key, desc) in enumerate(steps):
        if not config.has_option('Steps', key):
            continue
            
        value = config.get('Steps', key)
        
        # 判断是点击还是按键
        if value.strip().startswith('KEYCODE_'):
            parsed = parse_key_config(value)
            if parsed:
                keycode, count, _ = parsed
                for j in range(count):
                    key_event(adb_device, keycode, f"{desc} ({j+1}/{count})")
                    # 只有在多次点击时，点击之间才需要延迟
                    if j < count - 1:
                        print(f"[信息] 点击间隔等待 {click_interval} 秒")
                        time.sleep(click_interval)
        else:
            parsed = parse_tap_config(value)
            if parsed:
                x, y, count, _ = parsed
                for j in range(count):
                    tap_screen(adb_device, x, y, f"{desc} ({j+1}/{count})")
                    # 只有在多次点击时，点击之间才需要延迟
                    if j < count - 1:
                        print(f"[信息] 点击间隔等待 {click_interval} 秒")
                        time.sleep(click_interval)
        
        # 步骤之间的延迟（最后一个步骤不需要）
        if i < len(steps) - 1:
            # 特殊处理进入游戏点击与登录点击之间的间隔
            if key == 'tap_enter_game' and steps[i+1][0] == 'tap_login':
                print(f"[信息] 进入游戏与登录之间等待 {enter_login_interval} 秒")
                time.sleep(enter_login_interval)
            # 特殊处理登录点击到返回键之间的间隔（需要更长时间）
            elif key == 'tap_login' and steps[i+1][0] == 'tap_back':
                print(f"[信息] 登录到返回键之间等待 {enter_login_interval} 秒")
                time.sleep(enter_login_interval)
            else:
                # 除特殊间隔外，其他步骤之间使用step_base延迟
                print(f"[信息] 步骤间等待 {step_base} 秒")
                time.sleep(step_base)


def setup_logging():
    """设置日志系统"""
    # 删除已有日志文件
    log_file = "fgo_bot_log.txt"
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except Exception as e:
            print(f"[警告] 无法删除旧日志文件: {e}")
    
    # 创建空白日志文件
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"FGO自动化脚本日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
    except Exception as e:
        print(f"[警告] 无法创建日志文件: {e}")
    
    # 配置日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    """主流程"""
    # 设置日志
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("FGO自动化脚本启动")
    logger.info("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 获取延迟配置
    adb_timeout = config.getfloat('Delays', 'adb_timeout', fallback=60)
    adb_interval = config.getfloat('Delays', 'adb_interval', fallback=5)
    post_get_instance = config.getfloat('Delays', 'post_get_instance', fallback=2)
    post_launch_emulator = config.getfloat('Delays', 'post_launch_emulator', fallback=5)
    post_launch = config.getfloat('Delays', 'post_launch', fallback=5)
    step_base = config.getfloat('Delays', 'step_base', fallback=1)
    
    try:
        # 1. 获取模拟器实例信息
        logger.info("\n[阶段1] 获取模拟器信息")
        instance_id = get_emulator_instance(config)
        if instance_id is None:
            logger.error("无法获取模拟器实例，终止任务")
            return
        
        # 获取ADB端口
        adb_port = get_emulator_adb_port(config)
        if adb_port is None:
            logger.error("无法获取ADB端口，终止任务")
            return
        
        # 构建ADB设备地址
        adb_device = f"127.0.0.1:{adb_port}"
        logger.info(f"模拟器ADB端口: {adb_port}")
        logger.info(f"ADB设备地址: {adb_device}")
        
        # 获取模拟器信息后等待
        logger.info(f"等待 {post_get_instance} 秒...")
        time.sleep(post_get_instance)
        
        # 2. 启动模拟器
        logger.info("\n[阶段2] 启动模拟器")
        if not launch_emulator(config, instance_id):
            logger.error("模拟器启动失败，终止任务")
            return
        
        # 启动模拟器后等待
        logger.info(f"等待 {post_launch_emulator} 秒...")
        time.sleep(post_launch_emulator)
        
        # 等待ADB连接（动态检测，无需固定等待）
        if not connect_adb(adb_device, timeout=adb_timeout, interval=adb_interval):
            return
        
        # 3. 启动FGO
        logger.info("\n[阶段3] 启动FGO")
        if launch_fgo(config, adb_device):
            logger.info(f"等待游戏加载... ({post_launch}秒)")
            time.sleep(post_launch)
        
        # 4. 执行自动操作
        logger.info("\n[阶段4] 执行自动操作")
        execute_tap_steps(config, adb_device)
        
        # 5. 关闭FGO
        logger.info("\n[阶段5] 关闭FGO")
        stop_fgo(config, adb_device)
        time.sleep(2)
        
        # 6. 关闭模拟器
        logger.info("\n[阶段6] 关闭模拟器")
        shutdown_emulator(config)
        
        logger.info("\n" + "=" * 50)
        logger.info("任务完成！")
        logger.info("=" * 50)
        
    except KeyboardInterrupt:
        logger.info("\n\n用户中断，正在清理...")
        try:
            stop_fgo(config, adb_device)
        except Exception:
            pass
        try:
            shutdown_emulator(config)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"\n[错误] {e}")
        try:
            stop_fgo(config, adb_device)
        except Exception:
            pass
        try:
            shutdown_emulator(config)
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()

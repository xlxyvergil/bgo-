# FGO自动登录种树脚本

自动启动 MuMu 模拟器、登录 FGO、执行种树操作的脚本。

## 使用前提

安装 Python 3.6+

## 快速开始

### 1. 配置脚本

编辑 `config.ini` 文件，修改以下关键配置：

```ini
[Emulator]
; 模拟器名称（MuMu管理器中显示的名字）
name = kuku
; ADB连接地址（MuMu模拟器默认端口为 16384 + 实例索引 * 32）
ip_port = 127.0.0.1:16416

[Paths]
; MuMuManager.exe 路径，根据实际安装位置修改
muemu_manager = G:\MuMu\nx_main\MuMuManager.exe
```

### 2. 配置点击步骤（可选）

`[Steps]` 区域定义了自动化点击流程，所有坐标已适配 1280x720 分辨率：

```ini
; 点击配置格式: x坐标 y坐标 点击次数
; 按键配置格式: KEYCODE_xxx 按键次数

; 进入游戏点击 (点击1次)
tap_enter_game = 533 133 1

; 登录点击 (点击1次)
tap_login = 533 133 1

; 返回键 (点击1次)
tap_back = KEYCODE_BACK 1

; 侧边栏防护 (点击5次)
tap_side = 67 333 5

; 点击体力条 (点击1次)
tap_energy = 253 693 1

; 点击种树 (点击1次)
tap_plant = 900 633 1

; 点击加号 (点击5次)
tap_plus = 907 300 5

; 点击交换按钮 (点击1次)
tap_swap_btn = 813 600 1

; 关闭交换 (点击1次)
tap_close_swap = 647 560 1

; 返回主界面 (点击1次)
tap_back_main = 647 613 1
```

### 3. 配置延迟时间（可选）

`[Delays]` 区域控制各种操作的等待时间：

```ini
; ADB连接超时时间（秒）
adb_timeout = 60

; ADB连接检测间隔（秒）
adb_interval = 5

; 获取模拟器信息后等待时间（秒）
post_get_instance = 5

; 启动模拟器后等待时间（秒）
post_launch_emulator = 5

; 启动游戏后等待时间（秒）
post_launch = 30

; 步骤间基础间隔（秒）
step_base = 5

; 点击间隔（多次点击时，点击之间的延迟）
click_interval = 1

; 进入游戏点击与登录点击之间的间隔（秒）
enter_login_interval = 20
```

### 4. 运行脚本

**方式一：双击运行（推荐）**
```
双击 run.bat
```

**方式二：命令行运行**
```bash
python fgo_bot.py
# 或
py fgo_bot.py
```

## 配置文件详解

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `name` | 模拟器实例名称 | `kuku` |
| `ip_port` | ADB 连接地址 | `127.0.0.1:16416` |
| `muemu_manager` | MuMuManager.exe 完整路径 | `G:\MuMu\nx_main\MuMuManager.exe` |
| `step_base` | 步骤间基础间隔（秒） | `5` |
| `click_interval` | 点击间隔（秒） | `1` |
| `enter_login_interval` | 进入游戏与登录间间隔，以及登录与进入主界面的间隔（秒） | `20` |
| `post_launch` | 启动游戏后等待时间（秒） | `30` |

## 脚本功能

1. **自动启动模拟器**：根据配置的名称查找并启动 MuMu 模拟器实例
2. **ADB 连接**：自动连接模拟器 ADB 端口
3. **启动 FGO**：启动游戏并等待加载
4. **自动登录**：执行进入游戏和登录操作
5. **种树流程**：自动完成侧边栏防护、体力条、种树、交换等操作
6. **日志记录**：所有操作都会记录到 `fgo_bot_log.txt`

## 常见问题

**Q: 提示 "未检测到Python"**
- 安装 Python 时勾选 "Add Python to PATH"
- 或直接使用 `py fgo_bot.py` 运行

**Q: ADB 连接失败**
- 检查 `ip_port` 配置是否正确
- 确保模拟器已启动
- 检查防火墙设置

**Q: 点击坐标不准确**
- 开启模拟器的 "显示点击位置" 或 "指针位置" 开发者选项
- 根据实际分辨率调整坐标（当前已适配 1280x720）

**Q: 模拟器自动关闭**
- 避免在沙箱环境中运行脚本
- 直接通过命令行或双击运行，不要使用 IDE 的内置终端

**Q: 游戏启动失败**
- 确保 FGO 已正确安装在模拟器中
- 检查网络连接是否正常
- 尝试手动启动游戏确认是否能正常运行

## 注意事项

- 脚本启动前会自动删除旧的日志文件
- 所有点击坐标基于 1280x720 分辨率
- 游戏包名和活动名已硬编码在脚本中（`com.bilibili.fatego` 和 `.UnityPlayerNativeActivity`）
- 建议在稳定的网络环境下运行
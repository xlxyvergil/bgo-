# FGO自动登录种树脚本

自动启动 MuMu 模拟器、登录 FGO、执行种树操作的脚本。

## 使用前提

1. 安装 Python 3.6+
2. 安装 MuMu 模拟器并配置好 FGO
3. 确保模拟器已创建实例并能正常运行

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
; 模拟器自带的 adb.exe 路径
adb_path = G:\MuMu\nx_main\MuMuPlayerGlobal-12.0\adb.exe
```

**如何查找 ADB 地址：**
- 打开 MuMu 模拟器
- 运行 `MuMuManager.exe info -v all` 查看实例信息
- 或使用 `adb devices` 查看已连接设备

**如何查找 adb_path：**
- 在 MuMu 安装目录搜索 `adb.exe`
- 常见位置：`MuMuPlayerGlobal-12.0\adb.exe` 或 `nx_main\adb.exe`

### 2. 配置点击步骤（可选）

`[Steps]` 区域定义了自动化点击流程：

```ini
; 格式: x坐标 y坐标 点击次数 延迟(秒)
tap_enter_game = 800 200 1 20

; 按键事件格式: KEYCODE_xxx 按键次数 延迟(秒)
tap_back = KEYCODE_BACK 1 10
```

根据你的屏幕分辨率和游戏界面调整坐标。

### 3. 运行脚本

**方式一：双击运行（推荐）**
```
双击 run.bat
```

**方式二：命令行运行**
```bash
python fgo_bot.py
```

## 配置文件详解

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `name` | 模拟器实例名称 | `kuku` |
| `ip_port` | ADB 连接地址 | `127.0.0.1:16416` |
| `muemu_manager` | MuMuManager.exe 完整路径 | `G:\MuMu\nx_main\MuMuManager.exe` |
| `adb_path` | 模拟器自带 adb 路径 | `G:\MuMu\nx_main\...\adb.exe` |
| `package` | FGO 包名 | `com.bilibili.fatego` |
| `activity` | FGO 启动 Activity | `.UnityPlayerNativeActivity` |

## 常见问题

**Q: 提示 "未检测到Python"**
- 安装 Python 时勾选 "Add Python to PATH"
- 或直接使用 `python fgo_bot.py` 运行

**Q: ADB 连接失败**
- 检查 `ip_port` 配置是否正确
- 检查 `adb_path` 是否指向模拟器自带的 adb
- 手动运行 adb 路径测试：`adb_path devices`

**Q: 点击坐标不准确**
- 开启模拟器的 "显示点击位置" 或 "指针位置" 开发者选项
- 根据实际分辨率调整坐标

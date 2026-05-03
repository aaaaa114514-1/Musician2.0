import os
import shutil
import subprocess
import ctypes
from flask import Flask, jsonify, send_from_directory
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
SYNC_DIR = ""

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def add_firewall_rule(port):
    if not is_admin():
        print("[Sync] Warning: Admin privileges not detected. Firewall rule might fail.")
        return
    rule_name = f"Musician_Sync_Port_{port}"
    subprocess.run(f'netsh advfirewall firewall delete rule name="{rule_name}"', shell=True, capture_output=True)
    cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=TCP localport={port}'
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode == 0:
        print(f"[Sync] Firewall rule added for port {port}.")

@app.route('/list')
def get_list():
    files = []
    for r, d, f in os.walk(SYNC_DIR):
        for name in f:
            if name.endswith(".mp3"):
                rel = os.path.relpath(os.path.join(r, name), SYNC_DIR)
                files.append({"name": name, "rel_path": rel.replace("\\", "/")})
    return jsonify(files)

@app.route('/download/<path:p>')
def get_file(p):
    return send_from_directory(SYNC_DIR, p)

def start_server(temp_dir, port=5000):
    global SYNC_DIR
    SYNC_DIR = temp_dir
    add_firewall_rule(port)
    print(f"\n[Sync] Service started!")
    # print(f"[Sync] Please check your IP (usually 192.168.137.1 for hotspots)")
    # print(f"[Sync] Access URL: http://<Your_PC_IP>:{port}/list")
    print(f"[Sync] Press Ctrl+C to stop and clear temporary files\n")
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass

def clear_temp_dir(temp_dir):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        return
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'[Sync] Failed to delete {file_path}: {e}')
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
咕咚(Codoon)跑步定位注入 —— 一体化守护脚本

常用命令：
  python codoon_hook.py          守护模式：咕咚一出现/一重启就自动注入
  python codoon_hook.py --spawn  先注入再拉起咕咚（推荐，抢在定位初始化之前）
  python codoon_hook.py --setup  只做设备端部署（推 frida-server16 并启动）
  python codoon_hook.py --stop   停止设备端的 frida-server

依赖：frida 16.x（工具包 python 目录里已带，setup.ps1 会解压到 python\\pylibs）
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"
JS_PATH = SCRIPTS / "hook5.js"
FS_LOCAL = BASE / "device" / "frida-server16"

PKG = "com.codoon.gps"
REMOTE = "/data/local/tmp/frida-server16"
PORT = 27042

SERIAL = os.environ.get("MUMU_SERIAL", "127.0.0.1:16384")
ADB = ""


# ---------------------------------------------------------------- 基础工具
def find_adb():
    cand = os.environ.get("MUMU_ADB")
    if cand and Path(cand).is_file():
        return cand
    bases = [
        Path(r"C:\Program Files\Netease\MuMu"),
        Path(r"D:\Program Files\Netease\MuMu"),
        Path(r"C:\Program Files (x86)\Netease\MuMu"),
    ]
    patterns = ("nx_device/*/shell/adb.exe", "nx_main/adb.exe", "adb.exe")
    for b in bases:
        if not b.is_dir():
            continue
        for pat in patterns:
            hits = sorted(b.glob(pat))
            if hits:
                return str(hits[-1])
    w = shutil.which("adb")
    if w:
        return w
    sys.exit("[x] 没找到 adb.exe：请设置环境变量 MUMU_ADB 指向 MuMu 的 adb.exe")


def run(args, timeout=180):
    return subprocess.run(
        [ADB, "-s", SERIAL] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


def sh(cmd, timeout=120):
    return run(["shell", cmd], timeout=timeout).stdout.strip()


def ok(res):
    return res.returncode == 0


# ---------------------------------------------------------------- 设备准备
def ensure_device():
    state = run(["get-state"]).stdout.strip()
    if "device" not in state:
        run(["connect", SERIAL])
        time.sleep(1.5)
        state = run(["get-state"]).stdout.strip()
    if "device" not in state:
        sys.exit("[x] 连不上模拟器 %s：请先启动 MuMu，并确认已开启 ADB 调试" % SERIAL)


def frida_pid():
    return sh("su 0 pidof frida-server16") or sh("pidof frida-server16")


def kill_frida():
    for p in frida_pid().split():
        sh("su 0 kill -9 " + p)
    time.sleep(0.5)


def setup_device():
    ensure_device()
    run(["forward", "tcp:%d" % PORT, "tcp:%d" % PORT])

    if frida_pid():
        print("[+] frida-server 已在运行")
        return

    exists = sh("su 0 test -f %s && echo yes || echo no" % REMOTE)
    if "yes" not in exists:
        if not FS_LOCAL.is_file():
            sys.exit("[x] 工具包不完整：缺少 device/frida-server16")
        print("[*] 首次部署：推送 frida-server16 到模拟器（约 110MB，1-3 分钟）")
        r = run(["push", str(FS_LOCAL), REMOTE], timeout=1800)
        if not ok(r):
            sys.exit("[x] 推送失败：" + (r.stderr or r.stdout).strip())

    sh("su 0 chmod 755 " + REMOTE)
    sh("su 0 sh -c 'setsid %s >/dev/null 2>&1 &'" % REMOTE)
    time.sleep(2)
    if not frida_pid():
        sys.exit("[x] frida-server 启动失败：请确认 MuMu 已开启 root（设置 → 其他 → root 权限）")
    print("[+] frida-server 已启动，adb forward tcp:%d 就绪" % PORT)


# ---------------------------------------------------------------- 注入
def pidof_pkg():
    try:
        out = sh("pidof " + PKG, timeout=30)
        return int(out.split()[0]) if out else None
    except Exception:
        return None


def on_message(msg, data):
    try:
        payload = msg.get("payload")
        if isinstance(payload, dict):
            payload = payload.get("payload", payload)
        print("    " + str(payload), flush=True)
    except Exception:
        print("    " + str(msg), flush=True)


def load_script(dev, pid, js_src):
    session = dev.attach(pid)
    script = session.create_script(js_src)
    script.on("message", on_message)
    script.load()
    print("[+] 已注入咕咚 pid=%d" % pid, flush=True)
    return session, script


def daemon(spawn_first=False):
    import frida

    js_src = JS_PATH.read_text(encoding="utf-8")
    mgr = frida.get_device_manager()
    dev = mgr.add_remote_device("127.0.0.1:%d" % PORT)

    if spawn_first:
        sh("am force-stop " + PKG)
        time.sleep(1)
        pid = dev.spawn([PKG])
        print("[*] 已挂起启动咕咚 pid=%d，注入后放行" % pid, flush=True)
        load_script(dev, pid, js_src)
        dev.resume(pid)
        cur = pid
    else:
        cur = None

    print("[*] 守护中：打开咕咚（或它崩溃重开）都会自动注入，Ctrl+C 停止", flush=True)
    while True:
        try:
            pid = pidof_pkg()
            if pid is None:
                time.sleep(2)
                continue
            if pid == cur:
                time.sleep(4)
                continue
            load_script(dev, pid, js_src)
            cur = pid
        except KeyboardInterrupt:
            print("\n[*] 已退出守护（设备端 frida-server 仍在，可用 --stop 关掉）")
            return
        except Exception as e:
            print("[!] 注入失败：%s（3 秒后重试）" % e, flush=True)
            cur = None
            time.sleep(3)


# ---------------------------------------------------------------- 入口
def main():
    global ADB
    ap = argparse.ArgumentParser(description="咕咚跑步定位注入守护")
    ap.add_argument("--spawn", action="store_true", help="先注入再拉起咕咚")
    ap.add_argument("--setup", action="store_true", help="只部署/启动设备端 frida-server")
    ap.add_argument("--stop", action="store_true", help="停止设备端 frida-server")
    args = ap.parse_args()

    ADB = find_adb()
    print("[*] adb: %s" % ADB)
    print("[*] 设备: %s" % SERIAL)

    if args.stop:
        ensure_device()
        kill_frida()
        print("[+] 已停止设备端 frida-server")
        return

    setup_device()
    if args.setup:
        return

    if not JS_PATH.is_file():
        sys.exit("[x] 缺少 scripts/hook5.js")
    daemon(spawn_first=args.spawn)


if __name__ == "__main__":
    main()

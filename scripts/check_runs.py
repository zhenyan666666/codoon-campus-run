#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看咕咚最近的跑步记录（只读：从模拟器把数据库拷出来看，不改任何东西）"""
import datetime
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

SERIAL = os.environ.get("MUMU_SERIAL", "127.0.0.1:16384")
DB = "/data/data/com.codoon.gps/databases/Sports.db"
TMP = "/sdcard/Download/Sports_check.db"


def find_adb():
    cand = os.environ.get("MUMU_ADB")
    if cand and Path(cand).is_file():
        return cand
    for b in (Path(r"C:\Program Files\Netease\MuMu"), Path(r"D:\Program Files\Netease\MuMu")):
        if not b.is_dir():
            continue
        for pat in ("nx_device/*/shell/adb.exe", "nx_main/adb.exe", "adb.exe"):
            hits = sorted(b.glob(pat))
            if hits:
                return str(hits[-1])
    w = shutil.which("adb")
    if w:
        return w
    sys.exit("[x] 没找到 adb.exe，请设置环境变量 MUMU_ADB")


def fmt(ms):
    try:
        return datetime.datetime.fromtimestamp(ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ms)


def main():
    adb = find_adb()
    a = lambda *args: subprocess.run([adb, "-s", SERIAL] + list(args), capture_output=True, text=True,
                                     encoding="utf-8", errors="replace", timeout=120)
    r = a("shell", "su 0 cp %s %s && chmod 666 %s && echo OK" % (DB, TMP, TMP))
    if "OK" not in (r.stdout or ""):
        sys.exit("[x] 拷贝数据库失败：" + (r.stderr or r.stdout).strip())

    local = Path(tempfile.gettempdir()) / "Sports_check.db"
    a("pull", TMP, str(local))
    a("shell", "rm -f " + TMP)

    con = sqlite3.connect(str(local))
    rows = list(con.execute(
        "SELECT id, distance, totaltime, averagespeed, locationcount, isupload, isFraud, "
        "iscrashrestore, startdatetime, enddatetime FROM gpsmain ORDER BY id DESC LIMIT 10"))
    print("%-4s %-9s %-10s %-9s %-6s %-5s %-5s %-4s %s" % (
        "id", "距离km", "时长", "配速km/h", "点数", "上传", "作弊", "崩溃", "开始时间"))
    for r_ in rows:
        rid, dist, tot, spd, pts, up, fraud, crash, st, et = r_
        m, s = divmod(int(tot or 0) // 1000, 60)
        h, m = divmod(m, 60)
        dur = ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))
        print("%-4d %-9.3f %-10s %-9.2f %-6s %-5s %-5s %-4s %s" % (
            rid, dist or 0, dur, spd or 0, pts or 0,
            "是" if up else "否", "是" if fraud else "否", "是" if crash else "否",
            fmt(st)))

    print()
    print("说明：上传=否 表示这条记录只在本地；作弊=是 会被咕咚标记为异常")


if __name__ == "__main__":
    main()

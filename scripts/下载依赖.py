"""下载运行本工具包需要的两个大文件（不含在仓库里）。

用法（在工具包根目录下）：
    python scripts\\下载依赖.py

会做两件事：
  1. 下载 frida 16.7.19 的 win_amd64 wheel，解压到 python\\pylibs\\
  2. 下载 frida-server 16.7.19 (android-x86_64)，解压到 device\\frida-server16
两个文件都支持镜像回退，任何一个已经存在就跳过。
"""
import io
import lzma
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYLIBS = os.path.join(ROOT, "python", "pylibs")
DEVICE = os.path.join(ROOT, "device")

WHL = "frida-16.7.19-cp37-abi3-win_amd64.whl"
WHL_URLS = [
    "https://pypi.org/simple/frida/",
    "https://pypi.tuna.tsinghua.edu.cn/simple/frida/",
]
SERVER = "frida-server16"
SERVER_URLS = [
    "https://ghfast.top/https://github.com/frida/frida/releases/download/16.7.19/frida-server-16.7.19-android-x86_64.xz",
    "https://gh-proxy.com/https://github.com/frida/frida/releases/download/16.7.19/frida-server-16.7.19-android-x86_64.xz",
    "https://github.com/frida/frida/releases/download/16.7.19/frida-server-16.7.19-android-x86_64.xz",
]


def fetch(url, timeout=60):
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def try_urls(urls, label):
    for u in urls:
        try:
            print("[*] 尝试 " + u, flush=True)
            return fetch(u)
        except Exception as e:  # noqa: BLE001
            print("[!] 失败: " + str(e)[:120], flush=True)
    print("[x] " + label + " 全部源失败", flush=True)
    return None


def find_whl():
    """从 PyPI 的 simple 页面里找 wheel 的真实链接。"""
    import re

    for base in WHL_URLS:
        try:
            html = fetch(base, timeout=40).decode("utf-8", "ignore")
        except Exception as e:  # noqa: BLE001
            print("[!] " + base + " -> " + str(e)[:80], flush=True)
            continue
        m = re.search(r'href="([^"]*' + re.escape(WHL) + r'[^"]*)"', html)
        if m:
            href = m.group(1)
            if href.startswith("../"):
                href = "https://pypi.org/" + href[3:]
            return href
    return None


def main():
    ok = True

    if os.path.isdir(os.path.join(PYLIBS, "frida")):
        print("[=] python\\pylibs\\frida 已存在，跳过", flush=True)
    else:
        url = find_whl()
        if not url:
            print("[x] 没找到 frida wheel 下载地址，请手动 pip download", flush=True)
            ok = False
        else:
            print("[*] 下载 " + url, flush=True)
            data = try_urls([url], "frida wheel")
            if data:
                os.makedirs(PYLIBS, exist_ok=True)
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    z.extractall(PYLIBS)
                print("[+] 已解压到 python\\pylibs", flush=True)
            else:
                ok = False

    target = os.path.join(DEVICE, SERVER)
    if os.path.isfile(target):
        print("[=] device\\" + SERVER + " 已存在，跳过", flush=True)
    else:
        data = try_urls(SERVER_URLS, "frida-server")
        if data:
            os.makedirs(DEVICE, exist_ok=True)
            raw = lzma.decompress(data)
            with open(target, "wb") as f:
                f.write(raw)
            print("[+] 已写入 device\\" + SERVER + " (%d 字节)" % len(raw), flush=True)
        else:
            ok = False

    print("", flush=True)
    print("完成。" if ok else "有文件没下载成功，请按上面的提示手动补齐。", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

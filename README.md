# 咕咚校园跑 · 自动跑步工具包（MuMu 模拟器 + frida 注入）

在 **MuMu 12 安卓模拟器**里，用 **frida 动态注入**接管咕咚（`com.codoon.gps`）的定位数据，让咕咚记录出一段沿固定校园路线、按设定配速移动的跑步轨迹。

> ⚠️ 仅供**学习 frida 注入 / 安卓定位链路 / 反作弊原理**使用。自动化工具违反绝大多数运动 App 的用户协议，账号有被风控的可能，**风险自负**。不建议用于任何线上赛事、排行榜或学校打卡考核。

---

## 为什么不走「虚拟定位 App」那条路

很多教程是「MuMu 刷 Magisk + 装 Fake Location」，这套现在已经走不通了（实测 2026-10）：

| 卡点 | 证据 |
|---|---|
| 旧版 Fake Location 启动即自杀 | 启动 0.3 秒后 `System.exit called, status: 0`，停在 `com.lerist.common.version.LOverrideActivity`（强制更新页），只有「更新」一个按钮，没有跳过入口 |
| 服务端授权被判死 | `authStatus_*.xml` 返回 `{"status":201,"message":"APP被用户自己禁用，请在控制台解禁"}`；新版 1.5.2 则把「导入位置 / 采集位置 / 路线模拟 / 数据导出」全部锁进「功能受限，请解锁专业版」（¥9/月起，无试用） |
| 免费版唯一的设点入口也没了 | 旧版只能靠地图点选取点，而作者的百度地图 AK 已被禁用：`Authentication Error … errorcode: 201 … APP被用户自己禁用` |
| 系统级 Test Provider 也不行 | 用 `cmd location providers set-test-provider-location` 播放轨迹，咕咚跑 84 秒距离仍是 `0.00`；logcat 持续报 `non-monotonic location received`，且 APK 里存在 `isFromMockProvider` / `isMock` / `getSatellites` 等反作弊字符串 |

**结论**：不修那个 App，直接在进程内把定位数据换成真的。本工具包就是这条路。

## 原理（一句话版）

咕咚的定位来自**高德定位 SDK**（`com.amap.api.location.AMapLocation`）。注入脚本 hook 掉这个类的 getter，按「路线插值 + 固定速度」实时返回经纬度、速度、精度、卫星数、`isFromMockProvider=false`，咕咚于是算出距离、配速、轨迹点——而真实 GPS 一动不动。

关键三点：

1. **挂在 AMapLocation 上**（不是 `android.location.Location`）——直接改 Location 只会被 SDK 读几次就被平滑掉，距离不涨；
2. **必须同时给 `getSpeed()` 一个非零值**，否则咕咚按速度 0 计距离；
3. **`isFromMockProvider` 必须返回 false**，且 `getSatellites()` 给个像样的数（如 12）。

## 目录结构

```
.
├─ README.md                  ← 本文件
├─ 使用指南.md                ← 完整说明书（部署 / 开跑 / 改路线 / 排错 / 清理）
├─ 快速开始.txt
├─ 安装.bat / 启动.bat / 停止.bat / 查看记录.bat
├─ scripts/
│   ├─ hook5.js               ← 注入脚本：路线 + 速度 + AMap/Location 覆写
│   ├─ codoon_hook.py         ← 守护进程：部署 frida-server、注入、重启后自动恢复
│   ├─ setup.ps1 / start.ps1 / stop.ps1 / records.ps1
│   ├─ check_runs.py          ← 只读查看最近跑步记录（拉 Sports.db 打印表格）
│   └─ 下载依赖.py            ← 没网盘文件时用：下载 frida 运行库与 frida-server
├─ device/                    ← 放 frida-server16（110 MB，需自行下载，见下）
└─ 旧方案_系统虚拟定位/        ← 早期 Test Provider 方案，已被咕咚识破，仅留档
```

## 快速开始

1. MuMu 12 → 设置里开 **root**、确认 **ADB 端口 16384**、启动模拟器；
2. 咕咚装好并登录；
3. 电脑装 **Python 3.10+ 64 位**（勾 Add to PATH）；
4. 双击 `安装.bat`（检查 python / 解压 frida 运行库）；
5. 双击 `启动.bat -Spawn`（自动推 frida-server、注入、守护）；
6. 咕咚：**运动 → 跑步 → 户外跑 → 开始 → 稍后**，等距离涨起来即可；
7. 结束：**暂停 → 结束 → 保存**；核对：双击 `查看记录.bat`。

## 需要自己补的两个大文件

仓库不放大二进制，运行前把它们放到对应位置：

| 文件 | 放哪里 | 来源 |
|---|---|---|
| `frida` 16.7.19 运行库（.whl） | 解压后放 `python\pylibs\` | `pip download frida==16.7.19 --only-binary=:all:` |
| `frida-server16`（Android x86_64） | `device\frida-server16` | [frida releases](https://github.com/frida/frida/releases) 里的 `frida-server-16.7.19-android-x86_64.xz`（解压后重命名） |

也可以直接跑 `python scripts\下载依赖.py`（带镜像回退）。

## 路线与速度

`scripts/hook5.js` 里的 `V` 是一圈闭合路线（默认是**占位方框**：5 个点、周长约 **429 m**，必须换成你自己学校），`SPEED` 默认 **3.0 m/s（10.8 km/h）**。

**换成你学校那一圈**：见 [使用指南 §7](使用指南.md)（含取坐标的正确工具、坐标系陷阱、闭合规则、验证方法）。

> ⚠️ 取坐标必须用**高德系**工具（[高德坐标拾取器](https://lbs.amap.com/tools/picker)，GCJ-02）；用百度坐标拾取器（BD09）或 Google 地图（WGS84）取的点会整体偏 300–600 米。距离只跟时间×速度有关，路线形状不影响成绩。

## 环境

- MuMu 12（机型 vivo X100 Ultra，Android 12，x86_64 + houdini）
- 咕咚 10.44.1（`com.codoon.gps`）
- frida 16.7.19（17.x 已移除内置 Java bridge，脚本不兼容）
- 主机 Windows 10/11 + PowerShell 5.1

## 免责

代码按「现状」提供，不保证咕咚后续版本仍可用；因使用造成的账号、成绩或校纪问题与作者无关。

## License

[MIT](LICENSE) © 2026 zhenyan666666

仓库本身不含 frida 二进制；`scripts/下载依赖.py` 会从 frida 官方 Release 下载（wxWindows Library Licence / LGPL 2.1 + 静态链接例外），重新分发请保留其版权声明。

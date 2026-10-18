# 启动咕咚定位注入守护进程（这个窗口开着才有用，最小化即可）
# 第一次运行会自动完成设备端部署（推 frida-server16 并启动）
# 可选参数：
#   -Spawn   先注入再拉起咕咚（更稳，推荐每次跑步用这个）
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$root = Split-Path -Parent $PSScriptRoot
$pylibs = Join-Path $root 'python\pylibs'

if (-not (Test-Path (Join-Path $pylibs 'frida'))) {
    Write-Host '[*] 首次运行，先安装 python 依赖...'
    & (Join-Path $PSScriptRoot 'setup.ps1')
}

if (Test-Path $pylibs) { $env:PYTHONPATH = $pylibs + ';' + $env:PYTHONPATH }

$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pyCmd) {
    Write-Host '[x] 没找到 python，请先安装 Python 3.10+ 64 位'
    exit 1
}

$pyArgs = @((Join-Path $PSScriptRoot 'codoon_hook.py'))
if ($args -contains '-Spawn' -or $args -contains 'spawn') { $pyArgs += '--spawn' }
if ($args -contains '-Setup' -or $args -contains 'setup') { $pyArgs += '--setup' }

& $pyCmd.Source @pyArgs

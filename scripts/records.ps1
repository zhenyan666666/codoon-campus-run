# 查看最近跑步记录（只读，不改任何东西）
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$root = Split-Path -Parent $PSScriptRoot
$pylibs = Join-Path $root 'python\pylibs'
if (Test-Path $pylibs) { $env:PYTHONPATH = $pylibs + ';' + $env:PYTHONPATH }
$py = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $py) { Write-Host '[x] 没找到 python，请先安装 Python 3.10+ 64 位'; exit 1 }
& $py.Source (Join-Path $PSScriptRoot 'check_runs.py')
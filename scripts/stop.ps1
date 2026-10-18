# 停止设备端的 frida-server（停止注入）
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$root = Split-Path -Parent $PSScriptRoot
$pylibs = Join-Path $root 'python\pylibs'
if (Test-Path $pylibs) { $env:PYTHONPATH = $pylibs + ';' + $env:PYTHONPATH }

$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pyCmd) { Write-Host '[x] 没找到 python'; exit 1 }

& $pyCmd.Source (Join-Path $PSScriptRoot 'codoon_hook.py') --stop

# 解压内置 frida 运行库到 python\pylibs（不需要联网、不需要 pip）
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$root = Split-Path -Parent $PSScriptRoot
$pyDir = Join-Path $root 'python'
$pylibs = Join-Path $pyDir 'pylibs'

Add-Type -AssemblyName System.IO.Compression.FileSystem

if (Test-Path (Join-Path $pylibs 'frida')) {
    Write-Host '[=] frida 运行库已就绪，跳过'
} else {
    $whl = Get-ChildItem $pyDir -Filter *.whl -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $whl) {
        Write-Host '[!] python 目录里没找到 .whl，请手动执行: python -m pip install frida==16.7.19'
    } else {
        Write-Host ('[*] 解压 ' + $whl.Name + ' ...')
        New-Item -ItemType Directory -Force -Path $pylibs | Out-Null
        [System.IO.Compression.ZipFile]::ExtractToDirectory($whl.FullName, $pylibs)
        Write-Host '[+] frida 运行库已解压到 python\pylibs'
    }
}

$py = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $py) {
    Write-Host '[!] 没找到 python：请安装 Python 3.10+ 64 位，安装时勾选 Add Python to PATH'
} else {
    Write-Host ('[+] python: ' + $py.Source)
    & $py.Source --version
}

Write-Host ''
Write-Host '准备完成。下一步：右键 使用 PowerShell 运行 start.ps1'

$ErrorActionPreference='Stop'
$python='C:\Tools\Embedded\venv\Scripts\python.exe'
$tool='C:\Tools\Embedded\picotool\picotool\picotool.exe'
$uf2=Join-Path $PSScriptRoot 'build-ram\sen0325_setup.uf2'
if(-not(Test-Path -LiteralPath $uf2)){$uf2=Join-Path $PSScriptRoot 'firmware\sen0325_setup-RAM.uf2'}
& $python (Join-Path $PSScriptRoot 'verify_ram.py') $uf2
if($LASTEXITCODE -ne 0){throw 'RAM-only validation failed; device has not been loaded.'}
& $tool load -v -x $uf2 -f
if($LASTEXITCODE -ne 0){throw 'Load failed. Connect one Pico; if needed, hold BOOTSEL while plugging in USB and retry.'}
Write-Host 'RAM diagnostic running in IDLE. After checking wiring, use Monitor.ps1 and send START.'

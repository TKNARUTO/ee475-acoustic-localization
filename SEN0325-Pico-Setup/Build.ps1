param([switch]$FlashBuild,[int]$UsbTxFifoBytes=4096,[int]$UsbEndpointBytes=512)
$ErrorActionPreference='Stop'
$root='C:\Tools\Embedded'
$env:PICO_SDK_PATH=Join-Path $root 'pico-sdk'
$env:PICO_TOOLCHAIN_PATH=Join-Path $root 'platformio\packages\toolchain-gccarmnoneeabi'
$env:Path=(Join-Path $root 'venv\Scripts')+';'+(Join-Path $root 'git\cmd')+';'+(Join-Path $env:PICO_TOOLCHAIN_PATH 'bin')+';'+$env:Path
$source=$PSScriptRoot
# Keep SDK/toolchain command lines ASCII while the real project lives in EE475.
$asciiAlias='C:\Dev\Embedded\SEN0325-Pico-Setup'
if($source -match '[^\x00-\x7F]'){
    $link=Get-Item -LiteralPath $asciiAlias -Force
    if($link.LinkType -ne 'Junction' -or [IO.Path]::GetFullPath([string]$link.Target) -ne [IO.Path]::GetFullPath($PSScriptRoot)){
        throw 'The ASCII build alias does not point to this EE475 project.'
    }
    $source=$asciiAlias
}
$build=Join-Path $source $(if($FlashBuild){'build-flash'}else{'build-ram'})
$noFlash=if($FlashBuild){'OFF'}else{'ON'}
& (Join-Path $root 'venv\Scripts\cmake.exe') -S $source -B $build -G Ninja '-DPICO_BOARD=pico' "-DPICO_NO_FLASH=$noFlash" '-DCMAKE_BUILD_TYPE=Debug' '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON' "-DRX2_USB_TX_FIFO_BYTES=$UsbTxFifoBytes" "-DRX2_USB_EP_BUFFER_BYTES=$UsbEndpointBytes" "-DPython3_EXECUTABLE=$root/venv/Scripts/python.exe" "-Dpicotool_DIR=$root/picotool/picotool" "-Dpioasm_DIR=$root/sdk-tools/pioasm"
if($LASTEXITCODE -ne 0){throw 'CMake configuration failed.'}
& (Join-Path $root 'venv\Scripts\cmake.exe') --build $build --parallel 2
if($LASTEXITCODE -ne 0){throw 'Compilation failed.'}
Get-Item -LiteralPath (Join-Path $build 'sen0325_setup.uf2'),(Join-Path $build 'sen0325_setup.elf') | Select-Object FullName,Length

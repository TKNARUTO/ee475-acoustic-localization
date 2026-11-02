param([ValidatePattern('^COM[0-9]+$')][string]$Port='')
$ErrorActionPreference='Stop'
$python='C:\Tools\Embedded\venv\Scripts\python.exe'
if(-not $Port){
    $ports=@(& $python -c 'from serial.tools import list_ports; [print(p.device) for p in list_ports.comports() if p.vid==0x2e8a]')
    if($ports.Count -ne 1){throw 'Connect one Pico serial device or pass -Port COMx. BOOTSEL mode has no serial port.'}
    $Port=$ports[0].Trim()
}
Write-Host 'After wiring checks, type START and press Enter. STOP stops the clocks. Ctrl+] exits the monitor.'
& $python -m serial.tools.miniterm $Port 115200 --eol LF

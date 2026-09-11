# Keep the roamer running on this machine.
#
# Starts roam.py, waits for it to exit, waits six seconds, starts it again.
# Register it once with Task Scheduler so it runs at logon:
#
#   schtasks /Create /TN flybrain /SC ONLOGON /RL LIMITED /F ^
#     /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\path\to\keepalive.ps1"
#
# and stop the machine from sleeping:
#
#   powercfg /change standby-timeout-ac 0
#   powercfg /change hibernate-timeout-ac 0
#
# Logs go to build\keepalive.log, one line per start and stop.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $root ".venv\Scripts\python.exe"
$log = Join-Path $root "build\keepalive.log"

function note($m) {
  $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
  Add-Content -Path $log -Value $line
}

note "keepalive up"
while ($true) {
  note "starting roam.py"
  $p = Start-Process -FilePath $py -ArgumentList "roam.py" -WorkingDirectory $root -PassThru -WindowStyle Hidden `
       -RedirectStandardOutput (Join-Path $root "build\roam.out.log") `
       -RedirectStandardError (Join-Path $root "build\roam.err.log")
  $p.WaitForExit()
  note ("roam.py exited with " + $p.ExitCode)
  Start-Sleep -Seconds 6
}

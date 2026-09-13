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
#
# Her state - the paper ledger, what she has learned, her day - lives in the
# folder FLY_STATE_DIR names (state\ next to this script by default), apart
# from build\, which only holds things that can be made again. Every fifteen
# minutes that folder is mirrored to a backup folder outside the checkout,
# and once a day a dated copy is kept, so a deleted folder is a nuisance and
# not a loss.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $root '.venv\Scripts\python.exe'
$log = Join-Path $root 'build\keepalive.log'
$state = Join-Path $root 'state'
$backup = Join-Path $env:USERPROFILE 'Backups\flybrain-state'

function note($m) {
  $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
  Add-Content -Path $log -Value $line
}

function backup-state {
  if (-not (Test-Path $state)) { return }
  $live = Join-Path $backup 'live'
  New-Item -ItemType Directory -Force $live | Out-Null
  robocopy $state $live /MIR /R:1 /W:1 /NP /NFL /NDL /NJH /NJS | Out-Null
  $daily = Join-Path $backup ('daily\' + (Get-Date -Format 'yyyy-MM-dd'))
  if (-not (Test-Path $daily)) {
    New-Item -ItemType Directory -Force $daily | Out-Null
    robocopy $state $daily /E /R:1 /W:1 /NP /NFL /NDL /NJH /NJS | Out-Null
    note "daily state copy $daily"
  }
}

New-Item -ItemType Directory -Force (Join-Path $root 'build') | Out-Null
note "keepalive up"
backup-state

# The betting room's bookie and the roamer share one secret for the life of
# this boot. It is minted here, handed to both as an environment variable,
# and written nowhere. The bookie is paper only; it listens on loopback.
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$env:FLY_INTENT_TOKEN = [System.BitConverter]::ToString($bytes).Replace("-", "").ToLower()

function start-bookie {
  note "starting bookie.py"
  return Start-Process -FilePath $py -ArgumentList "bookie.py" -WorkingDirectory $root -PassThru -WindowStyle Hidden `
       -RedirectStandardOutput (Join-Path $root 'build\bookie.out.log') `
       -RedirectStandardError (Join-Path $root 'build\bookie.err.log')
}

$b = start-bookie
while ($true) {
  if ($b.HasExited) {
    note ("bookie.py exited with " + $b.ExitCode)
    $b = start-bookie
  }
  note "starting roam.py"
  $p = Start-Process -FilePath $py -ArgumentList "roam.py" -WorkingDirectory $root -PassThru -WindowStyle Hidden `
       -RedirectStandardOutput (Join-Path $root 'build\roam.out.log') `
       -RedirectStandardError (Join-Path $root 'build\roam.err.log')
  while (-not $p.WaitForExit(900000)) { backup-state }
  note ("roam.py exited with " + $p.ExitCode)
  backup-state
  Start-Sleep -Seconds 6
}

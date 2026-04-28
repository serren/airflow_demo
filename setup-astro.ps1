#!/usr/bin/env pwsh
# setup-astro.ps1
# Initializes astro-machine for Airflow development.
# Run this after machine recreation or on a fresh machine.

$MachineName   = "astro-machine"
$PodmanApiPort = 2376

function Step($msg)  { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function OK($msg)    { Write-Host "    OK: $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "    WARN: $msg" -ForegroundColor Yellow }
function Fail($msg)  { Write-Host "    ERROR: $msg" -ForegroundColor Red; exit 1 }

# ── 1. Check / create machine ────────────────────────────────────────────────
Step "Checking Podman machine '$MachineName'..."

$machineList = podman machine list 2>&1 | Out-String
$machineExists = $machineList -match $MachineName

if (-not $machineExists) {
    Warn "Machine not found. Running 'astro dev start' to create it (first run may fail - that's OK)..."
    astro dev start -p $AirflowPort 2>&1 | Out-Null
    Start-Sleep -Seconds 5

    $machineList = podman machine list 2>&1 | Out-String
    if (-not ($machineList -match $MachineName)) {
        Fail "Machine was not created. Run 'astro dev start' manually and try again."
    }
}

# ── 2. Ensure machine is running ─────────────────────────────────────────────
Step "Checking machine status..."

$isRunning = $machineList -match "Currently running"
if (-not $isRunning) {
    Write-Host "    Starting machine..."
    podman machine start $MachineName
    Start-Sleep -Seconds 5
    OK "Machine started"
} else {
    OK "Already running"
}

# ── 3. Fix systemd directory ownership ───────────────────────────────────────
Step "Fixing ~/.config/systemd ownership..."
# The directory may be owned by root after machine init; chown it to the regular user
podman machine ssh $MachineName "sudo chown -R user:user ~/.config/systemd 2>/dev/null; true" | Out-Null
OK "Ownership fixed"

# ── 4. Install Podman API systemd service ────────────────────────────────────
Step "Installing podman-api-tcp.service (port $PodmanApiPort)..."

$serviceContent = @"
[Unit]
Description=Podman API TCP Service (for Astro CLI)
After=default.target

[Service]
Type=simple
ExecStart=/usr/bin/podman system service --time=0 tcp:0.0.0.0:$PodmanApiPort
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"@

# Pass content via base64 to avoid heredoc quoting issues over SSH
$b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($serviceContent))

podman machine ssh $MachineName @"
mkdir -p ~/.config/systemd/user
echo '$b64' | base64 -d > ~/.config/systemd/user/podman-api-tcp.service
systemctl --user daemon-reload
systemctl --user enable --now podman-api-tcp.service
"@

Start-Sleep -Seconds 3

$status = podman machine ssh $MachineName "systemctl --user is-active podman-api-tcp.service" 2>&1
if ($status.Trim() -eq "active") {
    OK "Service is active and enabled for autostart"
} else {
    Warn "Service status: $status — check manually: podman machine ssh $MachineName 'systemctl --user status podman-api-tcp.service'"
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next step:"
Write-Host "  .\start.ps1"

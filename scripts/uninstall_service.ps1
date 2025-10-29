param(
    [string]$ServiceName = "SystemHealthMonitor"
)

Write-Host "Attempting to stop Windows service '$ServiceName'..."

try {
    $service = Get-Service -Name $ServiceName -ErrorAction Stop
    if ($service.Status -ne 'Stopped') {
        Stop-Service -Name $ServiceName -Force -ErrorAction Stop
        $service.WaitForStatus('Stopped', '00:00:30')
        Write-Host "Service stopped."
    } else {
        Write-Host "Service already stopped."
    }
}
catch {
    Write-Warning "Unable to stop service '$ServiceName': $_"
}

Write-Host "Removing service '$ServiceName'..."
try {
    sc.exe delete $ServiceName | Out-Null
    Write-Host "Service removal requested. A system restart may be required to complete cleanup."
}
catch {
    Write-Warning "Failed to remove service '$ServiceName': $_"
}


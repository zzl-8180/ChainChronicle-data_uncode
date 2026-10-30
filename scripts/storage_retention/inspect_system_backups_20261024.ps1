# Read-only Windows backup inventory. Writes one new report; never restores or deletes files.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$reportRoot = Join-Path $projectRoot 'output\storage_retention\restore_20261024\system_backups'
[System.IO.Directory]::CreateDirectory($reportRoot) | Out-Null
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$result = [ordered]@{
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
    read_only = $true
    is_windows_administrator = $isAdmin
    volume = 'E:'
    vss = $null
    e_volume_shadow_copies = @()
    windows_backup = $null
    errors = @()
    deleted_files = 0
    restored_files = 0
}
function Invoke-ReadOnlyInventoryCommand {
    param([string]$Executable, [string[]]$CommandArguments)
    $savedPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $commandOutput = & $Executable @CommandArguments 2>&1
        return @{ exit_code = $LASTEXITCODE; output = @($commandOutput | ForEach-Object { $_.ToString() }) }
    } catch {
        return @{ exit_code = $null; output = @($_.Exception.Message); status = 'command_failed' }
    } finally {
        $ErrorActionPreference = $savedPreference
    }
}
if ($isAdmin) {
    $result.vss = Invoke-ReadOnlyInventoryCommand -Executable "$env:SystemRoot\System32\vssadmin.exe" -CommandArguments @('list', 'shadows', '/for=E:')
    try {
        $volume = Get-CimInstance -ClassName Win32_Volume -Filter "DriveLetter='E:'"
        if ($null -eq $volume) { throw 'E: volume was not found' }
        $copies = @(Get-CimInstance -ClassName Win32_ShadowCopy | Where-Object { $_.VolumeName -eq $volume.DeviceID })
        $result.e_volume_shadow_copies = @($copies | ForEach-Object {
            @{ id = $_.ID; device_object = $_.DeviceObject; volume_name = $_.VolumeName; install_date = [string]$_.InstallDate }
        })
    } catch {
        $result.errors += "Shadow copy metadata: $($_.Exception.Message)"
    }
    $wbadmin = Join-Path $env:SystemRoot 'System32\wbadmin.exe'
    if (Test-Path -LiteralPath $wbadmin) {
        $result.windows_backup = Invoke-ReadOnlyInventoryCommand -Executable $wbadmin -CommandArguments @('get', 'versions')
    } else {
        $result.windows_backup = @{ status = 'wbadmin_not_installed' }
    }
} else {
    $result.errors += 'Windows administrator privileges are required. Run this script in an administrator PowerShell window.'
}
$fileName = 'admin_inventory_' + (Get-Date -Format 'yyyyMMddTHHmmssfff') + '.json'
$reportPath = Join-Path $reportRoot $fileName
$result | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $reportPath -Encoding utf8 -NoClobber
Write-Output "Read-only report saved: $reportPath"
Write-Output "Windows administrator: $isAdmin"
Write-Output "E: shadow copies found: $(@($result.e_volume_shadow_copies).Count)"
Write-Output 'No files were deleted or restored by this inventory script.'

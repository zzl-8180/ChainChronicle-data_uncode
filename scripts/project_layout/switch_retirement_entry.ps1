param(
    [Parameter(Mandatory)][ValidateSet('C14','C15','C16','C17','C18')][string]$Cycle,
    [Parameter(Mandatory)][ValidateSet('CreateNext','RenameOld','RenameNext')][string]$Action,
    [Parameter(Mandatory)][string]$RunDirectory
)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$approved = Join-Path $repo 'operations/history/retired-packaging/20261108/share_bundle'
$dates = @{C14='20261103';C15='20261103';C16='20261104';C17='20261106';C18='20261106'}
$parent = Join-Path $repo ('work/' + $Cycle.ToLowerInvariant() + '_delivery_' + $dates[$Cycle] + '/impl/isolation_input/output')
$formal = Join-Path $parent 'share_bundle'
$next = Join-Path $parent 'share_bundle.retirement-next-20261108'
$previous = Join-Path $parent 'share_bundle.retirement-previous-20261108'
$old = Join-Path $repo 'output/share_bundle'
$run = [IO.Path]::GetFullPath($RunDirectory)
$reports = Join-Path $repo 'docs/project-layout/20261108-packaging-physical-v1'
if (-not $run.StartsWith($reports + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Receipt root outside this physical run' }

function Assert-Window {
    $now = [DateTimeOffset]::UtcNow
    $start = [DateTimeOffset]::Parse('2026-11-08T04:47:51Z')
    $end = [DateTimeOffset]::Parse('2026-11-08T06:00:00Z')
    if ($now -lt $start -or $now -ge $end) { throw ('Outside approved immediate-start to 14:00 Beijing window: ' + $now.ToString('o')) }
}
function Assert-RealAncestors([string]$path) {
    $current = [IO.Path]::GetFullPath($path)
    $chain = [Collections.Generic.List[string]]::new()
    while ($true) {
        $chain.Add($current)
        $up = [IO.Path]::GetDirectoryName($current)
        if (-not $up -or $up -eq $current) { break }
        $current = $up
    }
    for ($i=$chain.Count-1; $i -ge 0; $i--) {
        $item = Get-Item -LiteralPath $chain[$i] -Force
        if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw ('Not a real directory: '+$chain[$i]) }
    }
}
function Assert-Absent([string]$path) {
    if (Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue) { throw ('Name already occupied: '+$path) }
}
function Normal-Target([string]$path) {
    if ($path.StartsWith('\\?\')) { $path=$path.Substring(4) }
    return [IO.Path]::GetFullPath($path).TrimEnd('\')
}
function Assert-Junction([string]$path,[string]$target) {
    $item = Get-Item -LiteralPath $path -Force
    if ($item.LinkType -ne 'Junction' -or -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw ('Not a junction: '+$path) }
    $actual = @($item.Target)
    if ($actual.Count -ne 1 -or (Normal-Target $actual[0]) -ne (Normal-Target $target)) { throw ('Unexpected junction target: '+$path) }
    return @{path=$path;target=$actual[0];link_type=$item.LinkType}
}
function Save-New([string]$path,$value) {
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($value | ConvertTo-Json -Depth 12))
    $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}

Assert-Window
Assert-RealAncestors $run
Assert-RealAncestors $parent
Assert-RealAncestors $approved
$intentPath=Join-Path $run ($Cycle+'-'+$Action+'-intent.json')
$donePath=Join-Path $run ($Cycle+'-'+$Action+'-done.json')
Assert-Absent $intentPath
Assert-Absent $donePath
if ($Action -eq 'CreateNext') {
    $before=Assert-Junction $formal $old
    Assert-Absent $next
    Assert-Absent $previous
} elseif ($Action -eq 'RenameOld') {
    $before=Assert-Junction $formal $old
    $null=Assert-Junction $next $approved
    Assert-Absent $previous
} else {
    Assert-Absent $formal
    $before=Assert-Junction $next $approved
    $null=Assert-Junction $previous $old
}
$intent=@{cycle=$Cycle;action=$Action;started_utc=[DateTimeOffset]::UtcNow.ToString('o');before=$before;approved_target=$approved;status='INTENT';no_delete=$true}
Save-New $intentPath $intent
Assert-RealAncestors $run
Assert-RealAncestors $parent
Assert-RealAncestors $approved
Assert-Window
if ($Action -eq 'CreateNext') {
    $null=New-Item -ItemType Junction -Path $next -Target $approved
    $after=Assert-Junction $next $approved
} elseif ($Action -eq 'RenameOld') {
    Rename-Item -LiteralPath $formal -NewName 'share_bundle.retirement-previous-20261108'
    Assert-Absent $formal
    $after=Assert-Junction $previous $old
} else {
    Rename-Item -LiteralPath $next -NewName 'share_bundle'
    Assert-Absent $next
    $after=Assert-Junction $formal $approved
}
$done=@{cycle=$Cycle;action=$Action;finished_utc=[DateTimeOffset]::UtcNow.ToString('o');status='DONE_PENDING_CONTENT_CHECK';after=$after;intent_file=$intentPath;no_delete=$true}
Save-New $donePath $done
$done | ConvertTo-Json -Depth 12

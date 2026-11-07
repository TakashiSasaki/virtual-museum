# Publish an already-built Web player. Run from any directory with PowerShell.
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$buildRelative = 'unity/VirtualMuseum/Build/WebGL'
$cloneRelative = 'unity/VirtualMuseum/Temp/pages-publish'
$buildRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot $buildRelative))
$publishRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot $cloneRelative))
Get-Command git -ErrorAction Stop | Out-Null

function Invoke-Git([string[]]$Arguments) {
    # Windows PowerShell exposes native stderr as ErrorRecord even on success.
    $ErrorActionPreference = 'Continue'
    $lines = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Git failed ($LASTEXITCODE): $($lines -join [Environment]::NewLine)" }
    $lines | ForEach-Object { $_.ToString() }
}

function Assert-WorkspacePath([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = $repoRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (!$full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the repository: $full"
    }
    # Reject junctions/symlinks in every existing path component.
    $part = $full
    while ($part.Length -ge $repoRoot.Length) {
        if (Test-Path -LiteralPath $part) {
            $item = Get-Item -LiteralPath $part -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path is not allowed: $part" }
        }
        $part = [IO.Path]::GetDirectoryName($part)
        if (!$part) { break }
    }
}

function Test-PublicationPath([string]$Path) {
    if ($Path -in @('Content/catalog.json','Content/room.json')) { return $true }
    if ($Path -cmatch '^Content/room-[a-z0-9-]+-[a-f0-9]{32}\.bundle$') { return $true }
    if ($Path -cmatch '^Content/specimen-[0-9]{2}-[a-f0-9]{32}\.bundle$') { return $true }
    if ($Path -in @('index.html', 'museum.css', 'museum-sw.js', 'favicon.svg', 'manifest.webmanifest', '.nojekyll', 'FONT-LICENSE.txt',
        'THIRD-PARTY-NOTICES.txt', 'publication.json')) { return $true }
    if ($Path -cmatch '^Build/[A-Za-z0-9_.-]+\.(data|wasm|js)(\.unityweb|\.gz|\.br)?$') { return $true }
    return $Path -cmatch '^TemplateData/[A-Za-z0-9_./-]+\.(css|js|png|ico|svg|webp|jpg|jpeg|woff|woff2)$'
}

function Get-BuildFiles {
    $pending = New-Object 'System.Collections.Generic.Queue[string]'
    $pending.Enqueue($buildRoot)
    while ($pending.Count) {
        foreach ($item in Get-ChildItem -LiteralPath $pending.Dequeue() -Force) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "The build contains a linked file or directory: $($item.Name)"
            }
            if ($item.PSIsContainer) { $pending.Enqueue($item.FullName); continue }
            $relative = $item.FullName.Substring($buildRoot.Length + 1).Replace('\', '/')
            if (!(Test-PublicationPath $relative)) { throw "Unexpected build file; publication stopped: $relative" }
            if ($item.Length -eq 0 -and $relative -ne '.nojekyll') { throw "Empty build file: $relative" }
            if ($item.Length -ge 100MB) { throw "File reaches GitHub's 100 MiB limit: $relative" }
            [pscustomobject]@{ Source = $item.FullName; Relative = $relative }
        }
    }
}

$actualRoot = (Invoke-Git @('-C', $repoRoot, 'rev-parse', '--show-toplevel')).Trim()
if ([IO.Path]::GetFullPath($actualRoot) -ne $repoRoot) { throw 'The script must belong to the source repository.' }
Assert-WorkspacePath $buildRoot
Assert-WorkspacePath $publishRoot
if (!(Test-Path -LiteralPath $buildRoot -PathType Container)) { throw 'Build the Web player first with Museum/Web/Build GitHub Pages.' }
& git -C $repoRoot check-ignore --quiet --no-index -- ($cloneRelative + '/')
if ($LASTEXITCODE -ne 0) { throw 'The publication clone must be ignored by the source repository.' }
if (@(Invoke-Git @('-C', $repoRoot, 'status', '--porcelain=v1', '--untracked-files=no')).Count) {
    throw 'Commit the tracked source changes before publishing so publication.json identifies the saved source.'
}

$files = @(Get-BuildFiles)
if ((Get-Content -LiteralPath (Join-Path $buildRoot 'index.html') -Raw) -match '__MUSEUM_' -or
    (Get-Content -LiteralPath (Join-Path $buildRoot 'museum-sw.js') -Raw) -match '__MUSEUM_') {
    throw 'Web build has not been finalized. Run MuseumWebBuild.FinalizeOutput() first.'
}
if (!$files.Count) { throw 'The Web build directory is empty.' }
foreach ($required in @('index.html', 'museum-sw.js', 'favicon.svg', 'manifest.webmanifest', 'FONT-LICENSE.txt', 'THIRD-PARTY-NOTICES.txt')) {
    if ($required -notin $files.Relative) { throw "Required publication file is missing: $required. Run MuseumWebBuild.FinalizeOutput()." }
}
foreach ($pattern in @('^Build/.+\.wasm(\.unityweb|\.gz|\.br)?$', '^Build/.+\.data(\.unityweb|\.gz|\.br)?$',
    '^Build/.+\.framework\.js(\.unityweb|\.gz|\.br)?$', '^Build/.+\.loader\.js$')) {
    if (!@($files.Relative | Where-Object { $_ -match $pattern }).Count) { throw "Incomplete Unity build: missing $pattern" }
}
$contentCatalogPath = Join-Path $buildRoot 'Content/catalog.json'
if (!(Test-Path -LiteralPath $contentCatalogPath)) { throw 'Progressive content catalog is missing.' }
$contentCatalog = Get-Content -LiteralPath $contentCatalogPath -Raw | ConvertFrom-Json
if ($contentCatalog.version -ne 1 -or !$contentCatalog.entries.Count) { throw 'Invalid progressive content catalog.' }
foreach ($entry in $contentCatalog.entries) {
    if ($entry.file -cnotmatch '^specimen-[0-9]{2}-[a-f0-9]{32}\.bundle$') { throw 'Invalid content bundle name.' }
    $bundlePath = Join-Path $buildRoot ('Content/' + $entry.file)
    if (!(Test-Path -LiteralPath $bundlePath) -or (Get-Item -LiteralPath $bundlePath).Length -ne $entry.bytes) {
        throw "Missing or incomplete detail bundle: $($entry.file)"
    }
}
$roomCatalogPath = Join-Path $buildRoot 'Content/room.json'
if (!(Test-Path -LiteralPath $roomCatalogPath)) { throw 'Progressive room catalog is missing.' }
$roomCatalog = Get-Content -LiteralPath $roomCatalogPath -Raw | ConvertFrom-Json
if ($roomCatalog.version -ne 1 -or !$roomCatalog.entries.Count) { throw 'Invalid progressive room catalog.' }
foreach ($entry in $roomCatalog.entries) {
    if ($entry.file -cnotmatch '^room-[a-z0-9-]+-[a-f0-9]{32}\.bundle$') { throw 'Invalid room bundle name.' }
    $bundlePath = Join-Path $buildRoot ('Content/' + $entry.file)
    if (!(Test-Path -LiteralPath $bundlePath) -or (Get-Item -LiteralPath $bundlePath).Length -ne $entry.bytes) {
        throw "Missing or incomplete room bundle: $($entry.file)"
    }
}
$origin = (Invoke-Git @('-C', $repoRoot, 'remote', 'get-url', 'origin')).Trim()
if ($origin -notmatch '^(https://github\.com/|git@github\.com:)(?<owner>[A-Za-z0-9_.-]+)/(?<repo>[A-Za-z0-9_.-]+?)(\.git)?$') {
    throw 'Origin must be a GitHub HTTPS or SSH repository URL without embedded credentials.'
}
$pagesUrl = 'https://' + $Matches.owner + '.github.io/' + $Matches.repo + '/'
$sourceCommit = (Invoke-Git @('-C', $repoRoot, 'rev-parse', 'HEAD')).Trim()
$sourceBranch = (Invoke-Git @('-C', $repoRoot, 'rev-parse', '--abbrev-ref', 'HEAD')).Trim()
$authorName = (Invoke-Git @('-C', $repoRoot, 'config', 'user.name')).Trim()
$authorEmail = (Invoke-Git @('-C', $repoRoot, 'config', 'user.email')).Trim()
if (!$authorName -or !$authorEmail) { throw 'Configure the source repository Git author before publishing.' }

if (Test-Path -LiteralPath $publishRoot) {
    if (!(Test-Path -LiteralPath (Join-Path $publishRoot '.git') -PathType Container)) {
        throw 'The publication directory already exists but is not a dedicated clone. It has been left untouched.'
    }
    $cloneRoot = (Invoke-Git @('-C', $publishRoot, 'rev-parse', '--show-toplevel')).Trim()
    if ([IO.Path]::GetFullPath($cloneRoot) -ne $publishRoot) { throw 'Unexpected publication clone worktree.' }
    if ((Invoke-Git @('-C', $publishRoot, 'remote', 'get-url', 'origin')).Trim() -ne $origin) { throw 'Publication clone origin differs from source origin.' }
    if ((Invoke-Git @('-C', $publishRoot, 'branch', '--show-current')).Trim() -ne 'gh-pages') { throw 'Publication clone is not on gh-pages.' }
    if (@(Invoke-Git @('-C', $publishRoot, 'status', '--porcelain=v1', '--untracked-files=all', '--ignored=matching')).Count) {
        throw 'Publication clone contains local changes or extra files. It has been left untouched.'
    }
} else {
    Invoke-Git @('init', '--quiet', '--initial-branch=gh-pages', $publishRoot) | Out-Null
    Invoke-Git @('-C', $publishRoot, 'remote', 'add', 'origin', $origin) | Out-Null
}
Assert-WorkspacePath (Join-Path $publishRoot '.git')
Invoke-Git @('-C', $publishRoot, 'config', 'user.name', $authorName) | Out-Null
Invoke-Git @('-C', $publishRoot, 'config', 'user.email', $authorEmail) | Out-Null
Invoke-Git @('-C', $publishRoot, 'config', 'core.autocrlf', 'false') | Out-Null

$remoteRef = @(Invoke-Git @('-C', $publishRoot, 'ls-remote', '--heads', 'origin', 'refs/heads/gh-pages'))
$localRef = @(Invoke-Git @('-C', $publishRoot, 'for-each-ref', '--format=%(objectname)', 'refs/heads/gh-pages'))
if ($remoteRef.Count) {
    Invoke-Git @('-C', $publishRoot, 'fetch', '--quiet', '--no-tags', 'origin', 'refs/heads/gh-pages:refs/remotes/origin/gh-pages') | Out-Null
    if ($localRef.Count) {
        $counts = ((Invoke-Git @('-C', $publishRoot, 'rev-list', '--left-right', '--count', 'HEAD...origin/gh-pages')).Trim() -split '\s+')
        if ([int]$counts[0] -gt 0) { throw 'Publication clone has unpublished/divergent commits. Review them before rerunning; no history was replaced.' }
        Invoke-Git @('-C', $publishRoot, 'merge', '--ff-only', 'origin/gh-pages') | Out-Null
    } else {
        Invoke-Git @('-C', $publishRoot, 'checkout', '--quiet', '-B', 'gh-pages', 'origin/gh-pages') | Out-Null
    }
} elseif ($localRef.Count) {
    throw 'Local gh-pages exists but remote gh-pages does not. Review the clone before publishing.'
}

# Only replace previously generated deployment files in this isolated clone.
foreach ($tracked in @(Invoke-Git @('-C', $publishRoot, 'ls-files'))) {
    if (!(Test-PublicationPath $tracked)) { throw "gh-pages contains an unrelated tracked file: $tracked. Nothing has been removed." }
}
Assert-WorkspacePath $publishRoot
Invoke-Git @('-C', $publishRoot, 'rm', '-r', '--quiet', '--ignore-unmatch', '--', '.') | Out-Null
foreach ($file in $files) {
    $destination = Join-Path $publishRoot $file.Relative
    Assert-WorkspacePath $destination
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
    Copy-Item -LiteralPath $file.Source -Destination $destination -Force
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $publishRoot '.nojekyll'), '', $utf8)
$publication = [ordered]@{ sourceCommit = $sourceCommit; sourceBranch = $sourceBranch; repository = $origin }
[IO.File]::WriteAllText((Join-Path $publishRoot 'publication.json'), (($publication | ConvertTo-Json) + [Environment]::NewLine), $utf8)
Invoke-Git @('-C', $publishRoot, 'add', '--all', '--', '.') | Out-Null
$indexed = @(Invoke-Git @('-C', $publishRoot, 'ls-files'))
foreach ($expected in @($files.Relative) + @('.nojekyll', 'publication.json')) {
    if ($expected -notin $indexed) { throw "Publication file was excluded by a Git ignore rule: $expected" }
}
if (@(Invoke-Git @('-C', $publishRoot, 'diff', '--cached', '--name-only')).Count) {
    Invoke-Git @('-C', $publishRoot, 'commit', '--quiet', '-m', ('Publish WebGL museum from ' + $sourceCommit.Substring(0, 12))) | Out-Null
} else {
    Write-Host 'The generated publication is unchanged; no new commit is needed.'
}
Invoke-Git @('-C', $publishRoot, 'push', '--porcelain', 'origin', 'HEAD:refs/heads/gh-pages') | Write-Host
$publishedCommit = (Invoke-Git @('-C', $publishRoot, 'rev-parse', 'HEAD')).Trim()
$verifiedRemote = ((Invoke-Git @('-C', $publishRoot, 'ls-remote', '--heads', 'origin', 'refs/heads/gh-pages')).Trim() -split '\s+')[0]
if ($publishedCommit -ne $verifiedRemote) { throw 'Remote gh-pages did not match the publication commit.' }
Write-Host "Published branch commit: $publishedCommit"
Write-Host "Pages URL (check the GitHub Pages deployment result): $pagesUrl"

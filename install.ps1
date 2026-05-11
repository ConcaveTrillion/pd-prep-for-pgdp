# pgdp-prep installer (Windows PowerShell)
#
# Usage:
#   irm https://raw.githubusercontent.com/ConcaveTrillion/pd-prep-for-pgdp/main/install.ps1 | iex
#
# Downloads the prebuilt wheel attached to the latest GitHub Release and
# runs `uv tool install` against it. The wheel ships with the React SPA
# already bundled, so end users do NOT need Node, npm, or a JavaScript
# toolchain — only `uv` (which this script will install for you).

$ErrorActionPreference = "Stop"

$repo = "ConcaveTrillion/pd-prep-for-pgdp"

function Test-Command($name) {
    Get-Command $name -ErrorAction SilentlyContinue | ForEach-Object { return $true }
    return $false
}

# 1. Install uv if missing
if (-not (Test-Command "uv")) {
    Write-Host "uv not found — installing uv..."
    Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing | Invoke-Expression
    $env:Path = "$HOME\.local\bin;" + $env:Path
}

# 2. Detect NVIDIA GPU
$extraIndex = ""
$extras = ""
if (Test-Command "nvidia-smi") {
    try {
        $smiOutput = & nvidia-smi 2>$null | Out-String
        if ($smiOutput -match 'CUDA Version:\s+([0-9]+)\.([0-9]+)') {
            $cudaTag = "cu$($Matches[1])$($Matches[2])"
            $extraIndex = "https://download.pytorch.org/whl/$cudaTag"
            $extras = "[cuda]"
            Write-Host "Detected CUDA $($Matches[1]).$($Matches[2]) — installing with $cudaTag + CuPy."
        }
    } catch {
        Write-Host "nvidia-smi failed — falling back to CPU."
    }
} else {
    Write-Host "No NVIDIA GPU detected — installing CPU-only build."
}

# 3. Resolve latest tag
try {
    $tags = Invoke-RestMethod "https://api.github.com/repos/$repo/tags"
} catch {
    throw "Could not fetch tags from https://api.github.com/repos/$repo/tags : $_"
}
if (-not ($tags -and $tags[0].name)) {
    throw "Could not resolve the latest release tag from GitHub."
}
$latestTag = $tags[0].name
Write-Host "Installing pgdp-prep $latestTag..."

# 4. Find the wheel asset attached to the GitHub Release for this tag.
try {
    $release = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/tags/$latestTag" `
        -Headers @{ Accept = "application/vnd.github+json" }
} catch {
    $release = $null
}
$wheelAsset = $null
if ($release -and $release.assets) {
    $wheelAsset = $release.assets | Where-Object { $_.name -like "*.whl" } | Select-Object -First 1
}
if (-not $wheelAsset) {
    # Hard-fail rather than fall back to `git+...`. The git+ path requires
    # Node + npm on the user's machine to build the React SPA at install
    # time — exactly the requirement this script is designed to avoid.
    throw @"
No .whl asset attached to release $latestTag.
Expected a wheel uploaded by .github/workflows/release.yml.
Check https://github.com/$repo/releases/tag/$latestTag — the release
workflow may have failed, or this is an older tag from before wheel
publishing was wired up.
"@
}

# 5. Download the wheel to a temp dir and install it as a uv tool.
$tmpDir = New-Item -ItemType Directory -Path (Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString()))
try {
    $wheelFile = Join-Path $tmpDir.FullName $wheelAsset.name
    Write-Host "Downloading $($wheelAsset.browser_download_url)..."
    Invoke-WebRequest -Uri $wheelAsset.browser_download_url -OutFile $wheelFile -UseBasicParsing

    $installTarget = "$wheelFile$extras"
    if ($extraIndex) {
        & uv tool install --reinstall $installTarget --extra-index-url $extraIndex
    } else {
        & uv tool install --reinstall $installTarget
    }
} finally {
    Remove-Item -Recurse -Force $tmpDir.FullName -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Done! Run: pgdp-prep"

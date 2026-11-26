<#
.SYNOPSIS
Windows PowerShell PreToolUse Hook - Destructive Command Speed Bump
.DESCRIPTION
Delegates to the sibling zero-dependency Python lexer engine (block-dangerous.py)
when Python is available for full multi-line, quote-safe, and low-false-positive
inspection. Falls back to a hardened PowerShell regex checker when Python is absent.
Exits with code 2 on block; code 0 on allow.
Self-test:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\block-dangerous.ps1 -TestCommand "rm -rf *.py"
#>
param(
  [string]$TestCommand = ""
)

$ErrorActionPreference = 'Stop'

# Fast path: delegate to sibling block-dangerous.py when Python is available (unless disabled for fallback tests)
$pyEngine = Join-Path $PSScriptRoot "block-dangerous.py"
if (($env:GUARDRAIL_DISABLE_PYTHON -ne '1') -and (Test-Path -LiteralPath $pyEngine)) {
  $pyBin = $null
  foreach ($cand in @('python', 'python3', 'py')) {
    $found = Get-Command $cand -ErrorAction SilentlyContinue
    if ($null -ne $found) {
      $pyBin = $found.Source
      break
    }
  }
  if ($null -ne $pyBin) {
    if (-not [string]::IsNullOrEmpty($TestCommand)) {
      & $pyBin -B $pyEngine --dialect ps --test $TestCommand
      exit $LASTEXITCODE
    } else {
      $rawStdin = [Console]::In.ReadToEnd()
      $psi = New-Object System.Diagnostics.ProcessStartInfo
      $psi.FileName = $pyBin
      $psi.Arguments = "-B `"$pyEngine`" --dialect ps"
      $psi.UseShellExecute = $false
      $psi.RedirectStandardInput = $true
      $psi.RedirectStandardOutput = $true
      $psi.RedirectStandardError = $true
      $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
      $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
      $proc = [System.Diagnostics.Process]::Start($psi)
      $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
      $writer = New-Object System.IO.StreamWriter($proc.StandardInput.BaseStream, $utf8NoBom)
      $writer.Write($rawStdin)
      $writer.Close()
      $stdout = $proc.StandardOutput.ReadToEnd()
      $stderr = $proc.StandardError.ReadToEnd()
      $proc.WaitForExit()
      if ($stdout) { [Console]::Out.Write($stdout) }
      if ($stderr) { [Console]::Error.Write($stderr) }
      exit $proc.ExitCode
    }
  }
}

# Fallback path (pure PowerShell when Python is not installed)
$cmd = $TestCommand
if ([string]::IsNullOrEmpty($cmd)) {
  $raw = [Console]::In.ReadToEnd()
  if (-not [string]::IsNullOrWhiteSpace($raw)) {
    try {
      $obj = $raw | ConvertFrom-Json
      if ($null -ne $obj.tool_input -and $null -ne $obj.tool_input.command) {
        $cmd = [string]$obj.tool_input.command
      }
    } catch {
      $cmd = $raw
    }
  }
}

if ([string]::IsNullOrWhiteSpace($cmd)) { exit 0 }

function Strip-QuotedStrings {
  param([string]$Text)
  # Single-pass state-safe replacement so single quotes containing " do not desync
  return [regex]::Replace($Text, '''[^'']*''|"(?:\\.|[^"\\])*"', {
    param($m)
    if ($m.Value.StartsWith("'")) { return "''" } else { return '""' }
  })
}

function Strip-CommandPrefix {
  param([string]$Seg)
  $s = $Seg.Trim()
  while ($s -match '^(?:&\s+|[A-Za-z_][A-Za-z0-9_]*=\S+\s+|(?:sudo|env|command|time|nohup)\s+)') {
    $s = [regex]::Replace($s, '^(?:&\s+|[A-Za-z_][A-Za-z0-9_]*=\S+\s+|(?:sudo|env|command|time|nohup)\s+)', '').TrimStart()
  }
  return $s
}

function Block-Now {
  param([string]$Reason, [string]$OriginalCmd)
  [Console]::Error.WriteLine("BLOCKED BY GUARDRAIL: Destructive or wildcard command blocked ($Reason)")
  [Console]::Error.WriteLine("Command: $OriginalCmd")
  [Console]::Error.WriteLine("Safe alternative: Move unwanted files to _trash_box/ via exact paths, or use git stash / git revert.")
  exit 2
}

$segmentPatterns = @(
  @{ Name = 'wildcard-delete';  Pat = '(?i)^(Remove-Item|ri|del|erase|rd|rmdir|rm)\b.*(\*|\?)' },
  @{ Name = 'recurse-root';     Pat = '(?i)^(Remove-Item|ri|rd|rmdir)\b.*(?:-r(?:e(?:c(?:u(?:r(?:se?)?)?)?)?)?|/s)\b.*\s+([A-Za-z]:[\\/]?|/|~[\\/]?|\$HOME[\\/]?|\$env:USERPROFILE[\\/]?|\.\.?[\\/]?)(\s|$)' },
  @{ Name = 'rm-root-or-cwd';   Pat = '(?i)^rm\b.*\s-[a-z]*[rf][a-z]*\s+([A-Za-z]:[\\/]?|/|~[\\/]?|\$HOME[\\/]?|\.\.?[\\/]?)(\s|$)' },
  @{ Name = 'find-delete';      Pat = '(?i)^find\b.*(\s-delete(\s|$)|\s-exec(?:dir)?\s+(?:[^\s]*[\\/])?(rm|Remove-Item)\b)' },
  @{ Name = 'xargs-rm';         Pat = '(?i)^xargs\b(?:\s+-[^\s]+|\s+-[IlnPdE]\s+\S+)*\s+(?:[^\s]*[\\/])?(rm|Remove-Item)\b' },
  @{ Name = 'git-reset-hard';   Pat = '(?i)^git\b(?:\s+-[Cc]\s+\S+|\s+--[a-z-]+(?:=\S+)?)*\s+reset\b.*\s--hard\b' },
  @{ Name = 'git-clean-force';  Pat = '(?i)^git\b(?:\s+-[Cc]\s+\S+|\s+--[a-z-]+(?:=\S+)?)*\s+clean\b.*(\s-[a-z]*f|\s--force(\s|$))' },
  @{ Name = 'git-push-force';   Pat = '(?i)^git\b(?:\s+-[Cc]\s+\S+|\s+--[a-z-]+(?:=\S+)?)*\s+push\b.*(\s--force(?:=true)?(\s|$)|\s--mirror(\s|$)|\s-[a-z]*f[a-z]*(\s|$))' },
  @{ Name = 'git-discard-all';  Pat = '(?i)^git\b(?:\s+-[Cc]\s+\S+|\s+--[a-z-]+(?:=\S+)?)*\s+(checkout|restore)\b.*\s+\.[\\/]?(\s|$)' },
  @{ Name = 'git-stash-drop';   Pat = '(?i)^git\b(?:\s+-[Cc]\s+\S+|\s+--[a-z-]+(?:=\S+)?)*\s+stash\s+(clear|drop)\b' },
  @{ Name = 'terraform-destroy';Pat = '(?i)^(?:terraform|tofu)\s+(?:destroy\b|apply\b.*\s--?destroy\b)' }
)

$lines = $cmd -split "\r?\n"

foreach ($rawLine in $lines) {
  if ([string]::IsNullOrWhiteSpace($rawLine)) { continue }

  $cleanLine = Strip-QuotedStrings $rawLine
  # Strip trailing # comments outside quotes
  $cleanLine = [regex]::Replace($cleanLine, '(?:^|\s)#.*$', '')

  if ($cleanLine -match '(?i)\|\s*(Remove-Item|ri|del|erase)\b') {
    Block-Now 'pipeline-remove-item' $cmd
  }

  $rawSegments = [regex]::Split($rawLine, '\s*(?:&&|\|\||[;|])\s*')
  $cleanSegments = [regex]::Split($cleanLine, '\s*(?:&&|\|\||[;|])\s*')

  for ($idx = 0; $idx -lt $cleanSegments.Count; $idx++) {
    $norm = Strip-CommandPrefix $cleanSegments[$idx]
    if ([string]::IsNullOrWhiteSpace($norm)) { continue }

    foreach ($rule in $segmentPatterns) {
      if ($norm -match $rule.Pat) {
        Block-Now $rule.Name $cmd
      }
    }

    $rawSeg = if ($idx -lt $rawSegments.Count) { Strip-CommandPrefix $rawSegments[$idx] } else { "" }

    # Quoted wildcard or root/cwd target for delete commands
    if ($rawSeg -match '(?i)^(Remove-Item|ri|del|erase|rd|rmdir|rm)\b.*["''][^"'']*(\*|\?)[^"'']*["'']') {
      Block-Now 'wildcard-delete-quoted' $cmd
    }
    if ($rawSeg -match '(?i)^(Remove-Item|ri|rd|rmdir|rm)\b.*(?:-r\w*|-[a-z]*r[a-z]*|/s)\b.*\s+["'']([A-Za-z]:[\\/]?|/|~[\\/]?|\$HOME[\\/]?|\.\.?[\\/]?)["''](\s|$)') {
      Block-Now 'recurse-root-quoted' $cmd
    }

    # Per-segment SQL guard
    if ($norm -notmatch '(?i)^(echo|write-output|write-host|printf|grep|rg|select-string|git|curl|invoke-webrequest|python|python3|node|pytest|cd|cat)\b') {
      if ($rawSeg -match '(?i)\bDROP\s+(TABLE|DATABASE|SCHEMA)\b') {
        Block-Now 'sql-drop' $cmd
      }
      if ($rawSeg -match '(?i)\bTRUNCATE\s+(TABLE\s+)?[A-Za-z_"`\[]') {
        Block-Now 'sql-truncate' $cmd
      }
    }
  }
}

exit 0

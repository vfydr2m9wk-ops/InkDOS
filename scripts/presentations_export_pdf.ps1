<#
.SYNOPSIS
  Exports every PowerPoint deck in a folder to a PDF with the same name, using Microsoft PowerPoint.

.DESCRIPTION
  The PDFs are the reference for scripts/presentations_fidelity.py and
  scripts/presentations_acceptance.py: they look for "deck.pdf" next to "deck.pptx" / "deck.ppt".
  Runs on Windows with PowerPoint installed (desktop Office). Decks are opened read-only and
  never modified. Files that cannot be opened (password, damaged) are reported and skipped.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File presentations_export_pdf.ps1 -Source "C:\Apresentacoes" -Recurse
#>
param(
  [string]$Source = (Get-Location).Path,
  [switch]$Recurse,
  [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$ppSaveAsPDF = 32
$msoFalse = 0
$msoTrue = -1

$root = (Resolve-Path -LiteralPath $Source).Path
$decks = Get-ChildItem -LiteralPath $root -File -Recurse:$Recurse |
  Where-Object { $_.Extension -match '^\.(pptx?|ppsx?|pptm|potx?)$' -and -not $_.Name.StartsWith('~$') } |
  Sort-Object FullName
if (-not $decks) { Write-Host "Nenhuma apresentacao encontrada em $root"; exit 0 }

$app = New-Object -ComObject PowerPoint.Application
$done = 0; $skipped = 0; $failed = @()
try {
  foreach ($deck in $decks) {
    $pdf = [System.IO.Path]::ChangeExtension($deck.FullName, '.pdf')
    if ((Test-Path -LiteralPath $pdf) -and -not $Overwrite) {
      Write-Host "ja existe: $pdf"; $skipped++; continue
    }
    $pres = $null
    try {
      # Open(FileName, ReadOnly, Untitled, WithWindow)
      $pres = $app.Presentations.Open($deck.FullName, $msoTrue, $msoFalse, $msoFalse)
      $pres.SaveAs($pdf, $ppSaveAsPDF)
      Write-Host "ok: $($deck.Name) -> $([System.IO.Path]::GetFileName($pdf))"
      $done++
    } catch {
      Write-Warning "falhou: $($deck.FullName) - $($_.Exception.Message)"
      $failed += $deck.FullName
    } finally {
      if ($pres) { $pres.Close(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) }
    }
  }
} finally {
  $app.Quit()
  [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
  [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}

Write-Host ""
Write-Host "Exportados: $done  Ja existentes: $skipped  Falhas: $($failed.Count)"
if ($failed.Count) { $failed | ForEach-Object { Write-Host "  $_" } }

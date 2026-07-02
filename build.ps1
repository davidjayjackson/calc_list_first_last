<#
    build.ps1 - Assemble the LIST Calc add-in into build/LIST.oxt

    Steps:
      1. Compile idl/XList.idl into a UNO type library (types/XList.rdb)
         using the LibreOffice SDK's unoidl-write.
      2. Stage the Python component, XCU config, description and manifest.
      3. Zip the staging tree into build/LIST.oxt (forward-slash entry names).
#>
param(
    [string]$LibreOffice = 'C:\Program Files\LibreOffice'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$uw    = Join-Path $LibreOffice 'sdk\bin\unoidl-write.exe'
$types = Join-Path $LibreOffice 'program\types.rdb'
# unoidl-write needs the LibreOffice program dir on PATH for its DLLs.
$env:PATH = (Join-Path $LibreOffice 'program') + ';' + $env:PATH

$build = Join-Path $root 'build'
$stage = Join-Path $build 'oxt'
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
foreach ($d in 'types','python','config','META-INF','Scripts\python') {
    New-Item -ItemType Directory -Force -Path (Join-Path $stage $d) | Out-Null
}

# 1. Compile the IDL type library.
Write-Host 'Compiling IDL -> types/XList.rdb'
& $uw $types (Join-Path $root 'idl') (Join-Path $stage 'types\XList.rdb')
if ($LASTEXITCODE -ne 0) { throw "unoidl-write failed (exit $LASTEXITCODE)" }

# 2. Stage the remaining package files.
Copy-Item (Join-Path $root 'src\list_impl.py')            (Join-Path $stage 'python\list_impl.py')
Copy-Item (Join-Path $root 'src\list_rows.py')            (Join-Path $stage 'Scripts\python\list_rows.py')
Copy-Item (Join-Path $root 'registration\CalcAddIns.xcu') (Join-Path $stage 'config\CalcAddIns.xcu')
Copy-Item (Join-Path $root 'registration\Addons.xcu')     (Join-Path $stage 'config\Addons.xcu')
Copy-Item (Join-Path $root 'registration\description.xml') (Join-Path $stage 'description.xml')
Copy-Item (Join-Path $root 'registration\manifest.xml')   (Join-Path $stage 'META-INF\manifest.xml')

# 3. Zip the staging tree into the .oxt with forward-slash entry names.
$oxt = Join-Path $build 'LIST.oxt'
if (Test-Path $oxt) { Remove-Item $oxt -Force }
Add-Type -AssemblyName System.IO.Compression | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
$zip = [System.IO.Compression.ZipFile]::Open($oxt, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    Get-ChildItem $stage -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($stage.Length + 1) -replace '\\', '/'
        [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $rel)
    }
} finally {
    $zip.Dispose()
}
Write-Host "Built $oxt"

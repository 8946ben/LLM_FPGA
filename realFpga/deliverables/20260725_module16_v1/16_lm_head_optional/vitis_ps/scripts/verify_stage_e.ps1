$ErrorActionPreference = "Stop"

$debugDir = "D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\Debug"
$mapFile = Join-Path $debugDir "lm_head_net_diag.map"
$elfFile = Join-Path $debugDir "lm_head_net_diag.elf"
$readElf = "D:\install\Xilinx\Vitis\2021.1\gnu\aarch64\nt\aarch64-none\bin\aarch64-none-elf-readelf.exe"

function Get-MapAddress {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Symbol
    )

    $pattern = "0x([0-9a-fA-F]+)\s+" + [regex]::Escape($Symbol) + "\s*=\s*\."
    $match = [regex]::Match($script:mapText, $pattern)
    if (-not $match.Success) {
        throw "Symbol not found in map: $Symbol"
    }
    return [Convert]::ToUInt64($match.Groups[1].Value, 16)
}

function Assert-StageE {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$Condition,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

Assert-StageE (Test-Path -LiteralPath $mapFile) "Linker map is missing."
Assert-StageE (Test-Path -LiteralPath $elfFile) "ELF is missing."

$script:mapText = Get-Content -LiteralPath $mapFile -Raw
$runtimeEnd = Get-MapAddress "_end"
$ddrLimit = [uint64]0x7FF00000
$alignment = [uint64]64

$buffers = @(
    [pscustomobject]@{
        Name = "weight"
        Start = Get-MapAddress "__lmh_weight_start"
        End = Get-MapAddress "__lmh_weight_end"
        ExpectedBytes = [uint64]272269312
    },
    [pscustomobject]@{
        Name = "hidden"
        Start = Get-MapAddress "__lmh_hidden_start"
        End = Get-MapAddress "__lmh_hidden_end"
        ExpectedBytes = [uint64]1792
    },
    [pscustomobject]@{
        Name = "history"
        Start = Get-MapAddress "__lmh_history_start"
        End = Get-MapAddress "__lmh_history_end"
        ExpectedBytes = [uint64]18992
    },
    [pscustomobject]@{
        Name = "logits"
        Start = Get-MapAddress "__lmh_logits_start"
        End = Get-MapAddress "__lmh_logits_end"
        ExpectedBytes = [uint64]303872
    },
    [pscustomobject]@{
        Name = "network_rx"
        Start = Get-MapAddress "__lmh_network_rx_start"
        End = Get-MapAddress "__lmh_network_rx_end"
        ExpectedBytes = [uint64]1048576
    }
)

$buffersStart = Get-MapAddress "__lmh_buffers_start"
$buffersEnd = Get-MapAddress "__lmh_buffers_end"

Assert-StageE ($buffersStart -eq [uint64]0x40000000) "Unexpected LM Head buffer base."
Assert-StageE ($runtimeEnd -le $buffersStart) "Runtime image overlaps LM Head buffers."
Assert-StageE ($buffersEnd -le $ddrLimit) "LM Head buffers exceed low PS DDR."

for ($index = 0; $index -lt $buffers.Count; ++$index) {
    $buffer = $buffers[$index]
    $actualBytes = $buffer.End - $buffer.Start
    Assert-StageE (($buffer.Start % $alignment) -eq 0) "$($buffer.Name) is not 64-byte aligned."
    Assert-StageE ($actualBytes -eq $buffer.ExpectedBytes) "$($buffer.Name) has the wrong size."
    if ($index -gt 0) {
        Assert-StageE ($buffer.Start -ge $buffers[$index - 1].End) "$($buffer.Name) overlaps the previous buffer."
    }
}

$sectionOutput = & $readElf -S $elfFile
Assert-StageE ($LASTEXITCODE -eq 0) "readelf failed while reading ELF sections."
Assert-StageE (($sectionOutput -join "`n") -match "\.lmh_buffers\s+NOBITS") ".lmh_buffers is not NOBITS/NOLOAD."

$elfInfo = Get-Item -LiteralPath $elfFile
$mapInfo = Get-Item -LiteralPath $mapFile
Assert-StageE ($mapInfo.LastWriteTimeUtc -ge $elfInfo.LastWriteTimeUtc) "Linker map is older than the ELF; rebuild with -Wl,-Map."
Assert-StageE ($elfInfo.Length -lt 5MB) "ELF unexpectedly contains the large weight payload."

Write-Output "STAGE_E_VERIFY_BEGIN"
Write-Output ("runtime_end=0x{0:X}" -f $runtimeEnd)
foreach ($buffer in $buffers) {
    Write-Output ("{0}=0x{1:X}-0x{2:X} bytes={3}" -f
        $buffer.Name, $buffer.Start, $buffer.End, ($buffer.End - $buffer.Start))
}
Write-Output ("buffers_end=0x{0:X}" -f $buffersEnd)
Write-Output ("ddr_limit=0x{0:X}" -f $ddrLimit)
Write-Output ("elf_bytes={0}" -f $elfInfo.Length)
Write-Output "alignment=PASS"
Write-Output "sizes=PASS"
Write-Output "overlap=PASS"
Write-Output "noload=PASS"
Write-Output "STAGE_E_VERIFY_PASS"

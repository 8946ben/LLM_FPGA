$ErrorActionPreference = "Stop"

# 2026-07-24 zb: deterministic Stage F static/build verification.
$root = "D:\program\LLM_FPGA"
$appRoot = Join-Path $root "realFpga\vitis\workspace\lm_head_net_diag"
$debugDir = Join-Path $appRoot "Debug"
$sourceFile = Join-Path $appRoot "src\lwip_lm_head_raw_server.c"
$elfFile = Join-Path $debugDir "lm_head_net_diag.elf"
$mapFile = Join-Path $debugDir "lm_head_net_diag.map"
$nm = "D:\install\Xilinx\Vitis\2021.1\gnu\aarch64\nt\aarch64-none\bin\aarch64-none-elf-nm.exe"
$exportLwipOpts = Join-Path $root "realFpga\vitis\workspace\lm_head_axu9eg_platform\export\lm_head_axu9eg_platform\sw\lm_head_axu9eg_platform\standalone_domain\bspinclude\include\lwipopts.h"
$phyTarget = Join-Path $root "realFpga\vitis\workspace\lm_head_axu9eg_platform\psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0\libsrc\lwip211_v1_5\src\contrib\ports\xilinx\netif\xemacpsif_physpeed.c"
$phyReference = Join-Path $root "ref\xemacpsif_physpeed.c"

function Assert-StageF {
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

foreach ($path in @(
    $sourceFile,
    $elfFile,
    $mapFile,
    $nm,
    $exportLwipOpts,
    $phyTarget,
    $phyReference
)) {
    Assert-StageF (Test-Path -LiteralPath $path) "Required Stage F file is missing: $path"
}

$stageEOutput = & (Join-Path $root "realFpga\vitis\verify_stage_e.ps1")
Assert-StageF ($stageEOutput -contains "STAGE_E_VERIFY_PASS") "Stage E DDR/map regression failed."

$source = Get-Content -LiteralPath $sourceFile -Raw
foreach ($marker in @(
    "LMH_OPCODE_LOAD_WEIGHT",
    "LMH_OPCODE_RUN_TOKEN",
    "LMH_OPCODE_PING",
    "crc32_update",
    "Xil_DCacheFlushRange",
    "Xil_DCacheInvalidateRange",
    "XLm_head_argmax_Initialize",
    "XLm_head_argmax_Start",
    "XLm_head_argmax_IsDone",
    "tcp_accept",
    "tcp_recv",
    "tcp_sent"
)) {
    Assert-StageF ($source.Contains($marker)) "Server source is missing marker: $marker"
}

$lwipOpts = Get-Content -LiteralPath $exportLwipOpts -Raw
Assert-StageF ($lwipOpts -match "#define\s+MEM_SIZE\s+262144") "MEM_SIZE is not 262144."
Assert-StageF ($lwipOpts -match "#define\s+MEMP_NUM_TCP_SEG\s+512") "MEMP_NUM_TCP_SEG is not 512."
Assert-StageF ($lwipOpts -match "#define\s+PBUF_POOL_SIZE\s+256") "PBUF_POOL_SIZE is not 256."
Assert-StageF ($lwipOpts -match "#define\s+TCP_SND_BUF\s+32768") "TCP_SND_BUF is not 32768."
Assert-StageF ($lwipOpts -match "#define\s+TCP_WND\s+32768") "TCP_WND is not 32768."

$targetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $phyTarget).Hash
$referenceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $phyReference).Hash
Assert-StageF ($targetHash -eq $referenceHash) "AXU9EGB PHY patch differs from the colleague-provided reference."

$undefined = @(& $nm -u $elfFile)
Assert-StageF ($LASTEXITCODE -eq 0) "nm failed while checking undefined symbols."
Assert-StageF ($undefined.Count -eq 0) "ELF contains undefined symbols: $($undefined -join ', ')"

$symbols = (& $nm $elfFile) -join "`n"
foreach ($symbol in @(
    "XLm_head_argmax_Initialize",
    "XLm_head_argmax_Start",
    "XLm_head_argmax_IsDone",
    "XLm_head_argmax_Set_hidden",
    "XLm_head_argmax_Set_weight",
    "XLm_head_argmax_Get_selected_token",
    "XLm_head_argmax_Get_selected_score"
)) {
    Assert-StageF ($symbols -match [regex]::Escape($symbol)) "Linked ELF is missing HLS symbol: $symbol"
}

$elfInfo = Get-Item -LiteralPath $elfFile
$mapInfo = Get-Item -LiteralPath $mapFile
Assert-StageF ($mapInfo.LastWriteTimeUtc -ge $elfInfo.LastWriteTimeUtc) "Map is older than the ELF."
Assert-StageF ($elfInfo.LastWriteTimeUtc -ge (Get-Item -LiteralPath $sourceFile).LastWriteTimeUtc) "ELF is older than the LMH1 server source."

Write-Output "STAGE_F_VERIFY_BEGIN"
Write-Output "lmh1_source=PASS"
Write-Output "streaming_weight_rx=PASS"
Write-Output "segmented_tcp_tx=PASS"
Write-Output "cache_sync_calls=PASS"
Write-Output "hls_driver_symbols=PASS"
Write-Output "undefined_symbols=0"
Write-Output "lwip_mem_size=262144"
Write-Output "lwip_tcp_snd_buf=32768"
Write-Output "lwip_tcp_wnd=32768"
Write-Output "lwip_memp_num_tcp_seg=512"
Write-Output "phy_patch_sha256=$targetHash"
Write-Output "elf_bytes=$($elfInfo.Length)"
Write-Output "STAGE_F_VERIFY_PASS"

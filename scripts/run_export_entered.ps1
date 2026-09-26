# تشغيل تصدير أرقام المسجّلين إلكترونياً يلي دخلوا الجامعة (مرة على الأقل).
# نفس فكرة run_export.ps1 بس بيصدّر export_registered_entered.py.
#
# الاستخدام:
#     powershell -ExecutionPolicy Bypass -File scripts\run_export_entered.ps1

$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "export_registered_entered.py"
if (-not (Test-Path -LiteralPath $script)) {
    Write-Host "✗ ما لقيت السكريبت: $script" -ForegroundColor Red
    exit 2
}

$adminUser = Read-Host "اسم المستخدم الأدمن"
if ([string]::IsNullOrWhiteSpace($adminUser)) {
    Write-Host "✗ اسم المستخدم فاضي — وقفنا" -ForegroundColor Red
    exit 2
}

$secure = Read-Host "كلمة السر" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $env:WJ_API_USER = $adminUser
    $env:WJ_API_PASS = $plain
    python $script
    $code = $LASTEXITCODE
}
finally {
    if ($ptr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) | Out-Null
    }
    $plain = $null
    Remove-Item Env:\WJ_API_PASS -ErrorAction SilentlyContinue
}

if ($code -eq 0) {
    Write-Host ""
    Write-Host "✓ خلص — الملف بمجلد exports/ بجذر المشروع" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ فشل التشغيل (exit $code)" -ForegroundColor Red
}
exit $code

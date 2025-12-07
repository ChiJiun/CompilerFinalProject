Write-Host "Starting Mini-LISP Test Suite..." -ForegroundColor Cyan
Write-Host "================================"

$files = Get-ChildItem "public_test_data\*.lsp" | Sort-Object Name

foreach ($file in $files) {
    Write-Host "Running $($file.Name)..." -ForegroundColor Yellow
    
    # 執行直譯器並傳入檔案路徑
    $output = & .\minilisp.exe $file.FullName
    
    # 顯示輸出結果
    $output
    
    Write-Host "--------------------------------"
}

Write-Host "All tests completed." -ForegroundColor Cyan

$filePath = "A:\nexus\data.js"
if (Test-Path $filePath) {
    $content = Get-Content $filePath -Raw -Encoding UTF8
    
    # We want to match: var DB = { ... };
    if ($content -match 'var\s+DB\s*=\s*(\{[\s\S]*\})\s*;') {
        $jsonStr = $Matches[1]
        Write-Host "Parsing JSON wrapper..."
        $jsonObj = ConvertFrom-Json $jsonStr
        
        if ($jsonObj.value -ne $null) {
            Write-Host "Found 'value' property. Re-serializing as top-level array..."
            $arrayStr = ConvertTo-Json $jsonObj.value -Depth 100
            $newContent = "var DB = " + $arrayStr + ";"
            [System.IO.File]::WriteAllText($filePath, $newContent, [System.Text.Encoding]::UTF8)
            Write-Host "Success! data.js corrected to array." -ForegroundColor Green
        } else {
            Write-Host "JSON parsed but 'value' property not found. data.js is probably already in correct array format." -ForegroundColor Yellow
        }
    } else {
        Write-Host "No match found for JSON wrapper." -ForegroundColor Yellow
    }
} else {
    Write-Error "File data.js not found!"
}

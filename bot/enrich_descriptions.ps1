$dbPath = "A:\nexus\data.js"
$dictPath = "A:\nexus\bot\enrichment_data.json"

if ((Test-Path $dbPath) -and (Test-Path $dictPath)) {
    Write-Host "Reading data from $dictPath..."
    $dictContent = Get-Content $dictPath -Raw -Encoding UTF8
    $dict = ConvertFrom-Json $dictContent
    
    $fb = $dict.'__fallback__'
    
    Write-Host "Reading data from $dbPath..."
    $dbContent = Get-Content $dbPath -Raw -Encoding UTF8
    
    if ($dbContent -match "var\s+DB\s*=\s*(\[[\s\S]*\])\s*;") {
        $jsonStr = $Matches[1]
        $db = ConvertFrom-Json $jsonStr
        
        $enrichedCount = 0
        
        foreach ($entry in $db) {
            $title = $entry.title.Trim().ToLower()
            
            $found = $null
            # Check dictionary keys
            foreach ($key in $dict.psobject.Properties.Name) {
                if ($key -ne "__fallback__" -and $title -like "*$key*") {
                    $found = $dict.$key
                    break
                }
            }
            
            $desc = $null
            $genres = $null
            $rating = $null
            
            if ($found -ne $null) {
                $desc = $found.desc
                $genres = $found.genres
                $rating = $found.rating
            }
            
            # Apply fallbacks
            if ($desc -eq $null) {
                $isPlaceholder = $false
                if ($entry.desc -eq $null -or $entry.desc -eq "") {
                    $isPlaceholder = $true
                } elseif ($entry.desc -like "*اكتشف*" -or $entry.desc -like "*قصة*") {
                    $isPlaceholder = $true
                } elseif ($entry.desc.Length -lt 50) {
                    $isPlaceholder = $true
                }
                
                if ($isPlaceholder) {
                    $desc = $fb.desc
                }
            }
            
            if ($genres -eq $null) {
                if ($entry.genres -eq $null -or $entry.genres.Count -eq 0) {
                    $genres = $fb.genres
                }
            }
            
            if ($rating -eq $null) {
                if ($entry.rating -eq $null -or $entry.rating -eq "") {
                    $rating = $fb.rating
                }
            }
            
            # Apply changes
            if ($desc -ne $null) {
                $entry | Add-Member -MemberType NoteProperty -Name "desc" -Value $desc -Force
                $entry.desc = $desc
                $enrichedCount++
            }
            if ($genres -ne $null) {
                $entry | Add-Member -MemberType NoteProperty -Name "genres" -Value $genres -Force
                $entry.genres = $genres
            }
            if ($rating -ne $null) {
                $entry | Add-Member -MemberType NoteProperty -Name "rating" -Value $rating -Force
                $entry.rating = $rating
            }
        }
        
        Write-Host "Saving back enriched data.js..."
        $newJsonStr = ConvertTo-Json $db -Depth 100
        $newContent = "var DB = " + $newJsonStr + ";"
        [System.IO.File]::WriteAllText($dbPath, $newContent, [System.Text.Encoding]::UTF8)
        Write-Host "🎉 Enrichment completed successfully! Enriched $enrichedCount works." -ForegroundColor Green
    } else {
        Write-Error "Failed to match var DB = [...];"
    }
} else {
    Write-Error "Required files not found!"
}

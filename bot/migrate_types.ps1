$filePath = "A:\nexus\data.js"
if (Test-Path $filePath) {
    Write-Host "Reading data.js..."
    $content = Get-Content $filePath -Raw -Encoding UTF8
    
    if ($content -match "var\s+DB\s*=\s*(\[[\s\S]*\])\s*;") {
        $jsonStr = $Matches[1]
        Write-Host "Parsing JSON database..."
        
        # Convert JSON safely
        $db = ConvertFrom-Json $jsonStr
        
        $mangaCount = 0
        $comicsCount = 0
        $manhwaCount = 0
        $novelsCount = 0
        
        $mangaTitles = @("one piece", "one piece (official colored)", "ichigo mashimaro", "yuukoku no moriarty", "time of the blind beast", "one piece (translated demo)")
        $comicsTitles = @("martial peak", "apotheosis", "magic emperor", "demonic emperor", "apocalypse sword god", "my simulated path to immortality", "global horror: start with trillions of coins", "logging 10.000 years into the future", "catastrophic necromancer")
        
        foreach ($entry in $db) {
            $title = $entry.title.Trim().ToLower()
            $genres = @()
            if ($entry.genres -ne $null) {
                foreach ($g in $entry.genres) {
                    $genres += $g.ToLower()
                }
            }
            
            $isNovel = $false
            if ($title -like "*novel*" -or $title -like "*رواية*") {
                $isNovel = $true
            }
            foreach ($g in $genres) {
                if ($g -like "*novel*" -or $g -like "*رواية*") { $isNovel = $true }
            }
            
            $isManga = $false
            foreach ($mt in $mangaTitles) {
                if ($title -like "*$mt*") { $isManga = $true }
            }
            foreach ($g in $genres) {
                if ($g -eq "manga" -or $g -eq "japanese" -or $g -eq "مانجا" -or $g -eq "يابانية") { $isManga = $true }
            }
            
            $isComics = $false
            foreach ($ct in $comicsTitles) {
                if ($title -like "*$ct*") { $isComics = $true }
            }
            foreach ($g in $genres) {
                if ($g -eq "manhua" -or $g -eq "chinese" -or $g -eq "مانها" -or $g -eq "صينية" -or $g -eq "comics" -or $g -eq "كوميكس") { $isComics = $true }
            }
            
            if ($isNovel) {
                $entry | Add-Member -MemberType NoteProperty -Name "type" -Value "novels" -Force
                $entry.type = "novels"
                $novelsCount++
            } elseif ($isManga) {
                $entry | Add-Member -MemberType NoteProperty -Name "type" -Value "manga" -Force
                $entry.type = "manga"
                $mangaCount++
            } elseif ($isComics) {
                $entry | Add-Member -MemberType NoteProperty -Name "type" -Value "comics" -Force
                $entry.type = "comics"
                $comicsCount++
            } else {
                $entry | Add-Member -MemberType NoteProperty -Name "type" -Value "manhwa" -Force
                $entry.type = "manhwa"
                $manhwaCount++
            }
        }
        
        Write-Host "Serializing and saving back to data.js..."
        # depth 100 to ensure chapters are fully preserved
        $newJsonStr = ConvertTo-Json $db -Depth 100
        
        $newContent = "var DB = " + $newJsonStr + ";"
        
        # Write UTF8 without BOM for clean web usage
        [System.IO.File]::WriteAllText($filePath, $newContent, [System.Text.Encoding]::UTF8)
        
        Write-Host ""
        Write-Host "🎉 Migration completed successfully!" -ForegroundColor Green
        Write-Host "  - Manhwa (Korean): $manhwaCount"
        Write-Host "  - Manga (Japanese): $mangaCount"
        Write-Host "  - Comics/Manhua (Chinese): $comicsCount"
        Write-Host "  - Novels (Translated): $novelsCount"
    } else {
        Write-Error "Failed to parse var DB = [...]; from data.js"
    }
} else {
    Write-Error "File data.js not found at $filePath"
}

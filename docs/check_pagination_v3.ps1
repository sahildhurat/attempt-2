$Categories = @(
    @{ Name="Search"; Id="photos_searching" },
    @{ Name="Organisation"; Id="photos_organize" },
    @{ Name="Albums"; Id="photos_albums" },
    @{ Name="Manage"; Id="photos_manage" },
    @{ Name="Sharing"; Id="photos_sharing" },
    @{ Name="Storage"; Id="photos_storage" }
)

$OutFile = "d:\Attempt 2\docs\pagination_results.txt"
"Category        | Max Results Req | Unique Threads | View More? | Oldest Date" | Out-File $OutFile -Encoding utf8

foreach ($Cat in $Categories) {
    foreach ($Max in @(500, 1000, 2000, 5000)) {
        $Url = "https://support.google.com/photos/threads?hl=en&thread_filter=(category%3A$($Cat.Id))&max_results=$Max"
        try {
            $Html = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 60 | Select-Object -ExpandProperty Content
            
            $Matches = [regex]::Matches($Html, 'data-stats-id="(\d+)"')
            $UniqueThreads = ($Matches | % { $_.Groups[1].Value } | Sort-Object -Unique).Count
            
            $HasMore = $Html -match "load-more-button"
            
            $DateMatches = [regex]::Matches($Html, 'class="thread-list-group__heading"[^>]*>([^<]+)<')
            $OldestDate = "N/A"
            if ($DateMatches -ne $null -and $DateMatches.Count -gt 0) {
                $OldestDate = $DateMatches[$DateMatches.Count - 1].Groups[1].Value.Trim()
            }
            
            $Result = "$($Cat.Name.PadRight(15)) | $($Max.ToString().PadRight(15)) | $($UniqueThreads.ToString().PadRight(14)) | $($HasMore.ToString().PadRight(10)) | $OldestDate"
            $Result | Out-File -Append $OutFile -Encoding utf8
            
            if (-not $HasMore -or $UniqueThreads -eq 0) {
                break
            }
        } catch {
            "$($Cat.Name.PadRight(15)) | $Max | ERROR | $_" | Out-File -Append $OutFile -Encoding utf8
        }
    }
}

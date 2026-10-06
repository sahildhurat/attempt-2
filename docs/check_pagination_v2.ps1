$Categories = @(
    @{ Name="Search"; Id="photos_searching" },
    @{ Name="Organisation"; Id="photos_organize" },
    @{ Name="Albums"; Id="photos_albums" }
)

$OutFile = "d:\Attempt 2\docs\pagination_results.txt"
"Category        | Max Results Req | Unique Threads | View More? | Oldest Date" | Out-File $OutFile

foreach ($Cat in $Categories) {
    foreach ($Max in @(500, 1000, 5000)) {
        $Url = "https://support.google.com/photos/threads?hl=en&thread_filter=(category%3A$($Cat.Id))&max_results=$Max"
        try {
            $Html = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 60 | Select-Object -ExpandProperty Content
            
            # Count unique thread IDs
            $Matches = [regex]::Matches($Html, 'data-stats-id="(\d+)"')
            $UniqueThreads = ($Matches | % { $_.Groups[1].Value } | Sort-Object -Unique).Count
            
            $HasMore = $Html -match "load-more-button"
            
            # Find dates (look for thread-list-thread__snippet or similar, but the prompt asks for "oldest created_at date you can reach"
            # We can grab the last thread's time or the last date group.
            # In Google Forums SSR, dates are usually in "thread-list-group__heading" or inside the thread.
            $DateMatches = [regex]::Matches($Html, 'class="thread-list-group__heading"[^>]*>([^<]+)<')
            $OldestDate = if ($DateMatches.Count -gt 0) { $DateMatches[-1].Groups[1].Value.Trim() } else { "N/A" }
            
            $Result = "$($Cat.Name.PadRight(15)) | $($Max.ToString().PadRight(15)) | $($UniqueThreads.ToString().PadRight(14)) | $($HasMore.ToString().PadRight(10)) | $OldestDate"
            $Result | Out-File -Append $OutFile
            
            if (-not $HasMore) {
                break
            }
        } catch {
            "$($Cat.Name.PadRight(15)) | $Max | ERROR | $_" | Out-File -Append $OutFile
        }
    }
}

$Categories = @(
    @{ Name="Search"; Id="photos_searching" },
    @{ Name="Organisation"; Id="photos_organize" },
    @{ Name="Albums"; Id="photos_albums" },
    @{ Name="Manage"; Id="photos_manage" },
    @{ Name="Sharing"; Id="photos_sharing" },
    @{ Name="Storage"; Id="photos_storage" }
)

Write-Host "Category        | Count | View More?"
Write-Host "----------------------------------------"

foreach ($Cat in $Categories) {
    $Url = "https://support.google.com/photos/threads?hl=en&thread_filter=(category%3A$($Cat.Id))&max_results=500"
    Write-Host "Fetching $($Cat.Name)..." -NoNewline
    
    try {
        $Html = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15 | Select-Object -ExpandProperty Content
        $ThreadCount = ([regex]::Matches($Html, "thread-list-thread__title")).Count
        $HasMore = $Html -match "load-more-button"
        
        Write-Host "`r$($Cat.Name.PadRight(15)) | $($ThreadCount.ToString().PadRight(5)) | $HasMore"
    } catch {
        Write-Host "`r$($Cat.Name.PadRight(15)) | ERROR | $_"
    }
}

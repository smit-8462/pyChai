# pyChai install script
 
$ExtensionName = "pyChai"
$RepoUrl       = "https://github.com/smit-8462/pyChai.git"
$Branch        = "main"
$PythonPackagesZipName = "python-packages-site-packages.zip"
$ExtensionPath = "$($env:APPDATA)\pyRevit\Extensions\$($ExtensionName).extension"
$ZipPath = "$($ExtensionPath)\bin\python_package_zip\$($PythonPackagesZipName)"
# $NotNeededFolderList = @("assets", "docs", "bin", "scripts")
 
pyrevit extend ui $ExtensionName $RepoUrl --branch=$Branch

if ($LASTEXITCODE -eq 0) {
    Write-Host "$($ExtensionName) installed successfully."

    Write-Host "Extracting Python packages dependency..."

    if (Test-Path $ExtensionPath) {
        # Extracting ZIP
        Expand-Archive -Path $ZipPath -DestinationPath $ExtensionPath -Force
        Write-Host "ZIP contents extracted successfully."

        # # Removing unnecessary files
        # foreach ($folderName in $NotNeededFolderList) {
        #     <# $folderName is the current item #>
        #     $folderPath = "$($ExtensionPath)\$($folderName)"
        #     if (Test-Path $folderPath) {
        #         Remove-Item -Path $folderPath -Recurse -Force
        #     }
        # }

        Write-Host "Congratulations🎊! pyChai extension is installed successfully."
    }
    else {
        Write-Host "$($ExtensionName) is not installed correctly."
    }
}
else {
    Write-Host "Installation failed. pyRevit is not installed."
}

# pyChai install script
 
$ExtensionName = "pyChai"
$RepoUrl       = "https://github.com/smit-8462/pyChai.git"
$Branch        = "main"
$PythonPackagesZipName = "python-packages-site-packages.zip"
$ExtensionPath = "$($env:APPDATA)\pyRevit\Extensions\$($ExtensionName).extension"
$ZipPath = "$($ExtensionPath)\bin\python_package_zip\$($PythonPackagesZipName)"
$SitePackagesPath = "$($ExtensionPath)\site-packages"
 
pyrevit extend ui $ExtensionName $RepoUrl --branch=$Branch

if ($LASTEXITCODE -eq 0) {
    Write-Host "$($ExtensionName) installed successfully."

    Write-Host "Extracting Python packages dependency..."

    if (Test-Path $ExtensionPath) {
        # Check if folder path exists, if not then create folder
        if (-not (Test-Path $SitePackagesPath)) {
            Write-Host "Folder missing!!!"
            New-Item -ItemType Directory -Path $SitePackagesPath | Out-Null
            Write-Host "Folder created successfully at path = $($SitePackagesPath)"
        }

        # Extracting ZIP
        Expand-Archive -Path $ZipPath -DestinationPath $SitePackagesPath -Force
        Write-Host "ZIP contents extracted successfully at path = $($SitePackagesPath)"

        Write-Host "Congratulations🎊! pyChai extension is installed successfully."
    }
    else {
        Write-Host "$($ExtensionName) is not installed correctly."
    }
}
else {
    Write-Host "Installation failed. pyRevit is not installed."
}

# This script updates an Emby server running in the Windows portable mode.
# Portable mode is easier to backup without having to re-match users and emails.

# Elevate the script if not run as admin
if (-Not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    if ([int](Get-CimInstance -Class Win32_OperatingSystem | Select-Object -ExpandProperty BuildNumber) -ge 6000) {
     $CommandLine = "-File `"" + $MyInvocation.MyCommand.Path + "`" " + $MyInvocation.UnboundArguments
     Start-Process -FilePath PowerShell.exe -Verb Runas -ArgumentList $CommandLine
     Exit
    }
   }
   
   # Set ErrorActionPreference for try-catch expressions
   $ErrorActionPreference = 'Stop'
   
   function Download-GitHubRelease {
       param(
           [string] $repo,
           [string] $filenamePattern
       )
   
       $releaseUri = "https://api.github.com/repos/$repo/releases"
       $downloadUri = ((Invoke-RestMethod -Method GET -Uri $releaseUri)[0].assets | Where-Object name -like $filenamePattern).browser_download_url
   
       $pathZip = Join-Path -Path $([System.IO.Path]::GetTempPath()) -ChildPath $(Split-Path -Path $downloadUri -Leaf)
       Invoke-WebRequest -Uri $downloadUri -Out $pathZip
   
       return $pathZip
   }
   
   # Ensure 7Zip4Powershell is installed
   try {
       Import-Module 7Zip4Powershell
   } catch {
       Write-Warning '7Zip4Powershell is not installed. Installing now...'
       Install-Module -Name 7Zip4Powershell -Force
       Import-Module 7Zip4Powershell
   }
   
   # Declare vars
   $installLocation = 'F:\Emby'
   $githubRepo = 'MediaBrowser/Emby.Releases'
   $serviceName = 'Emby Server'
   
   try {
       # Stop service so we can replace the files
       Stop-Service $serviceName
   
       # Remove the old system backup
       Remove-Item "$installLocation\system.bak" -Recurse
   
       # Create new system backup
       Move-Item "$installLocation\system" "$installLocation\system.bak"
   
       # Download and extract new system folder
       $zippedFile = Download-GitHubRelease -repo $githubRepo -filenamePattern 'embyserver-win-x64-*.7z'
       Expand-7Zip -ArchiveFileName $zippedFile -TargetPath $installLocation
   
       # Start the service again
       Start-Service $serviceName
   
   } catch {
       $_.exception.message
       Write-Warning 'Terminating Script'
       pause
       exit
   }
$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = $ws.CreateShortcut("$desktop\KeyClick.lnk")
$shortcut.TargetPath = (Get-Command python).Source
$shortcut.Arguments = "main.py"
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Description = "KeyClick - Keyboard to Mouse Mapper"
$shortcut.Save()
Write-Host "Shortcut created at $desktop\KeyClick.lnk"

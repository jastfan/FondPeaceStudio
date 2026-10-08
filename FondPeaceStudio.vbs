' FondPeace Studio — Silent Native Desktop App Launcher
' Runs launch_app.py silently without any black CMD console window

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Run python launch_app.py with hidden window (0)
WshShell.CurrentDirectory = currentDir
WshShell.Run "python """ & currentDir & "\launch_app.py""", 0, False

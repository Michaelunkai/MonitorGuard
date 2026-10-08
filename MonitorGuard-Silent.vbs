' ═══════════════════════════════════════════════════════════════════
' MonitorGuard — Silent Launcher (no console window)
' 
' Double-click this file to start MonitorGuard silently.
' The tray icon will appear in the system tray.
' Press Shift+S to toggle isolation, Shift+Q to quit.
'
' Project: F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard
' ═══════════════════════════════════════════════════════════════════

Set WshShell = CreateObject("WScript.Shell")

projectDir = "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard"

' Check if already running
Set fso = CreateObject("Scripting.FileSystemObject")
mainPy = projectDir & "\main.py"

If Not fso.FileExists(mainPy) Then
    MsgBox "MonitorGuard not found at:" & vbCrLf & vbCrLf & projectDir, vbCritical, "MonitorGuard"
    WScript.Quit 1
End If

' Launch Python silently (no console window)
' Use pythonw.exe for truly silent execution, or python.exe with window hidden
WshShell.CurrentDirectory = projectDir
WshShell.Run "pythonw.exe main.py", 0, False

' Brief pause to let it start
WScript.Sleep 1000

' Verify it started by checking for the process
Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colProcesses = objWMIService.ExecQuery("SELECT * FROM Win32_Process WHERE Name = 'pythonw.exe'")

found = False
For Each objProcess in colProcesses
    If InStr(objProcess.CommandLine, "main.py") > 0 Then
        found = True
        Exit For
    End If
Next

If Not found Then
    ' Fallback: try regular python with window hidden
    WshShell.Run "python.exe main.py", 0, False
End If

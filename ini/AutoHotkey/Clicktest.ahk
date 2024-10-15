#SingleInstance, Force
SendMode Input
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.


WinWait, HPD-TA 9 (High Performance Digital Temporal Analyzer)
WinActivate, HPD-TA 9 (High Performance Digital Temporal Analyzer)
; "Acquisition_Button"ボタンのハンドルを取得する
ControlGet, Acquisition_Button, Hwnd,, WindowsForms10.Window.8.app.0.378734a5, HPD-TA 9 (High Performance Digital Temporal Analyzer)
Sleep, 500
; "Acquisition_Button"ボタンをクリックする
ControlClick,, ahk_id %Acquisition_Button%
ExitApp
Return

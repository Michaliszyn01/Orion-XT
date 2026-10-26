APPS = {
    "notepad": {
        "aliases": ["notepad", "bloco de notas"],
        "paths": ["notepad.exe"],
        "process_names": ["notepad.exe"],
    },
    "calculadora": {
        "aliases": ["calculadora", "calc"],
        "paths": ["calc.exe"],
        "process_names": ["CalculatorApp.exe", "WinStore.App.exe", "calc.exe"],
    },
    "explorador": {
        "aliases": ["explorador", "explorador de arquivos"],
        "paths": ["explorer.exe"],
        "process_names": ["explorer.exe"],
    },
    "gerenciador de tarefas": {
        "aliases": ["gerenciador de tarefas", "task manager"],
        "paths": ["taskmgr.exe"],
        "process_names": ["Taskmgr.exe"],
    },
    "cmd": {
        "aliases": ["cmd", "prompt de comando"],
        "paths": ["cmd.exe"],
        "process_names": ["cmd.exe"],
    },
    "powershell": {
        "aliases": ["powershell"],
        "paths": ["powershell.exe"],
        "process_names": ["powershell.exe"],
    },
    "configurações": {
        "aliases": ["configurações", "configuracoes"],
        "paths": ["ms-settings:"],
        "process_names": [],
    },
    "steam": {
        "aliases": ["steam"],
        "paths": ["%ProgramFiles(x86)%/Steam/steam.exe"],
        "process_names": ["steam.exe"],
    },
    "spotify": {
        "aliases": ["spotify"],
        "paths": ["%LOCALAPPDATA%/Microsoft/WindowsApps/Spotify.exe"],
        "process_names": ["Spotify.exe"],
    },
    "chrome": {
        "aliases": ["chrome", "google chrome"],
        "paths": ["%ProgramFiles%/Google/Chrome/Application/chrome.exe"],
        "process_names": ["chrome.exe"],
    },
    "edge": {
        "aliases": ["edge", "microsoft edge"],
        "paths": ["msedge.exe"],
        "process_names": ["msedge.exe"],
    },
    "firefox": {
        "aliases": ["firefox"],
        "paths": ["firefox.exe"],
        "process_names": ["firefox.exe"],
    },
    "vscode": {
        "aliases": ["vscode", "vs code", "visual studio code"],
        "paths": ["%LOCALAPPDATA%/Programs/Microsoft VS Code/Code.exe"],
        "process_names": ["Code.exe"],
    },
    "discord": {
        "aliases": ["discord"],
        "paths": ["%LOCALAPPDATA%/Discord/Update.exe"],
        "process_names": ["Discord.exe", "Update.exe"],
        "launch_args": ["--processStart", "Discord.exe"],
    },
    "notion": {
        "aliases": ["notion"],
        "paths": [
            "%LOCALAPPDATA%/Programs/Notion/Notion.exe",
            "%APPDATA%/Notion/Notion.exe",
            "%LOCALAPPDATA%/Notion/Notion.exe",
        ],
        "process_names": ["Notion.exe"],
    },
    "excel": {
        "aliases": ["excel", "microsoft excel"],
        "paths": [
            "%ProgramFiles%/Microsoft Office/root/Office16/EXCEL.EXE",
            "%ProgramFiles(x86)%/Microsoft Office/root/Office16/EXCEL.EXE",
            "%ProgramFiles%/Microsoft Office/Office16/EXCEL.EXE",
            "%ProgramFiles(x86)%/Microsoft Office/Office16/EXCEL.EXE",
        ],
        "process_names": ["EXCEL.EXE"],
    },
    "word": {
        "aliases": ["word", "microsoft word"],
        "paths": [
            "%ProgramFiles%/Microsoft Office/root/Office16/WINWORD.EXE",
            "%ProgramFiles(x86)%/Microsoft Office/root/Office16/WINWORD.EXE",
            "%ProgramFiles%/Microsoft Office/Office16/WINWORD.EXE",
            "%ProgramFiles(x86)%/Microsoft Office/Office16/WINWORD.EXE",
        ],
        "process_names": ["WINWORD.EXE"],
    },
}
# X-UP

![X-UP Logo](static/icon.ico)

X-UP is a lightweight tool for [EVE Online](https://www.eveonline.com/) that helps players keep track of counts easily. It monitors log files in real time and updates a counter based on in-game events. The project is written in Python and compiled to a single executable using [Nuitka](https://nuitka.net/).

## Features

- **Real-Time Monitoring:** Watches fleet chat log files for (e.g., "x" patterns) and updates the counter accordingly.
- **In-Game Reset:** Resets the counter when dashes (`---`) are detected.
- **Dynamic Client Detection:** Uses Windows API (via ctypes) to list active EVE client windows.
- **GUI:** Built with Tkinter, the GUI automatically refreshes the available EVE clients and displays the current log file and count.
- **Standalone Executable:** Compiled with Nuitka to produce a single EXE with no external dependencies.


## Compiling with Nuitka

Since X-UP is compiled into a standalone executable using Nuitka, there are no runtime dependencies other than what is included in the build. You will need:

- Python 3.7+  
- [Nuitka](https://nuitka.net/)  
- A C compiler (e.g., Microsoft Visual Studio Build Tools)  

A sample PowerShell compile script (`compile.ps1`) is provided in the repository
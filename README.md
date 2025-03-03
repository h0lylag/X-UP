# X-UP

X-UP is a lightweight tool for [EVE Online](https://www.eveonline.com/) that helps players keep track of counts easily. It monitors log files in real time and updates a counter.

![X-UP Screenshot](https://i.imgur.com/1OHUkjW.png)

## Features

- **Real-Time Monitoring:** Instantly updates the counter when "x" is typed in fleet chat.
- **Quantity Recognition:** Accurately handles multipliers like "x25 conduit".
- **In-Game Reset:** Automatically resets the counter on detecting `---`.
- **Dynamic Client Detection:** Detects active EVE client windows using the Windows API.
- **GUI:** User-friendly interface with Tkinter showing current log file and count.
- **Standalone Executable:** Compiled with Nuitka, no extra dependencies.

## Compiling with Nuitka

Since X-UP is compiled into a standalone executable using Nuitka, there are no runtime dependencies other than what is included in the build. You will need:

- Python 3.7+  
- [Nuitka](https://nuitka.net/)  
- A C compiler (e.g., Microsoft Visual Studio Build Tools)  

A sample PowerShell compile script (`compile.ps1`) is provided in the repository
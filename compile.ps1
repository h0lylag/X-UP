# compile.ps1
# Configuration Variables
$ENTRY_POINT = "x-up.py"                          # Main entry script for the application
$ICON_PATH   = "static/icon.ico"                # Path to the icon file
$DATA_DIR    = "./static"                         # Directory to include as data
$DATA_DEST   = "static"                           # Destination folder name inside the executable
$OUTPUT_NAME = "x-up.exe"                         # Desired output executable name
$NUITKA_FLAGS = "--standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter"

# Display configuration
Write-Host "Compiling X-UP with Nuitka..."
Write-Host "Entry point: $ENTRY_POINT"
Write-Host "Icon path: $ICON_PATH"
Write-Host "Data directory: $DATA_DIR -> $DATA_DEST"
Write-Host "Output filename: $OUTPUT_NAME"
Write-Host "Nuitka flags: $NUITKA_FLAGS"
Write-Host ""

# Prepare additional flags with proper quoting
$includeDataFlag = "--include-data-dir=`"$DATA_DIR=$DATA_DEST`""
$windowsIconFlag = "--windows-icon-from-ico=`"$ICON_PATH`""
$outputFlag      = "--output-filename=`"$OUTPUT_NAME`""

# Build the full command string
$command = "nuitka $NUITKA_FLAGS $includeDataFlag $windowsIconFlag $outputFlag `"$ENTRY_POINT`""
Write-Host "Running command: $command"
Write-Host ""

# Execute the command
Invoke-Expression $command

# Check for errors
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nCompilation successful."
} else {
    Write-Host "`nCompilation failed." -ForegroundColor Red
    exit 1
}

# Advanced File System Recovery & Optimization Tool

A lightweight Windows GUI tool (PyQt5) for scanning, monitoring, recovering, and optimizing local file systems.

## Overview

This project provides a graphical application that:

- Scans drives for files and reports unused files
- Monitors a selected folder for file deletion events
- Recovers files from the Recycle Bin to a chosen recovery folder
- Runs basic storage optimization (invokes Windows Disk Cleanup)
- Displays real-time CPU and memory usage graphs

The main GUI is implemented in `project.py`. A small helper `filesystem_tool.py` prints a startup message.

## Requirements

All Python dependencies are listed in `requirements.txt`.

Key packages:

- `PyQt5` (GUI)
- `psutil` (system information)
- `pywin32` (Windows shell / Recycle Bin access)
- `watchdog` (filesystem events)
- `pyqtgraph` (graphs)

## Installation

1. (Recommended) Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running

Run the GUI application with:

```bash
python project.py
```

(There is a simple `filesystem_tool.py` that prints a message; the full GUI lives in `project.py`.)

## Usage

- Use the drive selector to choose a drive and click **Scan System** to scan files and list unused files.
- Use **Monitor Files** after selecting a folder to watch for deletions (logs appear in the output pane).
- **Recover Files** opens a folder chooser and moves items from the Recycle Bin to the selected folder.
- **Optimize Storage** triggers Windows Disk Cleanup (`cleanmgr /sagerun:1`).
- System Info tab shows CPU and memory usage graphs updated in real-time.

Notes:
- Recovering files requires access to the Windows Recycle Bin (Windows only).
- `cleanmgr` is a Windows tool — this feature only applies on Windows.

## Troubleshooting

- If PyQt5 or other packages fail to install, try upgrading `pip` first:

```bash
python -m pip install --upgrade pip
```

- If the app crashes on startup, run `python project.py` from a terminal to see traceback and missing-package errors.

## Contributing

Contributions and improvements are welcome. Open an issue or submit a pull request with clear descriptions and tests where appropriate.

## License

Specify a license here (e.g., MIT) or remove this section if unspecified.

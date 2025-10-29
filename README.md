# System Health Monitor

This repository contains a demo/educational Python-based monitor that tracks CPU, memory, and disk usage and sends alert emails when thresholds are exceeded. Treat it as a learning reference rather than production-ready software.

## How It Works
- Reads system metrics using the psutil library.
- Compares the metrics against thresholds defined in `config.json`.
- Sends an email alert when usage is higher than expected (configure an SMTP account such as Gmail with an app password).

## Local Setup
1. Create and activate a virtual environment (optional but recommended).
2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `config.example.json` to `config.json`, then edit the copy with your thresholds and email credentials. Do not commit real secrets.
4. Run the monitor from source:
   ```bash
   python -m agent.monitor
   ```

## Build Instructions
1. Install build tooling:
   ```bash
   pip install pyinstaller
   ```
2. Build a standalone executable:
   ```bash
   pyinstaller --onefile --name SystemHealthMonitor agent/monitor.py --add-data "config.example.json;."
   ```
   The executable appears in the `dist` folder.

## Installer
An Inno Setup script (`installer/SystemHealthMonitor.iss`) builds a Windows installer that registers the program as a Windows service using NSSM. Build it with:

```bash
ISCC.exe installer/SystemHealthMonitor.iss
```

## Uninstall
Use the generated uninstaller from the Control Panel, or run:

```powershell
scripts/uninstall_service.ps1
```

## Security Warning
Do not store passwords or app secrets in this repository. Use `config.example.json` as a template, keep real credentials local, and prefer provider-specific app passwords (for example, Gmail app passwords when using Gmail SMTP).

## Third-Party Licenses
Licensing notices for bundled tools and dependencies are recorded in `THIRD_PARTY_LICENSES.txt`. Review that file before redistributing binaries.

# Pratibha · ప్రతిభ

**A small, offline desktop journal for the moments away from your paper notebook.**

Pratibha is a companion to a paper journal: capture a quick thought, write down
something you want to work on, or remember a task. Open it, write, and get back
to your day. Your notes stay on your computer, with no account, cloud sync,
analytics, or AI services.

- **Journal:** a quiet plain-text notebook page with Date, Context, Location,
  and Time. Meaningful drafts autosave; **Finish entry** makes an entry read-only.
- **Insights:** your own observations and things to work on, with a **Worked on**
  checkbox you can undo.
- **Reminders:** one-time tasks shown as square cards. Complete one to fade it
  out and close the gap. View completed cards to reopen or clear them.
- **Calendar:** finished entries and reminders on their recorded or due dates,
  including completed reminders.
- **Appearance:** a dark, flat theme with a customizable accent color and locally
  bundled fonts. The Home title alternates between English and Telugu.
- **Optional entry passwords:** off by default; enable the toggle when creating
  an entry to encrypt its text, context, and location.

Built with Python, PySide6 Widgets, Python's `sqlite3`, and `cryptography`.

## Platforms and requirements

Pratibha runs from source; there is currently no packaged `.exe`, `.dmg`, or Linux
installer. Instructions below cover Windows, macOS, and Linux desktops. It is
not a mobile or browser app.

| Platform | Verification |
| --- | --- |
| Fedora Linux 42, Python 3.13, native Wayland | Tested, including GUI and offline checks |
| Other Linux desktop distributions | Installation guidance; not tested |
| Windows | Designed to be portable; not tested |
| macOS, Intel or Apple Silicon | Designed to be portable; not tested |

You need Python and a desktop environment supported by the installed PySide6
release. **Python 3.13** matches the version used for development. The code uses
Python 3.10+ features, but dependency support also depends on your Python version,
OS version, and processor architecture. Use a standard 64-bit Python build on
Windows. Do not copy a Linux `.venv` to another OS; create a new one there.

**Downloading the project and installing dependencies may need internet access.
Once installed, normal app use works offline.** SQLite and the fonts do not need
separate installation.

## Get the project

Choose either method:

- **Without Git:** open [the repository](https://github.com/Adi-Turaga/pratibha),
  select **Code → Download ZIP**, and extract it into a permanent folder.
  If the repository is private, sign in with a GitHub account that has access.
- **With Git:** authenticate to GitHub if needed, then run:

  ```bash
  git clone https://github.com/Adi-Turaga/pratibha.git
  cd pratibha
  ```

For every setup command below, first open a terminal **in the folder containing
`requirements.txt`**. The ZIP's extracted folder may be named `pratibha-main`.
Keep this folder after installation; it contains the app and its virtual environment.

## Install on Windows

1. Install **Python 3.13** from [python.org](https://www.python.org/downloads/windows/).
   Follow the [official Windows setup instructions](https://docs.python.org/3.13/using/windows.html)
   and include pip and the Python launcher. Open a new PowerShell window afterward.
2. Open the project folder in File Explorer, right-click an empty area, and choose
   **Open in Terminal**. Use a PowerShell tab.
3. Create the environment, install dependencies, and launch:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m pratibha
   ```

For later launches, run this from the project folder:

```powershell
.\.venv\Scripts\python.exe -m pratibha
```

No PowerShell activation script or execution-policy change is required. If `py`
is not recognized, check the Python installation and reopen your terminal.

For a double-click launcher, save the following as **`Launch Pratibha.bat`** beside
`requirements.txt` (ensure the filename does not end in `.txt`):

```bat
@echo off
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" -m pratibha
```

If that launcher fails silently, use the PowerShell command above to see errors.

## Install on macOS

1. Install **Python 3.13** using the macOS installer from
   [python.org](https://www.python.org/downloads/macos/). Follow the
   [official macOS setup instructions](https://docs.python.org/3.13/using/mac.html),
   including the installer's certificate setup instructions.
2. Open Terminal and change into your downloaded or cloned project folder.
3. Create the environment, install dependencies, and launch:

   ```bash
   python3.13 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python -m pratibha
   ```

For later launches, run this from the project folder:

```bash
.venv/bin/python -m pratibha
```

Use a Python installer matching your Mac; the official universal2 installer
supports both Intel and Apple Silicon. The selected dependency versions must
also support your macOS release.

## Install on Linux

Install Python, pip, and virtual-environment support using your distribution's
package manager. Choose the appropriate command:

**Fedora:**

```bash
sudo dnf install python3 python3-pip
```

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Arch Linux:**

```bash
sudo pacman -Syu python python-pip
```

On other distributions, install the equivalent packages. Then, from the project
folder, create the environment, install dependencies, and launch:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pratibha
```

For later launches, run this from the project folder:

```bash
.venv/bin/python -m pratibha
```

Run the app as your normal user, not with `sudo`. A desktop session is required
for normal use; the headless test mode below is for verification only.

If Qt reports missing X11/xcb libraries, these packages may be needed:

```bash
# Fedora
sudo dnf install libxcb xcb-util-cursor libxkbcommon-x11
```

```bash
# Ubuntu / Debian
sudo apt install libxcb-cursor0 libxkbcommon-x11-0
```

For other missing libraries, use the specific error message to find the matching
package for your distribution. See [Qt for Python setup](https://doc.qt.io/qtforpython-6/gettingstarted.html).

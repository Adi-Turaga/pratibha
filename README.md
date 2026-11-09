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

## Everyday use

Press **+** on Home to capture an entry. Context and location are optional; start
writing immediately if you prefer. The editor's first four lines contain date,
context, location, and local time in AM/PM format. Adjust them to record an earlier
moment. The rest of the page is yours.

Drafts save after a short pause and before leaving or closing the editor. Blank
new captures never appear in Journal. Use the **Journal** tab to return to drafts
or read finished entries. **Finish entry is final:** the text and metadata become
read-only, and the entry contributes to the Home count. Deleting an entry requires
confirmation.

Use **Insights** and **Reminders** from Home. Reminder cards are ordered by due
date/time, latest first, from left to right and top to bottom. **Show completed**
lets you reopen reminders; **Clear all completed** permanently deletes completed
reminders after confirmation and keeps open ones.

The top-right **calendar icon** opens Calendar; the **palette icon** changes the
accent color. Calendar markers distinguish finished journal entries from reminders.
Select a date to browse or create items for that day.

Keyboard controls include Tab / Shift+Tab, Ctrl+N for a new entry, and Ctrl+S to
save the current draft. Enter / Space activate buttons; Calendar supports arrow keys.

## Reminders and alerts

**Pratibha must be running to show alerts.** There is no background service or
scheduled OS alarm. Timed reminders show an in-app banner and, where supported,
a best-effort desktop notification. Desktop delivery and sound are not guaranteed.

The app checks at launch, every 15 seconds, and when it becomes active. The next
check after sleep catches missed reminders. Reminders that became due while the
app was closed appear overdue on reopening and missed timed reminders alert once.
Date-only reminders stay in Today throughout their due date, become overdue the
next day, and do not send timed alerts.

Alert state survives restart. Editing a title or completion state does not repeat
an alert; changing the due date or time makes the reminder eligible at its new
schedule. Reopening a completed reminder that never alerted makes it eligible;
reopening one that already alerted does not repeat it without rescheduling.
Timed alerts follow the current local wall clock, not a fixed worldwide instant.

## Privacy, passwords, and backups

Everything is stored locally. Click **Storage** at the bottom center to see the
exact SQLite database path. Qt chooses the per-user application data directory on
each OS; the database is outside the project folder. Appearance preferences are
stored in `appearance.ini` beside it.

Password protection is **per entry**, optional at creation, and off by default.
Protected text, context, and location use AES-256-GCM encryption with a fresh nonce
per save and a per-entry random salt for scrypt key derivation. Opening the entry
requires its password; leaving the editor locks it again. Passwords and encryption
keys are not saved to disk.

**There is no password recovery.** Recorded dates, times, and finished state remain
visible for Calendar and sorting. Unprotected entries, Insights, Reminders, and
calendar metadata are plaintext. Protection does not lock the whole application
or prevent confirmed deletion. Older backups of unprotected data remain unprotected.

Close Pratibha before copying `pratibha.sqlite3` for a backup; copy `appearance.ini`
as well if you want your color preference. There are no automatic backups or sync.
Use one running app instance per database. Local calendar dates remain stable across
restarts and system time-zone changes. Existing databases migrate automatically;
newer unsupported schema versions are rejected rather than modified.

## Updates

Close the app before updating. With a Git checkout, run `git pull` from the project
folder. With a ZIP download, extract the newer version into a folder and follow
setup again. Then reinstall dependencies using that platform's command above.
Your database remains in the per-user data directory. Back it up before updating.

## Checks and tested behavior

On Linux or macOS, from the project folder:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```

On Windows PowerShell:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:QT_QPA_PLATFORM
```

Tests use temporary databases. Omit the offscreen setting for native desktop GUI
checks. A POSIX time-zone-specific test skips on Windows.

**Verified on Fedora 42 with Python 3.13 and PySide6 6.12.0:** 22 tests passed,
covering draft recovery, read-only finished entries, date rendering, encryption,
schema migration, calendar grouping, reminder restart/rescheduling, card completion
and reflow, and clearing completed cards. The acceptance flow—capture, finish,
create a same-day reminder, see both in Calendar, and reopen—passed. Offline checks
ran in an isolated Linux network namespace, and GUI checks also ran on Wayland.

Windows, macOS, other Linux distributions, actual desktop notification delivery,
and real suspend/resume have not been verified. Catch-up behavior was checked with
simulated wall-clock times.

Bundled Varela Round and Noto Sans Telugu fonts include their SIL Open Font
Licenses under `pratibha/assets/fonts/`. All visual assets load locally.

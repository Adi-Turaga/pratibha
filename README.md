# Pratibha

A small offline desktop notebook for the moments away from your paper journal.
Python, PySide6 Widgets, and Python's built-in `sqlite3`. The interface uses flat
charcoal and muted purple tones, following the supplied notebook sketch's cover,
quick-capture dialog, and spacious writing page. The larger Home wordmark alternates between ప్రతిభ and Pratibha every five
seconds, retyping each version with a blinking cursor. Telugu syllables stay intact.
Buttons have rounded corners and subtle shadows; capture buttons are circular.
Varela Round is bundled locally for the interface, with Noto Sans Telugu for
the Telugu wordmark and Telugu text. Font files and their SIL Open Font Licenses
are in `pratibha/assets/fonts/`; no font downloads occur at runtime.

## Fedora setup and launch

From a terminal, install Python if needed:

```bash
sudo dnf install python3 python3-pip
```

Set up the project (these installation steps may require internet access):

```bash
cd /home/adi/pratibha
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Then launch:

```bash
cd /home/adi/pratibha
.venv/bin/python -m pratibha
```

After dependencies are installed, normal app use requires no internet access.
There are no accounts, remote fonts, cloud services, analytics, or AI features.
The reference photograph is not required at runtime.

If Qt reports a missing Linux platform library, install the matching Fedora Qt
runtime dependencies. For an X11/xcb error, the commonly needed packages are:

```bash
sudo dnf install libxcb xcb-util-cursor libxkbcommon-x11
```

## Using the notebook

- **Home:** larger Telugu wordmark, finished-entry count, centered, vertically stacked Insights
  and Reminders shortcuts, and **+**. Home and Journal appear in the top navigation. The top-right calendar icon opens Calendar;
  the palette icon beside it chooses an accent color, saved in `appearance.ini`
  beside the database. Use the Journal tab to browse entries. Capture location and
  descriptor are optional; select **Start writing** immediately to skip them.
- **Editor:** a minimal notebook page with four editable lines in order: date,
  descriptor, location, and time. The remaining page is a borderless plain-text
  writing area; Finish entry and save status sit below the page. Drafts save locally after a 600 ms pause and before navigation
  or closing. The status below the editor reports saving and errors. New blank
  captures, including metadata-only captures, are not stored. A draft is
  meaningful once it contains non-whitespace journal text.
- **Finish entry:** saves and returns Home. Finished entries are read-only,
  including their date, descriptor, location, and time. They can be opened for
  reading or deleted with confirmation, but cannot be edited or reopened as
  drafts. Drafts remain editable.
- **Password protection:** off by default in the capture dialog. Enable the
  iOS-style toggle and enter/confirm a password to protect that entry. Journal
  text, descriptor, and location are encrypted from the first autosave using
  AES-256-GCM with a fresh nonce for every save and a per-entry random salt for
  scrypt key derivation. Opening a protected draft or finished entry prompts for
  its password. Lists show a generic protected-entry label. The recorded date,
  time, and finished state remain visible for Calendar and sorting. Passwords
  and encryption keys are never written to disk. There is no password recovery;
  losing the password means losing access to that entry. Deletion still uses the
  normal confirmation. Protection applies per entry, not to Insights, Reminders,
  or the whole app. Close or leave the editor to lock a protected entry again.
- **Journal:** drafts and finished entries survive restart. Select an item and
  use **Open / edit selected**, or double-click it. Home offers **Continue latest
  draft**. Choose **Delete selected** for a confirmation before permanent deletion.
- **Insights:** write your own observations, edit them, and check **Worked on**.
  Uncheck it to reopen. Open items appear first. Deletion requires confirmation.
- **Reminders:** square cards in a responsive grid, sorted by due date/time
  descending, left to right and then top to bottom. Each card shows its title,
  due date, optional AM/PM time, and Overdue/Today/Upcoming status. Check
  **Complete** to save completion immediately, fade the card out, and animate
  the remaining cards into the gap. **Show completed** displays completed cards;
  uncheck one to reopen it. **Clear all completed** appears in this view and
  permanently removes completed reminders after confirmation, keeping open ones. Each card has Edit and Delete actions; deletion
  requires confirmation. Date-only reminders stay in Today all day and become
  overdue the following day. Timed reminders become overdue after their due minute.
- **Calendar:** choose a date in the month grid. A lavender circle marks finished
  journal entries; a tan square marks reminders. Below the grid are that date's
  finished entries and all reminders, including visibly completed reminders.
  Click an item or press Enter to open it. The two creation buttons use the
  selected date. New entries still default to the current local time.
- Keyboard: Tab / Shift+Tab traverse controls, Enter / Space activate buttons,
  Ctrl+N starts capture, and Ctrl+S saves the current entry. Calendar supports
  Qt's normal arrow-key navigation.

## Reminder behavior

**Pratibha must be running to show alerts.** There is no background daemon,
startup service, or operating-system scheduled alarm in v1. A timed reminder
shows an in-app banner, plus a best-effort desktop notification if Qt detects
system-tray notification support. Some desktops, including GNOME installations
without a tray extension, may show only the in-app banner. Dismissing the banner
does not complete the reminder; use its Completed checkbox.

The app checks at launch, every 15 seconds, and when it becomes active. The next
timer tick after sleep catches missed reminders. Missed timed reminders alert
once on reopening; they also appear in Overdue if their due time has passed.
Date-only reminders have no timed alert. No sound or notification delivery is
guaranteed by the desktop.

The alert flag is saved in SQLite when an alert is generated, so it does not
repeat after restart. Editing the title or completion state preserves that flag;
changing the due date or time resets it for the new schedule. Reopening a
completed reminder that has never alerted makes it eligible to alert; reopening
one that already alerted does not repeat it unless rescheduled. V1 uses the
current local wall clock for timed alerts, including after a time-zone change;
it is not a travel-aware or recurring alarm system.

## Local storage and portability

The app creates `pratibha.sqlite3` beneath Qt's per-user `AppDataLocation` with
organization and application name `Pratibha`. Click the small **Storage** button at the bottom center
for the exact database path on your machine. On Linux this is normally beneath
`~/.local/share/Pratibha/Pratibha/` (or `$XDG_DATA_HOME`). It is outside the source
folder and survives upgrades or removal of the virtual environment.

Journal recorded dates and reminder due dates are literal ISO calendar dates,
with separate local `HH:mm` values internally (displayed as AM/PM in the UI). They are never converted from UTC, so
calendar placement remains stable after restart or a system time-zone change.
Database operations live in `pratibha/storage.py`; widgets live in
`pratibha/app.py`. SQLite `PRAGMA user_version=2` adds optional per-entry protection, migrating
existing entries without changing their contents.
Newer unsupported schema versions are rejected rather than modified.

Close the app before copying the database for a backup. Unprotected entries, Insights, Reminders,
and calendar metadata use plaintext SQLite storage. Only entries created with
password protection enabled have encrypted text and private metadata. Backups
of older unprotected data remain unprotected. There are no automatic backups. Use one running instance per user database.

## Windows and macOS

Use Python 3.10 or later and a PySide6-supported OS/Python combination.
From the project directory in Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pratibha
```

On macOS, from the project directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pratibha
```

These platforms have launch guidance only; neither was tested. Code uses Qt's
portable widgets, paths, timers, and notification API, and no Linux-only runtime
commands.

## Verification

Database checks use the installed dependencies and temporary databases:

```bash
.venv/bin/python -m unittest discover -s tests -p test_storage.py -v
```

With dependencies installed, run the complete suite, including headless Qt GUI
smoke checks:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```

For a real desktop GUI run, omit `QT_QPA_PLATFORM=offscreen`. In PowerShell, set
`$env:QT_QPA_PLATFORM = 'offscreen'` before the test command if needed.

The tests cover draft recovery, blank captures, pending edits, finish/read-only/delete
counts, calendar grouping including completed reminders, stable dates across
TZ changes, insight lifecycle, date-only reminders, missed alerts, exact due
minutes, restart suppression, and rescheduling. The GUI acceptance check captures
and finishes text, creates a same-day reminder, checks Calendar markers/items,
and reopens the database in a new window. All GUI tests use temporary data.

**Actually verified in the build environment:** Fedora Linux 42, Python 3.13,
PySide6 6.12.0. All 22 tests passed (13 database checks and 9 GUI checks), with
networking disabled using a separate Linux network namespace. The nine GUI
checks also passed on the native Wayland desktop backend with networking
disabled. The capture → finish → same-day reminder → Calendar → reopen flow
passed using temporary data. Home, editor, and Calendar screenshots were
visually inspected at a 900 × 700 logical window size. Python compilation passed.

Dependencies were successfully installed into `.venv` after network permissions
were enabled. Desktop notification delivery and real suspend/resume remain
unverified; catch-up logic was tested with simulated wall-clock times. Windows
and macOS were not tested.

To repeat the isolated offline suite on Linux (where unprivileged user/network
namespaces are enabled):

```bash
unshare --user --map-root-user --net env QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```

Manual acceptance after installing dependencies:

1. Disconnect networking and launch the app.
2. Press **+**, skip metadata, write a short entry, and **Finish entry**.
3. Create a reminder for today; optionally give it a time one minute ahead.
4. Open **Calendar**, select today, and confirm both the entry and reminder.
5. Wait for the timed banner, then close and reopen the app. Verify both items
   persist and that the reminder does not alert again unless rescheduled.

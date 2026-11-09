"""Portable Qt Widgets interface; all persistence lives in storage.py."""
import sys
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QDate, QTime, QTimer, QStandardPaths, QObject, QEvent, QSize, QSettings
from PySide6.QtGui import QColor, QPainter, QIcon, QPixmap, QShortcut, QKeySequence, QFontDatabase, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QDialog, QFormLayout, QLineEdit, QPlainTextEdit,
    QDateEdit, QTimeEdit, QDialogButtonBox, QCheckBox, QListWidget,
    QListWidgetItem, QMessageBox, QCalendarWidget, QSystemTrayIcon, QFrame, QToolButton, QGraphicsDropShadowEffect, QColorDialog, QInputDialog,
)
from .storage import Store

STYLE = '''
QWidget { font-family: "Varela Round", "Noto Sans Telugu"; background: #211f29; color: #eae5f2; font-size: 15px; }
QMainWindow, QDialog { background: #211f29; }
QLabel#muted { color: #bcb3ca; font-size: 13px; }
QLabel#wordmark { font-family: "Noto Sans Telugu"; font-size: 104px; color: #ded0f6; }
QLabel#heading { font-size: 30px; }
QPushButton { background: #34303f; border: 1px solid #51485f; padding: 10px 17px; border-radius: 13px; }
QPushButton:hover { background: #443b54; }
QPushButton:focus, QLineEdit:focus, QPlainTextEdit:focus, QDateEdit:focus, QTimeEdit:focus, QListWidget:focus { border: 2px solid #c4a0ed; }
QPushButton#primary { background: #b493df; color: #241a32; font-weight: bold; }
QPushButton#capture { background: #b493df; color: #241a32; font-size: 36px; padding: 0; border-radius: 36px; }
QPushButton#calendarShortcut, QPushButton#colorShortcut { background: #b493df; color: #241a32; font-size: 25px; padding: 0; border-radius: 21px; }
QPushButton#storage { font-size: 13px; padding: 4px 12px; border-radius: 10px; }
QPushButton:pressed { background: #584869; }
QPlainTextEdit, QLineEdit, QDateEdit, QTimeEdit, QListWidget { background: #2a2633; border: 1px solid #51465e; padding: 8px; border-radius: 4px; selection-background-color: #615078; }
QPlainTextEdit { font-size: 18px; }
QListWidget::item { padding: 12px; border-bottom: 1px solid #42394e; }
QListWidget::item:selected { background: #51415f; }
QCalendarWidget QAbstractItemView { alternate-background-color: #34303f; background: #2a2633; selection-background-color: #615078; color: #eae5f2; }
QCalendarWidget QWidget#qt_calendar_navigationbar { background: #34303f; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #bcb3ca; border-radius: 4px; background: #2a2633; }
QCheckBox::indicator:checked { background: #b493df; border-color: #b493df; image: url("@CHECK_ICON@"); }
QCheckBox::indicator:hover { border: 2px solid #c4a0ed; }
QWidget#notebookPage { background: #2a2633; border-radius: 6px; }
QWidget#notebookPage QLabel { background: transparent; font-size: 15px; color: #bcb3ca; }
QWidget#notebookPage QLineEdit, QWidget#notebookPage QDateEdit, QWidget#notebookPage QTimeEdit { background: transparent; border: none; border-radius: 0; padding: 3px 0; font-size: 18px; }
QWidget#notebookPage QLineEdit:focus, QWidget#notebookPage QDateEdit:focus, QWidget#notebookPage QTimeEdit:focus { border-bottom: 1px solid #c4a0ed; }
QWidget#notebookPage QPlainTextEdit { background: transparent; border: none; padding: 0; }
QFrame#reminderCard { background: #34303f; border: 1px solid #51485f; border-radius: 14px; }
QFrame#reminderCard QLabel, QFrame#reminderCard QCheckBox { background: transparent; font-size: 13px; }
QFrame#reminderCard QLabel#reminderTitle { font-size: 17px; }
QFrame#reminderCard QPushButton { font-size: 13px; padding: 5px 8px; border-radius: 9px; }
QLabel#alert { background: #493753; color: #f0ddff; padding: 12px; }
'''

STYLE = STYLE.replace('@CHECK_ICON@', (Path(__file__).parent / 'assets' / 'check.svg').as_posix())


def accent_style(color):
    """Keep paper-dark surfaces and readable text while changing the accent hue."""
    hue, saturation, _ = color.getHslF()[:3]
    hue = max(0, hue)
    result = STYLE
    import re
    for value in set(re.findall(r'#[0-9a-f]{6}', STYLE)):
        original = QColor(value)
        replacement = QColor.fromHslF(hue, min(.8, original.hslSaturationF() * saturation / .54), original.lightnessF())
        if value == '#b493df':
            replacement = color
        if value == '#241a32':
            # WCAG relative luminance selects the more legible icon/button ink.
            rgb = [color.redF(), color.greenF(), color.blueF()]
            linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
            luminance = sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))
            replacement = QColor('#17141d' if luminance > .179 else '#ffffff')
        result = result.replace(value, replacement.name())
    return result


class AnimatedWordmark(QLabel):
    """Alternate languages every five seconds, revealing intact Telugu syllables."""
    VARIANTS = (('ప్ర', 'తి', 'భ'), tuple('Pratibha'))

    def __init__(self):
        super().__init__()
        self.setObjectName('wordmark')
        self.setAccessibleName('Pratibha · ప్రతిభ')
        self.variant = 0
        self.parts = self.VARIANTS[self.variant]
        self.revealed = 0
        self.cursor_visible = True
        self.timer = QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.language_timer = QTimer(self)
        self.language_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.language_timer.setInterval(5000)
        self.language_timer.timeout.connect(self.switch_language)
        self.language_timer.start()

    def title_font(self, variant):
        font = QFont(self.font())
        font.setFamily('Noto Sans Telugu' if variant == 0 else 'Varela Round')
        return font

    def sizeHint(self):
        # Reserve room for both languages so typing and switching never shift layout.
        metrics = [QFontMetrics(self.title_font(i)) for i in range(2)]
        width = max(m.horizontalAdvance(''.join(parts)) for m, parts in zip(metrics, self.VARIANTS))
        return QSize(width + 32, max(m.height() for m in metrics) + 24)

    def minimumSizeHint(self):
        return self.sizeHint()

    def switch_language(self):
        self.variant = 1 - self.variant
        self.parts = self.VARIANTS[self.variant]
        self.revealed = 0
        self.cursor_visible = True
        self.timer.start(300)
        self.update()

    def tick(self):
        if self.revealed < len(self.parts):
            self.revealed += 1
            if self.revealed == len(self.parts):
                self.timer.setInterval(550)
        else:
            self.cursor_visible = not self.cursor_visible
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        font = self.title_font(self.variant)
        painter.setFont(font)
        painter.setPen(self.palette().windowText().color())
        metrics = QFontMetrics(font)
        x = (self.width() - metrics.horizontalAdvance(''.join(self.parts))) // 2
        baseline = (self.height() - metrics.height()) // 2 + metrics.ascent()
        prefix = ''.join(self.parts[:self.revealed])
        painter.drawText(x, baseline, prefix)
        if self.cursor_visible:
            cursor_x = x + metrics.horizontalAdvance(prefix) + 6
            painter.drawLine(cursor_x, baseline - metrics.ascent(), cursor_x, baseline + 4)


class ButtonShadows(QObject):
    """Give application and Qt-created dialog/calendar buttons the same elevation."""
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Polish and isinstance(watched, (QPushButton, QToolButton)):
            if watched.graphicsEffect() is None:
                shadow = QGraphicsDropShadowEffect(watched)
                shadow.setBlurRadius(8)
                shadow.setOffset(0, 2)
                shadow.setColor(QColor(0, 0, 0, 85))
                watched.setGraphicsEffect(shadow)
        return super().eventFilter(watched, event)


def configure_theme(app):
    """Load bundled fonts without requiring network or system font installation."""
    fonts = Path(__file__).parent / 'assets' / 'fonts'
    for filename in ('VarelaRound-Regular.ttf', 'NotoSansTelugu.ttf'):
        QFontDatabase.addApplicationFont(str(fonts / filename))
    app.setFont(QFont('Varela Round', 11))
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    app._button_shadows = ButtonShadows(app)
    app.installEventFilter(app._button_shadows)


def button(text, callback, name=None):
    result = QPushButton(text)
    if name:
        result.setObjectName(name)
    if name == 'capture':
        result.setFixedSize(72, 72)
    elif name in ('calendarShortcut', 'colorShortcut'):
        result.setFixedSize(42, 42)
    if name == 'capture':
        result.setAccessibleName('Capture a new journal entry')
    result.clicked.connect(callback)
    return result


def label(text, name=None):
    result = QLabel(text)
    result.setWordWrap(True)
    if name:
        result.setObjectName(name)
    return result


def display_time(value):
    return QTime.fromString(value, 'HH:mm').toString('h:mm AP') if value else 'All day'


def entry_preview(row):
    if row['password_salt']:
        return 'Password-protected entry'
    return row['descriptor'] or row['body'][:90].replace('\n', ' ')


class PasswordSwitch(QCheckBox):
    """Keyboard-accessible toggle with a compact iOS-style track and thumb."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(52, 30)
        self.setAccessibleName('Password protect this entry')
        self.setToolTip('Password protect this entry')
        self.toggled.connect(lambda checked: self.update())

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.window().parentWidget().accent if self.isChecked() else QColor('#625c6c'))
        painter.drawRoundedRect(2, 3, 48, 24, 12, 12)
        painter.setBrush(QColor('#ffffff'))
        painter.drawEllipse(27 if self.isChecked() else 5, 6, 18, 18)
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QColor('#eae5f2'))
            painter.drawRoundedRect(0, 1, 51, 28, 14, 14)


def date_edit(day=None):
    result = QDateEdit(day or QDate.currentDate())
    result.setCalendarPopup(True)
    result.setDisplayFormat('yyyy-MM-dd')
    result.setAccessibleName('Date')
    return result


def time_edit(value=None):
    result = QTimeEdit(value or QTime.currentTime())
    result.setDisplayFormat('h:mm AP')
    result.setAccessibleName('Time')
    return result


def dialog_buttons(dialog, layout, save):
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)


class NotebookCalendar(QCalendarWidget):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.refresh_marks()

    def refresh_marks(self):
        self.entry_days = {r['day'] for r in self.store.rows('entries') if r['finished']}
        self.reminder_days = {r['day'] for r in self.store.rows('reminders')}
        self.updateCells()

    def paintCell(self, painter, rect, day):
        super().paintCell(painter, rect, day)
        key = day.toString('yyyy-MM-dd')
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        if key in self.entry_days:
            painter.setBrush(QColor('#c4a0ed'))
            painter.drawEllipse(rect.center().x() - 10, rect.bottom() - 8, 6, 6)
        if key in self.reminder_days:
            painter.setBrush(QColor('#d8ad7c'))
            painter.drawRect(rect.center().x() + 4, rect.bottom() - 8, 6, 6)
        painter.restore()


class Editor(QWidget):
    def __init__(self, window, row=None, day=None, location='', descriptor='', password=None):
        super().__init__()
        self.window = window
        self.password = password
        self.ident = row['id'] if row else None
        self.finished = bool(row['finished']) if row else False
        self.dirty = False
        self.loading = True
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 12, 30, 20)
        page = QWidget()
        page.setObjectName('notebookPage')
        paper = QVBoxLayout(page)
        paper.setContentsMargins(24, 20, 24, 24)
        paper.setSpacing(14)
        form = QFormLayout()
        form.setContentsMargins(4, 0, 4, 0)
        form.setVerticalSpacing(2)
        form.setHorizontalSpacing(16)
        self.day = date_edit(QDate.fromString(row['day'], 'yyyy-MM-dd') if row else day)
        self.time = time_edit(QTime.fromString(row['time'], 'HH:mm') if row else None)
        self.location = QLineEdit(row['location'] if row else location)
        self.descriptor = QLineEdit(row['descriptor'] if row else descriptor)
        self.location.setPlaceholderText('—')
        self.descriptor.setPlaceholderText('—')
        # Keep default spin-button geometry: Qt clips the inner text to 1 px
        # with NoButtons when the calendar popup is disabled for finished entries.
        self.time.setMinimumWidth(180)
        self.time.setMinimumHeight(34)
        self.descriptor.setAccessibleName('Context')
        self.location.setAccessibleName('Location')
        form.addRow('&Date', self.day)
        form.addRow('&Context', self.descriptor)
        form.addRow('&Location', self.location)
        form.addRow('&Time', self.time)
        paper.addLayout(form)
        self.body = QPlainTextEdit(row['body'] if row else '')
        self.body.setAccessibleName('Journal text')
        paper.addWidget(self.body, 1)
        layout.addWidget(page, 1)
        footer = QHBoxLayout()
        self.status = label('Finished · read-only' if self.finished else 'Draft · saved locally' if row else 'Start writing · drafts save automatically', 'muted')
        footer.addWidget(self.status, 1)
        self.finish_button = button('Finish entry', self.finish, 'primary')
        footer.addWidget(self.finish_button)
        layout.addLayout(footer)
        QWidget.setTabOrder(self.day, self.descriptor)
        QWidget.setTabOrder(self.descriptor, self.location)
        QWidget.setTabOrder(self.location, self.time)
        QWidget.setTabOrder(self.time, self.body)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(600)
        self.timer.timeout.connect(self.save)
        for signal in (self.body.textChanged, self.location.textChanged, self.descriptor.textChanged, self.day.dateChanged, self.time.timeChanged):
            signal.connect(self.changed)
        self.loading = False
        self.update_finish()

    def update_finish(self):
        self.finish_button.setVisible(not self.finished)
        self.body.setReadOnly(self.finished)
        for field in (self.day, self.time, self.location, self.descriptor):
            field.setReadOnly(self.finished)
        self.day.setCalendarPopup(not self.finished)

    def changed(self, *_):
        if self.loading or self.finished:
            return
        self.dirty = True
        self.status.setText('Saving…')
        self.timer.start()

    def save(self):
        self.timer.stop()
        if not self.dirty:
            return True
        try:
            if not self.body.toPlainText().strip():
                self.finished = False
                self.update_finish()
            self.ident = self.window.store.save_entry(self.ident, self.day.date().toString('yyyy-MM-dd'), self.time.time().toString('HH:mm'), self.location.text(), self.descriptor.text(), self.body.toPlainText(), self.finished, self.password)
        except Exception as error:
            self.status.setText('Could not save — your text is still in this window')
            QMessageBox.critical(self, 'Save failed', str(error))
            return False
        self.dirty = False
        self.status.setText(('Finished · ' if self.finished else 'Draft · ') + 'saved locally' if self.ident else 'Blank entry · nothing saved')
        return True

    def finish(self):
        if self.finished:
            return
        if not self.body.toPlainText().strip():
            QMessageBox.information(self, 'Write a little first', 'An entry needs some journal text before you can finish it.')
            return
        previous = self.finished
        self.finished = not self.finished
        self.dirty = True
        if not self.save():
            self.finished = previous
        self.update_finish()
        if self.finished:
            self.window.navigate('Home')


class Window(QMainWindow):
    def __init__(self, store, database_path):
        super().__init__()
        self.store = store
        self.database_path = str(database_path)
        self.appearance = QSettings(str(Path(database_path).with_name('appearance.ini')), QSettings.Format.IniFormat)
        self.accent = QColor(self.appearance.value('accent', '#b493df'))
        if not self.accent.isValid():
            self.accent = QColor('#b493df')
        QApplication.instance().setStyleSheet(accent_style(self.accent))
        self.setWindowTitle('Pratibha')
        self.resize(1000, 780)
        self.setMinimumSize(700, 580)
        self.editor = None
        self.current_view = 'Home'
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 16, 20, 16)
        nav = QHBoxLayout()
        for name in ('Home', 'Journal'):
            nav.addWidget(button(name, lambda checked=False, n=name: self.navigate(n)))
        nav.addStretch()
        calendar_shortcut = button('', lambda: self.navigate('Calendar'), 'calendarShortcut')
        calendar_shortcut.setIcon(QIcon(str(Path(__file__).parent / 'assets' / 'calendar.svg')))
        calendar_shortcut.setIconSize(QSize(24, 24))
        calendar_shortcut.setAccessibleName('Calendar')
        calendar_shortcut.setToolTip('Calendar')
        nav.addWidget(calendar_shortcut)
        color_shortcut = button('', self.choose_accent, 'colorShortcut')
        color_shortcut.setIcon(QIcon(str(Path(__file__).parent / 'assets' / 'palette.svg')))
        color_shortcut.setIconSize(QSize(24, 24))
        color_shortcut.setAccessibleName('Change accent color')
        color_shortcut.setToolTip('Change accent color')
        nav.insertWidget(nav.count() - 1, color_shortcut)
        self.theme_icons = (calendar_shortcut, color_shortcut)
        self.tint_theme_icons()
        layout.addLayout(nav)
        alert_bar = QHBoxLayout()
        self.alert = label('', 'alert')
        self.alert.setTextFormat(Qt.TextFormat.PlainText)
        self.alert.hide()
        self.dismiss = button('Dismiss alert', self.dismiss_alert)
        self.dismiss.hide()
        alert_bar.addWidget(self.alert, 1)
        alert_bar.addWidget(self.dismiss)
        layout.addLayout(alert_bar)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        footer = QHBoxLayout()
        footer.addStretch()
        storage_button = button('Storage', self.show_storage, 'storage')
        storage_button.setFixedSize(84, 30)
        footer.addWidget(storage_button)
        footer.addStretch()
        layout.addLayout(footer)
        self.statusBar().hide()
        icon = QPixmap(32, 32)
        icon.fill(QColor('#b493df'))
        self.setWindowIcon(QIcon(icon))
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip('Pratibha')
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        self.alert_timer = QTimer(self)
        self.alert_timer.setInterval(15000)
        self.alert_timer.timeout.connect(self.check_reminders)
        self.alert_timer.start()
        self.last_day = QDate.currentDate()
        self.navigate('Home')
        QTimer.singleShot(0, self.check_reminders)
        QApplication.instance().applicationStateChanged.connect(self.application_state_changed)
        QShortcut(QKeySequence('Ctrl+N'), self, activated=self.capture)
        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.save_current)

    def tint_theme_icons(self):
        # Match icon ink to the chosen accent's button text color.
        import re
        ink = QColor(re.search(r'QPushButton#primary \{[^}]*color: (#[0-9a-f]+)', accent_style(self.accent)).group(1))
        for control, filename in zip(self.theme_icons, ('calendar.svg', 'palette.svg')):
            pixmap = QIcon(str(Path(__file__).parent / 'assets' / filename)).pixmap(24, 24)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), ink)
            painter.end()
            control.setIcon(QIcon(pixmap))

    def choose_accent(self):
        chosen = QColorDialog.getColor(self.accent, self, 'Choose an accent color')
        if chosen.isValid():
            self.accent = chosen
            QApplication.instance().setStyleSheet(accent_style(chosen))
            self.appearance.setValue('accent', chosen.name())
            self.appearance.sync()
            self.tint_theme_icons()

    def application_state_changed(self, state):
        if state == Qt.ApplicationState.ApplicationActive:
            self.check_reminders()

    @staticmethod
    def write_safely(parent, operation):
        try:
            operation()
            return True
        except Exception as error:
            QMessageBox.critical(parent, 'Could not save changes', str(error))
            return False

    def show_storage(self):
        QMessageBox.information(self, 'Local storage', 'SQLite database:\n' + self.database_path + '\n\nEverything stays here. Close Pratibha before copying this file for a backup.')

    def save_current(self):
        return self.editor.save() if self.editor else True

    def set_page(self, page):
        old = self.stack.currentWidget()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        if old:
            self.stack.removeWidget(old)
            old.deleteLater()

    def navigate(self, name):
        if not self.save_current():
            return
        self.editor = None
        self.current_view = name
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 14, 30, 20)
        if name == 'Home':
            layout.addWidget(label(f'{self.store.count_finished()} finished journal entries', 'muted'))
            layout.addStretch(2)
            wordmark = AnimatedWordmark()
            wordmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(wordmark)
            layout.addSpacing(24)
            shortcuts = QVBoxLayout()
            shortcuts.setSpacing(12)
            for target in ('Insights', 'Reminders'):
                shortcut = button(target, lambda checked=False, n=target: self.navigate(n))
                shortcut.setFixedWidth(240)
                shortcuts.addWidget(shortcut, alignment=Qt.AlignmentFlag.AlignHCenter)
            layout.addLayout(shortcuts)
            drafts = [r for r in self.store.rows('entries') if not r['finished']]
            if drafts:
                ident = drafts[0]['id']
                layout.addWidget(button('Continue latest draft', lambda: self.open_entry(ident)))
            layout.addStretch(3)
            bottom = QHBoxLayout()
            bottom.addStretch()
            add = button('+', self.capture, 'capture')
            add.setAccessibleName('Capture a new journal entry')
            add.setFixedSize(72, 72)
            bottom.addWidget(add)
            layout.addLayout(bottom)
        else:
            layout.addWidget(label(name, 'heading'))
            if name == 'Calendar':
                self.build_calendar(layout)
            else:
                self.build_list(name, layout)
        self.set_page(page)

    def build_list(self, name, layout):
        if name == 'Reminders':
            from .reminder_grid import ReminderGrid
            layout.addWidget(label('Alerts require Pratibha to be running. Date-only reminders do not send alerts. Cards are ordered by due date and time, latest first.', 'muted'))
            self.reminder_grid = ReminderGrid(self)
            layout.addWidget(self.reminder_grid, 1)
            return
        add = {'Journal': self.capture, 'Insights': self.edit_insight, 'Reminders': self.edit_reminder}[name]
        layout.addWidget(button('New ' + {'Journal': 'entry', 'Insights': 'insight', 'Reminders': 'reminder'}[name], add, 'primary'))
        listing = QListWidget()
        listing.setAccessibleName(name + ' list')
        layout.addWidget(listing, 1)
        table = {'Journal': 'entries', 'Insights': 'insights', 'Reminders': 'reminders'}[name]
        rows = self.store.rows(table)
        if name == 'Journal':
            rows = sorted(rows, key=lambda r: (r['day'], r['time'], r['id']), reverse=True)
            for row in rows:
                self.list_item(listing, f"{'Finished' if row['finished'] else 'Draft'} · {row['day']} {display_time(row['time'])}\n{entry_preview(row)}", table, row['id'])
        elif name == 'Insights':
            for row in sorted(rows, key=lambda r: (r['done'], -r['id'])):
                self.list_item(listing, ('Worked on' if row['done'] else 'Open') + ' · ' + row['body'], table, row['id'])
        if not rows:
            layout.addWidget(label('Nothing here yet. Start with one small note.', 'muted'))
        listing.itemDoubleClicked.connect(self.open_list_item)
        listing.itemActivated.connect(self.open_list_item)
        controls = QHBoxLayout()
        controls.addWidget(button('Open / edit selected', lambda: self.open_list_item(listing.currentItem())))
        controls.addWidget(button('Delete selected', lambda: self.delete_selected(listing)))
        layout.addLayout(controls)

    @staticmethod
    def list_item(listing, text, table, ident):
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, (table, ident))
        listing.addItem(item)

    def open_list_item(self, item):
        data = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not data:
            return
        table, ident = data
        if table == 'entries':
            self.open_entry(ident)
        elif table == 'insights':
            self.edit_insight(ident=ident)
        else:
            self.edit_reminder(ident=ident)

    def delete_selected(self, listing):
        item = listing.currentItem()
        data = item.data(Qt.ItemDataRole.UserRole) if item else None
        if data and QMessageBox.question(self, 'Delete permanently?', 'Delete this item? This cannot be undone.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.write_safely(self, lambda: self.store.delete(*data)):
                self.navigate(self.current_view)

    def capture(self, checked=False, day=None):
        if not self.save_current():
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('Capture a moment')
        dialog.setMinimumWidth(380)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label('Both fields are optional. You can start writing now.', 'muted'))
        form = QFormLayout()
        location, descriptor = QLineEdit(), QLineEdit()
        form.addRow('&Location', location)
        form.addRow('&Context', descriptor)
        layout.addLayout(form)
        protection_row = QHBoxLayout()
        protection_row.addWidget(label('Password protection'))
        protection_row.addStretch()
        protection = PasswordSwitch(dialog)
        protection_row.addWidget(protection)
        layout.addLayout(protection_row)
        password_fields = QWidget()
        password_form = QFormLayout(password_fields)
        password_form.setContentsMargins(0, 0, 0, 0)
        password, confirmation = QLineEdit(), QLineEdit()
        for field in (password, confirmation):
            field.setEchoMode(QLineEdit.EchoMode.Password)
        password_form.addRow('&Password', password)
        password_form.addRow('&Confirm password', confirmation)
        password_form.addRow(label('No password recovery. The recorded date and time remain visible.', 'muted'))
        password_fields.hide()
        protection.toggled.connect(password_fields.setVisible)
        layout.addWidget(password_fields)
        def start():
            if protection.isChecked():
                if not password.text():
                    QMessageBox.information(dialog, 'Password required', 'Enter a password or turn protection off.')
                    return
                if password.text() != confirmation.text():
                    QMessageBox.information(dialog, 'Passwords differ', 'Enter the same password in both fields.')
                    return
            dialog.accept()
        layout.addWidget(button('Start writing', start, 'primary'))
        layout.addWidget(button('Cancel', dialog.reject))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.open_entry(day=day, location=location.text(), descriptor=descriptor.text(), password=password.text() if protection.isChecked() else None)

    def open_entry(self, ident=None, day=None, location='', descriptor='', password=None):
        if not self.save_current():
            return
        row = self.store.get('entries', ident) if ident else None
        if row and row['password_salt']:
            while True:
                password, accepted = QInputDialog.getText(self, 'Unlock entry', 'Password', QLineEdit.EchoMode.Password)
                if not accepted:
                    return
                try:
                    row = self.store.unlock_entry(ident, password)
                    break
                except ValueError as error:
                    QMessageBox.warning(self, 'Cannot unlock entry', str(error))
        self.editor = Editor(self, row, day, location, descriptor, password)
        self.current_view = 'Editor'
        self.set_page(self.editor)
        self.editor.body.setFocus()

    def edit_insight(self, checked=False, ident=None):
        row = self.store.get('insights', ident) if ident else None
        dialog = QDialog(self)
        dialog.setWindowTitle('Insight')
        dialog.resize(520, 350)
        layout = QVBoxLayout(dialog)
        body = QPlainTextEdit(row['body'] if row else '')
        body.setAccessibleName('Insight text')
        body.setPlaceholderText('Something I noticed or want to work on…')
        done = QCheckBox('Worked on')
        done.setChecked(bool(row['done']) if row else False)
        layout.addWidget(body)
        layout.addWidget(done)
        def save():
            if not body.toPlainText().strip():
                QMessageBox.information(dialog, 'Add some text', 'Write an insight before saving.')
                return
            if self.write_safely(dialog, lambda: self.store.save_insight(ident, body.toPlainText(), done.isChecked())):
                dialog.accept()
        dialog_buttons(dialog, layout, save)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.navigate('Insights')

    def edit_reminder(self, checked=False, ident=None, day=None):
        row = self.store.get('reminders', ident) if ident else None
        dialog = QDialog(self)
        dialog.setWindowTitle('Reminder')
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        title = QLineEdit(row['title'] if row else '')
        due = date_edit(QDate.fromString(row['day'], 'yyyy-MM-dd') if row else day)
        timed = QCheckBox('Set a time (local clock)')
        timed.setChecked(bool(row['time']) if row else False)
        time = time_edit(QTime.fromString(row['time'], 'HH:mm') if row and row['time'] else None)
        time.setEnabled(timed.isChecked())
        timed.toggled.connect(time.setEnabled)
        done = QCheckBox('Completed')
        done.setChecked(bool(row['done']) if row else False)
        form.addRow('&Title', title)
        form.addRow('&Due date', due)
        form.addRow(timed)
        form.addRow('&Time', time)
        form.addRow(done)
        layout.addLayout(form)
        layout.addWidget(label('Alerts require the app to be running.', 'muted'))
        def save():
            if not title.text().strip():
                QMessageBox.information(dialog, 'Add a title', 'A reminder needs a title.')
                return
            if self.write_safely(dialog, lambda: self.store.save_reminder(ident, title.text().strip(), due.date().toString('yyyy-MM-dd'), time.time().toString('HH:mm') if timed.isChecked() else None, done.isChecked())):
                dialog.accept()
        dialog_buttons(dialog, layout, save)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if self.current_view == 'Calendar':
                self.refresh_calendar()
            else:
                self.navigate('Reminders')
            self.check_reminders()

    def build_calendar(self, layout):
        self.calendar_widget = NotebookCalendar(self.store)
        self.calendar_widget.setMinimumHeight(260)
        layout.addWidget(self.calendar_widget, 1)
        layout.addWidget(label('● Journal entry     ■ Reminder (including completed)', 'muted'))
        self.calendar_list = QListWidget()
        self.calendar_list.setAccessibleName('Items on selected date')
        layout.addWidget(self.calendar_list, 1)
        self.calendar_list.itemClicked.connect(self.open_list_item)
        self.calendar_list.itemActivated.connect(self.open_list_item)
        self.calendar_widget.selectionChanged.connect(self.refresh_calendar)
        controls = QHBoxLayout()
        controls.addWidget(button('Entry on selected date', lambda: self.capture(day=self.calendar_widget.selectedDate())))
        controls.addWidget(button('Reminder on selected date', lambda: self.edit_reminder(day=self.calendar_widget.selectedDate())))
        layout.addLayout(controls)
        self.refresh_calendar()

    def refresh_calendar(self):
        self.calendar_widget.refresh_marks()
        self.calendar_list.clear()
        entries, reminders = self.store.calendar(self.calendar_widget.selectedDate().toString('yyyy-MM-dd'))
        for row in entries:
            self.list_item(self.calendar_list, f"Journal · {display_time(row['time'])} · {entry_preview(row)}", 'entries', row['id'])
        for row in reminders:
            self.list_item(self.calendar_list, f"{'✓ Completed' if row['done'] else 'Reminder'} · {display_time(row['time'])} · {row['title']}", 'reminders', row['id'])
        if not entries and not reminders:
            item = QListWidgetItem('No finished entries or reminders for this date.')
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.calendar_list.addItem(item)

    def dismiss_alert(self):
        self.alert.clear()
        self.alert.hide()
        self.dismiss.hide()

    def check_reminders(self):
        try:
            due = self.store.due_alerts()
            if due:
                messages = [f"{r['title']} — {r['day']} {display_time(r['time'])}" for r in due]
                previous = self.alert.text()
                self.alert.setText((previous + '\n' if previous else '') + 'Reminder due: ' + '\n'.join(messages))
                self.alert.show()
                self.dismiss.show()
                if self.tray.isVisible() and QSystemTrayIcon.supportsMessages():
                    self.tray.showMessage('Pratibha · Reminder due', '\n'.join(messages))
            if due and self.current_view == 'Reminders':
                self.navigate('Reminders')
            if self.last_day != QDate.currentDate():
                self.last_day = QDate.currentDate()
                if self.current_view == 'Reminders':
                    self.navigate('Reminders')
        except Exception as error:
            self.statusBar().show()
            self.statusBar().showMessage('Reminder check failed: ' + str(error))

    def closeEvent(self, event):
        if self.save_current():
            self.alert_timer.stop()
            self.tray.hide()
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('Pratibha')
    app.setApplicationName('Pratibha')
    configure_theme(app)
    directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    try:
        directory.mkdir(parents=True, exist_ok=True)
        store = Store(directory / 'pratibha.sqlite3')
    except Exception as error:
        QMessageBox.critical(None, 'Cannot open Pratibha', str(error))
        return 1
    window = Window(store, directory / 'pratibha.sqlite3')
    window.show()
    result = app.exec()
    store.close()
    return result

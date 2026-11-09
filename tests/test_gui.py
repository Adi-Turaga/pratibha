"""Run with QT_QPA_PLATFORM=offscreen for a display-independent Qt smoke test."""
import importlib.util
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

HAVE_QT = importlib.util.find_spec('PySide6') is not None
if HAVE_QT:
    from PySide6.QtCore import QDate, QTime, QTimer, QCoreApplication, QEvent
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialogButtonBox, QLineEdit, QPushButton, QCheckBox, QInputDialog, QMessageBox
    from pratibha.app import Window, configure_theme, PasswordSwitch, display_time, entry_preview
    from pratibha.storage import Store


@unittest.skipUnless(HAVE_QT, 'PySide6 is not installed')
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        configure_theme(cls.app)

    @classmethod
    def tearDownClass(cls):
        # Dispose Qt windows while QApplication is still alive, including windows
        # replaced during restart checks, rather than during interpreter teardown.
        for widget in cls.app.topLevelWidgets():
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.sqlite3'
        self.store = Store(self.path)
        self.window = Window(self.store, self.path)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.store.close()
        self.temp.cleanup()

    def test_offline_acceptance_flow_and_restart(self):
        with patch('socket.create_connection', side_effect=AssertionError('Network attempted')):
            def start_capture():
                dialog = QApplication.activeModalWidget()
                for b in dialog.findChildren(QPushButton):
                    if b.text() == 'Start writing':
                        b.click()
                        return
                self.fail('Missing Start writing button')
            QTimer.singleShot(0, start_capture)
            self.window.capture()
            editor = self.window.editor
            self.assertIsNotNone(editor)
            editor.body.setPlainText('A short moment away from my notebook.')
            deadline = time.monotonic() + 3
            while not self.store.rows('entries') and time.monotonic() < deadline:
                QTest.qWait(50)
            self.assertEqual(len(self.store.rows('entries')), 1)
            editor.finish()
            self.assertEqual(self.store.count_finished(), 1)
            self.window.navigate('Calendar')
            day = self.window.calendar_widget.selectedDate()
            def save_reminder():
                dialog = QApplication.activeModalWidget()
                dialog.findChildren(QLineEdit)[0].setText('Bring notebook')
                dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).click()
            QTimer.singleShot(0, save_reminder)
            self.window.edit_reminder(day=day)
            self.assertEqual(self.window.calendar_list.count(), 2)
            self.assertIn(day.toString('yyyy-MM-dd'), self.window.calendar_widget.entry_days)
            self.assertIn(day.toString('yyyy-MM-dd'), self.window.calendar_widget.reminder_days)
            self.window.close()
            self.store.close()
            self.store = Store(self.path)
            self.window = Window(self.store, self.path)
            self.window.show()
            self.window.navigate('Calendar')
            self.window.calendar_widget.setSelectedDate(day)
            self.window.refresh_calendar()
            self.assertEqual(self.store.count_finished(), 1)
            self.assertEqual(self.window.calendar_list.count(), 2)

    def test_navigation_and_close_flush_pending_draft(self):
        self.window.open_entry()
        self.window.editor.body.setPlainText('Pending, before timer fires')
        self.window.navigate('Journal')
        ident = self.store.rows('entries')[0]['id']
        self.window.open_entry(ident)
        self.assertEqual(self.window.editor.body.toPlainText(), 'Pending, before timer fires')
        self.window.editor.body.setPlainText('Changed before close')
        self.window.close()
        self.assertEqual(self.store.get('entries', ident)['body'], 'Changed before close')

    def test_untouched_editor_is_not_saved(self):
        self.window.open_entry()
        self.window.navigate('Home')
        self.assertEqual(self.store.rows('entries'), [])

    def test_visible_alert_and_no_repeat_after_restart(self):
        self.store.save_reminder(None, 'Missed reminder', '2000-01-01', '09:00')
        self.window.check_reminders()
        self.assertFalse(self.window.alert.isHidden())
        self.assertIn('Missed reminder', self.window.alert.text())
        self.window.dismiss_alert()
        self.window.check_reminders()
        self.assertTrue(self.window.alert.isHidden())
        self.window.close()
        self.store.close()
        self.store = Store(self.path)
        self.window = Window(self.store, self.path)
        self.window.check_reminders()
        self.assertTrue(self.window.alert.isHidden())

    def test_finished_entry_readonly_and_ampm(self):
        self.window.open_entry()
        editor = self.window.editor
        editor.time.setTime(QTime(17, 45))
        editor.body.setPlainText('Keep this exactly as written')
        editor.finish()
        ident = self.store.rows('entries')[0]['id']
        self.window.open_entry(ident)
        editor = self.window.editor
        self.assertTrue(editor.body.isReadOnly())
        for field in (editor.day, editor.time, editor.location, editor.descriptor):
            self.assertTrue(field.isReadOnly())
        self.assertTrue(editor.finish_button.isHidden())
        self.app.processEvents()
        saved_date = self.store.get('entries', ident)['day']
        self.assertEqual(editor.day.text(), saved_date)
        date_text = editor.day.findChild(QLineEdit)
        self.assertGreater(date_text.width(), date_text.fontMetrics().horizontalAdvance(saved_date))
        QTest.keyClicks(editor.body, 'Must not be added')
        self.assertEqual(editor.body.toPlainText(), 'Keep this exactly as written')
        self.assertEqual(editor.time.text(), '5:45 PM')
        self.assertEqual(display_time('00:00'), '12:00 AM')
        self.assertEqual(display_time('12:00'), '12:00 PM')

    def test_capture_password_toggle_and_unlock(self):
        def protect():
            dialog = QApplication.activeModalWidget()
            toggle = dialog.findChild(PasswordSwitch)
            self.assertFalse(toggle.isChecked())
            toggle.click()
            fields = [field for field in dialog.findChildren(QLineEdit) if field.echoMode() == QLineEdit.EchoMode.Password]
            self.assertEqual(len(fields), 2)
            for field in fields:
                field.setText('secret test password')
            next(b for b in dialog.findChildren(QPushButton) if b.text() == 'Start writing').click()
        QTimer.singleShot(0, protect)
        self.window.capture()
        self.window.editor.body.setPlainText('Encrypted from the first save')
        self.window.navigate('Journal')
        row = self.store.rows('entries')[0]
        self.assertEqual(entry_preview(row), 'Password-protected entry')
        with patch.object(QInputDialog, 'getText', return_value=('', False)):
            self.window.open_entry(row['id'])
        self.assertEqual(self.window.current_view, 'Journal')
        with patch.object(QInputDialog, 'getText', return_value=('secret test password', True)):
            self.window.open_entry(row['id'])
        self.assertEqual(self.window.editor.body.toPlainText(), 'Encrypted from the first save')

    def test_reminder_grid_sort_complete_animate_reopen_and_resize(self):
        early = self.store.save_reminder(None, 'Early', '2099-01-01', '09:00')
        later = self.store.save_reminder(None, 'Later', '2099-01-02', '09:00')
        latest = self.store.save_reminder(None, 'Latest', '2099-01-02', '10:00')
        self.window.navigate('Reminders')
        self.app.processEvents()
        grid = self.window.reminder_grid
        self.assertEqual([c.row['id'] for c in grid.cards], [latest, later, early])
        first = grid.cards[0]
        next_card = grid.cards[1]
        first_position = first.pos()
        self.assertEqual(first.width(), first.height())
        first.check.click()
        self.assertTrue(self.store.get('reminders', latest)['done'])
        self.assertIn(first, grid.fading)
        deadline = time.monotonic() + 3
        while (grid.fading or next_card.pos() != first_position) and time.monotonic() < deadline:
            QTest.qWait(50)
        self.assertEqual([c.row['id'] for c in grid.cards], [later, early])
        self.assertEqual(next_card.pos(), first_position)
        grid.completed.setChecked(True)
        self.app.processEvents()
        self.assertEqual([c.row['id'] for c in grid.cards], [latest])
        self.assertTrue(grid.cards[0].check.isChecked())
        grid.cards[0].check.click()
        QTest.qWait(550)
        self.assertFalse(self.store.get('reminders', latest)['done'])
        grid.completed.setChecked(False)
        self.window.resize(700, 580)
        self.app.processEvents()
        grid.reflow(False)
        self.assertEqual([c.row['id'] for c in grid.cards], [latest, later, early])
        for card in grid.cards:
            self.assertGreaterEqual(card.x(), 0)
            self.assertLessEqual(card.geometry().right(), grid.scroll.viewport().width())
        self.window.navigate('Home')
        self.window.navigate('Reminders')
        self.assertEqual(len(self.window.reminder_grid.cards), 3)

    def test_clear_completed_confirmation_and_preserve_open(self):
        open_id = self.store.save_reminder(None, 'Keep open', '2099-01-01')
        self.store.save_reminder(None, 'Done one', '2099-01-02', done=True)
        self.store.save_reminder(None, 'Done two', '2099-01-03', done=True)
        self.window.navigate('Reminders')
        grid = self.window.reminder_grid
        self.assertTrue(grid.clear_completed.isHidden())
        grid.completed.setChecked(True)
        self.assertFalse(grid.clear_completed.isHidden())
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
            grid.clear_completed.click()
        self.assertEqual(len(self.store.rows('reminders')), 3)
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            grid.clear_completed.click()
        self.assertEqual([r['id'] for r in self.store.rows('reminders')], [open_id])
        self.assertEqual(grid.cards, [])
        self.assertFalse(grid.clear_completed.isEnabled())
        grid.completed.setChecked(False)
        self.assertEqual([card.row['id'] for card in grid.cards], [open_id])
        self.store.close()
        self.store = Store(self.path)
        self.window.store = self.store
        self.assertEqual([r['id'] for r in self.store.rows('reminders')], [open_id])

    def test_views_render_at_laptop_size(self):
        self.window.resize(900, 700)
        for view in ('Home', 'Journal', 'Insights', 'Reminders', 'Calendar'):
            self.window.navigate(view)
            self.app.processEvents()
            self.assertEqual(self.window.current_view, view)
        self.window.open_entry()
        self.assertGreater(self.window.editor.body.height(), 100)


if __name__ == '__main__':
    unittest.main()

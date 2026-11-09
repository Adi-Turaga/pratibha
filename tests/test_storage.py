import os
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from pratibha.storage import Store


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'journal.sqlite3'
        self.store = Store(self.path)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def restart(self):
        self.store.close()
        self.store = Store(self.path)

    def entry(self, body='A small thought', finished=False, ident=None, day='2026-11-08'):
        return self.store.save_entry(ident, day, '14:30', 'Home', 'Diwali', body, finished)

    def test_draft_survives_restart_and_blank_capture_is_ignored(self):
        self.assertIsNone(self.entry(' \n '))
        self.assertEqual(self.store.rows('entries'), [])
        ident = self.entry()
        self.restart()
        self.assertEqual(self.store.get('entries', ident)['body'], 'A small thought')
        self.assertEqual(self.store.count_finished(), 0)

    def test_finish_is_immutable_delete_and_count(self):
        ident = self.entry()
        self.entry('Finished thought', True, ident)
        self.entry('Another', True)
        self.assertEqual(self.store.count_finished(), 2)
        self.restart()
        self.assertEqual(self.store.count_finished(), 2)
        with self.assertRaises(ValueError):
            self.entry('Reopened', False, ident)
        self.assertEqual(self.store.count_finished(), 2)
        self.store.delete('entries', ident)
        self.assertIsNone(self.store.get('entries', ident))

    def test_clearing_existing_draft_saves(self):
        ident = self.entry()
        self.entry('', False, ident)
        self.restart()
        self.assertEqual(self.store.get('entries', ident)['body'], '')
        self.assertEqual(self.store.count_finished(), 0)

    def test_calendar_includes_finished_and_all_reminders_only(self):
        finished = self.entry(finished=True)
        self.entry('Draft')
        self.entry('Tomorrow', True, day='2026-11-09')
        reminder = self.store.save_reminder(None, 'Call', '2026-11-08', done=True)
        self.restart()
        entries, reminders = self.store.calendar('2026-11-08')
        self.assertEqual([r['id'] for r in entries], [finished])
        self.assertEqual([r['id'] for r in reminders], [reminder])
        self.assertTrue(reminders[0]['done'])

    @unittest.skipUnless(hasattr(time, 'tzset'), 'tzset is POSIX only')
    def test_dates_stable_when_timezone_changes(self):
        previous = os.environ.get('TZ')
        try:
            ident = self.entry(finished=True, day='2026-01-01')
            reminder = self.store.save_reminder(None, 'Remember', '2026-01-01', '00:15')
            for zone in ('Pacific/Honolulu', 'Asia/Kolkata'):
                os.environ['TZ'] = zone
                time.tzset()
                self.restart()
                entries, reminders = self.store.calendar('2026-01-01')
                self.assertEqual(entries[0]['id'], ident)
                self.assertEqual(reminders[0]['id'], reminder)
        finally:
            if previous is None:
                os.environ.pop('TZ', None)
            else:
                os.environ['TZ'] = previous
            time.tzset()

    def test_missed_alert_restart_no_repeat_and_reschedule(self):
        ident = self.store.save_reminder(None, 'Stretch', '2026-11-08', '09:00')
        self.restart()  # App was closed at the due time.
        self.assertEqual(len(self.store.due_alerts(datetime(2026, 11, 8, 10))), 1)
        self.restart()
        self.assertEqual(self.store.due_alerts(datetime(2026, 11, 8, 10)), [])
        self.store.save_reminder(ident, 'Stretch (edited)', '2026-11-08', '09:00')
        self.assertEqual(self.store.due_alerts(datetime(2026, 11, 8, 10)), [])
        self.store.save_reminder(ident, 'Stretch', '2026-11-08', '11:00')
        self.restart()
        self.assertEqual(self.store.due_alerts(datetime(2026, 11, 8, 10, 59)), [])
        self.assertEqual(len(self.store.due_alerts(datetime(2026, 11, 8, 11))), 1)

    def test_date_only_and_completed_do_not_alert_and_groups(self):
        all_day = self.store.save_reminder(None, 'All day', '2026-11-08')
        completed = self.store.save_reminder(None, 'Done', '2026-11-08', '09:00', True)
        future = self.store.save_reminder(None, 'Later', '2026-11-09', '09:00')
        self.assertEqual(self.store.due_alerts(datetime(2026, 11, 8, 12)), [])
        row = self.store.get('reminders', all_day)
        self.assertEqual(self.store.group(row, datetime(2026, 11, 8, 23, 59)), 'Today')
        self.assertEqual(self.store.group(row, datetime(2026, 11, 9)), 'Overdue')
        self.assertEqual(self.store.group(self.store.get('reminders', future), datetime(2026, 11, 8)), 'Upcoming')
        self.store.save_reminder(completed, 'Done', '2026-11-08', '09:00', False)
        self.assertEqual(len(self.store.due_alerts(datetime(2026, 11, 8, 12))), 1)

    def test_sleep_catchup_and_exact_due_time(self):
        ident = self.store.save_reminder(None, 'Wake', '2026-11-08', '15:00')
        self.assertEqual(self.store.due_alerts(datetime(2026, 11, 8, 14, 59)), [])
        self.assertEqual(len(self.store.due_alerts(datetime(2026, 11, 8, 15))), 1)
        self.store.save_reminder(ident, 'Wake', '2026-11-09', '15:00')
        self.assertEqual(len(self.store.due_alerts(datetime(2026, 11, 10, 8))), 1)
        self.assertEqual(self.store.due_alerts(datetime(2026, 11, 10, 8)), [])

    def test_insight_lifecycle(self):
        ident = self.store.save_insight(None, 'Listen more')
        self.store.save_insight(ident, 'Listen carefully', True)
        self.restart()
        self.assertTrue(self.store.get('insights', ident)['done'])
        self.store.save_insight(ident, 'Listen carefully', False)
        self.assertFalse(self.store.get('insights', ident)['done'])
        self.store.delete('insights', ident)
        self.assertEqual(self.store.rows('insights'), [])

    def test_protected_draft_finish_restart_and_wrong_password(self):
        args = ('2026-11-08', '14:30', 'Secret place', 'Secret descriptor', 'Private thoughts')
        ident = self.store.save_entry(None, *args, password='test password')
        raw = self.store.get('entries', ident)
        self.assertTrue(raw['password_salt'])
        self.assertEqual(raw['location'], '')
        self.assertEqual(raw['descriptor'], '')
        self.assertNotIn('Private thoughts', raw['body'])
        self.restart()
        with self.assertRaises(ValueError):
            self.store.unlock_entry(ident, 'wrong')
        with self.assertRaises(ValueError):
            self.store.save_entry(ident, *args)
        self.assertEqual(self.store.unlock_entry(ident, 'test password')['body'], 'Private thoughts')
        self.store.save_entry(ident, *args[:-1], 'Updated private thoughts', password='test password')
        self.store.save_entry(ident, *args, finished=True, password='test password')
        self.restart()
        self.assertEqual(self.store.unlock_entry(ident, 'test password')['location'], 'Secret place')
        self.assertEqual(len(self.store.calendar('2026-11-08')[0]), 1)
        with self.assertRaises(ValueError):
            self.store.save_entry(ident, *args, password='test password')
        self.assertNotIn(b'Private thoughts', self.path.read_bytes())

    def test_protection_defaults_off_and_blank_is_ignored(self):
        ident = self.entry()
        self.assertIsNone(self.store.get('entries', ident)['password_salt'])
        self.assertIsNone(self.store.save_entry(None, '2026-11-08', '14:30', '', '', '', password='secret'))

    def test_v1_migration_preserves_entries(self):
        # Recreate the original schema to exercise a real upgrade.
        ident = self.entry('Existing v1 journal text', finished=True)
        self.store.db.execute('ALTER TABLE entries DROP COLUMN password_salt')
        self.store.db.execute('PRAGMA user_version=1')
        self.store.db.commit()
        self.restart()
        self.assertEqual(self.store.db.execute('PRAGMA user_version').fetchone()[0], 2)
        self.assertEqual(self.store.get('entries', ident)['body'], 'Existing v1 journal text')
        self.assertEqual(self.store.count_finished(), 1)
        self.assertIsNone(self.store.get('entries', ident)['password_salt'])

    def test_schema_version_and_future_version_guard(self):
        self.assertEqual(self.store.db.execute('PRAGMA user_version').fetchone()[0], 2)
        self.store.db.execute('PRAGMA user_version=99')
        with self.assertRaises(RuntimeError):
            other = Store(self.path)
            other.close()


if __name__ == '__main__':
    unittest.main()

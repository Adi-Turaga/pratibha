"""Local storage. Dates are literal local calendar dates, never UTC conversions."""
import sqlite3
import os
from .protection import encrypt, decrypt
from datetime import datetime


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if version > 2:
            self.db.close()
            raise RuntimeError('This database needs a newer version of Pratibha.')
        if version == 0:
            self.db.executescript('''
                CREATE TABLE entries(id INTEGER PRIMARY KEY, day TEXT NOT NULL, time TEXT NOT NULL,
                    location TEXT NOT NULL, descriptor TEXT NOT NULL, body TEXT NOT NULL, finished INTEGER NOT NULL);
                CREATE TABLE insights(id INTEGER PRIMARY KEY, body TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE reminders(id INTEGER PRIMARY KEY, title TEXT NOT NULL, day TEXT NOT NULL,
                    time TEXT, done INTEGER NOT NULL DEFAULT 0, alerted INTEGER NOT NULL DEFAULT 0);
                PRAGMA user_version=1;
            ''')
            self.db.commit()
        if version < 2:
            with self.db:
                self.db.execute("ALTER TABLE entries ADD COLUMN password_salt BLOB")
                self.db.execute("PRAGMA user_version=2")

    def rows(self, table):
        if table not in ('entries', 'insights', 'reminders'):
            raise ValueError(table)
        return self.db.execute(f'SELECT * FROM {table} ORDER BY id DESC').fetchall()

    def get(self, table, ident):
        return next((r for r in self.rows(table) if r['id'] == ident), None)

    def save_entry(self, ident, day, time, location, descriptor, body, finished=False, password=None):
        old = self.get('entries', ident) if ident is not None else None
        if old and old['finished']:
            raise ValueError('Finished entries are read-only.')
        if old and old['password_salt']:
            self.unlock_entry(ident, password)
        if not body.strip() and ident is None:
            return None  # An empty new capture is never persisted.
        if not body.strip():
            finished = False
        salt = old['password_salt'] if old else None
        if password and salt is None:
            salt = os.urandom(16)
        if salt:
            body = encrypt(password, salt, location, descriptor, body)
            location = descriptor = ''
        values = (day, time, location, descriptor, body, int(finished), salt)
        with self.db:
            if ident is None:
                return self.db.execute('INSERT INTO entries(day,time,location,descriptor,body,finished,password_salt) VALUES(?,?,?,?,?,?,?)', values).lastrowid
            self.db.execute('UPDATE entries SET day=?,time=?,location=?,descriptor=?,body=?,finished=?,password_salt=? WHERE id=?', values + (ident,))
        return ident

    def unlock_entry(self, ident, password):
        row = dict(self.get('entries', ident))
        if row['password_salt']:
            row.update(decrypt(password, row['password_salt'], row['body']))
        return row

    def count_finished(self):
        return self.db.execute('SELECT count(*) FROM entries WHERE finished=1').fetchone()[0]

    def save_insight(self, ident, body, done=False):
        with self.db:
            if ident is None:
                return self.db.execute('INSERT INTO insights(body,done) VALUES(?,?)', (body, int(done))).lastrowid
            self.db.execute('UPDATE insights SET body=?,done=? WHERE id=?', (body, int(done), ident))
        return ident

    def save_reminder(self, ident, title, day, time=None, done=False):
        with self.db:
            if ident is None:
                return self.db.execute('INSERT INTO reminders(title,day,time,done) VALUES(?,?,?,?)', (title, day, time, int(done))).lastrowid
            old = self.get('reminders', ident)
            alerted = old['alerted'] if (old['day'], old['time']) == (day, time) else 0
            self.db.execute('UPDATE reminders SET title=?,day=?,time=?,done=?,alerted=? WHERE id=?', (title, day, time, int(done), alerted, ident))
        return ident

    def delete(self, table, ident):
        self.rows(table)  # Validate identifier.
        with self.db:
            self.db.execute(f'DELETE FROM {table} WHERE id=?', (ident,))

    def clear_completed_reminders(self):
        with self.db:
            self.db.execute('DELETE FROM reminders WHERE done=1')

    def calendar(self, day):
        return ([r for r in self.rows('entries') if r['day'] == day and r['finished']],
                [r for r in self.rows('reminders') if r['day'] == day])

    @staticmethod
    def group(reminder, today):
        if isinstance(today, datetime):
            stamp = today.strftime('%Y-%m-%d %H:%M')
            day = today.strftime('%Y-%m-%d')
            if reminder['time'] and reminder['day'] + ' ' + reminder['time'] < stamp:
                return 'Overdue'
        else:
            day = today
        return 'Overdue' if reminder['day'] < day else 'Today' if reminder['day'] == day else 'Upcoming'

    def due_alerts(self, now=None):
        now = now or datetime.now()
        stamp = now.strftime('%Y-%m-%d %H:%M')
        due = [r for r in self.rows('reminders') if not r['done'] and not r['alerted'] and r['time'] and r['day'] + ' ' + r['time'] <= stamp]
        with self.db:
            self.db.executemany('UPDATE reminders SET alerted=1 WHERE id=?', [(r['id'],) for r in due])
        return due

    def close(self):
        self.db.close()

"""Responsive reminder cards with completion fades and animated gap closing."""
from datetime import datetime
from math import ceil
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout,
    QScrollArea, QGraphicsOpacityEffect, QMessageBox,
)


class ReminderCard(QFrame):
    SIDE = 220

    def __init__(self, grid, row):
        super().__init__(grid.canvas)
        self.grid = grid
        self.row = row
        self.setObjectName('reminderCard')
        self.setFixedSize(self.SIDE, self.SIDE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        self.check = QCheckBox('Completed' if row['done'] else 'Complete')
        self.check.setAccessibleName(('Reopen ' if row['done'] else 'Complete ') + row['title'])
        self.check.setChecked(bool(row['done']))
        layout.addWidget(self.check)
        title = QLabel(row['title'])
        title.setTextFormat(Qt.TextFormat.PlainText)
        title.setWordWrap(True)
        title.setFixedHeight(56)
        title.setToolTip(row['title'])
        title.setObjectName('reminderTitle')
        layout.addWidget(title)
        state = 'Completed' if row['done'] else grid.window.store.group(row, datetime.now())
        layout.addWidget(QLabel(state + ' · ' + row['day']))
        from .app import display_time
        layout.addWidget(QLabel(display_time(row['time'])))
        layout.addStretch()
        actions = QHBoxLayout()
        self.edit = QPushButton('Edit')
        self.edit.setAccessibleName('Edit ' + row['title'])
        self.edit.clicked.connect(lambda: grid.window.edit_reminder(ident=row['id']))
        self.delete = QPushButton('Delete')
        self.delete.setAccessibleName('Delete ' + row['title'])
        self.delete.clicked.connect(self.delete_reminder)
        actions.addWidget(self.edit)
        actions.addWidget(self.delete)
        layout.addLayout(actions)
        self.check.toggled.connect(self.complete)

    def complete(self, checked):
        r = self.row
        if not self.grid.window.write_safely(self, lambda: self.grid.window.store.save_reminder(
            r['id'], r['title'], r['day'], r['time'], checked
        )):
            self.check.blockSignals(True)
            self.check.setChecked(bool(r['done']))
            self.check.blockSignals(False)
            return
        self.grid.fade_out(self)

    def delete_reminder(self):
        if QMessageBox.question(self, 'Delete permanently?', 'Delete this reminder? This cannot be undone.',
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.grid.window.write_safely(self, lambda: self.grid.window.store.delete('reminders', self.row['id'])):
                self.grid.fade_out(self)


class ReminderGrid(QWidget):
    GAP = 16
    MARGIN = 8

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.cards = []
        self.fading = set()
        self.moves = None
        self.fades = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        tools = QHBoxLayout()
        create = QPushButton('New reminder')
        create.setObjectName('primary')
        create.clicked.connect(window.edit_reminder)
        tools.addWidget(create)
        tools.addStretch()
        self.clear_completed = QPushButton('Clear all completed')
        self.clear_completed.clicked.connect(self.clear_all_completed)
        tools.addWidget(self.clear_completed)
        self.completed = QCheckBox('Show completed')
        self.completed.toggled.connect(self.reload)
        tools.addWidget(self.completed)
        layout.addLayout(tools)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.canvas = QWidget()
        self.scroll.setWidget(self.canvas)
        layout.addWidget(self.scroll, 1)
        self.empty = QLabel('')
        self.empty.setObjectName('muted')
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty)
        self.reload()

    def reload(self, *_):
        if self.moves:
            self.moves.stop()
        for animation in self.fades.values():
            animation.stop()
        self.fades.clear()
        self.fading.clear()
        for card in self.cards:
            card.hide()
            card.deleteLater()
        rows = [r for r in self.window.store.rows('reminders') if bool(r['done']) == self.completed.isChecked()]
        rows.sort(key=lambda r: (r['day'], r['time'] or '', r['id']), reverse=True)
        self.cards = [ReminderCard(self, row) for row in rows]
        for card in self.cards:
            card.show()
        self.reflow(False)
        self.update_empty()
        QTimer.singleShot(0, self.settle_reflow)

    def clear_all_completed(self):
        if not self.completed.isChecked():
            return
        if QMessageBox.question(
            self, 'Clear all completed?',
            'Permanently delete all completed reminders? This cannot be undone. Open reminders will be kept.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            if self.window.write_safely(self, self.window.store.clear_completed_reminders):
                self.reload()

    def update_empty(self):
        self.clear_completed.setVisible(self.completed.isChecked())
        self.clear_completed.setEnabled(bool(self.cards))
        self.empty.setText(('No completed reminders.' if self.completed.isChecked() else 'No open reminders. Enjoy the breathing room.') if not self.cards else '')
        self.empty.setVisible(not self.cards)

    def settle_reflow(self):
        self.reflow(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Allow the scroll viewport to settle before calculating the column count.
        QTimer.singleShot(0, self.settle_reflow)

    def reflow(self, animate=True):
        if self.moves:
            self.moves.stop()
            self.moves.deleteLater()
            self.moves = None
        available = max(1, self.scroll.viewport().width() - 2 * self.MARGIN)
        columns = max(1, (available + self.GAP) // (ReminderCard.SIDE + self.GAP))
        cards = [card for card in self.cards if card not in self.fading]
        self.canvas.setMinimumHeight(max(1, ceil(len(cards) / columns)) * (ReminderCard.SIDE + self.GAP) + 2 * self.MARGIN)
        group = QParallelAnimationGroup(self)
        for index, card in enumerate(cards):
            target = QPoint(self.MARGIN + (index % columns) * (ReminderCard.SIDE + self.GAP),
                            self.MARGIN + (index // columns) * (ReminderCard.SIDE + self.GAP))
            if animate and card.pos() != target:
                movement = QPropertyAnimation(card, b'pos', group)
                movement.setDuration(280)
                movement.setStartValue(card.pos())
                movement.setEndValue(target)
                movement.setEasingCurve(QEasingCurve.Type.InOutCubic)
                group.addAnimation(movement)
            else:
                card.move(target)
        self.moves = group
        group.start()
        # Keep Tab navigation consistent with the displayed descending order.
        previous = self.completed
        for card in cards:
            for control in (card.check, card.edit, card.delete):
                QWidget.setTabOrder(previous, control)
                previous = control

    def fade_out(self, card):
        if card in self.fading:
            return
        self.fading.add(card)
        card.setEnabled(False)
        # Nested Qt graphics effects can conflict; remove child button shadows
        # before applying a single opacity effect to the whole card.
        for control in card.findChildren(QPushButton):
            control.setGraphicsEffect(None)
        effect = QGraphicsOpacityEffect(card)
        card.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b'opacity', self)
        animation.setDuration(220)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.finished.connect(lambda: self.remove_card(card))
        self.fades[card] = animation
        animation.start()

    def remove_card(self, card):
        self.fades.pop(card).deleteLater()
        self.fading.remove(card)
        self.cards.remove(card)
        card.hide()
        card.deleteLater()
        self.update_empty()
        self.reflow(True)

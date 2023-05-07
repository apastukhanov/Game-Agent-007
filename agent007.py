from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import random
import time

from cell import Pos
from menu_windows import SettingsWindow, GameDescription


IMG_BOMB = QImage("./images/bomb.png")
IMG_CLOCK = QImage("./images/clock-select.png")

LEVELS = [
    (12, 5),
    (20, 25),
    (25, 50)
]

STATUS_READY = 0
STATUS_PLAYING = 1
STATUS_FAILED = 2
STATUS_SUCCESS = 3

STATUS_ICONS = {
    STATUS_READY: "./images/plus.png",
    STATUS_PLAYING: "./images/smiley.png",
    STATUS_FAILED: "./images/cross.png",
    STATUS_SUCCESS: "./images/smiley-lol.png",
}


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ws = SettingsWindow(parent=self)
        self.wd = GameDescription()

        self.lvl = int(self.ws.read_settings().get('level', 1))
        self.b_size, self.n_mines = LEVELS[self.lvl - 1]

        self.start_x = -1
        self.start_y = -1
        self.score = 0

        self._create_menu()
        self._create_ui()
        self.show()

    def _create_ui(self):
        w = QWidget()
        vb = QVBoxLayout()
        vb.addLayout(self._create_header_layout())
        vb.addLayout(self._create_grid_layout())
        w.setLayout(vb)
        self.setCentralWidget(w)
        self.init_map()
        self.update_status(STATUS_READY)
        self.reset_map()
        self.update_status(STATUS_READY)

    def _create_header_layout(self):
        hb = QHBoxLayout()
        hb.addStretch(1)
        hb.addWidget(self._create_score_label())
        hb.addStretch(1)
        hb.addWidget(self._create_button())
        hb.addStretch(1)
        hb.addWidget(self._create_clock_label())
        hb.addStretch(1)
        hb.addWidget(self._create_level_label())
        return hb

    def _create_score_label(self):
        self.mines = QLabel()
        f = self.mines.font()
        f.setPointSize(24)
        f.setWeight(75)
        self.mines.setFont(f)
        self.mines.setText("%04d" % self.score)
        return self.mines

    def _create_clock_label(self):
        self.clock = QLabel()
        f = self.clock.font()
        f.setPointSize(24)
        f.setWeight(75)
        self.clock.setFont(f)
        self._timer = QTimer()
        self._timer.timeout.connect(self.update_timer)
        self._timer.start(1000)  # 1 second timer
        self.clock.setText("000")
        return self.clock

    def _create_button(self):
        self.button = QPushButton()
        self.button.setFixedSize(QSize(32, 32))
        self.button.setIconSize(QSize(32, 32))
        self.button.setIcon(QIcon("./images/smiley.png"))
        self.button.setFlat(True)
        self.button.pressed.connect(self.button_pressed)
        return self.button

    def _create_level_label(self):
        l = QLabel()
        l.setText("Level: %1d" % self.lvl)
        return l

    def _create_grid_layout(self):
        self.grid = QGridLayout()
        self.grid.setSpacing(5)
        return self.grid

    def _create_menu(self):
        settings_action = QAction('Настройки', self)
        settings_action.setShortcut('Ctrl+S')
        settings_action.triggered.connect(self.show_settings)
        info_action = QAction('Правила игры', self)
        info_action.setShortcut('Ctrl+I')
        info_action.triggered.connect(self.show_info)
        menu = self.menuBar()
        menu.setNativeMenuBar(False)
        main_menu = menu.addMenu('&Game')
        main_menu.addAction(settings_action)
        main_menu.addAction(info_action)
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Агент 007')

    def show_settings(self):
        self.ws.show()

    def show_info(self):
        self.wd.show()

    def apply_settings(self):
        self.close()
        self.__init__()

    def init_map(self):
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = Pos(x, y)
                self.grid.addWidget(w, y, x)
                # Connect signal to handle expansion.
                w.clicked.connect(self.trigger_start)
                w.expandable.connect(self.expand_reveal)
                w.explode_bomb.connect(self.game_over)

    def reset_map(self):
        # Clear all mine positions
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.reset()

        # Add mines to the positions
        positions = []
        while len(positions) < self.n_mines:
            x, y = random.randint(0, self.b_size - 1), random.randint(0, self.b_size - 1)
            if (x, y) not in positions:
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_mine = True
                positions.append((x, y))

        # Place starting marker
        while True:
            x, y = random.randint(0, self.b_size - 1), random.randint(0, self.b_size - 1)
            w = self.grid.itemAtPosition(y, x).widget()
            # We don't want to start on a mine.
            if (x, y) not in positions:
                self.start_y = y
                self.start_x = x
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_start = True

                # Reveal all positions around this, if they are not mines either.
                for w in self.get_surrounding(x, y):
                    if not w.is_mine:
                        w.is_active = True
                break

    def update_start_cell(self, x, y, val):
        for w in self.get_surrounding(x, y):
            if not w.is_mine:
                w.is_active = True

        self.start_x = x
        self.start_y = y
        w = self.grid.itemAtPosition(self.start_y, self.start_x).widget()
        w.is_start = True
        w.is_active = False
        w.is_visited = True

    def remove_start_cell(self):
        w = self.grid.itemAtPosition(self.start_y, self.start_x).widget()
        w.is_start = False
        w.is_visited = True
        w.is_active = False

        x, y = self.start_x, self.start_y

        for w in self.get_surrounding(x, y):
            if not w.is_mine:
                w.is_active = False

    def get_surrounding(self, x, y):
        positions = []
        for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                positions.append(self.grid.itemAtPosition(yi, xi).widget())
        return positions

    def button_pressed(self):
        if self.status == STATUS_PLAYING:
            self.update_status(STATUS_FAILED)
            self.reveal_map()

        elif self.status == STATUS_FAILED:
            self.reset_map()
            self.update_status(STATUS_READY)
            self.score = -10
            self.update_score()

    def reset_game(self):
        self._create_ui()

    def reveal_map(self):
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.reveal()

    def expand_reveal(self, x, y):
        for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                w = self.grid.itemAtPosition(yi, xi).widget()
                if not w.is_mine:
                    w.click()

    def get_target_cell(self, x, y, val):
        dx = x - self.start_x
        dy = y - self.start_y

        w = self.grid.itemAtPosition(self.start_y,
                                     self.start_x).widget()

        for i in range(1, val+1):
            curr_x = self.start_x + i * dx
            curr_y = self.start_y + i * dy

            if (curr_y > self.b_size - 1) or (curr_y < 0) \
                    or (curr_x > self.b_size - 1) or (curr_x < 0):
                w.explode_bomb.emit()
                return w.x, w.y

            w = self.grid.itemAtPosition(curr_y,
                                         curr_x).widget()
            if w.is_visited or w.is_mine:
                w.explode_bomb.emit()
                return curr_x, curr_y

            self.update_score()

            w.is_visited = True

        return curr_x, curr_y

    def trigger_start(self, x, y, val):
        if self.status != STATUS_PLAYING:
            # First click.
            self.update_status(STATUS_PLAYING)
            # Start timer.
            self._timer_start_nsecs = int(time.time())
        print('here1')
        x_new, y_new = self.get_target_cell(x, y, val)
        print(f'updated: {x_new=}, {y_new=}')
        self.remove_start_cell()
        self.update_start_cell(x_new, y_new, val)

    def update_status(self, status):
        self.status = status
        self.button.setIcon(QIcon(STATUS_ICONS[self.status]))

    def update_timer(self):
        if self.status == STATUS_PLAYING:
            n_secs = int(time.time()) - self._timer_start_nsecs
            self.clock.setText("%03d" % n_secs)

    def game_over(self):
        self.reveal_map()
        print('game over!!!!')
        self.update_status(STATUS_FAILED)
        self.update()

    def update_score(self):
        self.score += 10
        self.mines.setText("%04d" % self.score)


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec_()

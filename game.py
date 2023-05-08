import random
import time

from enum import Enum

from PyQt5.QtCore import QTimer, QSize
from PyQt5.QtGui import QImage, QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout, QAction, \
    QApplication

from menu_windows import SettingsWindow, GameDescription
from cell import Cell


IMG_BOMB = QImage("./images/bomb.png")
IMG_CLOCK = QImage("./images/clock-select.png")


LEVELS = [
    (12, 5),
    (20, 25),
    (25, 50)
]


class Status(Enum):
    READY = 0
    PLAYING = 1
    FAILED = 2
    SUCCESS = 3


STATUS_ICONS = {
    Status.READY: "./images/plus.png",
    Status.PLAYING: "./images/smiley.png",
    Status.FAILED: "./images/cross.png",
    Status.SUCCESS: "./images/smiley-lol.png",
}


class GameBoard(QGridLayout):
    def __init__(self, b_size, n_mines, parent=None):
        super().__init__()
        self.b_size = b_size
        self.n_mines = n_mines
        self.parent = parent
        self.setSpacing(5)
        self.init_map()
        self.reset_map()

    def init_map(self):
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = Cell(x, y)
                self.addWidget(w, y, x)
                w.clicked.connect(self.move_head)
                w.explode_bomb.connect(self.parent.game_over)

    def reset_map(self):
        self.reset_cells_state()
        positions = self.set_mine(self, self.n_mines, self.b_size)

        while True:
            x, y = random.randint(0, self.b_size - 1), random.randint(0, self.b_size - 1)
            if (x, y) not in positions:
                Cell.set_start_y(y)
                Cell.set_start_x(x)
                w = self.head
                w.is_start = True
                self.activate_cells_slice(x, y)
                w.is_active = False
                break

    def activate_cells_slice(self, x, y):
        for yi, xi in self.get_surrounding(x, y, self.b_size):
            w = self.itemAtPosition(yi, xi).widget()
            if not w.is_mine:
                w.is_active = True

    def reset_cells_state(self):
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.itemAtPosition(y, x).widget()
                w.reset()

    @staticmethod
    def set_mine(grid, n_mines, b_size):
        positions = []
        while len(positions) < n_mines:
            x, y = random.randint(0, b_size - 1), random.randint(0, b_size - 1)
            if (x, y) not in positions:
                w = grid.itemAtPosition(y, x).widget()
                w.is_mine = True
                positions.append((x, y))
        return positions

    def update_start_cell(self, x, y):
        self.activate_cells_slice(x, y)
        Cell.set_start_x(x)
        Cell.set_start_y(y)
        w = self.head
        w.is_start = True
        w.is_active = False
        w.is_visited = True

    def remove_start_cell(self):
        w = self.head
        w.is_start = False
        w.is_active = False
        w.is_visited = True

        x, y = Cell.get_start_x(), Cell.get_start_y()

        for yi, xi in self.get_surrounding(x, y, self.b_size):
            w = self.itemAtPosition(yi, xi).widget()
            if not w.is_mine:
                w.is_active = False

    @staticmethod
    def get_surrounding(x, y, boarder):
        positions = []
        for xi in range(max(0, x - 1), min(x + 2, boarder)):
            for yi in range(max(0, y - 1), min(y + 2, boarder)):
                positions.append([yi, xi])
        return positions

    def reveal_map(self):
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.itemAtPosition(y, x).widget()
                w.reveal()

    def move_head(self, x, y, val):
        if self.parent.status == Status.FAILED:
            return
        if self.parent.status != Status.PLAYING:
            self.parent.update_status(Status.PLAYING)
            self.parent._timer_start_nsecs = int(time.time())
        x_new, y_new = self.get_target_cell(x, y, val)
        self.remove_start_cell()
        self.update_start_cell(x_new, y_new)

    @property
    def head(self):
        return self.itemAtPosition(Cell.get_start_y(),
                                   Cell.get_start_x()).widget()

    def get_target_cell(self, x, y, val):
        dx = Cell.get_dist_start_x(x)
        dy = Cell.get_dist_start_y(y)

        w = self.head

        for i in range(1, val + 1):
            curr_x = Cell.get_start_x() + i * dx
            curr_y = Cell.get_start_y() + i * dy

            if (curr_y > self.b_size - 1) or (curr_y < 0) \
                    or (curr_x > self.b_size - 1) or (curr_x < 0):
                w.explode_bomb.emit()
                return w.x, w.y

            w = self.itemAtPosition(curr_y,
                                    curr_x).widget()

            if w.is_visited or w.is_mine:
                w.explode_bomb.emit()
                return curr_x, curr_y

            self.parent.update_score()
            w.is_visited = True

        return curr_x, curr_y


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ws = SettingsWindow(parent=self)
        self.wd = GameDescription()

        self.lvl = int(self.ws.settings.get('level', 1))
        self.b_size, self.n_mines = LEVELS[self.lvl - 1]

        self.score = 0

        self.grid = GameBoard(self.b_size, self.n_mines, self)
        self._create_menu()
        self._create_ui()
        self.setWindowTitle('Агент 007')
        self.show()

    def _create_ui(self):
        w = QWidget()
        vb = QVBoxLayout()
        vb.addLayout(self._create_header_layout())
        vb.addLayout(self.grid)
        w.setLayout(vb)
        self.setCentralWidget(w)
        self.update_status(Status.READY)

    def _create_header_layout(self):
        hb = QHBoxLayout()
        score_label = QLabel()
        score_label.setText("Score:")
        hb.addWidget(score_label)
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

    def _create_menu(self):
        settings_action = QAction('Настройки', self)
        settings_action.setShortcut('Ctrl+S')
        settings_action.triggered.connect(self.show_settings)
        info_action = QAction('Правила игры', self)
        info_action.setShortcut('Ctrl+I')
        info_action.triggered.connect(self.show_info)
        menu = self.menuBar()
        menu.setNativeMenuBar(False)
        main_menu = menu.addMenu('&Меню')
        main_menu.addAction(settings_action)
        main_menu.addAction(info_action)

    def show_settings(self):
        self.ws.show()

    def show_info(self):
        self.wd.show()

    def apply_settings(self):
        self.close()
        self.__init__()

    def button_pressed(self):
        if self.status == Status.PLAYING:
            self.update_status(Status.FAILED)
            self.grid.reveal_map()

        elif self.status == Status.FAILED:
            self.grid.reset_map()
            self.update_status(Status.READY)
            self.score = -10
            self.update_score()

    def reset_game(self):
        self._create_ui()

    def update_status(self, status):
        self.status = status
        self.button.setIcon(QIcon(STATUS_ICONS[self.status]))

    def update_timer(self):
        if self.status == Status.PLAYING:
            n_secs = int(time.time()) - self._timer_start_nsecs
            self.clock.setText("%03d" % n_secs)

    def game_over(self):
        self.grid.reveal_map()
        self.update_status(Status.FAILED)

    def update_score(self):
        self.score += 10
        self.mines.setText("%04d" % self.score)


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec_()

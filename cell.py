from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import random

IMG_BOMB = QImage("./images/bomb.png")
IMG_FLAG = QImage("./images/flag.png")
IMG_START = QImage("./images/rocket.png")
IMG_CLOCK = QImage("./images/clock-select.png")
IMG_PLUS = QImage("./images/cross.png")


NUM_COLORS = {
    1: QColor('#000000'),
    2: QColor('#9C27B0'),
    3: QColor('#3F51B5'),
    4: QColor('#03A9F4'),
    5: QColor('#00BCD4'),
    6: QColor('#4CAF50'),
    7: QColor('#E91E63'),
    8: QColor('#FF9800')
}


class Pos(QWidget):
    expandable = pyqtSignal(int, int)
    clicked = pyqtSignal(int, int, int)
    explode_bomb = pyqtSignal()

    def __init__(self, x, y, *args, **kwargs):
        super(Pos, self).__init__(*args, **kwargs)

        self.is_game_over = False
        self.setFixedSize(QSize(20, 20))
        self.x = x
        self.y = y
        self.value = random.randint(1, 6)

    def reset(self):
        self.is_start = False
        self.is_mine = False
        self.is_visited = False
        self.is_active = False
        self.adjacent_n = 0
        self.is_game_over = False

        self.is_revealed = False
        self.is_flagged = False

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = event.rect()

        outer, inner = Qt.lightGray, Qt.lightGray

        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

        if self.is_start:
            p.drawPixmap(r, QPixmap(IMG_START))
        elif self.is_visited:
            p.drawPixmap(r, QPixmap(IMG_PLUS))
        elif self.is_mine:
            p.drawPixmap(r, QPixmap(IMG_BOMB))
        elif self.is_game_over:
            pass
        else:
            pen = QPen(NUM_COLORS[1])
            p.setPen(pen)
            f = p.font()
            f.setBold(True)
            p.setFont(f)
            p.drawText(r, Qt.AlignHCenter | Qt.AlignVCenter, str(self.value))

        self.update()

    def reveal(self):
        self.is_game_over = True
        self.update()

    def click(self):
        if not self.is_visited and self.is_active:
            self.clicked.emit(self.x, self.y, self.value)
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.click()

    def __repr__(self):
        return f'Pos[{self.x=}, {self.y=}, ' \
                 f'{self.is_active=}, {self.is_visited=}, ' \
                 f'{self.is_start=}, {self.is_mine=}]'

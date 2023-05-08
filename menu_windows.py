from PyQt5.QtWidgets import (QWidget, QLineEdit, QComboBox,
                             QPushButton, QFormLayout,
                             QHBoxLayout, QLabel, QVBoxLayout)


class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self._create_widgets()
        self._create_layout()
        self._setup_window()
        self.set_saved_settings()

    def _create_widgets(self):
        self.name_edit = QLineEdit()
        self.level_combo = QComboBox()
        self.level_combo.addItems(['Уровень 1', 'Уровень 2', 'Уровень 3'])

        self.apply_button = QPushButton('Применить')
        self.apply_button.clicked.connect(self.apply_settings)
        self.cancel_button = QPushButton('Отмена')
        self.cancel_button.clicked.connect(self.close)

    def _create_layout(self):
        layout = QFormLayout()
        layout.addRow('Имя игрока:', self.name_edit)
        layout.addRow('Уровень сложности:', self.level_combo)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)

        layout.addRow(button_layout)

        self.setLayout(layout)

    def _setup_window(self):
        self.setWindowTitle('Настройки')

    def apply_settings(self):
        self.save_settings()
        self.close()
        self.parent.apply_settings()

    def save_settings(self):
        name = self.name_edit.text()
        level = self.level_combo.currentIndex() + 1
        with open('settings.ini', 'w') as f:
            f.write(f'name={name}\n')
            f.write(f'level={level}\n')

    def set_saved_settings(self):
        settings = self.settings
        name = settings.get('name', 'Player1')
        level = int(settings.get('level', 1))
        self.name_edit.setText(name)
        self.level_combo.setCurrentIndex(level - 1)

    @property
    def settings(self):
        try:
            with open('settings.ini', 'r') as f:
                settings = dict(line.strip().split('=') for line in f)
            return settings
        except FileNotFoundError:
            return {}


class GameDescription(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Описание игры")
        self.setGeometry(100, 100, 600, 400)

        description = ("Представляем вам логическую онлайн флеш игру повышенной сложности <b>Агент 007</b>! "
                       "<br><br>"
                       "Задача игры Агент 007 - селать как можно больше ходов, не подорвавшись на мине, "
                       "и, соответственно, оставить как можно меньше свободных ячеек с цифрами.<br>"
                       "За один ход вы проходите столько ячеек, сколько указано в первой цифре от крутящейся звездочки. "
                       "Допускаются вертикальные, горизонтальные и диагональные ходы.<br><br> "
                       "Данная логическая игра относится к категории игр повышенной сложности, "
                       "хотя сам процесс игры не представляет из себя ничего сложного и в нее может играть человек любой подготовки, "
                       "только вот заданного показателя смогут достичь только суперпрофессионалы головоломок и логических игр.")
        label = QLabel(description)
        label.setWordWrap(True)

        button_ok = QPushButton("Ok", self)
        button_ok.clicked.connect(self.close)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(button_ok)

        self.setLayout(layout)

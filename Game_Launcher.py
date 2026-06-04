import sys
import os
import json
import subprocess
import random
import time
import threading
import re
import requests
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
import warnings
import webbrowser

warnings.filterwarnings("ignore", category=DeprecationWarning)

class InternetChecker:
    @staticmethod
    def check_internet():
        """Проверка наличия интернет соединения"""
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False

    @staticmethod
    def wait_for_internet(timeout=60, check_interval=1):
        """Ожидание подключения к интернету"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if InternetChecker.check_internet():
                return True
            time.sleep(check_interval)
        return False

class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.current_user = None
        self.users = self.load_users()

    def load_users(self):
        """Загрузка данных пользователей"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_users(self):
        """Сохранение данных пользователей"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения пользователей: {e}")

    def register_user(self, username, email, password):
        """Регистрация нового пользователя - УБРАНА КАПТЧА"""
        if username in self.users:
            return False, "Имя пользователя уже занято"

        # ИЗМЕНЕНИЕ: Добавлен символ "_" в допустимые символы
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,}$', username):
            return False, "Имя пользователя должно начинаться с буквы и содержать только латинские буквы, цифры и нижнее подчёркивание (_)"

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return False, "Неверный формат email"

        if len(password) < 6:
            return False, "Пароль должен содержать минимум 6 символов"

        self.users[username] = {
            "email": email,
            "password": password,  # В реальном приложении нужно хэшировать пароль
            "created": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "last_login": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
        self.save_users()
        return True, "Регистрация успешна"

    def login_user(self, username, password):
        """Вход пользователя"""
        if username not in self.users:
            return False, "Пользователь не найден"

        if self.users[username]["password"] != password:
            return False, "Неверный пароль"

        self.current_user = username
        self.users[username]["last_login"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        self.save_users()
        return True, "Вход успешен"

    def logout(self):
        """Выход пользователя"""
        self.current_user = None

class RegisterWindow(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.parent_window = parent 
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Создание аккаунта")
        self.setFixedSize(500, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit, QPushButton {
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Заголовок
        title_label = QLabel("Создание аккаунта")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Имя пользователя
        username_label = QLabel("Имя пользователя:")
        layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Латинские буквы, цифры и _ (нижнее подчёркивание), начинается с буквы")
        self.username_input.setFixedHeight(45) 
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                font-size: 14px;
                padding: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.username_input)

        email_label = QLabel("Email:")
        layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@mail.com")
        self.email_input.setFixedHeight(45)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                font-size: 14px;
                padding: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.email_input)

        # Пароль
        password_label = QLabel("Пароль:")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Минимум 6 символов")
        self.password_input.setFixedHeight(45)  # Увеличенная высота поля ввода
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                font-size: 14px;
                padding: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.password_input)

        # Подтверждение пароля
        confirm_label = QLabel("Подтвердите пароль:")
        layout.addWidget(confirm_label)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setFixedHeight(45)  # Увеличенная высота поля ввода
        self.confirm_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                font-size: 14px;
                padding: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.confirm_input)

        # КАПТЧА УБРАНА

        # Сообщения об ошибках
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f44336; font-size: 12px;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        # Кнопка регистрации
        register_btn = QPushButton("Создать аккаунт")
        register_btn.clicked.connect(self.register)
        register_btn.setFixedHeight(50)  # Увеличенная высота кнопки
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                font-weight: bold;
                margin-top: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        layout.addWidget(register_btn)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        # ИЗМЕНЕНИЕ: Исправлено соединение для возврата в окно входа
        back_btn.clicked.connect(self.back_to_login)
        back_btn.setFixedHeight(40)  # Увеличенная высота кнопки
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        layout.addWidget(back_btn)

        layout.addStretch()
        self.setLayout(layout)

    # Метод генерации каптчи убран

    def register(self):
        """Обработка регистрации - БЕЗ КАПТЧИ"""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        # captcha = self.captcha_input.text().strip() - УБРАНО

        # Валидация
        if not username:
            self.error_label.setText("Введите имя пользователя")
            return

        if not email:
            self.error_label.setText("Введите email")
            return

        if not password:
            self.error_label.setText("Введите пароль")
            return

        if password != confirm:
            self.error_label.setText("Пароли не совпадают")
            return

        # ПРОВЕРКА КАПТЧИ УБРАНА

        # Регистрация
        success, message = self.user_manager.register_user(username, email, password)

        if success:
            QMessageBox.information(self, "Успех", message)
            # Закрываем окно регистрации и возвращаемся к окну входа
            self.done(QDialog.Accepted)
        else:
            self.error_label.setText(message)

    def back_to_login(self):
        """Возврат к окну входа"""
        # ИЗМЕНЕНИЕ: Используем reject() для правильного закрытия окна регистрации
        self.reject()

class LoginWindow(QDialog):
    def __init__(self, user_manager):
        super().__init__()
        self.user_manager = user_manager
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Вход в аккаунт")
        self.setFixedSize(500, 650)  # Увеличена высота окна для добавления поля email
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                border: 2px solid #4CAF50;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit, QPushButton {
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)  # Увеличены отступы
        layout.setContentsMargins(40, 40, 40, 40)

        # Заголовок
        title_label = QLabel("Вход в Factory Market")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Имя пользователя ИЛИ Email (новое поле)
        username_email_label = QLabel("Имя пользователя или Email:")
        layout.addWidget(username_email_label)

        self.username_email_input = QLineEdit()
        self.username_email_input.setPlaceholderText("Введите имя пользователя или email")
        self.username_email_input.setFixedHeight(45)  # Увеличенная высота поля ввода
        self.username_email_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                font-size: 14px;
                padding: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.username_email_input)

        # Пароль
        password_label = QLabel("Пароль:")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setFixedHeight(45)  # Увеличенная высота поля ввода
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                font-size: 14px;
                padding: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.password_input)

        # Чекбокс "Запомнить меня"
        self.remember_check = QCheckBox("Запомнить меня")
        self.remember_check.setStyleSheet("color: #ffffff; font-size: 14px;")
        layout.addWidget(self.remember_check)

        # Сообщения об ошибках
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f44336; font-size: 12px;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        # Кнопка входа
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.login)
        login_btn.setFixedHeight(50)  # Увеличенная высота кнопки
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                font-weight: bold;
                margin-top: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(login_btn)

        # Ссылка на регистрацию
        register_link = QLabel(
            '<a href="#" style="color: #2196F3; text-decoration: none; font-size: 14px;">Нет аккаунта? Создайте бесплатный аккаунт</a>')
        register_link.setAlignment(Qt.AlignCenter)
        register_link.setTextFormat(Qt.RichText)
        register_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        register_link.linkActivated.connect(self.show_register)
        layout.addWidget(register_link)

        layout.addStretch()
        self.setLayout(layout)

    def login(self):
        """Обработка входа"""
        username_email = self.username_email_input.text().strip()
        password = self.password_input.text()

        if not username_email:
            self.error_label.setText("Введите имя пользователя или email")
            return

        if not password:
            self.error_label.setText("Введите пароль")
            return

        # Проверяем, является ли ввод email'ом
        if '@' in username_email:
            # Ищем пользователя по email
            username = None
            for user, data in self.user_manager.users.items():
                if data.get("email", "").lower() == username_email.lower():
                    username = user
                    break

            if not username:
                self.error_label.setText("Пользователь с таким email не найден")
                return
        else:
            username = username_email

        success, message = self.user_manager.login_user(username, password)

        if success:
            self.accept()
        else:
            self.error_label.setText(message)

    def show_register(self):
        """Показать окно регистрации - УЛУЧШЕННАЯ ЛОГИКА"""
        self.hide()

        register_window = RegisterWindow(self.user_manager, self)
        result = register_window.exec_()

        self.show()

        if result == QDialog.Accepted:
            if hasattr(register_window, 'username_input'):
                self.username_email_input.setText(register_window.username_input.text())
            if hasattr(register_window, 'password_input'):
                self.password_input.setText(register_window.password_input.text())
            self.error_label.setText("Регистрация успешна! Можете войти.")
            self.error_label.setStyleSheet("color: #4CAF50; font-size: 12px;")

class InternetCheckDialog(QDialog):
    def __init__(self, auto_reconnect=True):
        super().__init__()
        self.auto_reconnect = auto_reconnect
        self.connection_found = False
        self.initUI()
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_internet)
        self.check_timer.start(1000)  # Проверять каждую секунду

        # Таймер для авто-повторного поиска
        self.retry_timer = QTimer()
        if auto_reconnect:
            self.retry_timer.timeout.connect(self.auto_check_internet)
            self.retry_timer.start(5000)  # Авто-проверка каждые 5 секунд

    def initUI(self):
        self.setWindowTitle("Проверка подключения")
        self.setFixedSize(500, 300)  # Увеличил размер окна
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Иконка
        self.icon_label = QLabel("🌐")
        self.icon_label.setStyleSheet("font-size: 60px;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        # Заголовок
        self.title_label = QLabel("Проверка подключения")
        self.title_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold; text-align: center;")
        layout.addWidget(self.title_label)

        # Сообщение
        self.message_label = QLabel("Проверка подключения к интернету...")
        self.message_label.setStyleSheet("color: #aaaaaa; font-size: 16px; text-align: center;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        # Индикатор загрузки
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Бесконечная анимация
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        # Кнопка повторной проверки
        self.retry_button = QPushButton("🔄 Повторить проверку")
        self.retry_button.clicked.connect(self.manual_retry)
        self.retry_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.retry_button.hide()
        layout.addWidget(self.retry_button)

        # Информация о подключении
        self.info_label = QLabel("Приложение автоматически продолжит поиск подключения")
        self.info_label.setStyleSheet("color: #888888; font-size: 12px; text-align: center;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                background-color: #252525;
                height: 15px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

    def check_internet(self):
        """Основная проверка интернет соединения"""
        if InternetChecker.check_internet():
            self.connection_found = True
            self.show_connection_found()
        else:
            self.show_no_connection()

    def auto_check_internet(self):
        """Автоматическая проверка подключения"""
        if not self.connection_found and InternetChecker.check_internet():
            self.connection_found = True
            self.show_connection_found()
            self.accept()

    def manual_retry(self):
        """Ручная попытка проверки"""
        self.message_label.setText("Проверка подключения...")
        self.progress.show()
        self.retry_button.hide()
        self.check_internet()

    def show_connection_found(self):
        """Показать сообщение о найденном подключении"""
        self.icon_label.setText("✅")
        self.title_label.setText("Подключение найдено!")
        self.message_label.setText("Интернет соединение установлено успешно.")
        self.message_label.setStyleSheet("color: #4CAF50; font-size: 16px; text-align: center;")
        self.progress.hide()
        self.retry_button.hide()
        self.info_label.setText("Приложение будет запущено через 2 секунды...")

        # Закрыть диалог через 2 секунды
        QTimer.singleShot(2000, self.accept)

    def show_no_connection(self):
        """Показать сообщение об отсутствии подключения"""
        self.icon_label.setText("❌")
        self.title_label.setText("Подключение отсутствует")
        self.message_label.setText(
            "Не удалось установить соединение с интернетом.\nПроверьте ваше подключение и повторите попытку.")
        self.message_label.setStyleSheet("color: #f44336; font-size: 16px; text-align: center;")
        self.progress.hide()
        self.retry_button.show()

        if self.auto_reconnect:
            self.info_label.setText("Автоматический поиск продолжится через 5 секунд...")
        else:
            self.info_label.setText("Нажмите кнопку для повторной проверки")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if not self.connection_found:
            reply = QMessageBox.question(self, 'Выход',
                                         'Подключение к интернету не найдено. Вы уверены, что хотите закрыть приложение?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                event.accept()
                sys.exit(0)
            else:
                event.ignore()


# ============================================
# ИСХОДНЫЕ КЛАССЫ (сохраняем функционал)
# ============================================
class ImageManager(QObject):
    """Менеджер для загрузки и кэширования изображений из Steam"""
    cover_downloaded = pyqtSignal(str)  # Сигнал объявляется здесь

    def __init__(self):
        super().__init__()
        self.cache_dir = Path("image_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.screenshots_dir = Path("screenshot_game")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.trailers_dir = Path("trailer_game")
        self.trailers_dir.mkdir(exist_ok=True)
        self.network_manager = QNetworkAccessManager()
        self.memory_cache = {}

        # Steam App IDs для всех игр
        self.steam_app_ids = {
            # Существующие игры
            1: 1091500,  # Cyberpunk 2077
            2: 292030,  # The Witcher 3
            3: 730,  # Counter-Strike 2
            4: 1248130,  # Farming Simulator 22
            5: 949230,  # Cities Skylines II
            6: 990080,  # Hogwarts Legacy
            7: 747660,  # FNAF Security Breach
            8: 70,  # Half-Life
            9: 220,  # Half-Life 2
            10: 632470,  # Disco Elysium
            11: 620,  # Portal 2
            12: 413150,  # Stardew Valley
            13: 570,  # Dota 2
            16: 418370,  # Resident Evil 7

            # Существующие новые игры
            17: 271590,  # GTA V
            18: 400,  # Portal
            19: 440,  # Team Fortress 2
            20: 12100,  # GTA 3
            21: 105600,  # Terraria

            # Новые игры
            22: 391540,  # Undertale
            23: 12110,  # GTA Vice City
            24: 12120,  # GTA San Andreas
            25: 12210,  # GTA 4 The Complete Edition
            26: 1817190,  # Spider-Man 2 (PS5)
            27: 42700,  # Call of Duty: Black Ops
            28: 1671210,  # Deltarune Chapter 1-2

            # Новые игры
            29: 319510,  # Five Nights at Freddy's
            30: 1575870,  # UpGun

            # Игры с добавленными Steam ID
            31: 3527290,  # peak
            32: 418070,  # Turbo Pug

            # Добавленная новая игра
            33: 130,  # Half-Life: Blue Shift

            # Новые добавленные игры
            34: 332800,  # Five Nights at Freddy's 2
            35: 546560,  # Half-Life: Alyx

            # Новые добавленные игры
            36: 50,  # Half-Life: Opposing Force
            38: 362890,  # Black Mesa
            39: 10090,  # Call of Duty: World at War

            # Новые добавленные игры
            40: 500,  # Left 4 Dead
            41: 354140,  # Five Nights at Freddy's 3
            42: 388090,  # Five Nights at Freddy's 4
            43: 202970,  # Call of Duty: Black Ops 2
            44: 376870,  # Minecraft: Story Mode

            # Новые добавленные игры
            45: 550,  # Left 4 Dead 2
            46: 506610,  # Five Nights at Freddy's: Sister Location
            47: 2762040,  # Five Nights at Freddy's Help Wanted 2
            48: 739630,  # Phasmophobia
            49: 1172620,  # R.E.P.O
            50: 1332010,  # Stray

            # Новые добавленные игры
            51: 638070,  # Freddy Fazbear's Pizzeria Simulator
            52: 639170,  # Minecraft: Story Mode - Season Two
            53: 871720,  # Ultimate Custom Night
            54: 311210,  # Call of Duty: Black Ops 3
            55: 732690,  # FIVE NIGHTS AT FREDDY'S: HELP WANTED

            # Новая добавленная игра
            56: 2215390,  # Five Nights at Freddy's: Secret of the Mimic

            # Новые добавленные игры
            57: 1895880,  # Call of Duty: Black Ops 4
            58: 21690,  # Resident Evil 5
            59: 221040,  # Resident Evil 6
            60: 2577840,  # Five Nights at Freddy's: into the pit

            # ДОБАВЛЕНЫ 5 НОВЫХ ИГР
            61: 578080,  # PUBG: BATTLEGROUNDS
            62: 1174180,  # Red Dead Redemption 2
            63: 1085660,  # Destiny 2
            64: 1466860,  # Elden Ring
            65: 1245620,  # EA SPORTS FC™ 24

            # ДОБАВЛЕНЫ 3 НОВЫХ ЛЮБИМЫХ ИГРЫ
            66: 1240440,  # Halo Infinite
            67: 1145360,  # Hadas
            68: 1326470,  # Sons of the Forest

            # НОВЫЕ ДОБАВЛЕННЫЕ ИГРЫ
            69: 47890,  # The Sims
            70: 16700,  # The Sims 2
        }

    def get_game_cover(self, game_id, game_name, force_reload=False):
        """Получение обложки игры из Steam или создание серой заглушки"""
        cache_key = f"{game_id}_{game_name}"

        # Проверяем в памяти (если не форсируем перезагрузку)
        if not force_reload and cache_key in self.memory_cache:
            return self.memory_cache[cache_key]

        # Проверяем на диске
        cache_file = self.cache_dir / f"{cache_key}.jpg"
        if not force_reload and cache_file.exists():
            pixmap = QPixmap(str(cache_file))
            if not pixmap.isNull():
                self.memory_cache[cache_key] = pixmap
                return pixmap

        # Если есть Steam ID, загружаем из Steam
        if game_id in self.steam_app_ids and self.steam_app_ids[game_id]:
            steam_app_id = self.steam_app_ids[game_id]
            url = f"https://cdn.akamai.steamstatic.com/steam/apps/{steam_app_id}/header.jpg"
            self.download_cover(game_id, game_name, url)

        # Возвращаем серую заглушку
        pixmap = self.create_gray_placeholder(game_id, game_name)
        self.memory_cache[cache_key] = pixmap
        return pixmap

    def get_game_screenshots(self, game_id, max_count=5):
        """Получение скриншотов игры из Steam"""
        screenshots = []

        if game_id in self.steam_app_ids and self.steam_app_ids[game_id]:
            steam_app_id = self.steam_app_ids[game_id]

            # Специальная обработка для игры с ID 56 - измененное имя файла
            if game_id == 56:
                # Проверяем новый файл с измененным именем
                new_file = self.cache_dir / "56_fnaf_mimic.jpg"
                if new_file.exists():
                    # Копируем файл в директорию скриншотов для использования
                    import shutil
                    screenshot_file = self.screenshots_dir / "56_0.jpg"
                    if not screenshot_file.exists():
                        shutil.copy2(new_file, screenshot_file)

            # Проверяем, есть ли сохраненные скриншоты
            screenshot_files = list(self.screenshots_dir.glob(f"{game_id}_*.jpg"))

            if screenshot_files:
                # Загружаем сохраненные скриншоты
                for screenshot_file in screenshot_files[:max_count]:
                    pixmap = QPixmap(str(screenshot_file))
                    if not pixmap.isNull():
                        screenshots.append(pixmap)
            else:
                # Загружаем скриншоты из Steam
                for i in range(max_count):
                    url = f"https://cdn.akamai.steamstatic.com/steam/apps/{steam_app_id}/ss_{i}.jpg"
                    screenshot = self.download_screenshot(game_id, i, url)
                    if screenshot:
                        screenshots.append(screenshot)

        return screenshots

    def get_game_trailer_path(self, game_name):
        """Получение пути к трейлеру игры"""
        # Проверяем наличие трейлеров для конкретных игр FNAF
        trailer_files = {
            "Five Nights at Freddy's: Security Breach": "Five Nights at Freddy's Security Breach_trailer",
            "Five Nights at Freddy's: Secret of the Mimic": "Five Nights at Freddy's Secret of the Mimic_trailer"
        }

        if game_name in trailer_files:
            # Проверяем различные расширения видеофайлов
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
            for ext in video_extensions:
                trailer_path = self.trailers_dir / f"{trailer_files[game_name]}{ext}"
                if trailer_path.exists():
                    return str(trailer_path)

        return None

    def download_cover(self, game_id, game_name, url):
        """Асинхронная загрузка обложки"""
        cache_key = f"{game_id}_{game_name}"

        # Создаем поток для загрузки
        thread = threading.Thread(
            target=self.download_cover_thread,
            args=(game_id, game_name, url, cache_key),
            daemon=True
        )
        thread.start()

    def download_screenshot(self, game_id, index, url):
        """Загрузка скриншота"""
        try:
            import requests
            from io import BytesIO

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)

                # Сохраняем скриншот
                screenshot_file = self.screenshots_dir / f"{game_id}_{index}.jpg"
                with open(screenshot_file, 'wb') as f:
                    f.write(response.content)

                return pixmap
        except Exception as e:
            print(f"Ошибка загрузки скриншота для игры {game_id}: {e}")
        return None

    def download_cover_thread(self, game_id, game_name, url, cache_key):
        """Загрузка обложки в отдельном потоке"""
        try:
            import requests
            from io import BytesIO

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Сохраняем на диск
                cache_file = self.cache_dir / f"{cache_key}.jpg"
                with open(cache_file, 'wb') as f:
                    f.write(response.content)

                # Обновляем в памяти
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)

                # Используем QMetaObject для безопасного обновления UI из другого потока
                QMetaObject.invokeMethod(self, "update_cover_in_cache",
                                         Qt.QueuedConnection,
                                         Q_ARG(str, cache_key),
                                         Q_ARG(QPixmap, pixmap))

                # Отправляем сигнал для обновления UI
                self.cover_downloaded.emit(cache_key)
        except Exception as e:
            print(f"Ошибка загрузки обложки для {game_name}: {e}")
            # В случае ошибки создаем серую заглушку
            pixmap = self.create_gray_placeholder(game_id, game_name)
            QMetaObject.invokeMethod(self, "update_cover_in_cache",
                                     Qt.QueuedConnection,
                                     Q_ARG(str, cache_key),
                                     Q_ARG(QPixmap, pixmap))

    @pyqtSlot(str, QPixmap)
    def update_cover_in_cache(self, cache_key, pixmap):
        """Обновление кэша из основного потока"""
        self.memory_cache[cache_key] = pixmap

    def create_gray_placeholder(self, game_id, game_name):
        """Создание серой заглушки"""
        pixmap = QPixmap(300, 150)

        # Серый градиент
        gradient = QLinearGradient(0, 0, 300, 150)
        gradient.setColorAt(0, QColor(100, 100, 100))
        gradient.setColorAt(1, QColor(70, 70, 70))

        painter = QPainter(pixmap)
        painter.fillRect(pixmap.rect(), gradient)

        # Добавляем иконку игры
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Arial", 48, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🎮")

        # Добавляем текст с названием
        painter.setFont(QFont("Arial", 12, QFont.Normal))
        painter.setPen(QColor(180, 180, 180))

        # Обрезаем название если слишком длинное
        display_name = game_name
        if len(display_name) > 20:
            display_name = game_name[:17] + "..."

        text_rect = QRect(0, 100, 300, 50)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, display_name)

        painter.end()

        return pixmap


class StorePage(QWidget):
    """Страница магазина"""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.all_games = []
        self.filtered_games = []
        self.image_manager = ImageManager()
        self.image_manager.cover_downloaded.connect(self.on_cover_downloaded)
        self.initUI()
        self.shuffle_games()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок магазина
        title_label = QLabel("🎮 Factory Market")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Панель поиска и фильтров
        search_panel = self.create_search_panel()
        layout.addWidget(search_panel)

        # Прокручиваемая область с играми
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.store_widget = QWidget()
        self.store_layout = QVBoxLayout()
        self.store_layout.setContentsMargins(0, 0, 0, 0)
        self.store_widget.setLayout(self.store_layout)

        # Контейнер для сетки игр
        self.games_container = QWidget()
        self.games_grid = QGridLayout()
        self.games_grid.setSpacing(15)  # Уменьшили отступы для 5 колонок
        self.games_grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.games_container.setLayout(self.games_grid)

        self.store_layout.addWidget(self.games_container)
        self.scroll_area.setWidget(self.store_widget)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)

        # Загружаем игры магазина
        self.load_all_games()
        self.filtered_games = self.all_games.copy()
        self.display_games()

    def shuffle_games(self):
        """Перемешивание игр в магазине"""
        random.shuffle(self.all_games)
        if hasattr(self, 'category_combo') and self.category_combo.currentText() == "Все":
            random.shuffle(self.filtered_games)
            self.display_games()

    def on_cover_downloaded(self, cache_key):
        """Обновление обложек после загрузки"""
        self.display_games()

    def create_search_panel(self):
        """Панель поиска и фильтров магазина"""
        panel = QWidget()
        panel.setFixedHeight(60)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Поле поиска
        self.store_search = QLineEdit()
        self.store_search.setPlaceholderText("Поиск в магазине...")
        self.store_search.textChanged.connect(self.apply_filters)
        self.store_search.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 300px;
            }
        """)
        layout.addWidget(self.store_search)

        # Выбор категорий
        categories = ["Все", "Экшен", "RPG", "Стратегии", "Гонки", "Инди", "Хоррор", "Симуляторы", "Приключения",
                      "MOBA", "Шутер"]
        self.category_combo = QComboBox()
        self.category_combo.addItems(categories)
        self.category_combo.currentTextChanged.connect(self.apply_filters)
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        layout.addWidget(self.category_combo)

        layout.addStretch()

        # Кнопка профиля
        self.profile_button = QPushButton("👤 Профиль")
        self.profile_button.clicked.connect(self.show_profile_page)
        self.profile_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.profile_button)

        panel.setLayout(layout)
        return panel

    def show_profile_page(self):
        """Переход на страницу профиля"""
        self.main_app.show_profile_page()

    def load_all_games(self):
        """Загрузка всех игр магазина"""
        self.all_games = [
            # Существующие игры
            {
                "id": 1,
                "name": "Cyberpunk 2077",
                "developer": "CD Projekt Red",
                "category": "RPG",
                "rating": 4.5,
                "description": "Откройте для себя Найт-Сити — мегаполис будущего.",
                "release_date": "2020-12-10",
                "features": ["Открытый мир", "RPG", "Киберпанк"]
            },
            {
                "id": 2,
                "name": "The Witcher 3: Wild Hunt",
                "developer": "CD Projekt Red",
                "category": "RPG",
                "rating": 4.9,
                "description": "Беспощадный охотник на чудовищ в огромном фэнтезийном мире.",
                "release_date": "2015-05-19",
                "features": ["Открытый мир", "Фэнтези", "Сюжетная игра"]
            },
            {
                "id": 3,
                "name": "Counter-Strike 2",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.7,
                "description": "Бесплатный шутер от первого лица.",
                "release_date": "2023-09-27",
                "features": ["Мультиплеер", "Тактический", "Командный"]
            },
            {
                "id": 4,
                "name": "Farming Simulator 22",
                "developer": "GIANTS Software",
                "category": "Симуляторы",
                "rating": 4.2,
                "description": "Реалистичный симулятор фермера.",
                "release_date": "2021-11-22",
                "features": ["Симулятор", "Сельское хозяйство", "Расслабляющая"]
            },
            {
                "id": 5,
                "name": "Cities: Skylines II",
                "developer": "Colossal Order",
                "category": "Стратегии",
                "rating": 4.0,
                "description": "Стройте и управляйте мегаполисом будущего.",
                "release_date": "2023-10-24",
                "features": ["Город-строитель", "Стратегия", "Управление"]
            },
            {
                "id": 6,
                "name": "Hogwarts Legacy",
                "developer": "Avalanche Software",
                "category": "RPG",
                "rating": 4.6,
                "description": "Отправьтесь в Хогвартс 1800-х годов.",
                "release_date": "2023-02-10",
                "features": ["Хогвартс", "Магия", "Открытый мир"]
            },
            {
                "id": 7,
                "name": "Five Nights at Freddy's: Security Breach",
                "developer": "Steel Wool Studios",
                "category": "Хоррор",
                "rating": 3.8,
                "description": "Грегори - мальчик, который оказался в ловушке в гигантском мегапазио Freddy Fazbear. С помощью Фредди и его друзей Грегори должен выжить до 6 утра, скрываясь от кровожадного охранника, а также неутомимых аниматроников, которые его преследуют.",
                "steam_description": "Five Nights at Freddy's: Security Breach - это захватывающая хоррор-игра с элементами стелса и выживания, где вам предстоит провести ночь в огромном мегапазио, избегая опасных аниматроников.",
                "release_date": "2021-12-16",
                "features": ["Хоррор", "Выживание", "Аниматроники", "Стелс", "Исследование"]
            },
            {
                "id": 8,
                "name": "Half-Life",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.8,
                "description": "Культовая игра, изменившая индустрию.",
                "release_date": "1998-11-19",
                "features": ["Шутер", "Научная фантастика", "Культовая"]
            },
            {
                "id": 9,
                "name": "Half-Life 2",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.9,
                "description": "Продолжение легендарного шутера.",
                "release_date": "2004-11-16",
                "features": ["Шутер", "Физика", "Сюжет"]
            },
            {
                "id": 10,
                "name": "Disco Elysium",
                "developer": "ZA/UM",
                "category": "RPG",
                "rating": 4.7,
                "description": "Детективный RPG с глубоким диалоговым деревом.",
                "release_date": "2019-10-15",
                "features": ["Детектив", "Диалоги", "RPG"]
            },
            {
                "id": 11,
                "name": "Portal 2",
                "developer": "Valve",
                "category": "Приключения",
                "rating": 4.8,
                "description": "Головоломка с порталами и черным юмором.",
                "release_date": "2011-04-19",
                "features": ["Головоломка", "Научная фантастика", "Юмор"]
            },
            {
                "id": 12,
                "name": "Stardew Valley",
                "developer": "ConcernedApe",
                "category": "Симуляторы",
                "rating": 4.9,
                "description": "Фермерский симулятор в пиксельном стиле.",
                "release_date": "2016-02-26",
                "features": ["Ферма", "Расслабляющая", "Пиксельная графика"]
            },
            {
                "id": 13,
                "name": "Dota 2",
                "developer": "Valve",
                "category": "MOBA",
                "rating": 4.6,
                "description": "Бесплатная MOBA с миллионами игроков по всему миру.",
                "release_date": "2013-07-09",
                "features": ["MOBA", "Мультиплеер", "Бесплатная"]
            },
            {
                "id": 16,
                "name": "Resident Evil 7: Biohazard",
                "developer": "Capcom",
                "category": "Хоррор",
                "rating": 4.4,
                "description": "Возвращение к корням серии Resident Evil.",
                "release_date": "2017-01-24",
                "features": ["Хоррор", "Выживание", "От первого лица"]
            },
            {
                "id": 17,
                "name": "Grand Theft Auto V",
                "developer": "Rockstar Games",
                "category": "Экшен",
                "rating": 4.8,
                "description": "Культовая игра про криминальный мир Лос-Сантоса.",
                "release_date": "2015-04-14",
                "features": ["Открытый мир", "Криминал", "Мультиплеер"]
            },
            {
                "id": 18,
                "name": "Portal",
                "developer": "Valve",
                "category": "Приключения",
                "rating": 4.9,
                "description": "Культовая головоломка с портальной пушкой.",
                "release_date": "2007-10-10",
                "features": ["Головоломка", "Научная фантастика", "Юмор"]
            },
            {
                "id": 19,
                "name": "Team Fortress 2",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.8,
                "description": "Бесплатный командный шутер с уникальными классами.",
                "release_date": "2007-10-10",
                "features": ["Мультиплеер", "Командный", "Бесплатный"]
            },
            {
                "id": 20,
                "name": "Grand Theft Auto III",
                "developer": "Rockstar Games",
                "category": "Экшен",
                "rating": 4.5,
                "description": "Игра, определившая жанр открытого мира.",
                "release_date": "2001-10-22",
                "features": ["Открытый мир", "Криминал", "Классика"]
            },
            {
                "id": 21,
                "name": "Terraria",
                "developer": "Re-Logic",
                "category": "Приключения",
                "rating": 4.9,
                "description": "2D песочница с исследованием, крафтом и сражениями.",
                "release_date": "2011-05-16",
                "features": ["Песочница", "Крафт", "Исследование"]
            },
            {
                "id": 22,
                "name": "Undertale",
                "developer": "Toby Fox",
                "category": "Инди",
                "rating": 4.9,
                "description": "Культовая RPG, где никто не должен умереть.",
                "release_date": "2015-09-15",
                "features": ["RPG", "Инди", "Сюжетная"]
            },
            {
                "id": 23,
                "name": "Grand Theft Auto: Vice City",
                "developer": "Rockstar Games",
                "category": "Экшен",
                "rating": 4.7,
                "description": "Культовая игра про криминальный мир Вайс-Сити в 80-х.",
                "release_date": "2002-10-27",
                "features": ["Открытый мир", "Криминал", "80-е годы"]
            },
            {
                "id": 24,
                "name": "Grand Theft Auto: San Andreas",
                "developer": "Rockstar Games",
                "category": "Экшен",
                "rating": 4.8,
                "description": "Легендарная игра про банды в штате Сан-Андреас.",
                "release_date": "2004-10-26",
                "features": ["Открытый мир", "Гангстеры", "Кастомизация"]
            },
            {
                "id": 25,
                "name": "Grand Theft Auto IV",
                "developer": "Rockstar Games",
                "category": "Экшен",
                "rating": 4.7,
                "description": "История Нико Беллика в Либерти-Сити.",
                "release_date": "2008-04-29",
                "features": ["Открытый мир", "Драма", "Реализм"]
            },
            {
                "id": 26,
                "name": "Marvel's Spider-Man 2",
                "developer": "Insomniac Games",
                "category": "Экшен",
                "rating": 4.9,
                "description": "Приключения Питера Паркера и Майлза Моралеса.",
                "release_date": "2023-10-20",
                "features": ["Супергерои", "Открытый мир", "Марвел"]
            },
            {
                "id": 27,
                "name": "Call of Duty: Black Ops",
                "developer": "Treyarch",
                "category": "Шутер",
                "rating": 4.7,
                "description": "Легендарный шутер с захватывающим сюжетом.",
                "release_date": "2010-11-09",
                "features": ["Шутер", "Холодная война", "Мультиплеер"]
            },
            {
                "id": 28,
                "name": "Deltarune",
                "developer": "Toby Fox",
                "category": "Инди",
                "rating": 4.8,
                "description": "Приключенческая RPG от создателя Undertale.",
                "release_date": "2018-10-31",
                "features": ["RPG", "Приключение", "Инди"]
            },
            {
                "id": 29,
                "name": "Five Nights at Freddy's",
                "developer": "Scott Cawthon",
                "category": "Хоррор",
                "rating": 4.5,
                "description": "Культовая хоррор-игра про аниматроников.",
                "release_date": "2014-08-08",
                "features": ["Хоррор", "Выживание", "Инди"]
            },
            {
                "id": 30,
                "name": "UpGun",
                "developer": "Numinous Games",
                "category": "Шутер",
                "rating": 4.2,
                "description": "Быстрый шутер с уникальными режимами игры.",
                "release_date": "2022-03-15",
                "features": ["Шутер", "Мультиплеер", "Аркада"]
            },
            {
                "id": 31,
                "name": "peak",
                "developer": "Unknown",
                "category": "Инди",
                "rating": 3.9,
                "description": "Минималистичная инди-игра с уникальной механикой.",
                "release_date": "2022-03-15",
                "features": ["Минимализм", "Инди", "Расслабляющая"]
            },
            {
                "id": 32,
                "name": "Turbo Pug",
                "developer": "Pug Studios",
                "category": "Гонки",
                "rating": 4.2,
                "description": "Безумные гонки с мопсами на турбо-двигателях.",
                "release_date": "2021-07-20",
                "features": ["Гонки", "Мопсы", "Веселье"]
            },
            {
                "id": 33,
                "name": "Half-Life: Blue Shift",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.3,
                "description": "Аддон к Half-Life, рассказывающий историю Барни Калхуна.",
                "release_date": "2001-06-12",
                "features": ["Шутер", "Научная фантастика", "Аддон"]
            },
            {
                "id": 34,
                "name": "Five Nights at Freddy's 2",
                "developer": "Scott Cawthon",
                "category": "Хоррор",
                "rating": 4.6,
                "description": "Вторая часть культовой хоррор серии про аниматроников.",
                "release_date": "2014-11-10",
                "features": ["Хоррор", "Выживание", "Инди"]
            },
            {
                "id": 35,
                "name": "Half-Life: Alyx",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.9,
                "description": "Продолжение легендарной серии Half-Life в виртуальной реальности.",
                "release_date": "2020-03-23",
                "features": ["VR", "Шутер", "Научная фантастика"]
            },
            {
                "id": 36,
                "name": "Half-Life: Opposing Force",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.4,
                "description": "Дополнение к Half-Life с точки зрения солдата спецназа.",
                "release_date": "1999-11-10",
                "features": ["Шутер", "Научная фантастика", "Дополнение"]
            },
            {
                "id": 38,
                "name": "Black Mesa",
                "developer": "Crowbar Collective",
                "category": "Шутер",
                "rating": 4.8,
                "description": "Ремейк оригинального Half-Life на движке Source.",
                "release_date": "2020-03-06",
                "features": ["Шутер", "Ремейк", "Научная фантастика"]
            },
            {
                "id": 39,
                "name": "Call of Duty: World at War",
                "developer": "Treyarch",
                "category": "Шутер",
                "rating": 4.7,
                "description": "Эпический шутер про Вторую мировую войну.",
                "release_date": "2008-11-11",
                "features": ["Шутер", "Вторая мировая война", "Мультиплеер"]
            },
            {
                "id": 40,
                "name": "Left 4 Dead",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.8,
                "description": "Кооперативный шутер про выживание в зомби+апокалипсисе.",
                "release_date": "2008-11-17",
                "features": ["Зомби", "Кооператив", "Выживание"]
            },
            {
                "id": 41,
                "name": "Five Nights at Freddy's 3",
                "developer": "Scott Cawthon",
                "category": "Хоррор",
                "rating": 4.5,
                "description": "Третья часть культовой хоррор серии про аниматроников.",
                "release_date": "2015-03-02",
                "features": ["Хоррор", "Выживание", "Инди"]
            },
            {
                "id": 42,
                "name": "Five Nights at Freddy's 4",
                "developer": "Scott Cawthon",
                "category": "Хоррор",
                "rating": 4.4,
                "description": "Четвертая часть культовой хоррор серии про аниматроников.",
                "release_date": "2015-07-23",
                "features": ["Хоррор", "Выживание", "Инди"]
            },
            {
                "id": 43,
                "name": "Call of Duty: Black Ops 2",
                "developer": "Treyarch",
                "category": "Шутер",
                "rating": 4.8,
                "description": "Продолжение легендарного шутера с футуристическим сеттингом.",
                "release_date": "2012-11-12",
                "features": ["Шутер", "Будущее", "Мультиплеер"]
            },
            {
                "id": 44,
                "name": "Minecraft: Story Mode",
                "developer": "Telltale Games",
                "category": "Приключения",
                "rating": 4.3,
                "description": "Приключенческая игра в мире Minecraft от Telltale Games.",
                "release_date": "2015-10-13",
                "features": ["Minecraft", "Приключение", "Сюжетная"]
            },
            {
                "id": 45,
                "name": "Left 4 Dead 2",
                "developer": "Valve",
                "category": "Шутер",
                "rating": 4.9,
                "description": "Продолжение культового кооперативного шутера про зомби.",
                "release_date": "2009-11-17",
                "features": ["Зомби", "Кооператив", "Выживание"]
            },
            {
                "id": 46,
                "name": "Five Nights at Freddy's: Sister Location",
                "developer": "Scott Cawthon",
                "category": "Хоррор",
                "rating": 4.6,
                "description": "Пятая часть серии FNAF с новыми механиками и локацией.",
                "release_date": "2016-10-07",
                "features": ["Хоррор", "Выживание", "Инди"]
            },
            {
                "id": 47,
                "name": "Five Nights at Freddy's Help Wanted 2",
                "developer": "Steel Wool Studios",
                "category": "Хоррор",
                "rating": 4.5,
                "description": "Вторая часть VR-хоррора по вселенной FNAF.",
                "release_date": "2023-12-14",
                "features": ["VR", "Хоррор", "Выживание"]
            },
            {
                "id": 48,
                "name": "Phasmophobia",
                "developer": "Kinetic Games",
                "category": "Хоррор",
                "rating": 4.8,
                "description": "Кооперативный хоррор про охоту на привидений.",
                "release_date": "2020-09-18",
                "features": ["Привидения", "Кооператив", "Инди"]
            },
            {
                "id": 49,
                "name": "R.E.P.O",
                "developer": "DreamStorm Studios",
                "category": "Инди",
                "rating": 4.1,
                "description": "Инди-игра с уникальным геймплеем и стилем.",
                "release_date": "2021-03-15",
                "features": ["Инди", "Экшен", "Приключение"]
            },
            {
                "id": 50,
                "name": "Stray",
                "developer": "BlueTwelve Studio",
                "category": "Приключения",
                "rating": 4.7,
                "description": "Приключенческая игра, где вы играете за кота в киберпанк-городе.",
                "release_date": "2022-07-19",
                "features": ["Кот", "Киберпанк", "Приключение"]
            },
            # Новые добавленные игры
            {
                "id": 51,
                "name": "Freddy Fazbear's Pizzeria Simulator",
                "developer": "Scott Cawthon",
                "category": "Симуляторы",
                "rating": 4.5,
                "description": "Управляйте собственной пиццерией Freddy Fazbear и следите за аниматрониками.",
                "release_date": "2017-12-04",
                "features": ["Симулятор", "Хоррор", "Менеджмент"]
            },
            {
                "id": 52,
                "name": "Minecraft: Story Mode - Season Two",
                "developer": "Telltale Games",
                "category": "Приключения",
                "rating": 4.4,
                "description": "Продолжение приключенческой истории в мире Minecraft.",
                "release_date": "2017-07-11",
                "features": ["Minecraft", "Приключение", "Сюжетная", "Диалоги"]
            },
            {
                "id": 53,
                "name": "Ultimate Custom Night",
                "developer": "Scott Cawthon",
                "category": "Хоррор",
                "rating": 4.7,
                "description": "Создайте свою собственную ночь с более чем 50 аниматрониками из вселенной FNAF.",
                "release_date": "2018-06-27",
                "features": ["Хоррор", "Кастомизация", "Выживание"]
            },
            {
                "id": 54,
                "name": "Call of Duty: Black Ops 3",
                "developer": "Treyarch",
                "category": "Шутер",
                "rating": 4.6,
                "description": "Футуристический шутер с кооперативным кампанией и зомби-режимом.",
                "release_date": "2015-11-06",
                "features": ["Шутер", "Футуристический", "Кооператив", "Зомби"]
            },
            {
                "id": 55,
                "name": "FIVE NIGHTS AT FREDDY'S: HELP WANTED",
                "developer": "Steel Wool Studios",
                "category": "Хоррор",
                "rating": 4.8,
                "description": "VR-сборник лучших ночей из вселенной Five Nights at Freddy's.",
                "release_date": "2019-05-28",
                "features": ["VR", "Хоррор", "Сборник", "Аниматроники"]
            },
            # Новая игра: Five Nights at Freddy's: Secret of the Mimic
            {
                "id": 56,
                "name": "Five Nights at Freddy's: Secret of the Mimic",
                "developer": "Steel Wool Studios",
                "category": "Хоррор",
                "rating": 4.6,
                "description": "Новая захватывающая глава в серии Five Nights at Freddy's с новыми механиками и загадками.",
                "steam_description": "Five Nights at Freddy's: Secret of the Mimic - новая хоррор-игра, где вам предстоит столкнуться с таинственным мимиком, способным принимать облик других аниматроников.",
                "release_date": "2023-10-27",
                "features": ["Хоррор", "Выживание", "Аниматроники", "Загадки", "Новая механика"]
            },
            # Новые игры
            {
                "id": 57,
                "name": "Call of Duty: Black Ops 4",
                "developer": "Treyarch",
                "category": "Шутер",
                "rating": 4.4,
                "description": "Эпический шутер с акцентом на мультиплеер и зомби-режим.",
                "steam_description": "Call of Duty: Black Ops 4 - это культовый шутер с тремя режимами: Мультиплеер, Зомби и Боевая арена.",
                "release_date": "2018-10-12",
                "features": ["Шутер", "Мультиплеер", "Зомби", "Тактический"]
            },
            {
                "id": 58,
                "name": "Resident Evil 5",
                "developer": "Capcom",
                "category": "Экшен",
                "rating": 4.3,
                "description": "Кооперативный экшен-хоррор в африканском сеттинге.",
                "steam_description": "Resident Evil 5 - это захватывающий кооперативный экшен-хоррор с Крисом Редфилдом и Шевой Аломар.",
                "release_date": "2009-09-15",
                "features": ["Хоррор", "Кооператив", "Экшен", "Выживание"]
            },
            {
                "id": 59,
                "name": "Resident Evil 6",
                "developer": "Capcom",
                "category": "Экшен",
                "rating": 4.1,
                "description": "Масштабный экшен-хоррор с четырьмя переплетающимися кампаниями.",
                "steam_description": "Resident Evil 6 предлагает четыре переплетающиеся истории с любимыми персонажами серии.",
                "release_date": "2012-10-02",
                "features": ["Хоррор", "Экшен", "Мультиплеер", "Сюжетная"]
            },
            {
                "id": 60,
                "name": "Five Nights at Freddy's: into the pit",
                "developer": "Steel Wool Studios",
                "category": "Хоррор",
                "rating": 4.5,
                "description": "Новая глава в серии FNAF с путешествиями во времени и новыми угрозами.",
                "steam_description": "Five Nights at Freddy's: into the pit - хоррор-игра с элементами путешествий во времени и новыми механиками выживания.",
                "release_date": "2023-12-15",
                "features": ["Хоррор", "Путешествия во времени", "Выживание", "Загадки"]
            },
            # ДОБАВЛЕНЫ 5 НОВЫХ ИГР
            {
                "id": 61,
                "name": "PUBG: BATTLEGROUNDS",
                "developer": "KRAFTON, Inc.",
                "category": "Шутер",
                "rating": 4.7,
                "description": "Бесплатная королевская битва, которая определила жанр.",
                "steam_description": "Играйте в PUBG: BATTLEGROUNDS бесплатно. Приземляйтесь в стратегических местах, добывайте оружие и припасы и постарайтесь остаться последней командой на разнообразных и всё сужающихся аренах.",
                "release_date": "2017-12-20",
                "features": ["Королевская битва", "Мультиплеер", "Выживание", "Тактический"]
            },
            {
                "id": 62,
                "name": "Red Dead Redemption 2",
                "developer": "Rockstar Games",
                "category": "Экшен",
                "rating": 4.9,
                "description": "Эпическая история об outlaw Артуре Моргане и банде Ван дер Линде.",
                "steam_description": "Выходите на тропу вместе с бандой Ван дер Линде в Red Dead Redemption 2 — масштабной истории о жизни в Америке на заре современной эпохи.",
                "release_date": "2019-11-05",
                "features": ["Открытый мир", "Вестерн", "Сюжетная", "Приключение"]
            },
            {
                "id": 63,
                "name": "Destiny 2",
                "developer": "Bungie",
                "category": "Шутер",
                "rating": 4.5,
                "description": "Бесплатный онлайн-шутер с элементами RPG.",
                "steam_description": "Отыщите свое оружие и присоединяйтесь к миллионам игроков по всему миру в эпическом мире Destiny 2.",
                "release_date": "2019-10-01",
                "features": ["MMO", "Шутер", "Космос", "Кооператив"]
            },
            {
                "id": 64,
                "name": "Elden Ring",
                "developer": "FromSoftware",
                "category": "RPG",
                "rating": 4.9,
                "description": "Эпическая фэнтези-RPG от создателей Dark Souls.",
                "steam_description": "НОВАЯ ФЭНТЕЗИЙНАЯ РОЛЕВАЯ ИГРА. Восстань, Погасший, и да поможет тебе благодать, чтобы ты смог снова стать Владыкой Колец Элден.",
                "release_date": "2022-02-25",
                "features": ["Фэнтези", "Открытый мир", "RPG", "Сложная"]
            },
            {
                "id": 65,
                "name": "EA SPORTS FC™ 24",
                "developer": "EA Sports",
                "category": "Симуляторы",
                "rating": 4.3,
                "description": "Новая эра футбольных симуляторов.",
                "steam_description": "EA SPORTS FC™ 24 — это начало следующей главы в футбольных видеоиграх.",
                "release_date": "2023-09-29",
                "features": ["Футбол", "Симулятор", "Спорт", "Мультиплеер"]
            },
            # ДОБАВЛЕНЫ 3 НОВЫХ ЛЮБИМЫХ ИГРЫ
            {
                "id": 66,
                "name": "Halo Infinite",
                "developer": "343 Industries",
                "category": "Шутер",
                "rating": 4.6,
                "description": "Возвращение легендарного шутера от первого лица с мастером Чифом.",
                "steam_description": "Когда вся надежда потеряна и судьба человечества висит на волоске, Мастер Чиф готов противостоять самой грозной угрозе.",
                "release_date": "2021-12-08",
                "features": ["Шутер", "Научная фантастика", "Мультиплеер", "Кампания"]
            },
            {
                "id": 67,
                "name": "Hadas",
                "developer": "Supergiant Games",
                "category": "Инди",
                "rating": 4.8,
                "description": "Рогалик-экшен с божественным сюжетом и персонажами из греческой мифологии.",
                "steam_description": "Побеждайте смерть в этом рогалик-экшене от создателей Bastion и Transistor.",
                "release_date": "2020-09-17",
                "features": ["Рогалик", "Инди", "Греческая мифология", "Сюжетная"]
            },
            {
                "id": 68,
                "name": "Sons of the Forest",
                "developer": "Endnight Games",
                "category": "Хоррор",
                "rating": 4.7,
                "description": "Ужасающий симулятор выживания на затерянном острове.",
                "steam_description": "Отправляйтесь на одинокий остров в поисках пропавшего миллиардера в этом ужасающем симуляторе выживания.",
                "release_date": "2023-02-23",
                "features": ["Выживание", "Хоррор", "Открытый мир", "Крафт"]
            },
            # НОВЫЕ ДОБАВЛЕННЫЕ ИГРЫ: The Sims и The Sims 2
            {
                "id": 69,
                "name": "The Sims",
                "developer": "Maxis",
                "category": "Симуляторы",
                "rating": 4.7,
                "description": "Культовый симулятор жизни, где вы создаете и управляете виртуальными людьми.",
                "steam_description": "The Sims - первая часть легендарной серии симуляторов жизни. Создавайте персонажей, стройте дома и управляйте их жизнью в виртуальном мире.",
                "release_date": "2000-02-04",
                "features": ["Симулятор жизни", "Кастомизация", "Строительство", "Открытый мир"]
            },
            {
                "id": 70,
                "name": "The Sims 2",
                "developer": "Maxis",
                "category": "Симуляторы",
                "rating": 4.8,
                "description": "Улучшенная версия культового симулятора жизни с 3D-графикой и расширенными возможностями.",
                "steam_description": "The Sims 2 - продолжение легендарного симулятора жизни с улучшенной 3D-графикой, новой системой потребностей и возможностью создавать многопоколенные семьи.",
                "release_date": "2004-09-14",
                "features": ["3D графика", "Семейные династии", "Расширенный кастомизация", "Сюжетные линии"]
            }
        ]

    def apply_filters(self):
        """Применение фильтров магазина"""
        search_text = self.store_search.text().lower()
        category = self.category_combo.currentText()

        # Фильтрация игр
        self.filtered_games = self.all_games.copy()

        # Поиск по названию и разработчику
        if search_text:
            self.filtered_games = [
                game for game in self.filtered_games
                if search_text in game['name'].lower() or search_text in game['developer'].lower()
            ]

        # Фильтрация по категории
        if category != "Все":
            self.filtered_games = [
                game for game in self.filtered_games
                if game['category'] == category
            ]

        # Обновляем отображение
        self.display_games()

    def display_games(self):
        """Отображение всех отфильтрованных игр"""
        # Очищаем текущие игры
        for i in reversed(range(self.games_grid.count())):
            widget = self.games_grid.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Добавляем игры в сетку (5 колонок вместо 4)
        row, col = 0, 0
        for game in self.filtered_games:
            game_widget = self.create_store_game_widget(game)
            self.games_grid.addWidget(game_widget, row, col)
            col += 1
            if col > 4:  # 5 колонок
                col = 0
                row += 1

        # Если игр нет, показываем сообщение
        if not self.filtered_games:
            empty_label = QLabel("Игры не найдены")
            empty_label.setStyleSheet("color: #888888; font-size: 18px; padding: 50px; text-align: center;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.games_grid.addWidget(empty_label, 0, 0, 1, 5)

    def create_store_game_widget(self, game):
        """Создание виджета игры в магазине"""
        widget = QWidget()
        widget.setFixedSize(250, 350)  # Уменьшили высоту
        widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 10px;
                border: 1px solid #3d3d3d;
            }
            QWidget:hover {
                border-color: #4CAF50;
                background-color: #353535;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        widget.setLayout(layout)

        # Загрузка обложки из Steam
        cover_pixmap = self.image_manager.get_game_cover(game["id"], game["name"])

        cover_label = QLabel()
        cover_label.setPixmap(
            cover_pixmap.scaled(230, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))  # Уменьшили размер
        cover_label.setAlignment(Qt.AlignCenter)
        # Сделаем обложку кликабельной для перехода на страницу игры
        cover_label.setCursor(Qt.PointingHandCursor)
        cover_label.mousePressEvent = lambda e: self.show_game_details(game)
        layout.addWidget(cover_label)

        # Название игры
        name_label = QLabel(game["name"])
        name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 0;
            }
        """)
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        name_label.setCursor(Qt.PointingHandCursor)
        name_label.mousePressEvent = lambda e: self.show_game_details(game)
        layout.addWidget(name_label)

        # Разработчик
        dev_label = QLabel(f"Разработчик: {game['developer']}")
        dev_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        layout.addWidget(dev_label)

        # Категория
        cat_label = QLabel(f"Категория: {game['category']}")
        cat_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        layout.addWidget(cat_label)

        # Рейтинг
        rating_widget = QWidget()
        rating_layout = QHBoxLayout()
        rating_layout.setContentsMargins(0, 0, 0, 0)
        rating_widget.setLayout(rating_layout)

        rating_label = QLabel("Рейтинг:")
        rating_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        rating_layout.addWidget(rating_label)

        # Звезды рейтинга
        rating_layout.addStretch()
        rating_value = int(game["rating"])
        for i in range(5):
            star_label = QLabel("★" if i < rating_value else "☆")
            star_label.setStyleSheet("""
                QLabel {
                    color: #FFD700;
                    font-size: 12px;
                }
            """)
            rating_layout.addWidget(star_label)

        rating_layout.addStretch()
        layout.addWidget(rating_widget)

        # Кнопка просмотра деталей
        details_button = QPushButton("📄 Подробнее")
        details_button.clicked.connect(lambda: self.show_game_details(game))
        details_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: #ffffff;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(details_button)

        return widget

    def show_game_details(self, game):
        """Показать детальную страницу игры"""
        self.main_app.show_game_details(game)


class GameDetailsPage(QWidget):
    """Страница с детальной информацией об игре"""

    def __init__(self, main_app, game):
        super().__init__()
        self.main_app = main_app
        self.game = game
        self.image_manager = main_app.image_manager
        self.screenshots_loaded = False
        self.initUI()
        self.load_screenshots_async()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Кнопка назад
        back_button = QPushButton("← Назад в игры")
        back_button.clicked.connect(self.main_app.show_store)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        layout.addWidget(back_button)

        # Основная информация об игре
        main_info_widget = QWidget()
        main_layout = QHBoxLayout()
        main_info_widget.setLayout(main_layout)

        # Обложка игры
        # Используем измененное имя файла для игры с ID 56
        if self.game["id"] == 56:
            # Проверяем новый файл
            new_file = Path("image_cache") / "56_fnaf_mimic.jpg"
            if new_file.exists():
                cover_pixmap = QPixmap(str(new_file))
            else:
                cover_pixmap = self.image_manager.get_game_cover(self.game["id"], self.game["name"])
        else:
            cover_pixmap = self.image_manager.get_game_cover(self.game["id"], self.game["name"])

        cover_label = QLabel()
        cover_label.setPixmap(cover_pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        cover_label.setStyleSheet("border-radius: 10px;")
        main_layout.addWidget(cover_label)

        # Информация об игре
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        info_widget.setLayout(info_layout)

        # Название игры
        title_label = QLabel(self.game["name"])
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffffff;")
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)

        # Разработчик
        dev_label = QLabel(f"Разработчик: {self.game['developer']}")
        dev_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")
        info_layout.addWidget(dev_label)

        # Категория
        cat_label = QLabel(f"Категория: {self.game['category']}")
        cat_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")
        info_layout.addWidget(cat_label)

        # Рейтинг
        rating_widget = QWidget()
        rating_layout = QHBoxLayout()
        rating_widget.setLayout(rating_layout)

        rating_label = QLabel("Рейтинг:")
        rating_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")
        rating_layout.addWidget(rating_label)

        rating_value = int(self.game["rating"])
        for i in range(5):
            star_label = QLabel("★" if i < rating_value else "☆")
            star_label.setStyleSheet("""
                QLabel {
                    color: #FFD700;
                    font-size: 20px;
                }
            """)
            rating_layout.addWidget(star_label)

        rating_layout.addStretch()
        info_layout.addWidget(rating_widget)

        # Дата выхода
        date_label = QLabel(f"Дата выхода: {self.game['release_date']}")
        date_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")
        info_layout.addWidget(date_label)

        info_layout.addStretch()
        main_layout.addWidget(info_widget)

        layout.addWidget(main_info_widget)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #3d3d3d; height: 2px;")
        layout.addWidget(line)

        # ОБ ЭТОЙ ИГРЕ
        desc_label = QLabel("ОБ ЭТОЙ ИГРЕ")
        desc_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(desc_label)

        # Используем описание из Steam для игр FNAF, иначе обычное описание
        description_text = QTextEdit()
        description_text.setReadOnly(True)
        description_text.setStyleSheet("""
            QTextEdit {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        description_text.setMaximumHeight(150)

        # Устанавливаем описание
        description_text.setText(self.game.get("steam_description", self.game["description"]))

        layout.addWidget(description_text)

        # Особенности
        features_label = QLabel("Особенности:")
        features_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
        layout.addWidget(features_label)

        features_widget = QWidget()
        features_layout = QVBoxLayout()
        features_widget.setLayout(features_layout)

        for feature in self.game["features"]:
            feature_label = QLabel(f"• {feature}")
            feature_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
            features_layout.addWidget(feature_label)

        layout.addWidget(features_widget)

        # Скриншоты из Steam
        screenshots_label = QLabel("Скриншоты:")
        screenshots_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
        layout.addWidget(screenshots_label)

        # Прокручиваемая область для скриншотов
        self.screenshots_scroll = QScrollArea()
        self.screenshots_scroll.setWidgetResizable(True)
        self.screenshots_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.screenshots_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.screenshots_scroll.setFixedHeight(180)
        self.screenshots_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                background-color: #252525;
            }
        """)

        # Виджет для скриншотов
        self.screenshots_widget = QWidget()
        self.screenshots_layout = QHBoxLayout()
        self.screenshots_layout.setSpacing(10)
        self.screenshots_widget.setLayout(self.screenshots_layout)

        # Добавляем индикатор загрузки
        self.loading_label = QLabel("Загрузка скриншотов...")
        self.loading_label.setStyleSheet("color: #888888; font-size: 16px; padding: 70px; text-align: center;")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.screenshots_layout.addWidget(self.loading_label)

        self.screenshots_scroll.setWidget(self.screenshots_widget)
        layout.addWidget(self.screenshots_scroll)

        # Кнопка просмотра трейлера (только для игр с трейлерами)
        self.trailer_path = self.image_manager.get_game_trailer_path(self.game["name"])
        if self.trailer_path:
            self.trailer_button = QPushButton("🎬 Смотреть трейлер")
            self.trailer_button.clicked.connect(self.show_trailer)
            self.trailer_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF5722;
                    color: #ffffff;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    margin-top: 10px;
                }
                QPushButton:hover {
                    background-color: #E64A19;
                }
            """)
            layout.addWidget(self.trailer_button)

        # Кнопка просмотра игры
        self.view_game_button = QPushButton("🌐 Просмотр игры")
        self.view_game_button.clicked.connect(self.view_game_website)
        self.view_game_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: #ffffff;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(self.view_game_button)

        layout.addStretch()
        self.setLayout(layout)

    def show_trailer(self):
        """Показать трейлер игры"""
        if self.trailer_path:
            self.main_app.show_trailer(self.trailer_path, self.game["name"])

    def view_game_website(self):
        """Перейти на сайт игры"""
        # Ссылки для конкретных игр
        game_links = {
            "Deltarune": "https://thelastgame.ru/deltarune/",
            "Grand Theft Auto III": "https://itorrents-igruha.org/986-3-gta-3-pc.html",
            "Five Nights at Freddy's: Secret of the Mimic": "https://itorrents-igruha.org/19727-five-nights-at-freddys-secret-of-the-mimic.html",
            "Five Nights at Freddy's: Security Breach": "https://itorrents-igruha.org/6449-five-nights-at-freddys-security-breach.html",
            "Left 4 Dead": "https://itorrents-igruha.org/1441-01-left-4-dead-pc.html",
            "Half-Life 2": "https://itorrents-igruha.org/3336-half-life-21.html",
            "Grand Theft Auto: San Andreas": "https://itorrents-igruha.org/46-23-gta-san-andreas.html",
            "Cyberpunk 2077": "https://www.cyberpunk.net",
            "The Witcher 3: Wild Hunt": "https://www.thewitcher.com",
            "Counter-Strike 2": "https://www.counter-strike.net",
            "Farming Simulator 22": "https://www.farming-simulator.com",
            "Cities: Skylines II": "https://www.paradoxinteractive.com/games/cities-skylines-ii",
            "Hogwarts Legacy": "https://www.hogwartslegacy.com",
            "Portal": "https://www.thinkwithportals.com",
            "Portal 2": "https://www.thinkwithportals.com",
            "Team Fortress 2": "https://www.teamfortress.com",
            "Terraria": "https://www.terraria.org",
            "Undertale": "https://undertale.com",
            "Grand Theft Auto: Vice City": "https://www.rockstargames.com/vicecity",
            "Grand Theft Auto IV": "https://www.rockstargames.com/IV",
            "Marvel's Spider-Man 2": "https://insomniac.games/game/marvels-spider-man-2",
            "Call of Duty: Black Ops": "https://www.callofduty.com/blackops",
            "Five Nights at Freddy's": "https://www.scottgames.com",
            "UpGun": "https://store.steampowered.com/app/1575870/UpGun",
            "peak": "https://store.steampowered.com/app/3527290/peak",
            "Turbo Pug": "https://store.steampowered.com/app/418070/Turbo_Pug",
            "Half-Life: Blue Shift": "https://store.steampowered.com/app/130/HalfLife_Blue_Shift",
            "Five Nights at Freddy's 2": "https://store.steampowered.com/app/332800/Five_Nights_at_Freddys_2",
            "Half-Life: Alyx": "https://www.half-life.com/alyx",
            "Half-Life: Opposing Force": "https://store.steampowered.com/app/50/HalfLife_Opposing_Force",
            "Black Mesa": "https://www.blackmesasource.com",
            "Call of Duty: World at War": "https://www.callofduty.com/worldatwar",
            "Five Nights at Freddy's 3": "https://store.steampowered.com/app/354140/Five_Nights_at_Freddys_3",
            "Five Nights at Freddy's 4": "https://store.steampowered.com/app/388090/Five_Nights_at_Freddys_4",
            "Call of Duty: Black Ops 2": "https://www.callofduty.com/blackops2",
            "Minecraft: Story Mode": "https://www.telltale.com/series/minecraft-story-mode",
            "Left 4 Dead 2": "https://store.steampowered.com/app/550/Left_4_Dead_2",
            "Five Nights at Freddy's: Sister Location": "https://store.steampowered.com/app/506610/Five_Nights_at_Freddys_Sister_Location",
            "Five Nights at Freddy's Help Wanted 2": "https://store.steampowered.com/app/2762040/Five_Nights_at_Freddys_Help_Wanted_2",
            "Phasmophobia": "https://store.steampowered.com/app/739630/Phasmophobia",
            "R.E.P.O": "https://store.steampowered.com/app/1172620/REPO",
            "Stray": "https://store.steampowered.com/app/1332010/Stray",
            "Freddy Fazbear's Pizzeria Simulator": "https://store.steampowered.com/app/638070/Freddy_Fazbears_Pizzeria_Simulator",
            "Minecraft: Story Mode - Season Two": "https://store.steampowered.com/app/639170/Minecraft_Story_Mode__Season_Two",
            "Ultimate Custom Night": "https://store.steampowered.com/app/871720/Ultimate_Custom_Night",
            "Call of Duty: Black Ops 3": "https://www.callofduty.com/blackops3",
            "FIVE NIGHTS AT FREDDY'S: HELP WANTED": "https://store.steampowered.com/app/732690/FIVE_NIGHTS_AT_FREDDYS_HELP_WANTED",
            "Call of Duty: Black Ops 4": "https://www.callofduty.com/blackops4",
            "Resident Evil 5": "https://www.residentevil.com/5",
            "Resident Evil 6": "https://www.residentevil.com/6",
            "Five Nights at Freddy's: into the pit": "https://store.steampowered.com/app/2577840/Five_Nights_at_Freddys_into_the_pit",
            "PUBG: BATTLEGROUNDS": "https://www.pubg.com",
            "Red Dead Redemption 2": "https://www.rockstargames.com/reddeadredemption2",
            "Destiny 2": "https://www.bungie.net/7",
            "Elden Ring": "https://www.eldenring.com",
            "EA SPORTS FC™ 24": "https://www.ea.com/games/ea-sports-fc/fc-24",
            "Halo Infinite": "https://www.halowaypoint.com/halo-infinite",
            "Hadas": "https://www.supergiantgames.com/games/hades",
            "Sons of the Forest": "https://www.endnightgames.com/game/sotf",
            "The Sims": "https://www.ea.com/games/the-sims/the-sims-4",
            "The Sims 2": "https://www.ea.com/games/the-sims/the-sims-4",
        }
        
        game_name = self.game["name"]
        url = game_links.get(game_name)
        
        if url:
            try:
                webbrowser.open(url)
                QMessageBox.information(self, "Переход на сайт", 
                                       f"Открываю сайт игры '{game_name}' в вашем браузере...")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", 
                                  f"Не удалось открыть сайт: {str(e)}")
        else:
            QMessageBox.information(self, "Информация", 
                                   f"Для игры '{game_name}' ссылка на сайт не указана.\n\nВы можете найти игру самостоятельно.")

    def load_screenshots_async(self):
        """Асинхронная загрузка скриншотов"""
        thread = threading.Thread(target=self.load_screenshots_thread, daemon=True)
        thread.start()

    def load_screenshots_thread(self):
        """Загрузка скриншотов в отдельном потоке"""
        # Получаем скриншоты из Steam
        screenshots = self.image_manager.get_game_screenshots(self.game["id"], max_count=5)

        # Если скриншотов нет, пробуем создать заглушки
        if not screenshots and self.game["id"] in [56]:  # Для игры с ID 56
            screenshots = self.create_fallback_screenshots()

        # Обновляем UI в основном потоке
        QMetaObject.invokeMethod(self, "update_screenshots_ui",
                                 Qt.QueuedConnection,
                                 Q_ARG(list, screenshots))

    def create_fallback_screenshots(self):
        """Создание заглушек для скриншотов"""
        screenshots = []
        # Создаем 3 заглушки
        for i in range(3):
            pixmap = QPixmap(300, 150)
            pixmap.fill(QColor(50, 50, 50))

            painter = QPainter(pixmap)
            painter.setPen(QColor(200, 200, 200))
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, f"Скриншот {i + 1}")

            painter.setFont(QFont("Arial", 10))
            painter.drawText(pixmap.rect().adjusted(0, 40, 0, 0), Qt.AlignCenter, self.game["name"])
            painter.end()

            screenshots.append(pixmap)

        return screenshots

    @pyqtSlot(list)
    def update_screenshots_ui(self, screenshots):
        """Обновление UI скриншотов в основном потоке"""
        # Удаляем индикатор загрузки
        if self.loading_label:
            self.loading_label.deleteLater()
            self.loading_label = None

        if screenshots:
            # Добавляем скриншоты
            for i, screenshot in enumerate(screenshots):
                screenshot_container = QWidget()
                container_layout = QVBoxLayout()
                screenshot_container.setLayout(container_layout)

                screenshot_label = QLabel()
                screenshot_label.setPixmap(screenshot.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                screenshot_label.setStyleSheet("border: 1px solid #3d3d3d; border-radius: 8px;")
                container_layout.addWidget(screenshot_label)

                screenshot_text = QLabel(f"Скриншот {i + 1}")
                screenshot_text.setStyleSheet("color: #888888; font-size: 12px;")
                screenshot_text.setAlignment(Qt.AlignCenter)
                container_layout.addWidget(screenshot_text)

                self.screenshots_layout.addWidget(screenshot_container)
        else:
            # Если скриншотов нет, показываем сообщение
            no_screenshots_label = QLabel("Скриншоты временно недоступны")
            no_screenshots_label.setStyleSheet("color: #888888; font-size: 14px; padding: 70px; text-align: center;")
            no_screenshots_label.setAlignment(Qt.AlignCenter)
            self.screenshots_layout.addWidget(no_screenshots_label)

        self.screenshots_loaded = True


class TrailerWindow(QDialog):
    """Окно для просмотра трейлеров игр"""

    def __init__(self, trailer_path, game_name, parent=None):
        super().__init__(parent)
        self.trailer_path = trailer_path
        self.game_name = game_name
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Трейлер - {self.game_name}")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Виджет для видео
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)

        # Медиа-плеер
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)

        # Устанавливаем видео
        if os.path.exists(self.trailer_path):
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.trailer_path)))
        else:
            # Если файл не найден, показываем сообщение
            error_label = QLabel(f"Трейлер не найден по пути: {self.trailer_path}")
            error_label.setStyleSheet("color: #f44336; font-size: 16px; padding: 20px; text-align: center;")
            layout.addWidget(error_label)

        # Панель управления
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)

        # Кнопка воспроизведения/паузы
        self.play_button = QPushButton("▶️ Воспроизвести")
        self.play_button.clicked.connect(self.toggle_play)
        control_layout.addWidget(self.play_button)

        # Кнопка остановки
        self.stop_button = QPushButton("⏹️ Стоп")
        self.stop_button.clicked.connect(self.stop_playback)
        control_layout.addWidget(self.stop_button)

        # Ползунок громкости
        volume_label = QLabel("🔊")
        control_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        control_layout.addWidget(self.volume_slider)

        control_layout.addStretch()

        # Кнопка закрытия
        close_button = QPushButton("✕ Закрыть")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        control_layout.addWidget(close_button)

        layout.addWidget(control_panel)

        # Стилизация
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3d3d3d;
                height: 8px;
                background: #252525;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #3d3d3d;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)

        # Устанавливаем начальную громкость
        self.media_player.setVolume(50)

        self.setLayout(layout)

    def toggle_play(self):
        """Включить/выключить воспроизведение"""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶️ Воспроизвести")
        else:
            self.media_player.play()
            self.play_button.setText("⏸️ Пауза")

    def stop_playback(self):
        """Остановить воспроизведение"""
        self.media_player.stop()
        self.play_button.setText("▶️ Воспроизвести")

    def set_volume(self, value):
        """Установить громкость"""
        self.media_player.setVolume(value)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.media_player.stop()
        event.accept()


class GameLauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        # Инициализация менеджера пользователей
        self.user_manager = UserManager()

        # Проверка интернета перед запуском
        if not InternetChecker.check_internet():
            self.show_no_internet_dialog()
            return

        # Показать окно входа
        self.show_login_window()

    def show_login_window(self):
        """Показать окно входа"""
        self.login_window = LoginWindow(self.user_manager)
        result = self.login_window.exec_()

        if result == QDialog.Accepted:
            # Если вход успешен, инициализируем основное приложение
            self.initialize_main_app()
        else:
            # Закрыть приложение если пользователь не вошел
            sys.exit(0)

    def initialize_main_app(self):
        """Инициализация основного приложения после успешного входа"""
        self.setWindowTitle("Factory Market")

        # Запускаем приложение в большом оконном режиме
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(100, 100, screen.width() - 200, screen.height() - 100)

        # Конфигурация
        self.config_file = "launcher_config.json"
        self.config = self.load_config()

        # Статистика пользователя
        self.user_stats = self.load_user_stats()

        # Таймер для отслеживания времени работы приложения
        self.app_timer = QTimer()
        self.app_timer.timeout.connect(self.update_app_time)
        self.app_start_time = time.time()
        self.total_app_time = self.user_stats.get("total_app_time", 0)
        self.last_update_time = time.time()

        # Таймер для проверки интернета с автоматическим поиском
        self.internet_check_timer = QTimer()
        self.internet_check_timer.timeout.connect(self.check_internet_connection_with_reconnect)
        self.internet_check_timer.start(10000)  # Проверять каждые 10 секунд
        self.internet_connection_attempts = 0
        self.max_internet_connection_attempts = 12  # 2 минуты при проверке каждые 10 секунд

        # Image Manager
        self.image_manager = ImageManager()

        # Стили
        self.setup_styles()

        # Создание UI
        self.create_menu()
        self.create_sidebar()
        self.create_main_area()

        # Показываем магазин при запуске
        self.show_store()

        # Запускаем таймер
        self.app_timer.start(1000)

    def show_no_internet_dialog(self):
        """Показать диалог отсутствия интернета с авто-поиском"""
        dialog = InternetCheckDialog(auto_reconnect=True)
        if dialog.exec_() == QDialog.Accepted:
            # Если интернет появился, показать окно входа
            self.show_login_window()
        else:
            # Закрыть приложение если интернет не появился
            sys.exit(0)

    def check_internet_connection_with_reconnect(self):
        """Проверка интернет соединения с автоматическим поиском подключения"""
        if not InternetChecker.check_internet():
            self.internet_connection_attempts += 1

            if self.internet_connection_attempts >= self.max_internet_connection_attempts:
                # Превышено максимальное количество попыток, показать диалог
                self.show_internet_recovery_dialog()
            else:
                if self.try_auto_reconnect():
                    self.internet_connection_attempts = 0
        else:
            self.internet_connection_attempts = 0

    def try_auto_reconnect(self):
        """Попытка автоматического восстановления подключения"""
        if InternetChecker.wait_for_internet(timeout=5, check_interval=1):
            QMessageBox.information(self, "Подключение восстановлено",
                                    "Интернет соединение было автоматически восстановлено.")
            return True
        return False

    def show_internet_recovery_dialog(self):
        """Показать диалог восстановления подключения"""
        reply = QMessageBox.question(self, "Ошибка подключения",
                                     "Отсутствует подключение к интернету более 2 минут.\n\n"
                                     "Хотите попробовать найти подключение автоматически?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            dialog = InternetCheckDialog(auto_reconnect=True)
            result = dialog.exec_()

            if result == QDialog.Accepted:
                self.internet_connection_attempts = 0
                QMessageBox.information(self, "Подключение восстановлено",
                                        "Интернет соединение было успешно восстановлено.")
            else:
                reply2 = QMessageBox.question(self, "Закрыть приложение",
                                              "Подключение к интернету не найдено.\n"
                                              "Хотите закрыть приложение?",
                                              QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

                if reply2 == QMessageBox.Yes:
                    self.close()
        else:
            reply2 = QMessageBox.question(self, "Закрыть приложение",
                                          "Подключение к интернету не найдено.\n"
                                          "Хотите закрыть приложение?",
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

            if reply2 == QMessageBox.Yes:
                self.close()

    def load_config(self):
        """Загрузка конфигурации лаунчера"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return {"theme": "dark", "user_stats": {}}
        return {"theme": "dark", "user_stats": {}}

    def save_config(self):
        """Сохранение конфигурации"""
        self.user_stats["total_app_time"] = self.total_app_time
        self.config["user_stats"] = self.user_stats

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")

    def load_user_stats(self):
        """Загрузка статистики пользователя"""
        stats = self.config.get("user_stats", {})

        if not stats:
            stats = {
                "account_created": datetime.now().strftime("%d.%m.%Y"),
                "total_app_time": 0,
                "last_login": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }
        else:
            stats["last_login"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        return stats

    def setup_styles(self):
        """Настройка стилей приложения"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton#active {
                background-color: #4CAF50;
                border-color: #45a049;
            }
        """)

    def create_menu(self):
        """Создание меню приложения"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #252525;
                color: #ffffff;
                border-bottom: 1px solid #3d3d3d;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)

    def create_sidebar(self):
        """Создание боковой панели навигации (только магазин и профиль)"""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QWidget#sidebar {
                background-color: #252525;
                border-right: 1px solid #3d3d3d;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        sidebar.setLayout(layout)

        logo_label = QLabel("🎮 Factory Market")
        logo_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 20px;
                font-weight: bold;
                padding: 20px;
                text-align: center;
            }
        """)
        layout.addWidget(logo_label)

        if self.user_manager.current_user:
            user_label = QLabel(f"👤 {self.user_manager.current_user}")
            user_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    padding: 10px 20px;
                    text-align: center;
                    background-color: #3d3d3d;
                    margin: 0 10px;
                    border-radius: 5px;
                }
            """)
            layout.addWidget(user_label)

        layout.addSpacing(10)

        self.store_btn = QPushButton("🎮 Игры")
        self.store_btn.setObjectName("active")
        self.store_btn.clicked.connect(self.show_store)
        layout.addWidget(self.store_btn)

        self.profile_btn = QPushButton("👤 Профиль")
        self.profile_btn.clicked.connect(self.show_profile_page)
        layout.addWidget(self.profile_btn)

        logout_btn = QPushButton("🚪 Выйти")
        logout_btn.clicked.connect(self.logout)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
                text-align: left;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        layout.addWidget(logout_btn)

        layout.addStretch()

        sidebar_dock = QDockWidget("", self)
        sidebar_dock.setWidget(sidebar)
        sidebar_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        sidebar_dock.setTitleBarWidget(QWidget())
        self.addDockWidget(Qt.LeftDockWidgetArea, sidebar_dock)

    def logout(self):
        """Выход из аккаунта"""
        reply = QMessageBox.question(self, 'Выход', 'Вы уверены, что хотите выйти?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.user_manager.logout()
            self.close()

    def update_app_time(self):
        """Обновление времени работы приложения"""
        current_time = time.time()
        elapsed = current_time - self.last_update_time

        if elapsed >= 1.0:
            self.total_app_time += 1
            self.last_update_time = current_time

            if self.total_app_time % 30 == 0:
                self.save_config()

    def create_main_area(self):
        """Создание основной области контента"""
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.store_page = StorePage(self)
        self.profile_page = QWidget()
        self.game_details_page = None

        self.central_widget.addWidget(self.store_page)
        self.central_widget.addWidget(self.profile_page)

    def update_nav_buttons(self, active_button):
        """Обновление состояния кнопок навигации"""
        buttons = [self.store_btn, self.profile_btn]

        for btn in buttons:
            if btn == active_button:
                btn.setObjectName("active")
                btn.setStyleSheet("""
                    QPushButton#active {
                        background-color: #4CAF50;
                        border-color: #45a049;
                    }
                """)
            else:
                btn.setObjectName("")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #3d3d3d;
                        padding: 10px 15px;
                        border-radius: 5px;
                        font-size: 14px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                        border-color: #4d4d4d;
                    }
                """)

    def show_store(self):
        """Показать страницу магазина (игр)"""
        self.central_widget.setCurrentWidget(self.store_page)
        self.update_nav_buttons(self.store_btn)
        self.setWindowTitle("Factory Market - Игры")

    def show_game_details(self, game):
        """Показать страницу с детальной информацией об игре"""
        if not game:
            return

        self.game_details_page = GameDetailsPage(self, game)

        if self.central_widget.indexOf(self.game_details_page) == -1:
            self.central_widget.addWidget(self.game_details_page)

        self.central_widget.setCurrentWidget(self.game_details_page)
        self.setWindowTitle(f"Factory Market - {game['name']}")

    def show_trailer(self, trailer_path, game_name):
        """Показать трейлер игры"""
        if os.path.exists(trailer_path):
            trailer_window = TrailerWindow(trailer_path, game_name, self)
            trailer_window.exec_()
        else:
            QMessageBox.warning(self, "Трейлер не найден",
                                f"Файл трейлера не найден по пути:\n{trailer_path}\n\n"
                                "Убедитесь, что файл существует в папке trailer_game")

    def show_profile_page(self):
        """Показать страницу профиля"""
        for i in range(self.central_widget.count()):
            widget = self.central_widget.widget(i)
            if widget == self.profile_page:
                self.central_widget.removeWidget(widget)
                widget.deleteLater()
                break

        self.profile_page = QWidget()
        self.central_widget.addWidget(self.profile_page)
        self.create_profile_page()
        self.central_widget.setCurrentWidget(self.profile_page)
        self.update_nav_buttons(self.profile_btn)
        self.setWindowTitle("Factory Market - Профиль")

    def create_profile_page(self):
        """Создание страницы профиля"""
        if self.profile_page.layout():
            old_layout = self.profile_page.layout()
            if old_layout:
                QWidget().setLayout(old_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title_label = QLabel("👤 Профиль")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        if self.user_manager.current_user:
            user_info = self.user_manager.users.get(self.user_manager.current_user, {})

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background-color: #2d2d2d;
                    border-radius: 10px;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: #2d2d2d;
                }
            """)

            profile_widget = QWidget()
            profile_layout = QVBoxLayout()
            profile_layout.setSpacing(20)
            profile_layout.setContentsMargins(20, 20, 20, 20)
            profile_widget.setLayout(profile_layout)

            user_info_widget = QWidget()
            user_info_widget.setStyleSheet("background-color: #3d3d3d; border-radius: 10px; padding: 15px;")
            user_info_layout = QHBoxLayout()
            user_info_widget.setLayout(user_info_layout)

            avatar_container = QWidget()
            avatar_container_layout = QVBoxLayout()
            avatar_container.setLayout(avatar_container_layout)

            self.profile_icon_path = self.config.get("profile_icon", None)

            self.avatar_label = QLabel()
            self.avatar_label.setFixedSize(184, 184)
            self.avatar_label.setStyleSheet("""
                QLabel {
                    border: 3px solid #4CAF50;
                    border-radius: 10px;
                    background-color: #252525;
                }
            """)
            self.avatar_label.setAlignment(Qt.AlignCenter)

            if self.profile_icon_path and os.path.exists(self.profile_icon_path):
                pixmap = QPixmap(self.profile_icon_path)
                if not pixmap.isNull():
                    self.avatar_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    self.avatar_label.setText("👤")
                    self.avatar_label.setStyleSheet("""
                        QLabel {
                            font-size: 100px;
                            border: 3px solid #4CAF50;
                            border-radius: 10px;
                            background-color: #252525;
                        }
                    """)
            else:
                self.avatar_label.setText("👤")
                self.avatar_label.setStyleSheet("""
                    QLabel {
                        font-size: 100px;
                        border: 3px solid #4CAF50;
                        border-radius: 10px;
                        background-color: #252525;
                    }
                """)

            avatar_container_layout.addWidget(self.avatar_label)

            # Кнопка для выбора иконки профиля
            change_icon_btn = QPushButton("📷 Выбрать иконку")
            change_icon_btn.clicked.connect(self.select_profile_icon)
            change_icon_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 6px;
                    margin-top: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            avatar_container_layout.addWidget(change_icon_btn)

            user_info_layout.addWidget(avatar_container)

            info_widget = QWidget()
            info_layout = QVBoxLayout()
            info_widget.setLayout(info_layout)

            name_label = QLabel(f"👤 {self.user_manager.current_user}")
            name_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
            info_layout.addWidget(name_label)

            email_label = QLabel(f"📧 {user_info.get('email', 'Не указан')}")
            email_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
            info_layout.addWidget(email_label)

            status_label = QLabel("🟢 Статус: Активен")
            status_label.setStyleSheet("color: #4CAF50; font-size: 14px;")
            info_layout.addWidget(status_label)

            user_info_layout.addWidget(info_widget)
            user_info_layout.addStretch()

            profile_layout.addWidget(user_info_widget)

            # Разделитель
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #3d3d3d; height: 1px; margin: 10px 0;")
            profile_layout.addWidget(line)

            # Основная информация
            info_label = QLabel("📊 Информация")
            info_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
            profile_layout.addWidget(info_label)

            info_widget = QWidget()
            info_widget.setStyleSheet("background-color: #3d3d3d; border-radius: 10px; padding: 15px;")
            info_layout = QGridLayout()
            info_widget.setLayout(info_layout)

            reg_label = QLabel("📅 Дата регистрации:")
            reg_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
            info_layout.addWidget(reg_label, 0, 0)

            reg_date = user_info.get("created", datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
            reg_date_label = QLabel(reg_date)
            reg_date_label.setStyleSheet("color: #ffffff; font-size: 14px;")
            info_layout.addWidget(reg_date_label, 0, 1)

            login_label = QLabel("🕒 Последний вход:")
            login_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
            info_layout.addWidget(login_label, 1, 0)

            last_login = user_info.get("last_login", datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
            login_date_label = QLabel(last_login)
            login_date_label.setStyleSheet("color: #ffffff; font-size: 14px;")
            info_layout.addWidget(login_date_label, 1, 1)

            time_label = QLabel("⏱️ Время в приложении:")
            time_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
            info_layout.addWidget(time_label, 2, 0)

            total_time = self.total_app_time
            hours = total_time // 3600
            minutes = (total_time % 3600) // 60
            seconds = total_time % 60
            time_value_label = QLabel(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            time_value_label.setStyleSheet("color: #ffffff; font-size: 14px;")
            info_layout.addWidget(time_value_label, 2, 1)

            info_layout.setColumnStretch(0, 1)
            info_layout.setColumnStretch(1, 1)
            profile_layout.addWidget(info_widget)

            profile_layout.addStretch()
            scroll_area.setWidget(profile_widget)
            layout.addWidget(scroll_area)
        else:
            error_label = QLabel("❌ Вы не авторизованы")
            error_label.setStyleSheet("color: #f44336; font-size: 18px; font-weight: bold; text-align: center;")
            layout.addWidget(error_label)

        self.profile_page.setLayout(layout)

    def select_profile_icon(self):
        """Выбор иконки профиля из файлов"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")

        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]

            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                final_pixmap = QPixmap(184, 184)
                final_pixmap.fill(Qt.transparent)

                painter = QPainter(final_pixmap)
                painter.setPen(QPen(QColor(76, 175, 80), 3))
                painter.drawRect(0, 0, 183, 183)

                x = (184 - scaled_pixmap.width()) // 2
                y = (184 - scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, scaled_pixmap)
                painter.end()

                self.avatar_label.setPixmap(final_pixmap)

                self.profile_icon_path = file_path
                self.config["profile_icon"] = file_path
                self.save_config()

                QMessageBox.information(self, "Успех", "Иконка профиля успешно изменена!")

    def closeEvent(self, event):
        """Обработка закрытия приложения"""
        try:
            self.save_config()
            event.accept()
        except Exception as e:
            print(f"Ошибка при закрытии приложения: {e}")
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Factory Market")
    app.setOrganizationName("FactoryMarket")

    if not InternetChecker.check_internet():
        dialog = InternetCheckDialog(auto_reconnect=True)
        if dialog.exec_() != QDialog.Accepted:
            sys.exit(0)

    launcher = GameLauncher()
    launcher.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
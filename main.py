import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QMessageBox, QAction, QScrollArea, QFrame,
                             QTabWidget, QDialog, QDialogButtonBox, QTextEdit,
                             QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon

# Модули
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.chibi_widget import FloatingChibi
from modules.notes_manager import NotesManager
from modules.settings_manager import SettingsManager
from modules.image_processor import ImageProcessor

# Диалоговое окно для создания заметки
class NoteDialog(QDialog):
    def __init__(self, parent=None, existing_text=""):
        super().__init__(parent)
        self.setWindowTitle("Новая заметка")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Заголовок (необязательно):")
        layout.addWidget(self.title_label)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Введите заголовок...")
        layout.addWidget(self.title_edit)
        
        self.text_label = QLabel("Текст заметки:")
        layout.addWidget(self.text_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Введите текст заметки...")
        if existing_text:
            self.text_edit.setText(existing_text)
        self.text_edit.setMinimumHeight(120)
        layout.addWidget(self.text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_note_data(self):
        return self.title_edit.text(), self.text_edit.toPlainText()

# Диалоговое окно настроек
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setFixedSize(350, 250)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        size_layout = QHBoxLayout()
        size_label = QLabel("Высота области заметок:")
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(100, 400)
        self.size_spinbox.setValue(140)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_spinbox)
        layout.addLayout(size_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_height(self):
        return self.size_spinbox.value()

# Главное окно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Инициализация модулей
        self.settings_manager = SettingsManager()
        self.notes_manager = NotesManager()
        self.image_processor = ImageProcessor()
        
        self.floating_widget = None
        self.notes_height = self.settings_manager.get_setting("notes_height", 140)
        
        # Настройка окна
        self.setWindowTitle("Дом Али")
        self.setFixedSize(550, 600)
        self.setWindowIcon(self.create_icon())
        self.create_menu_bar()
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # layout
        main_layout = QVBoxLayout(central_widget)
        
        # Вкладки
        self.create_tabs()
        main_layout.addWidget(self.tab_widget)
        
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Статусная строка
        self.status_label = QLabel("✨ Аля дома. Добро пожаловать!")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; padding: 10px; font-size: 11px;")
        main_layout.addWidget(self.status_label)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
    
    # Главное меню
    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("📁 Файл")
        settings_action = QAction("⚙️ Настройки", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Аля"
        chibi_menu = menubar.addMenu("🐱 Аля")
        start_action = QAction("▶ Запустить", self)
        start_action.triggered.connect(self.start_chibi)
        chibi_menu.addAction(start_action)
        stop_action = QAction("■ Остановить", self)
        stop_action.triggered.connect(self.stop_chibi)
        chibi_menu.addAction(stop_action)
        chibi_menu.addSeparator()
        
        chibi_mode_action = QAction("🐱 Режим чиби", self)
        chibi_mode_action.triggered.connect(self.set_chibi_mode)
        chibi_menu.addAction(chibi_mode_action)
        board_mode_action = QAction("📋 Режим доски", self)
        board_mode_action.triggered.connect(self.set_board_mode)
        chibi_menu.addAction(board_mode_action)
        
        # Меню "Заметки"
        notes_menu = menubar.addMenu("📝 Заметки")
        add_note_action = QAction("➕ Новая заметка", self)
        add_note_action.setShortcut("Ctrl+N")
        add_note_action.triggered.connect(self.open_note_dialog)
        notes_menu.addAction(add_note_action)
        export_action = QAction("💾 Экспорт заметок", self)
        export_action.triggered.connect(self.export_notes)
        notes_menu.addAction(export_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu("❓ Справка")
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_tabs(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
                background-color: #e0e0e0;
                border-radius: 5px 5px 0 0;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #45a049;
                color: white;
            }
        """)
        
        # Вкладка 1: Дом Али
        self.home_tab = self.create_home_tab()
        self.tab_widget.addTab(self.home_tab, "🏠 Дом Али")
        
        # Вкладка 2: Заметки
        self.notes_tab = self.create_notes_tab()
        self.tab_widget.addTab(self.notes_tab, "📝 Заметки")
        
        # Вкладка 3: О программе
        self.about_tab = self.create_about_tab()
        self.tab_widget.addTab(self.about_tab, "ℹ️ О программе")
    
    def create_home_tab(self):
        """Создание вкладки 'Дом Али'"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        preview_label = QLabel("🐱 Это Аля")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setStyleSheet("border: 2px solid #ccc; border-radius: 10px; background-color: #f0f0f0;")
        self.update_preview()
        layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
        
        buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶ Запустить")
        self.start_button.setStyleSheet(self.button_style("#4CAF50"))
        self.start_button.clicked.connect(self.start_chibi)
        
        self.stop_button = QPushButton("■ Остановить")
        self.stop_button.setStyleSheet(self.button_style("#f44336"))
        self.stop_button.clicked.connect(self.stop_chibi)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        layout.addLayout(buttons_layout)
        
        mode_label = QLabel("🎮 Режимы Али:")
        mode_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(mode_label)
        mode_buttons_layout = QHBoxLayout()
        
        self.chibi_mode_btn = QPushButton("🐱 Режим чиби")
        self.chibi_mode_btn.setStyleSheet(self.button_style("#2196F3"))
        self.chibi_mode_btn.clicked.connect(self.set_chibi_mode)
        
        self.board_mode_btn = QPushButton("📋 Режим доски")
        self.board_mode_btn.setStyleSheet(self.button_style("#FF9800"))
        self.board_mode_btn.clicked.connect(self.set_board_mode)
        
        mode_buttons_layout.addWidget(self.chibi_mode_btn)
        mode_buttons_layout.addWidget(self.board_mode_btn)
        layout.addLayout(mode_buttons_layout)
        
        layout.addStretch()
        return tab
    
    # Вкладка с заметками
    def create_notes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        buttons_row = QHBoxLayout()
        
        self.add_note_btn = QPushButton("➕ Новая заметка")
        self.add_note_btn.setStyleSheet(self.button_style("#9C27B0"))
        self.add_note_btn.clicked.connect(self.open_note_dialog)
        buttons_row.addWidget(self.add_note_btn)
        
        self.export_notes_btn = QPushButton("💾 Экспорт")
        self.export_notes_btn.setStyleSheet(self.button_style("#FF9800"))
        self.export_notes_btn.clicked.connect(self.export_notes)
        buttons_row.addWidget(self.export_notes_btn)
        
        self.clear_all_btn = QPushButton("🗑 Очистить всё")
        self.clear_all_btn.setStyleSheet(self.button_style("#f44336"))
        self.clear_all_btn.clicked.connect(self.clear_all_notes)
        buttons_row.addWidget(self.clear_all_btn)
        layout.addLayout(buttons_row)
        
        # Статистика заметок
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.stats_label)
        
        # Область для списка заметок
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: 1px solid #ccc; border-radius: 5px; background-color: white;")
        self.notes_widget = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_widget)
        self.notes_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.notes_widget)
        layout.addWidget(scroll_area)
        self.refresh_notes_list()
        
        return tab
    
    # Вкладка "О программе"
    def create_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        logo_label = QLabel("🐱")
        logo_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        
        title_label = QLabel("Аля")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        version_label = QLabel("Версия 2.0.0")
        version_label.setStyleSheet("color: #888;")
        layout.addWidget(version_label, alignment=Qt.AlignCenter)
        
        desc_label = QLabel(
            "Аля — ваш настольный помощник!\n\n"
            "Возможности:\n"
            "• Плавающий виджет с режимом доски\n"
            "• Система заметок с сохранением\n"
            "• Перетаскивание изображений на доску\n\n"
            "Горячие клавиши:\n"
            "• Ctrl + N - создание заметки\n"
            "• Ctrl + Q - выход из программы"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555; line-height: 1.5;")
        layout.addWidget(desc_label, alignment=Qt.AlignCenter)
        
        layout.addStretch()
        return tab
    
    def button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {color}cc;
            }}
            QPushButton:disabled {{
                background-color: #ccc;
            }}
        """
    
    def create_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(255, 100, 150))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        return QIcon(pixmap)
    
    def update_preview(self):
        if os.path.exists("assets/sprite.png"):
            pixmap = QPixmap("assets/sprite.png")
        elif os.path.exists("sprite.png"):
            pixmap = QPixmap("sprite.png")
        else:
            pixmap = QPixmap(180, 180)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QColor(255, 100, 150))
            painter.drawEllipse(15, 15, 150, 150)
            painter.setPen(Qt.white)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "Аля")
            painter.end()
            self.preview_label.setPixmap(pixmap)
            return
        
        if not pixmap.isNull():
            self.preview_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    # Статистика заметок
    def update_stats(self):
        count = self.notes_manager.get_notes_count()
        self.stats_label.setText(f"📊 Всего заметок: {count}")
    
    def open_note_dialog(self):
        dialog = NoteDialog(self)
        if dialog.exec_():
            title, text = dialog.get_note_data()
            if self.notes_manager.add_note(title, text):
                self.refresh_notes_list()
                self.status_label.setText("📝 Заметка сохранена!")
                self.status_label.setStyleSheet("color: #4CAF50; padding: 10px; font-size: 11px;")
                if self.floating_widget is not None:
                    self.floating_widget.show_nom_sprite()
                QMessageBox.information(self, "Успех", "Заметка успешно сохранена!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить заметку")
    
    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            new_height = dialog.get_height()
            self.settings_manager.set_setting("notes_height", new_height)
            self.status_label.setText("⚙️ Настройки сохранены")
            QMessageBox.information(self, "Настройки", f"Высота области заметок изменена на {new_height}px")
    
    # Экспорт заметок
    def export_notes(self):
        filepath = self.notes_manager.export_to_file()
        if filepath:
            QMessageBox.information(self, "Экспорт", f"Заметки экспортированы в файл:\n{filepath}")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось экспортировать заметки")
    
    # Очистка заметок
    def clear_all_notes(self):
        reply = QMessageBox.question(self, "Подтверждение", 
                                     "🗑 Удалить ВСЕ заметки?\n\nЭто действие нельзя отменить.",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.notes_manager.clear_all_notes():
                self.refresh_notes_list()
                self.status_label.setText("🗑 Все заметки удалены")
    
    def show_about_dialog(self):
        QMessageBox.about(self, "О программе",
            "🐱 Аля\n\n"
            "Настольный помощник.\n\n"
            "Возможности:\n"
            "• Плавающий виджет (поверх всех окон)\n"
            "• Режим доски для изображений\n"
            "• Система заметок\n"
            "• Экспорт заметок\n"
            "• Горячие клавиши")
    
    def on_tab_changed(self, index):
        tab_name = self.tab_widget.tabText(index)
        self.status_label.setText(f"📂 Переход на вкладку: {tab_name}")
    
    def refresh_notes_list(self):
        while self.notes_layout.count():
            item = self.notes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        notes = self.notes_manager.get_all_notes()
        self.update_stats()
        
        if not notes:
            empty_label = QLabel("📭 Здесь пока пусто.\nНажмите 'Новая заметка' или Ctrl+N")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999; padding: 30px;")
            self.notes_layout.addWidget(empty_label)
        else:
            for i, note in enumerate(reversed(notes)):
                note_widget = self.create_note_widget(note, len(notes) - 1 - i)
                self.notes_layout.addWidget(note_widget)
    
    def create_note_widget(self, note, index):
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                margin: 2px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        
        title_label = QLabel(f"📌 {note.get('title', 'Без заголовка')}")
        title_label.setStyleSheet("font-weight: bold; color: #333; font-size: 11px;")
        layout.addWidget(title_label)
        
        date_label = QLabel(f"📅 {note['date']}")
        date_label.setStyleSheet("color: #888; font-size: 9px;")
        layout.addWidget(date_label)
        
        text_label = QLabel(note['text'])
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 11px; padding: 5px; color: #555;")
        layout.addWidget(text_label)
        
        delete_btn = QPushButton("🗑 Удалить")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 4px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        delete_btn.clicked.connect(lambda checked, idx=index: self.delete_note(idx))
        layout.addWidget(delete_btn, alignment=Qt.AlignRight)
        
        return widget
    
    def delete_note(self, index):
        reply = QMessageBox.question(self, "Подтверждение", 
                                     "🗑 Удалить эту заметку?\n\nЭто действие нельзя отменить.",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.notes_manager.delete_note(index):
                self.refresh_notes_list()
                self.status_label.setText("🗑 Заметка удалена")
    
    def start_chibi(self):
        if self.floating_widget is None:
            self.floating_widget = FloatingChibi()
            self.status_label.setText("✨ Аля на рабочем столе!")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
    
    def stop_chibi(self):
        if self.floating_widget is not None:
            self.floating_widget.close()
            self.floating_widget = None
            self.status_label.setText("🏠 Аля вернулась домой")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    def set_chibi_mode(self):
        if self.floating_widget is not None:
            self.floating_widget.switch_to_chibi_mode()
            self.status_label.setText("🐱 Аля трогает траву")
        else:
            QMessageBox.information(self, "Информация", "Сначала запустите Алю!")
    
    def set_board_mode(self):
        if self.floating_widget is not None:
            self.floating_widget.switch_to_board_mode()
            self.status_label.setText("📋 Аля в режиме доски")
        else:
            QMessageBox.information(self, "Информация", "Сначала запустите Алю!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
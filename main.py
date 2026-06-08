import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QMessageBox, QMenu, QAction, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon, QDragEnterEvent, QDropEvent

# Виджет ====================================================
class FloatingChibi(QWidget): 
    def __init__(self):
        super().__init__()
        
        # Настройка окна
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 300)
        
        self.mode = 'chibi'
        
        # Спрайты
        self.chibi_pixmap = self.load_sprite("sprite.png", (255, 100, 150), "Аля")
        self.nom_pixmap = self.load_sprite("nom.png", (255, 200, 50), "Ном")
        self.grab_pixmap = self.load_sprite("grab.png", (100, 150, 255), "Хвать")
        self.current_pixmap = self.chibi_pixmap
        
        # Таймер для ном
        self.nom_timer = QTimer()
        self.nom_timer.timeout.connect(self.reset_sprite)
        self.nom_timer.setSingleShot(True)
        
        # Режим доски
        self.images = []
        self.dragging_image_index = -1
        self.drag_start_pos = QPoint()
        self.setAcceptDrops(True)

        # Перемнные для перетаскивания окна
        self.dragging = False
        self.drag_position = QPoint()
        self.show()
    
    # Загрузка спрайта
    def load_sprite(self, filename, color, text):
        if os.path.exists(filename):
            pixmap = QPixmap(filename)
            if not pixmap.isNull():
                return pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Заглушка
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(*color))
        painter.drawEllipse(50, 50, 100, 100)
        painter.setPen(Qt.white)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        return pixmap
    
    # Анимации
    def show_nom_sprite(self):
        self.current_pixmap = self.nom_pixmap
        self.update()
        self.nom_timer.start(500)

    def show_grab_sprite(self):
        self.current_pixmap = self.grab_pixmap
        self.update()
    
    def reset_sprite(self):
        self.current_pixmap = self.chibi_pixmap
        self.update()
    
    # Доска
    def switch_to_board_mode(self):
        if self.mode == 'board':
            return
        
        self.mode = 'board'
        self.setFixedSize(480, 480) 
        self.rearrange_images()
        self.update()
    
    def switch_to_chibi_mode(self):
        self.mode = 'chibi'
        self.current_pixmap = self.chibi_pixmap
        self.setFixedSize(300, 300)
        self.update()
    
    def add_image_to_board(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            cols = max(1, self.width() // 160)
            row = len(self.images) // cols
            col = len(self.images) % cols
            
            x = col * 160
            y = row * 160
            
            rect = QRect(x, y, scaled_pixmap.width(), scaled_pixmap.height())
            
            self.images.append({
                'pixmap': scaled_pixmap,
                'rect': rect,
                'path': image_path
            })
            self.update()
    
    def remove_image(self, index):
        if 0 <= index < len(self.images):
            del self.images[index]
            self.rearrange_images()
            self.update()
    
    def get_image_at_position(self, pos):
        for i, img in enumerate(self.images):
            if img['rect'].contains(pos):
                return i
        return -1
    
    def rearrange_images(self):
        cols = max(1, self.width() // 160)
        for i, img in enumerate(self.images):
            row = i // cols
            col = i % cols
            x = col * 160 + 10
            y = row * 160 + 10
            img['rect'].moveTo(x, y)
    
    def clear_board(self):
        self.images.clear()
        self.update()
    
    # Перетаскивание изображений
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    if self.mode == 'chibi':
                        self.show_nom_sprite()
                    event.acceptProposedAction()
                    return
    
    def dragLeaveEvent(self, event):
        if self.mode == 'chibi':
            self.reset_sprite()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                if self.mode == 'chibi':
                    self.show_nom_sprite()
                    self.switch_to_board_mode()
                    self.add_image_to_board(file_path)
                else:
                    self.add_image_to_board(file_path)
                break
    
    # Обработка мыши
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            if self.mode == 'board':
                image_idx = self.get_image_at_position(event.pos())
                if image_idx != -1:
                    self.dragging_image_index = image_idx
                    self.drag_start_pos = event.pos()
                    event.accept()
                    return
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            if self.mode == 'chibi':
                self.show_grab_sprite()
            event.accept()  

        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
            event.accept()
    
    def mouseMoveEvent(self, event):
        if self.dragging_image_index != -1 and self.mode == 'board':
            new_pos = event.pos() - self.drag_start_pos
            img = self.images[self.dragging_image_index]
            new_rect = img['rect'].translated(new_pos)
            
            new_rect.setLeft(max(0, min(new_rect.left(), self.width() - img['rect'].width())))
            new_rect.setTop(max(0, min(new_rect.top(), self.height() - img['rect'].height())))
            
            img['rect'] = new_rect
            self.drag_start_pos = event.pos()
            self.update()
            event.accept()
            return
        
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_image_index = -1
            self.dragging = False
            if self.mode == 'chibi':
                self.reset_sprite()
    
    def show_context_menu(self, position):
        menu = QMenu(self)
        if self.mode == 'chibi':
            board_action = QAction("Доска", self)
            board_action.triggered.connect(self.switch_to_board_mode)
            menu.addAction(board_action)
        else:
            chibi_action = QAction("Режим чиби", self)
            chibi_action.triggered.connect(self.switch_to_chibi_mode)
            menu.addAction(chibi_action)
            if len(self.images) > 0:
                menu.addSeparator()
                clear_action = QAction("Очистить доску", self)
                clear_action.triggered.connect(self.clear_board)
                menu.addAction(clear_action)

        menu.addSeparator()
        close_action = QAction("Закрыть", self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)
        
        menu.exec_(position)
    
    # Отрисовка виджета
    def paintEvent(self, event):
        painter = QPainter(self)
        
        if self.mode == 'chibi':
            if self.current_pixmap:
                x = (self.width() - self.current_pixmap.width()) // 2
                y = (self.height() - self.current_pixmap.height()) // 2
                painter.drawPixmap(x, y, self.current_pixmap)
        else:
            # Режим доски (серый фон с сеткой)
            painter.setBrush(QColor(80, 80, 80, 200))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())
            
            # Сетка
            painter.setPen(QColor(120, 120, 120, 100))
            for x in range(0, self.width(), 160):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 160):
                painter.drawLine(0, y, self.width(), y)
            
            # Изображения
            for img in self.images:
                painter.drawPixmap(img['rect'], img['pixmap'])
                painter.setPen(QColor(200, 200, 200, 150))
                painter.drawRect(img['rect'])


# Окно ======================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.floating_widget = None
        self.notes_manager = NotesManager()
        
        # Окно
        self.setWindowTitle("Дом Али")
        self.setFixedSize(500, 650)
        self.setWindowIcon(self.create_icon())
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # layout
        main_layout = QVBoxLayout(central_widget)
        
        # Область с превью
        preview_label = QLabel("Это Аля")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(preview_label)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setStyleSheet("border: 2px solid #ccc; border-radius: 10px; background-color: #f0f0f0;")
        
        self.update_preview()
        main_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
        
        # Кнопки управления
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
        main_layout.addLayout(buttons_layout)
        
        # Режимы работы
        mode_label = QLabel("Режимы:")
        mode_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(mode_label)
        
        mode_buttons_layout = QHBoxLayout()
        
        self.chibi_mode_btn = QPushButton("Режим чиби")
        self.chibi_mode_btn.setStyleSheet(self.button_style("#2196F3"))
        self.chibi_mode_btn.clicked.connect(self.set_chibi_mode)
        
        self.board_mode_btn = QPushButton("Режим доски")
        self.board_mode_btn.setStyleSheet(self.button_style("#FF9800"))
        self.board_mode_btn.clicked.connect(self.set_board_mode)
        
        mode_buttons_layout.addWidget(self.chibi_mode_btn)
        mode_buttons_layout.addWidget(self.board_mode_btn)
        main_layout.addLayout(mode_buttons_layout)

        # Замтеки
        notes_label = QLabel("Заметки:")
        notes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(notes_label)
        
        # Поле для ввода
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите заметку и нажмите Enter или кнопку 'Добавить'...")
        self.input_field.setStyleSheet("padding: 8px; font-size: 12px; border-radius: 5px; border: 1px solid #ccc;")
        self.input_field.returnPressed.connect(self.add_note)
        main_layout.addWidget(self.input_field)
        
        # Кнопка добавления
        self.add_note_button = QPushButton("➕ Добавить заметку")
        self.add_note_button.setStyleSheet(self.button_style("#9C27B0"))
        self.add_note_button.clicked.connect(self.add_note)
        main_layout.addWidget(self.add_note_button)
        
        # Область для списка заметок
        scroll_area = QScrollArea()
        scroll_area.setFixedSize(480, 140)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: 1px solid #ccc; border-radius: 5px; background-color: white;")
        
        self.notes_widget = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_widget)
        self.notes_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.notes_widget)
        main_layout.addWidget(scroll_area)
        
        # Поле для заметок (тестовое)
        """""
        msg_label = QLabel("Заметки:")
        msg_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(msg_label)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Оставьте заметку")
        self.input_field.setStyleSheet("padding: 8px; font-size: 12px; border-radius: 5px; border: 1px solid #ccc;")
        main_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Отправить")
        self.send_button.setStyleSheet(self.button_style("#9C27B0"))
        self.send_button.clicked.connect(self.send_message)
        main_layout.addWidget(self.send_button)
        """

        # Статусная строка
        self.status_label = QLabel("Аля дома")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; padding: 10px; font-size: 11px;")
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()
        
        # Общие стили
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)

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
    # Иконка
    def create_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(255, 100, 150))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        return QIcon(pixmap)
    
    # Аля в превью
    def update_preview(self):
        if os.path.exists("sprite.png"):
            pixmap = QPixmap("sprite.png")
            if not pixmap.isNull():
                self.preview_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        
        # Заглушка
        pixmap = QPixmap(180, 180)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(255, 100, 150))
        painter.drawEllipse(15, 15, 150, 150)
        painter.setPen(Qt.white)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Аля")
        painter.end()
        self.preview_label.setPixmap(pixmap)
    
    # Запуск виджета
    def start_chibi(self):
        if self.floating_widget is None:
            self.floating_widget = FloatingChibi()
            self.status_label.setText("Аля на рабочем столе")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 10px; font-size: 11px;")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
    
    # Остановка виджета
    def stop_chibi(self):
        if self.floating_widget is not None:
            self.floating_widget.close()
            self.floating_widget = None
            self.status_label.setText("Аля снова дома")
            self.status_label.setStyleSheet("color: #888; padding: 10px; font-size: 11px;")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    # Переключение в чиби
    def set_chibi_mode(self):
        if self.floating_widget is not None:
            self.floating_widget.switch_to_chibi_mode()
            self.status_label.setText("Аля вышла трогать траву")
        else:
            QMessageBox.information(self, "Информация", "Аля не работает из дома, сначала запустите виджет")
    
    # Переключение в доску
    def set_board_mode(self):
        if self.floating_widget is not None:
            self.floating_widget.switch_to_board_mode()
            self.status_label.setText("Аля держит доску")
        else:
            QMessageBox.information(self, "Информация", "Аля не работает из дома, сначала запустите виджет")
    
    # Отправка заметок (тестовая)
    """
    def send_message(self):
        user_text = self.input_field.text().strip()
        if user_text:
            if self.floating_widget is not None:
                self.floating_widget.show_nom_sprite()
                self.status_label.setText(f"Пока без заметок")
                self.status_label.setStyleSheet("color: #4CAF50; padding: 10px; font-size: 11px;")
            else:
                self.status_label.setText(f"Пока без заметок")
                self.status_label.setStyleSheet("color: #4CAF50; padding: 10px; font-size: 11px;")
            
            self.input_field.clear()
        else:
            QMessageBox.warning(self, "Предупреждение", "Пожалуйста, введите сообщение!")
    """

    # Обновление списка заметок
    def refresh_notes_list(self):
        while self.notes_layout.count():
            item = self.notes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        notes = self.notes_manager.get_all_notes()
        if not notes:
            empty_label = QLabel("Здесь пока пусто")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999; padding: 30px;")
            self.notes_layout.addWidget(empty_label)
        else:
            for i, note in enumerate(reversed(notes)):
                note_widget = self.create_note_widget(note, len(notes) - 1 - i)
                self.notes_layout.addWidget(note_widget)
    
    # Создание отдельной заметки
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
        
        date_label = QLabel(f"{note['date']}")
        date_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(date_label)

        text_label = QLabel(note['text'])
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 12px; padding: 5px;")
        layout.addWidget(text_label)

        delete_btn = QPushButton("Удалить")
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
    
    def add_note(self):
        text = self.input_field.text().strip()
        if text:
            if self.notes_manager.add_note(text):
                self.input_field.clear()
                self.refresh_notes_list()
                self.status_label.setText("Заметка сохранена!")
                self.status_label.setStyleSheet("color: #4CAF50; padding: 10px; font-size: 11px;")
                if self.floating_widget is not None:
                    self.floating_widget.show_nom_sprite()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить заметку")
        else:
            QMessageBox.warning(self, "Предупреждение", "Введите текст заметки!")
    
    def delete_note(self, index):
        reply = QMessageBox.question(self, "Подтверждение", 
                                     "Удалить эту заметку?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.notes_manager.delete_note(index):
                self.refresh_notes_list()
                self.status_label.setText("Заметка удалена")
                self.status_label.setStyleSheet("color: #888; padding: 10px; font-size: 11px;")

# Заметки ====================================================
class NotesManager:  
    def __init__(self, filename="notes.json"):
        self.filename = filename
        self.notes = self.load_notes()
    
    def load_notes(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_notes(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def add_note(self, text):
        if text.strip():
            note = {
                'id': len(self.notes) + 1,
                'text': text,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.notes.append(note)
            self.save_notes()
            return True
        return False
    
    def delete_note(self, index):
        if 0 <= index < len(self.notes):
            del self.notes[index]
            self.save_notes()
            return True
        return False
    
    def get_all_notes(self):
        return self.notes

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
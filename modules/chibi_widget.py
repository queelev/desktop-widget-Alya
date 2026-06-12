"""
Модуль плавающего виджета чиби
"""

import os
from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QDragEnterEvent, QDropEvent

from .image_processor import ImageProcessor

# Плавающий виджет с режимом доски
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
        self.image_processor = ImageProcessor()
        
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
        paths = ["assets/" + filename, filename]
        
        for path in paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
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
        self.nom_timer.start(5000)
    
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
        pixmap = self.image_processor.load_image(image_path, 300)
        if pixmap and not pixmap.isNull():
            cols = max(1, self.width() // 160)
            row = len(self.images) // cols
            col = len(self.images) % cols
            
            x = col * 160
            y = row * 160
            
            rect = QRect(x, y, pixmap.width(), pixmap.height())
            
            self.images.append({
                'pixmap': pixmap,
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
            x = col * 160
            y = row * 160
            img['rect'].moveTo(x, y)
    
    def clear_board(self):
        self.images.clear()
        self.update()
    
    # Перетаскивание изображений
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if self.image_processor.is_image_file(url.toLocalFile()):
                    if self.mode == 'chibi':
                        self.show_nom_sprite()
                    event.acceptProposedAction()
                    return
    
    def dragLeaveEvent(self, event):
        if self.mode == 'chibi':
            self.reset_sprite()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if self.image_processor.is_image_file(file_path):
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
            painter.setBrush(QColor(80, 80, 80, 200))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())
            painter.setPen(QColor(120, 120, 120, 100))
            for x in range(0, self.width(), 160):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 160):
                painter.drawLine(0, y, self.width(), y)
            for img in self.images:
                painter.drawPixmap(img['rect'], img['pixmap'])
                painter.setPen(QColor(200, 200, 200, 150))
                painter.drawRect(img['rect'])
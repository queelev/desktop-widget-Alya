"""
Модуль обработки изображений
"""

import os
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class ImageProcessor:
    SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    @staticmethod
    def is_image_file(filepath):
        return filepath.lower().endswith(ImageProcessor.SUPPORTED_FORMATS)
    
    @staticmethod
    def load_image(filepath, max_size=300):
        if not os.path.exists(filepath):
            return None
        
        pixmap = QPixmap(filepath)
        if pixmap.isNull():
            return None
        
        return pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    @staticmethod
    def get_image_info(filepath):
        if not os.path.exists(filepath):
            return None
        
        pixmap = QPixmap(filepath)
        if pixmap.isNull():
            return None
        
        return {
            'path': filepath,
            'size': (pixmap.width(), pixmap.height()),
            'filename': os.path.basename(filepath)
        }
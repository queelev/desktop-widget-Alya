"""
Модуль управления заметками
"""

import sqlite3
import os
import json
from datetime import datetime

class NotesManager:
    def __init__(self, db_path="data/alya.db"):
        self.db_path = db_path
        self.init_database()
    
    # Инициализация БД
    def init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                text TEXT NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    # Возвращает все заметки
    def get_all_notes(self):
        self.cursor.execute("SELECT id, title, text, date FROM notes ORDER BY id DESC")
        rows = self.cursor.fetchall()
        notes = []
        for row in rows:
            notes.append({
                'id': row[0],
                'title': row[1] if row[1] else "Без заголовка",
                'text': row[2],
                'date': row[3]
            })
        return notes
    
    # Новая заметка
    def add_note(self, title, text):
        if text.strip():
            self.cursor.execute(
                "INSERT INTO notes (title, text, date) VALUES (?, ?, ?)",
                (title if title else "Без заголовка", text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.conn.commit()
            return True
        return False
    
    # Удаление заметкаи
    def delete_note(self, index):
        notes = self.get_all_notes()
        if 0 <= index < len(notes):
            note_id = notes[index]['id']
            self.cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            self.conn.commit()
            return True
        return False
    
    # Очистка заметок
    def clear_all_notes(self):
        self.cursor.execute("DELETE FROM notes")
        self.conn.commit()
        return True
    
    # Количество заметок
    def get_notes_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM notes")
        return self.cursor.fetchone()[0]
    
    # Экспорт заметок
    def export_to_file(self, filename="notes_export.json"):
        notes = self.get_all_notes()
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(notes, f, ensure_ascii=False, indent=2)
            return os.path.abspath(filename)
        except:
            return None
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
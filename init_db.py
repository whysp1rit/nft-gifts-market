#!/usr/bin/env python3
"""
Инициализация базы данных для Render.com
"""

import os
import sqlite3

def init_database():
    """Создает базу данных и таблицы"""
    # Создаем папку data если не существует
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect('data/mini_app.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            username TEXT,
            first_name TEXT,
            balance_stars INTEGER DEFAULT 0,
            balance_rub REAL DEFAULT 0,
            successful_deals INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица сделок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            seller_id TEXT,
            buyer_id TEXT,
            nft_link TEXT,
            nft_username TEXT,
            amount REAL,
            currency TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP,
            completed_at TIMESTAMP,
            description TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

if __name__ == '__main__':
    init_database()
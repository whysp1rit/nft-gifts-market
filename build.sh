#!/bin/bash

echo "🚀 Сборка NFT Gifts Market для Render.com..."

# Установка зависимостей
pip install -r requirements.txt

# Инициализация базы данных
python init_db.py

echo "✅ Сборка завершена!"
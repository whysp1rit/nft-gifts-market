# Основной файл для Render.com
import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simple_mini_app import app

# Настройки для продакшена
app.config['DEBUG'] = False
app.config['ENV'] = 'production'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

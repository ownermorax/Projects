from flask import Flask, request, render_template_string
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import json
from datetime import datetime
import user_agents
import requests

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

DATA_FILE = 'visitors_data.json'

def get_real_ip():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

def get_geo_data(ip):
    geo_data = {
        'country': 'Unknown',
        'country_code': 'Unknown',
        'region': 'Unknown',
        'city': 'Unknown',
        'latitude': 'Unknown',
        'longitude': 'Unknown',
        'zip_code': 'Unknown',
        'timezone': 'Unknown',
        'asn': 'Unknown',
        'isp': 'Unknown',
        'is_proxy': False
    }
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                geo_data.update({
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('countryCode', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'latitude': data.get('lat', 'Unknown'),
                    'longitude': data.get('lon', 'Unknown'),
                    'zip_code': data.get('zip', 'Unknown'),
                    'timezone': data.get('timezone', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'asn': data.get('as', 'Unknown')
                })
    except:
        pass
    return geo_data

def get_device_data(user_agent):
    ua = user_agents.parse(user_agent)
    return {
        'browser': f"{ua.browser.family} {ua.browser.version_string}",
        'os': f"{ua.os.family} {ua.os.version_string}",
        'device': ua.device.family,
        'is_mobile': ua.is_mobile,
        'is_tablet': ua.is_tablet,
        'is_pc': ua.is_pc,
        'is_bot': ua.is_bot
    }

def update_visitor_data():
    ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    geo_data = get_geo_data(ip)
    device_data = get_device_data(user_agent)

    visitor_info = {
        'ip': ip,
        'first_visit': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_visit': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'visit_count': 1,
        'referrer': referrer,
        'location': {
            'country': geo_data.get('country', 'Unknown'),
            'country_code': geo_data.get('country_code', 'Unknown'),
            'region': geo_data.get('region', 'Unknown'),
            'city': geo_data.get('city', 'Unknown'),
            'zip_code': geo_data.get('zip_code', 'Unknown'),
            'timezone': geo_data.get('timezone', 'Unknown'),
            'coordinates': {
                'latitude': geo_data.get('latitude', 'Unknown'),
                'longitude': geo_data.get('longitude', 'Unknown'),
                'map_link': f"https://www.openstreetmap.org/?mlat={geo_data.get('latitude', '')}&mlon={geo_data.get('longitude', '')}#map=12/{geo_data.get('latitude', '')}/{geo_data.get('longitude', '')}"
            }
        },
        'network': {
            'isp': geo_data.get('isp', 'Unknown'),
            'asn': geo_data.get('asn', 'Unknown'),
            'is_proxy': geo_data.get('is_proxy', False)
        },
        'device': {
            'type': device_data['device'],
            'os': device_data['os'],
            'browser': device_data['browser'],
            'is_mobile': device_data['is_mobile'],
            'is_tablet': device_data['is_tablet'],
            'is_pc': device_data['is_pc'],
            'is_bot': device_data['is_bot']
        }
    }

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = {}
    else:
        existing_data = {}

    if ip in existing_data:
        existing_visitor = existing_data[ip]
        visitor_info['first_visit'] = existing_visitor.get('first_visit', visitor_info['first_visit'])
        visitor_info['visit_count'] = existing_visitor.get('visit_count', 0) + 1

    existing_data[ip] = visitor_info

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

MAIN_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Простой сайт</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            text-align: center;
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        p {
            font-size: 1.2em;
            line-height: 1.6;
            margin-bottom: 30px;
        }
        .data-link {
            display: inline-block;
            padding: 15px 30px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            border: 2px solid rgba(255,255,255,0.3);
            transition: all 0.3s;
            font-size: 1.1em;
        }
        .data-link:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Добро пожаловать!</h1>
        <p>Это простой сайт с красивым дизайном. Здесь вы можете найти полезную информацию и ссылки на другие страницы.</p>
        <p>Сайт создан для демонстрации возможностей веб-разработки и отслеживания посещений.</p>
        
        <a href="/data" class="data-link">📊 Посмотреть статистику посещений</a>
    </div>
</body>
</html>
"""

DATA_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Данные посещений</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #e0e0e0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #8b0000;
            text-align: center;
            margin-bottom: 30px;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #8b0000;
            text-decoration: none;
            padding: 10px 20px;
            border: 1px solid #8b0000;
            border-radius: 5px;
        }
        .visitor-card {
            background: #2a2a2a;
            border: 1px solid #8b0000;
            margin-bottom: 20px;
            padding: 20px;
            border-radius: 10px;
        }
        .visitor-header {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #8b0000;
            border-bottom: 1px solid #8b0000;
            padding-bottom: 10px;
        }
        .visitor-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        .detail-group {
            margin-bottom: 10px;
        }
        .detail-label {
            font-weight: bold;
            color: #b8860b;
        }
        .map-link {
            color: #8b0000;
            text-decoration: none;
        }
        .map-link:hover {
            text-decoration: underline;
        }
        .proxy-badge {
            display: inline-block;
            padding: 2px 8px;
            background: #8b0000;
            color: white;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        .stats {
            background: #2a2a2a;
            padding: 20px;
            border: 1px solid #8b0000;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← На главную</a>
        <h1>📊 Данные о посетителях</h1>
        
        <div class="stats">
            <h2>Общая статистика</h2>
            <p>Всего уникальных посетителей: <strong>{{ total_visitors }}</strong></p>
            <p>Общее количество посещений: <strong>{{ total_visits }}</strong></p>
        </div>

        {% for ip, data in visitors_data.items() %}
        <div class="visitor-card">
            <div class="visitor-header">
                🖥️ {{ ip }}
                {% if data.network.is_proxy %}<span class="proxy-badge">PROXY</span>{% endif %}
            </div>
            <div class="visitor-details">
                <div>
                    <div class="detail-group">
                        <span class="detail-label">Посещения:</span> {{ data.visit_count }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Первое посещение:</span> {{ data.first_visit }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Последнее посещение:</span> {{ data.last_visit }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Источник:</span> {{ data.referrer }}
                    </div>
                </div>
                <div>
                    <div class="detail-group">
                        <span class="detail-label">Страна:</span> {{ data.location.country }} ({{ data.location.country_code }})
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Регион:</span> {{ data.location.region }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Город:</span> {{ data.location.city }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Часовой пояс:</span> {{ data.location.timezone }}
                    </div>
                </div>
                <div>
                    <div class="detail-group">
                        <span class="detail-label">Координаты:</span>
                        {{ data.location.coordinates.latitude }}, {{ data.location.coordinates.longitude }}
                        {% if data.location.coordinates.latitude != 'Unknown' %}
                        <a href="{{ data.location.coordinates.map_link }}" class="map-link" target="_blank">(открыть карту)</a>
                        {% endif %}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Провайдер:</span> {{ data.network.isp }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">ASN:</span> {{ data.network.asn }}
                    </div>
                </div>
                <div>
                    <div class="detail-group">
                        <span class="detail-label">Устройство:</span> {{ data.device.type }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">ОС:</span> {{ data.device.os }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Браузер:</span> {{ data.device.browser }}
                    </div>
                    <div class="detail-group">
                        <span class="detail-label">Тип:</span>
                        {% if data.device.is_mobile %} Телефон{% endif %}
                        {% if data.device.is_tablet %} Планшет{% endif %}
                        {% if data.device.is_pc %} Компьютер{% endif %}
                        {% if data.device.is_bot %} Бот{% endif %}
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    update_visitor_data()
    return MAIN_PAGE

@app.route('/data')
def show_data():
    update_visitor_data()
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            visitors_data = json.load(f)
    else:
        visitors_data = {}

    total_visitors = len(visitors_data)
    total_visits = sum(visitor['visit_count'] for visitor in visitors_data.values())

    return render_template_string(DATA_PAGE, 
                                visitors_data=visitors_data,
                                total_visitors=total_visitors,
                                total_visits=total_visits)

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

import requests
import time
from datetime import datetime
import socket
import socks
from urllib.parse import urlparse

def detect_proxy_type(proxy):
    proxy_types = ['socks5', 'socks4', 'https', 'http']
    
    for proxy_type in proxy_types:
        try:
            proxies = {
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            }
            
            start_time = time.time()
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=5
            )
            
            if response.status_code == 200:
                response_time = round((time.time() - start_time) * 1000)
                return proxy_type, response_time
        except:
            continue
    
    return None, 0

def load_proxies(filename='proxy.txt'):
    try:
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return list(set(proxies))
    except FileNotFoundError:
        print(f"Файл {filename} не найден!")
        return []

def check_proxy(proxy):
    print(f"Проверяем {proxy}...", end=' ', flush=True)
    
    proxy_type, response_time = detect_proxy_type(proxy)
    
    if proxy_type:
        print(f"✓ [{proxy_type.upper()}] Работает ({response_time}мс)")
        return True, proxy_type, response_time
    
    print("✗ Не удалось определить тип или прокси не работает")
    return False, None, 0

def save_working_proxies(proxies, filename='working_proxy.txt'):
    with open(filename, 'w') as f:
        for proxy_info in proxies:
            proxy, proxy_type, response_time = proxy_info
            f.write(f"{proxy_type}://{proxy} # {response_time}ms\n")
    print(f"\nСохранено {len(proxies)} рабочих прокси в {filename}")

def main():
    print("=== Автоматическая проверка прокси ===")
    print(f"Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    proxies = load_proxies()
    if not proxies:
        return
    
    print(f"Загружено {len(proxies)} уникальных прокси\n")
    print("Определение типа прокси...\n")
    
    working_proxies = []
    for proxy in proxies:
        is_working, proxy_type, response_time = check_proxy(proxy)
        if is_working:
            working_proxies.append((proxy, proxy_type, response_time))
    
    if working_proxies:
        save_working_proxies(working_proxies)
        
        type_stats = {}
        for _, proxy_type, _ in working_proxies:
            type_stats[proxy_type] = type_stats.get(proxy_type, 0) + 1
        
        print("\nСтатистика по типам прокси:")
        for p_type, count in type_stats.items():
            print(f"{p_type.upper()}: {count}")
    else:
        print("\nНе найдено рабочих прокси!")

if __name__ == "__main__":
    main()

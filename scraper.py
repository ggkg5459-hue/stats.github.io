import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

def fetch_data():
    url = "https://kyiv.digital/storage/air-alert/stats.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        counts = [0] * 60
        durations = [0.0] * 60
        
        # Шукаємо всі рядки таблиці
        rows = soup.find_all('tr')
        if not rows:
            print("Таблицю не знайдено! Можливо, сайт змінив структуру.")
            return
            
        print(f"Знайдено {len(rows)} рядків у таблиці. Починаємо аналіз історії...")
        current_alert_idx = None
        
        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 2:
                time_str = cols[0].get_text(separator=" ", strip=True)
                event_str = cols[1].get_text(separator=" ", strip=True)
                
                # Шукаємо дату (наприклад: 09.10.26)
                date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2,4})', time_str)
                if not date_match: 
                    continue
                    
                day = int(date_match.group(1))
                month = int(date_match.group(2))
                year_part = date_match.group(3)
                year = int(year_part) if len(year_part) == 4 else 2000 + int(year_part)
                
                if 2022 <= year <= 2026:
                    month_idx = (year - 2022) * 12 + (month - 1)
                    
                    # Рахуємо старт тривоги
                    if "Повітряна тривога" in event_str or "тривога" in event_str.lower():
                        counts[month_idx] += 1
                        current_alert_idx = month_idx
                        
                # Рахуємо тривалість після відбою
                if "Відбій" in event_str or "відбій" in event_str.lower():
                    dur_str = ""
                    if len(cols) >= 3:
                        dur_str = cols[2].get_text(separator=" ", strip=True)
                    else:
                        dur_str = event_str
                        
                    h_match = re.search(r'(\d+)\s*год', dur_str)
                    m_match = re.search(r'(\d+)\s*хвил', dur_str)
                    
                    h = int(h_match.group(1)) if h_match else 0
                    m = int(m_match.group(1)) if m_match else 0
                    
                    # Записуємо години у той місяць, коли тривога почалася
                    target_idx = current_alert_idx if current_alert_idx is not None else (
                        (year - 2022) * 12 + (month - 1) if 2022 <= year <= 2026 else -1
                    )
                    
                    if 0 <= target_idx < 60:
                        durations[target_idx] += h + (m / 60.0)
                        
                    current_alert_idx = None

        # Округлюємо тривалість до 1 знаку
        durations = [round(d, 1) for d in durations]
        
        total_found = sum(counts)
        print(f"Успішно зібрано історичні дані! Всього знайдено тривог: {total_found}")
        
        if total_found == 0:
            print("Помилка: не вдалося розпізнати тривоги з таблиці.")
            return

        # Відкриваємо та перезаписуємо файл data.json
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        kyiv_tz = timezone(timedelta(hours=3))
        data['last_update'] = datetime.now(kyiv_tz).strftime("%d.%m.%Y %H:%M")
        
        data['all']['counts'] = counts
        data['all']['durations'] = durations
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("Файл data.json успішно оновлено!")
        
    except Exception as e:
        print(f"Помилка: {e}")

if __name__ == "__main__":
    fetch_data()

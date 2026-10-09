import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

def fetch_data():
    url = "https://kyiv.digital/storage/air-alert/stats.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text_element = soup.find(string=re.compile(r'пролунало\s+\d+'))
        if not text_element:
            print("Текст зі статистикою не знайдено на сторінці!")
            return
            
        text = text_element.text.strip()
        
        alerts_match = re.search(r'пролунало\s+(\d+)', text)
        hours_match = re.search(r'тривала\s+(\d+)', text)
        mins_match = re.search(r'(\d+)\s*хвилин', text)
        
        if alerts_match and hours_match and mins_match:
            total_alerts = int(alerts_match.group(1))
            total_hours = int(hours_match.group(1))
            total_mins = int(mins_match.group(1))
            
            total_duration = total_hours + (total_mins / 60.0)
            
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Визначаємо поточний рік та місяць (за Київським часом UTC+3)
            kyiv_tz = timezone(timedelta(hours=3))
            now = datetime.now(kyiv_tz)
            current_year = now.year
            current_month = now.month
            
            # Записуємо час останнього оновлення
            data['last_update'] = now.strftime("%d.%m.%Y %H:%M")
            
            if 2022 <= current_year <= 2026:
                current_index = (current_year - 2022) * 12 + (current_month - 1)
                
                past_alerts = sum(data['all']['counts'][:current_index])
                past_durations = sum(data['all']['durations'][:current_index])
                
                current_month_alerts = total_alerts - past_alerts
                current_month_duration = total_duration - past_durations
                
                data['all']['counts'][current_index] = max(0, current_month_alerts)
                data['all']['durations'][current_index] = max(0, round(current_month_duration, 1))
                
                with open('data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
                print(f"Успішно оновлено о {data['last_update']}.")
        else:
            print("Не вдалося розпізнати цифри у знайденому тексті.")
            
    except Exception as e:
        print(f"Виникла помилка: {e}")

if __name__ == "__main__":
    fetch_data()

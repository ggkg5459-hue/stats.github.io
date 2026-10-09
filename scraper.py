import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_data():
    url = "https://kyiv.digital/storage/air-alert/stats.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Шукаємо блок з загальною статистикою
        text_element = soup.find(string=re.compile(r'пролунало\s+\d+'))
        if not text_element:
            print("Текст зі статистикою не знайдено на сторінці!")
            return
            
        text = text_element.text.strip()
        print(f"Знайдено текст на сайті: {text}")
        
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
                
            # Отримуємо поточний рік та місяць
            now = datetime.now()
            current_year = now.year
            current_month = now.month
            
            # Працюємо в межах 2022-2026 років (масив з 60 елементів)
            if 2022 <= current_year <= 2026:
                # Розраховуємо індекс масиву (від 0 до 59)
                current_index = (current_year - 2022) * 12 + (current_month - 1)
                
                # Підсумовуємо всі дані за попередні місяці
                past_alerts = sum(data['all']['counts'][:current_index])
                past_durations = sum(data['all']['durations'][:current_index])
                
                # Обчислюємо дані САМЕ за поточний місяць
                current_month_alerts = total_alerts - past_alerts
                current_month_duration = total_duration - past_durations
                
                # Захист від від'ємних значень
                data['all']['counts'][current_index] = max(0, current_month_alerts)
                data['all']['durations'][current_index] = max(0, round(current_month_duration, 1))
                
                # Зберігаємо оновлену базу
                with open('data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
                print(f"Успішно оновлено! Місяць: {current_month}, Рік: {current_year} (Індекс {current_index}).")
                print(f"Тривог у поточному місяці: {current_month_alerts}, Годин: {round(current_month_duration, 1)}")
            else:
                print(f"Поточний рік ({current_year}) знаходиться поза межами діапазону графіка (2022-2026).")
        else:
            print("Не вдалося розпізнати цифри у знайденому тексті.")
            
    except Exception as e:
        print(f"Виникла помилка: {e}")

if __name__ == "__main__":
    fetch_data()

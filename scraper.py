import json
import re
import requests
from bs4 import BeautifulSoup

def fetch_data():
    url = "https://kyiv.digital/storage/air-alert/stats.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # Завантажуємо сторінку
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Шукаємо текст, який містить слово "пролунало"
        text_element = soup.find(string=re.compile(r'пролунало\s+\d+'))
        if not text_element:
            print("Текст зі статистикою не знайдено на сторінці!")
            return
            
        text = text_element.text.strip()
        print(f"Знайдено текст на сайті: {text}")
        
        # Витягуємо цифри з тексту
        alerts_match = re.search(r'пролунало\s+(\d+)', text)
        hours_match = re.search(r'тривала\s+(\d+)', text)
        mins_match = re.search(r'(\d+)\s*хвилин', text)
        
        if alerts_match and hours_match and mins_match:
            total_alerts = int(alerts_match.group(1))
            total_hours = int(hours_match.group(1))
            total_mins = int(mins_match.group(1))
            
            # Переводимо хвилини в десяткові долі години (наприклад, 30 хв = 0.5 год)
            total_duration = total_hours + (total_mins / 60.0)
            
            # Відкриваємо нашу базу даних
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Оскільки на сайті є лише "Загальна" статистика, 
            # ми вирахуємо дані за поточний 2024 рік: 
            # (Загальна кількість) мінус (Дані за 2022 і 2023 роки)
            alerts_2022_2023 = data['all']['counts'][0] + data['all']['counts'][1]
            durations_2022_2023 = data['all']['durations'][0] + data['all']['durations'][1]
            
            alerts_2024 = total_alerts - alerts_2022_2023
            durations_2024 = total_duration - durations_2022_2023
            
            # Записуємо оновлені дані за 2024 рік у масив
            data['all']['counts'][2] = alerts_2024
            data['all']['durations'][2] = round(durations_2024, 1)
            
            # Зберігаємо оновлений файл
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"Успішно оновлено! Всього тривог: {total_alerts}, Тривалість: {round(total_duration, 1)} год.")
        else:
            print("Не вдалося розпізнати цифри у знайденому тексті.")
            
    except Exception as e:
        print(f"Виникла помилка: {e}")

if __name__ == "__main__":
    fetch_data()

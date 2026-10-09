import json
import re
import requests
import sys
import traceback
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

def fetch_data():
    url = "https://kyiv.digital/storage/air-alert/stats.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Масиви для зберігання точної статистики
        counts = [0] * 60
        durations = [0.0] * 60
        year_counts = [0] * 12
        year_durations = [0.0] * 12
        week_counts = [0] * 7
        week_durations = [0.0] * 7
        
        # Часовий пояс Києва
        kyiv_tz = timezone(timedelta(hours=3))
        now = datetime.now(kyiv_tz)
        current_year = now.year
        
        # Початок поточного тижня
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Беремо весь текст зі сторінки, розбиваємо на рядки
        # Це працює незалежно від того, використовується <table>, <div> чи <ul>
        text_lines = soup.get_text(separator='\n', strip=True).split('\n')
        
        alerts_found = 0
        
        for i, line in enumerate(text_lines):
            line = line.strip()
            # Шукаємо формат дати і часу, напр. "03:36 09.10.26"
            if re.match(r'^\d{2}:\d{2}\s\d{2}\.\d{2}\.\d{2}$', line):
                try:
                    dt = datetime.strptime(line, "%H:%M %d.%m.%y").replace(tzinfo=kyiv_tz)
                except ValueError:
                    continue
                    
                month_idx = (dt.year - 2022) * 12 + (dt.month - 1)
                
                # Подія зазвичай знаходиться в наступному рядку
                if i + 1 < len(text_lines):
                    event = text_lines[i+1].strip()
                    
                    if "Повітряна тривога" in event:
                        alerts_found += 1
                        if 0 <= month_idx < 60:
                            counts[month_idx] += 1
                        if dt.year == current_year:
                            year_counts[dt.month - 1] += 1
                        if dt >= start_of_week:
                            week_counts[dt.weekday()] += 1
                            
                    elif "Відбій" in event:
                        # Тривалість може бути в цьому ж рядку або через один
                        dur_str = ""
                        if i + 2 < len(text_lines) and ("год" in text_lines[i+2] or "хвил" in text_lines[i+2]):
                            dur_str = text_lines[i+2]
                        else:
                            dur_str = event
                            
                        hours, mins = 0, 0
                        h_match = re.search(r'(\d+)\s*год', dur_str)
                        m_match = re.search(r'(\d+)\s*хвил', dur_str)
                        
                        if h_match: hours = int(h_match.group(1))
                        if m_match: mins = int(m_match.group(1))
                        dur_hours = hours + (mins / 60.0)
                        
                        if 0 <= month_idx < 60:
                            durations[month_idx] += dur_hours
                        if dt.year == current_year:
                            year_durations[dt.month - 1] += dur_hours
                        if dt >= start_of_week:
                            week_durations[dt.weekday()] += dur_hours
                            
        if alerts_found == 0:
            print("Не знайдено жодної тривоги. Можливо, сайт тимчасово недоступний або змінив формат.")
            sys.exit(1) # Тепер, якщо помилка, GitHub Action покаже червоний хрестик
            
        durations = [round(d, 1) for d in durations]
        year_durations = [round(d, 1) for d in year_durations]
        week_durations = [round(d, 1) for d in week_durations]
        
        new_data = {
            "last_update": now.strftime("%d.%m.%Y %H:%M"),
            "all": { "counts": counts, "durations": durations },
            "year": { "counts": year_counts, "durations": year_durations },
            "week": { "counts": week_counts, "durations": week_durations }
        }
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
            
        print(f"Дані успішно зібрано! Знайдено тривог: {alerts_found}")
        
    except Exception as e:
        print(f"Помилка: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    fetch_data()

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
        
        # Масиви для зберігання точної статистики (5 років, 12 місяців, 7 днів)
        counts = [0] * 5
        durations = [0.0] * 5
        year_counts = [0] * 12
        year_durations = [0.0] * 12
        week_counts = [0] * 7
        week_durations = [0.0] * 7
        
        kyiv_tz = timezone(timedelta(hours=3))
        now = datetime.now(kyiv_tz)
        current_year = now.year
        
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        table = soup.find('table')
        if not table:
            print("Таблицю не знайдено!")
            return
            
        rows = table.find_all('tr')
        current_alert_year_index = None
        current_alert_dt = None
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                time_str = cols[0].get_text(strip=True)
                event_str = cols[1].get_text(strip=True) 
                
                try:
                    dt = datetime.strptime(time_str, "%H:%M %d.%m.%y")
                    dt = dt.replace(tzinfo=kyiv_tz)
                except ValueError:
                    continue
                    
                year_idx = dt.year - 2022
                
                if "Повітряна тривога" in event_str:
                    current_alert_dt = dt
                    current_alert_year_index = year_idx
                    
                    if 0 <= year_idx < 5:
                        counts[year_idx] += 1
                    if dt.year == current_year:
                        year_counts[dt.month - 1] += 1
                    if dt >= start_of_week:
                        week_counts[dt.weekday()] += 1
                        
                elif "Відбій" in event_str:
                    if len(cols) >= 3:
                        dur_str = cols[2].get_text(strip=True)
                        hours, mins = 0, 0
                        h_match = re.search(r'(\d+)\s*год', dur_str)
                        m_match = re.search(r'(\d+)\s*хвил', dur_str)
                        
                        if h_match: hours = int(h_match.group(1))
                        if m_match: mins = int(m_match.group(1))
                        dur_hours = hours + (mins / 60.0)
                        
                        target_idx = current_alert_year_index if current_alert_year_index is not None else year_idx
                        target_dt = current_alert_dt if current_alert_dt is not None else dt
                        
                        if target_idx is not None and 0 <= target_idx < 5:
                            durations[target_idx] += dur_hours
                        if target_dt.year == current_year:
                            year_durations[target_dt.month - 1] += dur_hours
                        if target_dt >= start_of_week:
                            week_durations[target_dt.weekday()] += dur_hours
                            
                    current_alert_year_index = None
                    current_alert_dt = None
                            
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
            
        print(f"Дані успішно зібрано з таблиці! Всього тривог: {sum(counts)}")
        
    except Exception as e:
        print(f"Помилка: {e}")

if __name__ == "__main__":
    fetch_data()

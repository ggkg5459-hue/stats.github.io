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
        
        # Ініціалізуємо порожні масиви
        counts = [0] * 60
        durations = [0.0] * 60
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
        current_alert_idx = None
        current_alert_dt = None
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                time_str = cols[0].get_text(strip=True)
                event_str = cols[1].get_text(strip=True)
                
                try:
                    # Шукаємо дату у форматі DD.MM.YY або DD.MM.YYYY
                    date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2,4})', time_str)
                    if not date_match: continue
                    
                    day = int(date_match.group(1))
                    month = int(date_match.group(2))
                    year_part = date_match.group(3)
                    year = int(year_part) if len(year_part) == 4 else 2000 + int(year_part)
                    
                    # Визначаємо, в яку колонку з 60 записати дані
                    if 2022 <= year <= 2026:
                        month_idx = (year - 2022) * 12 + (month - 1)
                    else:
                        month_idx = -1
                        
                    time_match = re.search(r'(\d{2}):(\d{2})', time_str)
                    hour = int(time_match.group(1)) if time_match else 0
                    minute = int(time_match.group(2)) if time_match else 0
                    
                    dt = datetime(year, month, day, hour, minute, tzinfo=kyiv_tz)
                except Exception:
                    continue
                    
                if "Повітряна тривога" in event_str:
                    current_alert_idx = month_idx
                    current_alert_dt = dt
                    
                    if 0 <= month_idx < 60:
                        counts[month_idx] += 1
                        
                    if year == current_year:
                        year_counts[month - 1] += 1
                        
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
                        
                        target_idx = current_alert_idx if current_alert_idx is not None else month_idx
                        target_dt = current_alert_dt if current_alert_dt is not None else dt
                        
                        if target_idx is not None and 0 <= target_idx < 60:
                            durations[target_idx] += dur_hours
                            
                        if target_dt.year == current_year:
                            year_durations[target_dt.month - 1] += dur_hours
                            
                        if target_dt >= start_of_week:
                            week_durations[target_dt.weekday()] += dur_hours
                            
                    current_alert_idx = None
                    current_alert_dt = None
        
        # Округлюємо тривалість до 1 знака після коми
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
            
        print(f"Дані успішно зібрано! Записано історію з {sum(counts)} тривог.")
        
    except Exception as e:
        print(f"Помилка: {e}")

if __name__ == "__main__":
    fetch_data()

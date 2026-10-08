Python
import json
from datetime import datetime

# Тут у майбутньому буде код, який зчитує сайт Київ Цифровий.
# Оскільки для парсингу реального сайту треба аналізувати його HTML-теги,
# зараз ми робимо "заглушку", яка імітує отримання нових даних (додає +1 тривогу для прикладу).

def fetch_data():
    try:
        # Читаємо старий файл
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Симулюємо отримання свіжих даних (додаємо 1 тривогу в "За весь час")
        data['all']['counts'][2] += 1 
        data['all']['durations'][2] += 1.5
        
        # Зберігаємо оновлений файл
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("Дані успішно оновлено!")
    except Exception as e:
        print(f"Помилка: {e}")

if __name__ == "__main__":
    fetch_data()

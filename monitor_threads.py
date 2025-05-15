import psutil
import time
import os
import csv
import json
from datetime import datetime

TXT_LOG = "monitor_log.txt"
CSV_LOG = "monitor_log.csv"
JSON_LOG = "monitor_log.json"

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def format_bytes(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def log_to_txt(entries, timestamp):
    try:
        with open(TXT_LOG, "a") as f:
            f.write(f"\n===== Мониторинг: {timestamp} =====\n")
            f.write(f"{'PID':<8} {'Name':<25} {'Threads':<10} {'CPU %':<10} {'Memory':<15}\n")
            f.write("-" * 70 + "\n")
            for entry in entries:
                f.write(f"{entry['pid']:<8} {entry['name']:<25} {entry['threads']:<10} {entry['cpu']:<10.1f} {entry['mem']:<15}\n")
    except Exception as e:
        print(f"[TXT] Ошибка при логировании: {e}")

def log_to_csv(entries, timestamp):
    try:
        file_exists = os.path.isfile(CSV_LOG)
        with open(CSV_LOG, "a", newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "PID", "Name", "Threads", "CPU %", "Memory"])
            for entry in entries:
                writer.writerow([
                    timestamp,
                    entry['pid'],
                    entry['name'],
                    entry['threads'],
                    entry['cpu'],
                    entry['mem']
                ])
    except Exception as e:
        print(f"[CSV] Ошибка при логировании: {e}")

def log_to_json(entries, timestamp):
    try:
        log_entry = {
            "timestamp": timestamp,
            "processes": entries
        }
        if not os.path.isfile(JSON_LOG):
            with open(JSON_LOG, "w") as f:
                json.dump([log_entry], f, indent=4)
        else:
            with open(JSON_LOG, "r+", encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.append(log_entry)
                f.seek(0)
                json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[JSON] Ошибка при логировании: {e}")

def clear_logs():
    for path in [TXT_LOG, CSV_LOG, JSON_LOG]:
        try:
            open(path, "w").close()
            print(f"[OK] Очищен: {path}")
        except Exception as e:
            print(f"[Ошибка] Не удалось очистить {path}: {e}")
            
def monitor_processes(refresh_interval=5, sort_by='none'):
    try:
        for proc in psutil.process_iter():
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        while True:
            clear_screen()
            entries = []
            print(f"{'PID':<8} {'Name':<25} {'Threads':<10} {'CPU %':<10} {'Memory':<15}")
            print("-" * 70)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for proc in psutil.process_iter(['pid', 'name', 'num_threads', 'memory_info']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name'][:24]
                    threads = proc.info['num_threads']
                    cpu = proc.cpu_percent(interval=None)
                    mem_raw = proc.info['memory_info'].rss
                    mem = format_bytes(mem_raw)

                    entries.append({
                        "pid": pid,
                        "name": name,
                        "threads": threads,
                        "cpu": cpu,
                        "mem": mem,
                        "mem_raw": mem_raw  # для сортировки
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # 🔽 Сортировка по выбранному полю
            if sort_by == 'cpu':
                entries.sort(key=lambda x: x['cpu'], reverse=True)
            elif sort_by == 'memory':
                entries.sort(key=lambda x: x['mem_raw'], reverse=True)
            elif sort_by == 'threads':
                entries.sort(key=lambda x: x['threads'], reverse=True)

            # Печать после сортировки
            for entry in entries:
                print(f"{entry['pid']:<8} {entry['name']:<25} {entry['threads']:<10} {entry['cpu']:<10.1f} {entry['mem']:<15}")

            # Убираем mem_raw перед логированием
            for entry in entries:
                entry.pop('mem_raw', None)

            log_to_txt(entries, timestamp)
            log_to_csv(entries, timestamp)
            log_to_json(entries, timestamp)

            print(f"\nОбновление через {refresh_interval} сек. Нажмите Ctrl+C для выхода.")
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\nМониторинг завершён пользователем.")

def main_menu():
    while True:
        clear_screen()
        print("=== Мониторинг процессов ===")
        print("1. Начать мониторинг")
        print("2. Очистить логи")
        print("3. Выбрать сортировку")
        print("4. Выйти")
        choice = input("Выберите опцию (1–4): ").strip()

        if choice == '1':
            monitor_processes(sort_by=current_sorting)
        elif choice == '2':
            clear_logs()
            input("\nНажмите Enter для возврата в меню...")
        elif choice == '3':
            select_sorting()
        elif choice == '4':
            print("Выход.")
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)

def select_sorting():
    global current_sorting
    print("\nВыберите способ сортировки:")
    print("1. Без сортировки")
    print("2. По CPU")
    print("3. По памяти")
    print("4. По количеству потоков")
    option = input("Выбор (1–4): ").strip()

    if option == '1':
        current_sorting = 'none'
    elif option == '2':
        current_sorting = 'cpu'
    elif option == '3':
        current_sorting = 'memory'
    elif option == '4':
        current_sorting = 'threads'
    else:
        print("Неверный выбор. Сортировка не изменена.")
    time.sleep(1)

# По умолчанию без сортировки
current_sorting = 'none'

if name == "main":
    main_menu()
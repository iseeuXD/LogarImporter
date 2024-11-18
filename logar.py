#iseeu

import pymysql
from tqdm import tqdm
import os
import sys
import pyfiglet
from colorama import Fore, Style, init
import json

init(autoreset=True)

CONFIG_FILE = "db_config.json"


def print_banner():
    ascii_art = pyfiglet.figlet_format("LOGAR IMPORTER")
    print(Fore.CYAN + ascii_art)
    print(Fore.YELLOW + "=" * 50)
    print(Fore.GREEN + "  Veritabanına hızlı ve kolay veri aktarımı")
    print(Fore.YELLOW + "=" * 50 + "\n")


def load_configs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}


def save_configs(configs):
    with open(CONFIG_FILE, "w") as file:
        json.dump(configs, file, indent=4)


def ask_database_info():
    configs = load_configs()
    if configs:
        print(Fore.GREEN + "Kayıtlı veritabanı bilgileri:")
        for i, (name, config) in enumerate(configs.items(), start=1):
            print(Fore.YELLOW + f"{i}. {name} ({config['host']})")
        print(Fore.CYAN + "Yeni veritabanı eklemek için 'n' tuşuna basın.")
        choice = input(Fore.CYAN + "Seçiminiz: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(configs):
            selected_name = list(configs.keys())[int(choice) - 1]
            return configs[selected_name]
        elif choice.lower() == 'n':
            return add_new_database(configs)
    else:
        print(Fore.RED + "Kayıtlı bir veritabanı bulunamadı.")
        return add_new_database(configs)


def add_new_database(configs):
    name = input(Fore.CYAN + "Veritabanı adı: ").strip()
    host = input(Fore.CYAN + "Host: ").strip()
    user = input(Fore.CYAN + "Kullanıcı adı: ").strip()
    password = input(Fore.CYAN + "Şifre: ").strip()
    database = input(Fore.CYAN + "Veritabanı: ").strip()
    configs[name] = {"host": host, "user": user, "password": password, "database": database}
    save_configs(configs)
    return configs[name]


def connect_to_database(config):
    try:
        connection = pymysql.connect(**config)
        cursor = connection.cursor()
        print(Fore.GREEN + "[✓] Veritabanı bağlantısı başarılı.\n")
        return connection, cursor
    except pymysql.MySQLError as e:
        print(Fore.RED + f"[!] Veritabanı bağlantısı hatası: {e}")
        sys.exit()


def get_file_path():
    while True:
        file_path = input(Fore.CYAN + "Dosyanın tam yolunu girin: ").strip()
        if os.path.isfile(file_path):
            print(Fore.GREEN + f"[✓] Dosya bulundu: {file_path}\n")
            return file_path
        else:
            print(Fore.RED + "[!] Geçersiz dosya yolu. \n")


def process_file(file_path, cursor):
    log_file = "error_log.txt"
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            total_lines = sum(1 for _ in file)
        with open(file_path, "r", encoding="utf-8", errors="replace") as file, open(log_file, "w", encoding="utf-8") as log:
            for line in tqdm(file, total=total_lines, desc="Veriler aktarılıyor", unit="satır", colour="green"):
                line = line.strip()
                try:
                    parts = line.split(":")
                    if len(parts) < 3:
                        parts += [""] * (3 - len(parts))
                    link, username, password = parts[:3]
                    if not link or not username or not password:
                        raise ValueError("Eksik bir alan var")
                    insert_query = """
                    INSERT INTO users (link, username, password)
                    VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_query, (link, username, password))
                except ValueError as e:
                    log.write(f"Hatalı satır: {line} | Hata: {e}\n")
                    print(Fore.YELLOW + f"[!] Satır format hatası: {line}")
    except FileNotFoundError:
        print(Fore.RED + f"[!] Dosya bulunamadı: {file_path}")
    except Exception as e:
        print(Fore.RED + f"[!] Bir hata oluştu: {e}")


def main():
    print_banner()
    db_config = ask_database_info()
    connection, cursor = connect_to_database(db_config)
    try:
        file_path = get_file_path()
        process_file(file_path, cursor)
        connection.commit()
        print(Fore.GREEN + "\n[✓] Tüm veriler başarıyla veritabanına aktarıldı.")
    except Exception as e:
        print(Fore.RED + f"[!] Hata: {e}")
    finally:
        cursor.close()
        connection.close()
        print(Fore.BLUE + "\n[✓] Veritabanı bağlantısı kapatıldı.")


if __name__ == "__main__":
    main()

import pydivert
import socket
import psutil
import os
import time
import smtplib
import logging
from ipaddress import ip_address, ip_network
from collections import defaultdict
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import tkinter as tk
from tkinter import filedialog

class ParentControl:        
    def __init__(self, user: str, password: str, check_interval: int) -> None:
        self.user = user
        self.password = password
        self.blocked_sites = set()  # Множество заблокированных сайтов
        self.blocked_applications = set()  # Множество заблокированных приложений
        self.internet_disabled = False  # Флаг для включения и выключения интернета
        self.check_interval = check_interval  # Интервал проверки
        self.sender_email = "alexvolkov082004@gmail.com"
        self.sender_password = "taugsshrahdbzkto"
        self.active_processes = {}  # Для отслеживания активных процессов
        self.log_file_internet = "site_visits.log"
        self.log_file = "activity_log.txt"  # Файл для записи активности пользователя
        self.system_processes = {
            "System Idle Process", "System", "Registry", "smss.exe",
            "csrss.exe", "wininit.exe", "services.exe", "lsass.exe",
            "svchost.exe", "explorer.exe", "SearchUI.exe"
        }
        self.system_ips = {"127.0.0.1", "::1"}  # Локальные системные IP
        self.private_ip_ranges = [
            ("10.0.0.0", "10.255.255.255"),       # 10.0.0.0/8
            ("172.16.0.0", "172.31.255.255"),     # 172.16.0.0/12
            ("192.168.0.0", "192.168.255.255"),   # 192.168.0.0/16
        ]

        # Настройка логирования
        log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        log_file_handler = RotatingFileHandler(
            "parent_control.log", maxBytes=1_000_000, backupCount=3
        )
        log_file_handler.setFormatter(log_formatter)
        log_file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.INFO)

        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[log_file_handler, console_handler]
        )

        logging.info("Инициализация ParentControl.")

    def start_blocking(self) -> None:
        """
        Запускает процесс блокировки указанных сайтов, преобразуя их в IP-адреса.
        """
        try:
            blocked_ips = set()
            for site in self.blocked_sites:
                try:
                    ip = socket.gethostbyname(site)
                    blocked_ips.add(ip)
                    logging.info(f"Сайт {site} преобразован в IP {ip} для блокировки.")
                except socket.gaierror:
                    logging.warning(f"Ошибка: '{site}' не является валидным доменным именем. Пропускаем.")
            if not blocked_ips:
                logging.warning("Нет валидных IP-адресов для блокировки. Завершаем.")
                return

            logging.info(f"Заблокированные IP: {blocked_ips}")
            with pydivert.WinDivert("tcp and outbound") as w:
                logging.info("Начинается блокировка...")
                for packet in w:
                    if packet.dst_addr in blocked_ips:
                        logging.debug(f"Блокируется доступ к IP: {packet.dst_addr}")
                        continue  # Не пропускаем пакет 
                    w.send(packet)  # Пропускаем остальные пакеты
        except Exception as e:
            logging.error(f"Ошибка в процессе блокировки: {e}")

    def add_site(self, site: str) -> None:
        """
        Добавляет домен в список блокировки.
        """
        if site not in self.blocked_sites:
            self.blocked_sites.add(site)
            logging.info(f"Сайт {site} добавлен в список блокировки.")
        else:
            logging.warning(f"Сайт {site} уже находится в списке блокировки.")

    def remove_site(self, site: str) -> None:
        """
        Удаляет домен из списка блокировки.
        """
        if site in self.blocked_sites:
            self.blocked_sites.remove(site)
            logging.info(f"Сайт {site} удалён из списка блокировки.")
        else:
            logging.warning(f"Сайт {site} отсутствует в списке блокировки.")

    def show_blocked_sites(self) -> None:
        """
        Показывает текущий список заблокированных сайтов.
        """
        if not self.blocked_sites:
            logging.info("Список заблокированных сайтов пуст.")
        else:
            logging.info("Заблокированные сайты:")
            for site in self.blocked_sites:
                logging.info(f"- {site}")

    def disable_internet(self) -> None:
        """
        Отключает интернет, блокируя весь сетевой трафик.
        """
        if self.internet_disabled:
            logging.warning("Интернет уже отключён.")
            return

        self.internet_disabled = True
        logging.info("Интернет отключён. Перехватываю все пакеты...")
        try:
            with pydivert.WinDivert("true") as w:  # Перехват всех пакетов
                for packet in w:
                    if not self.internet_disabled:
                        break
        except Exception as e:
            logging.error(f"Ошибка при отключении интернета: {e}")

    def enable_internet(self) -> None:
        """
        Включает интернет, разблокируя сетевой трафик.
        """
        if not self.internet_disabled:
            logging.warning("Интернет уже включён.")
            return

        self.internet_disabled = False
        logging.info("Интернет включён.")
    
    def add_applications(self, application: str) -> None:
        """
        Добавляет приложение в список блокировки.
        """
        if application not in self.blocked_applications:
            self.blocked_applications.add(application)
            logging.info(f"Приложение {application} добавлено в список блокировки.")
        else:
            logging.warning(f"Приложение {application} уже есть в списке блокировки.")

    def select_and_add_application(self) -> None:
        """
        Открывает окно выбора файла и добавляет выбранное приложение в список блокировки.
        """
        try:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Выберите приложение для блокировки",
                filetypes=[("Программы", "*.exe"), ("Все файлы", "*.*")]
            )
            if file_path:
                app_name = os.path.basename(file_path)
                self.blocked_applications.add(app_name)
                logging.info(f"Приложение {app_name} добавлено в список блокировки.")
            else:
                logging.info("Выбор файла отменён пользователем.")
        except Exception as e:
            logging.error(f"Ошибка при добавлении приложения: {e}")

    def remove_applications(self, application: str) -> None:
        """
        Удаляет приложение из списка блокировки.
        """
        if application in self.blocked_applications:
            self.blocked_applications.remove(application)
            logging.info(f"Приложение {application} удалено из списка блокировки.")
        else:
            logging.warning(f"Приложение {application} нет в списке блокировки.")
    
    def show_appplications(self) -> None:
        """
        Показывает список заблокированных приложений.
        """
        if self.blocked_applications:
            logging.info(f"Заблокированные приложения: {', '.join(self.blocked_applications)}")
        else:
            logging.info("Список заблокированных приложений пуст.")
    
    def block_applications(self) -> None:
        """
        Запускает мониторинг процессов и завершает указанные приложения.
        """
        try:
            logging.info("Запуск мониторинга для блокировки приложений.")
            while True:
                for process in psutil.process_iter(['pid', 'name']):
                    try:
                        if process.info['name'] in self.blocked_applications:
                            os.kill(process.info['pid'], 9)
                            logging.info(f"Приложение {process.info['name']} (PID: {process.info['pid']}) завершено.")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logging.info("Мониторинг блокировки приложений завершён.")
        except Exception as e:
            logging.error(f"Ошибка в процессе блокировки приложений: {e}")

    def send_email(self, recipient_email: str, smtp_server: str, smtp_port: int) -> None:
        """
        Отправляет уведомление о начале сеанса на указанную почту.
        """
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = "Уведомление: Начало сеанса"
            body = f"Сеанс пользователя начался в {now}."
            message = MIMEMultipart()
            message['From'] = self.sender_email
            message['To'] = recipient_email
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                logging.info(f"Уведомление успешно отправлено на {recipient_email}.")
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")

    def monitor_activity(self) -> None:
        """
        Запускает мониторинг активности пользователя.
        """
        try:
            logging.info("Начинается мониторинг активности пользователя...")
            while True:
                current_processes = {p.pid: p.info for p in psutil.process_iter(['pid', 'name', 'create_time'])}
                for pid, info in current_processes.items():
                    if pid not in self.active_processes and info['name'] not in self.system_processes:
                        self.active_processes[pid] = info
                        self.log_process_start(info)
                ended_processes = set(self.active_processes.keys()) - set(current_processes.keys())
                for pid in ended_processes:
                    if self.active_processes[pid]['name'] not in self.system_processes:
                        self.log_process_end(self.active_processes[pid])
                    del self.active_processes[pid]
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logging.info("Мониторинг завершён.")
        except Exception as e:
            logging.error(f"Ошибка в процессе мониторинга: {e}")

    def write_to_log(self, log_entry) -> None:
        """
        Записывает лог в файл.
        """
        with open(self.log_file, "a", encoding="utf-8") as log:
            log.write(log_entry)
    
    def monitor_sites_console(self):
        """
        Мониторинг посещений сайтов с логированием уникальных IP-адресов (с записью в файл).
        """
        try:
            logging.info("Начинается мониторинг посещений сайтов...")
            visited_ips = set()
            last_logged_time = {}
            log_interval = timedelta(seconds=10)

            with pydivert.WinDivert("tcp and outbound and (tcp.DstPort == 80 or tcp.DstPort == 443)") as w:
                for packet in w:
                    try:
                        ip_address = packet.dst_addr
                        if ip_address in self.system_ips or self.is_private_ip(ip_address):
                            w.send(packet)
                            continue

                        current_time = datetime.now()
                        if ip_address not in visited_ips or (current_time - last_logged_time.get(ip_address, datetime.min) > log_interval):
                            logging.info(f"Посещение сайта: IP {ip_address}")
                            visited_ips.add(ip_address)
                            last_logged_time[ip_address] = current_time

                    except Exception as log_error:
                        logging.error(f"Ошибка при логировании пакета: {log_error}")
                    w.send(packet)
        except KeyboardInterrupt:
            logging.info("Мониторинг посещений сайтов завершён.")
        except Exception as e:
            logging.error(f"Ошибка в процессе мониторинга: {e}")
    
    def is_private_ip(self, ip: str) -> bool:
        """
        Проверяет, является ли IP адресом из частного диапазона.
        :param ip: строка с IP-адресом.
        :return: True, если IP из частного диапазона, иначе False.
        """
        try:
            ip_obj = ip_address(ip)
            for start, end in self.private_ip_ranges:
                if ip_obj in ip_network(f"{start}/{end}"):
                    logging.info(f"IP {ip} является частным.")
                    return True
            logging.info(f"IP {ip} не является частным.")
            return False
        except ValueError:
            logging.error(f"Некорректный IP-адрес: {ip}")
            return False
    
    def get_visits_in_period(self, days: int) -> None:
        """
        Показывает посещения сайтов за указанный период времени из файла логов.
        :param days: Количество дней для фильтрации.
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            with open(self.log_file, "r", encoding="utf-8") as log:
                lines = log.readlines()

            logging.info(f"Получение посещений сайтов за последние {days} дней.")
            print(f"Посещения сайтов за последние {days} дней:")

            for line in lines:
                try:
                    timestamp = datetime.strptime(line.split("]")[0][1:], "%Y-%m-%d %H:%M:%S")
                    if timestamp >= cutoff:
                        print(line.strip())
                        logging.info(f"Запись из лога: {line.strip()}")
                except ValueError:
                    logging.warning(f"Некорректный формат даты в строке: {line.strip()}")
                    continue
        except FileNotFoundError:
            logging.error("Файл логов не найден. Начните мониторинг, чтобы создать его.")
            print("Файл логов не найден. Начните мониторинг, чтобы создать его.")
    
    def log_process_start(self, info) -> None:
        """
        Логирует запуск нового процесса.
        """
        start_time = datetime.fromtimestamp(info['create_time']).strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{start_time}] Запуск: {info['name']} (PID: {info['pid']})"
        logging.info(log_entry)

    def log_process_end(self, info) -> None:
        """
        Логирует завершение процесса.
        """
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{end_time}] Завершение: {info['name']} (PID: {info['pid']})"
        logging.info(log_entry)

if __name__ == "__main__":
    control = ParentControl(user="admin", password="1234",check_interval = 5)
    control.add_site("habr.com")
    #control.select_and_add_application()
    control.show_appplications()
    control.show_blocked_sites()
    control.select_and_add_application()
    control.block_applications()
    #control.send_email(recent_email='egor.valyukhov@mail.ru',smtp_server='smtp.gmail.com',smtp_port=465)



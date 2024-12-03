import pydivert
import socket
import psutil
import os
import time
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog
###############################################################################################Task######################################################################################
#И это все должно быть в классе
# 1) Написать методы ограничивающие доступ к сайтам(Делаем с помощью библиотеки pydivert,почитать)
        #написать сам метод ограничивающий доступ
        # метод добавления сайта   
        # метод удаления   сайта
        # метод показывающий сайты находящиеся в блокировке 
        #Сделано .Завтра надо проверить функционал и почитать библиотеки Рабает
        
# 2) Написать метод выключающий интернет(Делаем с помощью библиотеки pydivert,почитать)
        #Сделано Работает
# 3) Написать метод дающий опредленное время проведение за компьютером,а потом бы вылазила табличка просящая пароль ,иначе не продолжиать(tkinter,datetime,ctypes,pyautogui,psutil).
# 4) Написать метод отправляющий на почту или Тг сообщение о том что сеанс начался ,либо же об установке каких-то приложений на пк или посещение сайтов(smtplib для почт и надо еще написать telegramm бота чтобы на него приходили уведомления).
# 5) Методы показывающие Историю поиска на ютубе за день/неделю и удаления ее через определенное время(Библиотеки:google-api-python-client, oauth2client)
    #Метод показывающий историю за день
    #Метод показывающий историю за неделю 
    #метод удаления истории через определенноее время
# 6) Написать метод показывающий отчет об использовании приложений за день /неделю  
# 7)Написить Графическое приложение с помщоью tkinter
# 8)Обеспечить логирование с помощью logging
# 9)Сделать exe - файл и логотип на него(сгенерировать с помощью AI)
########################################################################################################################################################################################
class ParentControl:        
    def __init__(self, user: str, password: str, check_interval: int) -> None:
        self.user = user
        self.password = password
        self.blocked_sites = set()  # Множество заблокированных сайтов
        self.blocked_applications = set() # Множество заблокированных приложения
        self.internet_disabled = False # флаг для включения и выключения интернета
        self.check_interval = check_interval

    def start_blocking(self) -> None:
        """
        Запускает процесс блокировки указанных сайтов, преобразуя их в IP-адреса.
        """
        try:
            # Преобразуем домены в IP-адреса
            blocked_ips = set()
            for site in self.blocked_sites:
                try:
                    ip = socket.gethostbyname(site)
                    blocked_ips.add(ip)
                    print(f"Сайт {site} преобразован в IP {ip} для блокировки.")
                except socket.gaierror:
                    print(f"Ошибка: '{site}' не является валидным доменным именем. Пропускаем.")
            if not blocked_ips:
                print("Нет валидных IP-адресов для блокировки. Завершаем.")
                return
            print(f"Заблокированные IP: {blocked_ips}")
            with pydivert.WinDivert("tcp and outbound") as w:
                print("Начинается блокировка...")
                for packet in w:
                    if packet.dst_addr in blocked_ips:
                        print(f"Блокируется доступ к IP: {packet.dst_addr}")
                        continue  # Не пропускаем пакет

                    w.send(packet)  # Пропускаем остальные пакеты
        except Exception as e:
            print(f"Ошибка в процессе блокировки: {e}")

    def add_site(self, site: str) -> None:
        """
        Добавляет домен в список блокировки.
        """
        if site not in self.blocked_sites:
            self.blocked_sites.add(site)
            print(f"Сайт {site} добавлен в список блокировки.")
        else:
            print(f"Сайт {site} уже находится в списке блокировки.")

    def remove_site(self, site: str) -> None:
        """
        Удаляет домен из списка блокировки.
        """
        if site in self.blocked_sites:
            self.blocked_sites.remove(site)
            print(f"Сайт {site} удалён из списка блокировки.")
        else:
            print(f"Сайт {site} отсутствует в списке блокировки.")

    def show_blocked_sites(self) -> None:
        """
        Показывает текущий список заблокированных сайтов.
        """
        if not self.blocked_sites:
            print("Список заблокированных сайтов пуст.")
        else:
            print("Заблокированные сайты:")
            for site in self.blocked_sites:
                print(f"- {site}")

    def disable_internet(self) -> None:
        """
        Отключает интернет, блокируя весь сетевой трафик.
        """
        if self.internet_disabled:
            print("Интернет уже отключён.")
            return

        self.internet_disabled = True
        print("Интернет отключён. Перехватываю все пакеты...")

        try:
            with pydivert.WinDivert("true") as w:  # Перехват всех пакетов
                for packet in w:
                    if not self.internet_disabled:
                        break  # Если интернет включён, прекращаем блокировку
                    # Пакеты просто игнорируются
        except Exception as e:
            print(f"Ошибка при отключении интернета: {e}")

    def enable_internet(self) -> None:
        """
        Включает интернет, разблокируя сетевой трафик.
        """
        if not self.internet_disabled:
            print("Интернет уже включён.")
            return

        self.internet_disabled = False
        print("Интернет включён.")
    
    def add_applications(self,application:str)->None:
        if application not in self.blocked_applications:
            self.blocked_applications.add(application)
            print(f"Приложение {application} добавлено в список блокировки.")
        else:
            print(f"Приложение {application} уже есть в списки блокировки")

    def select_and_add_application(self) -> None:
        """
        Открывает окно выбора файла и добавляет выбранное приложение в список блокировки.
        """
        # Создаём окно, но не отображаем его
        root = tk.Tk()
        root.withdraw()  # Скрываем основное окно

        # Открываем диалог выбора файла
        file_path = filedialog.askopenfilename(
            title="Выберите приложение для блокировки",
            filetypes=[("Программы", "*.exe"), ("Все файлы", "*.*")]
        )

        if file_path:  # Если файл выбран
            app_name = os.path.basename(file_path)  # Получаем имя файла
            self.add_applications(app_name)
        else:
            print("Файл не выбран.")

    def remove_applications(self,application:str)->None:
        if application in self.blocked_applications:
            self.blocked_applications.remove(application)
            print(f"Приложение {application} удалено из списка блокировки")
        else:
            print(f"Приложения {application} нет в списке блокировки")
    
    def show_appplications(self)->None:
        if self.blocked_applications:
            print(f"Список заблокированных приложений:")
            print(f"{self.blocked_applications}")
        else:
            print(f"Заблокированных приложений нет")
    
    def block_applications(self) -> None:
        """
        Запускает мониторинг процессов и завершает указанные приложения.
        """
        print("Начинается мониторинг приложений...")
        while True:
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    if process.info['name'] in self.blocked_applications:
                        print(f"Обнаружено приложение: {process.info['name']} (PID: {process.info['pid']}). Завершение...")
                        os.kill(process.info['pid'], 9)  # Принудительное завершение
                        print(f"Приложение {process.info['name']} завершено.")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue  
            time.sleep(self.check_interval)  


if __name__ == "__main__":
    # Создаём экземпляр класса ParentControl
    control = ParentControl(user="admin", password="1234",check_interval = 5)

    # Добавляем сайты в список блокировки
    control.add_site("habr.com")
    control.select_and_add_application()
    control.show_appplications()

    # Отображаем список заблокированных сайтов
    control.show_blocked_sites()

    # Запускаем блокировку
    control.block_applications()


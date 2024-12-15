import tkinter as tk
from tkinter import Menu, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
from threading import Thread
import psutil
import os
import time
from control import ParentControl


class ParentControlGUI:
    def __init__(self, root, parent_control):
        self.root = root
        self.parent_control = parent_control
        self.root.title("Родительский контроль")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Локальные списки
        self.blocked_applications = set()
        self.opened_windows = {}  # Для отслеживания открытых окон

        # Устанавливаем Canvas для фона
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        # Загружаем изображение и сохраняем оригинал для последующего масштабирования
        try:
            self.original_background_image = Image.open("background.jpg")  # Сохраняем оригинал
            self.bg_image = None
            self.bg_image_id = None
        except FileNotFoundError:
            print("Файл background.jpg не найден. Убедитесь, что изображение находится в правильной папке.")

        # Устанавливаем фон после инициализации интерфейса
        self.root.update_idletasks()
        self.set_initial_background()

        # Обрабатываем изменение размера окна
        self.root.bind("<Configure>", self.resize_background)

        # Добавляем верхнее меню
        self.add_menu()

        # Добавляем основные кнопки
        self.add_main_buttons()

    def set_initial_background(self):
        """
        Устанавливает фон в соответствии с текущими размерами окна после полной инициализации.
        """
        if hasattr(self, "original_background_image"):
            width = 800
            height = 600
            resized_image = self.original_background_image.resize((width, height), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(resized_image)
            self.bg_image_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

    def resize_background(self, event):
        """
        Обновляет фон при изменении размеров окна.
        """
        if hasattr(self, "original_background_image"):
            new_width = event.width
            new_height = event.height
            resized_image = self.original_background_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(resized_image)

            if self.bg_image_id is None:
                self.bg_image_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
            else:
                self.canvas.itemconfig(self.bg_image_id, image=self.bg_image)
            self.canvas.config(width=new_width, height=new_height)

    def add_menu(self):
        """
        Добавляет верхнее меню с функциями блокировки/разблокировки интернета и справкой.
        """
        menu = Menu(self.root)

        # Меню справки
        help_menu = Menu(menu, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_help)
        menu.add_cascade(label="Справка", menu=help_menu)

        # Меню интернета
        internet_menu = Menu(menu, tearoff=0)
        internet_menu.add_command(label="Заблокировать интернет", command=self.disable_internet)
        internet_menu.add_command(label="Разблокировать интернет", command=self.enable_internet)
        menu.add_cascade(label="Интернет", menu=internet_menu)

        self.root.config(menu=menu)

    def add_main_buttons(self):
        """
        Добавляет основные кнопки на главном экране.
        """
        buttons = [
            {"text": "Мониторинг", "command": self.open_monitoring_window, "relx": 0.3, "rely": 0.3},
            {"text": "Приложения", "command": self.open_applications_window, "relx": 0.3, "rely": 0.45},
            {"text": "Сайты", "command": self.open_sites_window, "relx": 0.3, "rely": 0.6},
        ]

        for btn_config in buttons:
            button = tk.Button(
                self.root,
                text=btn_config["text"],
                command=btn_config["command"],
                bg="lightblue",
                font=("Arial", 14, "bold"),
            )
            button.place(relx=btn_config["relx"], rely=btn_config["rely"], relwidth=0.4, relheight=0.1)

    def show_help(self):
        messagebox.showinfo(
            "О программе",
            "Программа Родительский контроль.\n"
            "Функционал:\n"
            "- Блокировка интернета\n"
            "- Мониторинг активности\n"
            "- Управление доступом к приложениям и сайтам\n"
            "Разработчик: Волков Александр Юрьевич 6311-1005033D."
        )

    def disable_internet(self):
        self.run_in_thread(self.parent_control.disable_internet)
        messagebox.showinfo("Интернет", "Интернет заблокирован.")

    def enable_internet(self):
        self.run_in_thread(self.parent_control.enable_internet)
        messagebox.showinfo("Интернет", "Интернет разблокирован.")

    def open_monitoring_window(self):
        if "Мониторинг" not in self.opened_windows:
            self.opened_windows["Мониторинг"] = self.open_themed_window("Мониторинг", [
                {"text": "Запустить мониторинг", "command": self.run_monitoring}
            ])

    def open_applications_window(self):
        if "Приложения" not in self.opened_windows:
            self.opened_windows["Приложения"] = self.open_themed_window("Приложения", [
                {"text": "Добавить приложение", "command": self.add_blocked_application},
                {"text": "Удалить приложение", "command": self.remove_blocked_application},
                {"text": "Показать приложения", "command": self.show_blocked_applications},
                {"text": "Запустить блокировку приложений", "command": self.start_blocking_applications}
            ])

    def open_sites_window(self):
        if "Сайты" not in self.opened_windows:
            self.opened_windows["Сайты"] = self.open_themed_window("Сайты", [
                {"text": "Добавить сайт", "command": self.add_blocked_site},
                {"text": "Удалить сайт", "command": self.remove_blocked_site},
                {"text": "Показать сайты", "command": self.show_blocked_sites},
                {"text": "Запустить блокировку сайтов", "command": self.start_blocking_sites}
            ])

    def open_themed_window(self, title, buttons):
        if title in self.opened_windows:
            return  # Не создаём окно, если оно уже открыто

        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("800x600")
        window.resizable(True, True)

        # Canvas для фона
        canvas = tk.Canvas(window, width=800, height=600)
        canvas.pack(fill="both", expand=True)

        # Установка начального масштаба фона
        self.resize_subwindow_background(None, canvas, window)

        # Добавление кнопок
        for i, btn_config in enumerate(buttons):
            button = tk.Button(
                window,
                text=btn_config["text"],
                command=btn_config["command"],
                bg="lightblue",
                font=("Arial", 12, "bold")
            )
            button.place(relx=0.3, rely=0.2 + i * 0.15, relwidth=0.4, relheight=0.1)

        # Обработчик закрытия окна
        window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(title))

        # Обработчик изменения размера
        window.bind("<Configure>", lambda event: self.resize_subwindow_background(event, canvas, window))

        return window

    def close_window(self, title):
        """
        Закрытие окна и удаление из списка открытых окон.
        """
        if title in self.opened_windows:
            self.opened_windows[title].destroy()
            del self.opened_windows[title]

    def resize_subwindow_background(self, event, canvas, window):
        """
        Масштабирует фон в новых окнах.
        """
        if hasattr(self, "original_background_image"):
            new_width = window.winfo_width()
            new_height = window.winfo_height()

            # Масштабирование изображения под размеры окна
            resized_image = self.original_background_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(resized_image)

            # Установка фонового изображения
            canvas.create_image(0, 0, image=bg_image, anchor="nw")
            canvas.image = bg_image
            canvas.config(width=new_width, height=new_height)

    def run_monitoring(self):
        self.run_in_thread(self.parent_control.monitor_activity)
        messagebox.showinfo("Мониторинг", "Мониторинг процессов запущен.")

    def add_blocked_application(self):
        app_path = filedialog.askopenfilename(
            title="Выберите приложение для блокировки",
            filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
        )
        if app_path:
            app_name = os.path.basename(app_path)
            self.blocked_applications.add(app_name)
            messagebox.showinfo("Приложение добавлено", f"Приложение {app_name} добавлено в список блокировки.")

    def remove_blocked_application(self):
        app = simpledialog.askstring("Удалить приложение", "Введите имя приложения для удаления:")
        if app and app in self.blocked_applications:
            self.blocked_applications.remove(app)
            messagebox.showinfo("Приложение удалено", f"Приложение {app} удалено из списка блокировки.")
        elif app:
            messagebox.showwarning("Ошибка", f"Приложение {app} не найдено в списке блокировки.")

    def show_blocked_applications(self):
        if self.blocked_applications:
            messagebox.showinfo("Заблокированные приложения", "\n".join(self.blocked_applications))
        else:
            messagebox.showinfo("Заблокированные приложения", "Список заблокированных приложений пуст.")

    def start_blocking_applications(self):
        def block_applications():
            while True:
                for process in psutil.process_iter(['pid', 'name']):
                    try:
                        if process.info['name'] in self.blocked_applications:
                            os.kill(process.info['pid'], 9)  # Принудительное завершение
                            print(f"Приложение {process.info['name']} (PID: {process.info['pid']}) завершено.")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                time.sleep(1)

        thread = Thread(target=block_applications, daemon=True)
        thread.start()
        messagebox.showinfo("Блокировка приложений", "Запущен процесс блокировки приложений.")

    def add_blocked_site(self):
        site = simpledialog.askstring("Добавить сайт", "Введите адрес сайта для блокировки:")
        if site:
            self.parent_control.add_site(site)
            messagebox.showinfo("Сайт добавлен", f"Сайт {site} добавлен в список блокировки.")

    def remove_blocked_site(self):
        site = simpledialog.askstring("Удалить сайт", "Введите адрес сайта для удаления:")
        if site:
            self.parent_control.remove_site(site)
            messagebox.showinfo("Сайт удален", f"Сайт {site} удален из списка блокировки.")

    def show_blocked_sites(self):
        sites = self.parent_control.blocked_sites
        if sites:
            messagebox.showinfo("Заблокированные сайты", "\n".join(sites))
        else:
            messagebox.showinfo("Заблокированные сайты", "Список заблокированных сайтов пуст.")

    def start_blocking_sites(self):
        self.run_in_thread(self.parent_control.start_blocking)
        messagebox.showinfo("Блокировка сайтов", "Блокировка сайтов активирована.")

    def run_in_thread(self, target):
        thread = Thread(target=target)
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    parent_control = ParentControl(user="admin", password="1234", check_interval=5)
    app = ParentControlGUI(root, parent_control)
    root.mainloop()

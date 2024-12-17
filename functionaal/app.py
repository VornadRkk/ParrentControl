import tkinter as tk
from tkinter import Menu, messagebox, simpledialog, filedialog, Label, Entry, Button
from PIL import Image, ImageTk
import psutil
import os
import logging
import threading
import time
import pyautogui
from control import ParentControl

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parent_gui.log", mode="a"),
        logging.StreamHandler()
    ]
)

class ParentControlGUI:
    def __init__(self, root, parent_control):
        self.root = root
        self.parent_control = parent_control
        self.root.title("Родительский контроль")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Локальные списки и данные
        self.opened_windows = {}  
        self.child_profiles = {}
        self.current_profile = None
        self.session_timer_id = None
        self.session_remaining_time = 0
        self.session_window = None
        self.cursor_blocking_event = threading.Event()
        self.block_cursor_thread = None

        # Canvas для фона
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        try:
            self.original_background_image = Image.open("background.jpg")
            self.bg_image = None
            self.bg_image_id = None
        except FileNotFoundError:
            print("Файл background.jpg не найден.")

        self.root.update_idletasks()
        self.set_initial_background()
        self.root.bind("<Configure>", self.resize_background)

        # Добавляем меню
        self.add_menu()

        # Кнопки на главном экране
        self.add_main_buttons()

    def set_initial_background(self):
        if hasattr(self, "original_background_image"):
            width = 800
            height = 600
            resized_image = self.original_background_image.resize((width, height), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(resized_image)
            self.bg_image_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

    def resize_background(self, event):
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
        menu = Menu(self.root)

        help_menu = Menu(menu, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_help)
        menu.add_cascade(label="Справка", menu=help_menu)

        internet_menu = Menu(menu, tearoff=0)
        internet_menu.add_command(label="Заблокировать интернет", command=self.disable_internet)
        internet_menu.add_command(label="Разблокировать интернет", command=self.enable_internet)
        menu.add_cascade(label="Интернет", menu=internet_menu)

        self.root.config(menu=menu)

    def add_main_buttons(self):
        add_profile_button = tk.Button(
            self.root,
            text="Добавить профиль",
            command=self.open_add_profile_window,
            bg="lightblue",
            font=("Arial", 14, "bold"),
        )
        add_profile_button.place(relx=0.3, rely=0.3, relwidth=0.4, relheight=0.1)

        select_profile_button = tk.Button(
            self.root,
            text="Выбрать профиль",
            command=self.select_child_profile,
            bg="lightblue",
            font=("Arial", 14, "bold"),
        )
        select_profile_button.place(relx=0.3, rely=0.45, relwidth=0.4, relheight=0.1)

    def show_help(self):
        messagebox.showinfo(
            "О программе",
            "Программа Родительский контроль.\n"
            "Функционал:\n"
            "- Блокировка интернета\n"
            "- Мониторинг активности\n"
            "- Управление доступом к приложениям и сайтам\n"
            "- Управление профилями детей\n"
            "Разработчик: Волков Александр Юрьевич 6311-1005033D."
        )

    def disable_internet(self):
        self.run_in_thread(self.parent_control.disable_internet)
        messagebox.showinfo("Интернет", "Интернет заблокирован.")

    def enable_internet(self):
        self.run_in_thread(self.parent_control.enable_internet)
        messagebox.showinfo("Интернет", "Интернет разблокирован.")

    def open_add_profile_window(self):
        add_profile_window = tk.Toplevel(self.root)
        add_profile_window.title("Добавить профиль")
        add_profile_window.geometry("800x600")
        add_profile_window.resizable(True, True)

        canvas = tk.Canvas(add_profile_window, width=800, height=600)
        canvas.pack(fill="both", expand=True)

        if hasattr(self, "original_background_image"):
            resized_image = self.original_background_image.resize((800, 600), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(resized_image)
            canvas.create_image(0, 0, image=bg_image, anchor="nw")
            canvas.image = bg_image

        frame = tk.Frame(add_profile_window, bg="lightgray", bd=2, relief="flat")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        Label(frame, text="Имя профиля:", font=("Arial", 14, "bold"), bg="lightgray").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        profile_name_entry = Entry(frame, font=("Arial", 12))
        profile_name_entry.grid(row=0, column=1, padx=10, pady=10)

        Label(frame, text="Возраст:", font=("Arial", 14, "bold"), bg="lightgray").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        age_entry = Entry(frame, font=("Arial", 12))
        age_entry.grid(row=1, column=1, padx=10, pady=10)

        Label(frame, text="Пароль:", font=("Arial", 14, "bold"), bg="lightgray").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        password_entry = Entry(frame, font=("Arial", 12), show="*")
        password_entry.grid(row=2, column=1, padx=10, pady=10)

        Label(frame, text="Лимит времени (минуты):", font=("Arial", 14, "bold"), bg="lightgray").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        time_limit_entry = Entry(frame, font=("Arial", 12))
        time_limit_entry.grid(row=3, column=1, padx=10, pady=10)

        save_button = Button(frame, text="Сохранить", font=("Arial", 12), bg="lightgreen", cursor="hand2",
                             command=lambda: self.save_profile(
                                 profile_name_entry.get(),
                                 age_entry.get(),
                                 password_entry.get(),
                                 time_limit_entry.get(),
                                 add_profile_window
                             ))
        save_button.grid(row=4, column=0, columnspan=2, pady=10)

        add_profile_window.bind("<Configure>", lambda event: self.resize_subwindow_background(event, canvas, add_profile_window))

    def save_profile(self, name, age, password, time_limit, window):
        if not name or not age or not password or not time_limit:
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        try:
            age = int(age)
            time_limit = int(time_limit)
        except ValueError:
            messagebox.showerror("Ошибка", "Возраст и лимит времени должны быть числами.")
            return

        if name in self.child_profiles:
            messagebox.showerror("Ошибка", "Профиль с таким именем уже существует.")
            return

        self.child_profiles[name] = {
            "age": age,
            "password": password,
            "blocked_sites": set(),
            "blocked_apps": set(),
            "daily_limit": time_limit,
            "used_time": 0, 
            "activity_logs": []
        }

        messagebox.showinfo("Успех", f"Профиль '{name}' успешно создан.")
        logging.info(f"Профиль '{name}' добавлен.")
        window.destroy()

    def select_child_profile(self):
        if not self.child_profiles:
            messagebox.showwarning("Ошибка", "Нет доступных профилей для выбора.")
            return
        profile_name = simpledialog.askstring("Выбрать профиль", f"Доступные профили:\n{', '.join(self.child_profiles.keys())}")
        if profile_name in self.child_profiles:
            self.current_profile = profile_name
            logging.info(f"Выбран профиль: {profile_name}")
            self.open_profile_main_window(profile_name)
        else:
            if profile_name:
                messagebox.showwarning("Ошибка", "Выбранный профиль не найден.")

    def open_profile_main_window(self, profile_name):
        if "Профиль" in self.opened_windows:
            self.opened_windows["Профиль"].destroy()
            del self.opened_windows["Профиль"]

        profile_window = tk.Toplevel(self.root)
        profile_window.title(f"Профиль: {profile_name}")
        profile_window.geometry("800x600")
        profile_window.resizable(True, True)

        canvas = tk.Canvas(profile_window, width=800, height=600)
        canvas.pack(fill="both", expand=True)

        if hasattr(self, "original_background_image"):
            resized_image = self.original_background_image.resize((800, 600), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(resized_image)
            canvas.create_image(0, 0, image=bg_image, anchor="nw")
            canvas.image = bg_image

        profile_data = self.child_profiles[profile_name]

        # Информация о профиле в правом верхнем углу
        info_frame = tk.Frame(profile_window, bg="lightgray")
        info_frame.place(relx=0.7, rely=0.05, relwidth=0.25, relheight=0.2)
        Label(info_frame, text=f"Профиль: {profile_name}", font=("Arial", 12, "bold"), bg="lightgray").pack(anchor="w", pady=5)
        Label(info_frame, text=f"Возраст: {profile_data['age']} лет", font=("Arial", 12), bg="lightgray").pack(anchor="w", pady=5)
        remaining = profile_data['daily_limit'] - profile_data['used_time']
        self.time_label = Label(info_frame, text=f"Доступное время: {remaining} мин", font=("Arial", 12), bg="lightgray")
        self.time_label.pack(anchor="w", pady=5)

        # Четыре кнопки по центру
        btn_frame = tk.Frame(profile_window, bg="lightblue")
        btn_frame.place(relx=0.3, rely=0.3, relwidth=0.4, relheight=0.4)

        apps_button = tk.Button(btn_frame, text="Приложения", font=("Arial", 14, "bold"), bg="lightblue",
                                command=self.open_applications_window)
        apps_button.pack(pady=5, fill="x")

        monitoring_button = tk.Button(btn_frame, text="Мониторинг", font=("Arial", 14, "bold"), bg="lightblue",
                                    command=self.open_monitoring_window)
        monitoring_button.pack(pady=5, fill="x")

        sites_button = tk.Button(btn_frame, text="Сайты", font=("Arial", 14, "bold"), bg="lightblue",
                                command=self.open_sites_window)
        sites_button.pack(pady=5, fill="x")

        start_session_button = tk.Button(btn_frame, text="Начать сессию", font=("Arial", 14, "bold"), bg="lightgreen",
                                        command=self.start_session)
        start_session_button.pack(pady=5, fill="x")

        profile_window.bind("<Configure>", lambda event: self.resize_subwindow_background(event, canvas, profile_window))
        self.opened_windows["Профиль"] = profile_window

    def start_session(self):
        if not self.current_profile:
            messagebox.showerror("Ошибка", "Сначала выберите профиль.")
            return
        profile_data = self.child_profiles[self.current_profile]
        remaining = profile_data['daily_limit'] - profile_data['used_time']
        if remaining <= 0:
            messagebox.showinfo("Информация", "Лимит времени исчерпан.")
            return
        # Конвертируем оставшееся время в секунды
        self.session_remaining_time = remaining * 60
        messagebox.showinfo("Сеанс начался", "Ваш сеанс начался. Время отсчитывается.")
        self.update_session_time()

    def update_session_time(self):
        if not self.current_profile:
            return
        if self.session_remaining_time > 0:
            self.session_remaining_time -= 1
            # Обновляем использованное время в профиле
            total_used = self.child_profiles[self.current_profile]['used_time'] * 60
            total_limit = self.child_profiles[self.current_profile]['daily_limit'] * 60
            used = total_limit - self.session_remaining_time
            # Пересчитываем used_time в минутах
            self.child_profiles[self.current_profile]['used_time'] = used // 60
            remaining_minutes = self.session_remaining_time // 60

            # Обновим метку с оставшимся временем в окне профиля
            if "Профиль" in self.opened_windows and self.opened_windows["Профиль"]:
                profile_data = self.child_profiles[self.current_profile]
                remain = profile_data['daily_limit'] - profile_data['used_time']
                self.time_label.config(text=f"Доступное время: {remain} мин")

            self.session_timer_id = self.root.after(1000, self.update_session_time)
        else:
            self.end_session()

    def end_session(self):
        # По окончании сессии показываем блокирующее окно
        self.show_blocking_window()

    def show_blocking_window(self):
        block_window = tk.Toplevel(self.root)
        block_window.title("Время истекло")
        block_window.geometry("400x200")
        block_window.attributes("-topmost", True)
        block_window.overrideredirect(1) # Без рамки

        # Центрируем окно
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - 200
        y = (screen_height // 2) - 100
        block_window.geometry(f"+{x}+{y}")

        block_window.grab_set()  # Захватываем фокус, чтобы нельзя было переключиться
        block_window.focus_force()

        Label(block_window, text="Время истекло. Введите пароль для разблокировки:").pack(pady=10)
        password_entry = Entry(block_window, show="*")
        password_entry.pack(pady=5)

        Button(block_window, text="Разблокировать", command=lambda: self.verify_password_input(
            password_entry,
            self.child_profiles[self.current_profile]['password'],
            block_window,
            cursor_block=True,
            success_callback=self.unblock_after_session
        )).pack(pady=10)

        self.start_cursor_blocking(block_window)

    def unblock_after_session(self):
        # Снимаем блокировку курсора
        self.cursor_blocking_event.set()

    def start_cursor_blocking(self, window):
        """
        Блокирует курсор внутри границ окна.
        """
        self.cursor_blocking_event.clear()

        def block_cursor():
            while not self.cursor_blocking_event.is_set():
                # Получаем координаты окна и его размеры
                window.update_idletasks()
                x1 = window.winfo_rootx()
                y1 = window.winfo_rooty()
                x2 = x1 + window.winfo_width()
                y2 = y1 + window.winfo_height()

                # Получаем текущие координаты курсора
                cursor_x, cursor_y = pyautogui.position()

                # Ограничиваем координаты курсора в пределах окна
                new_x = max(x1, min(cursor_x, x2 - 1))
                new_y = max(y1, min(cursor_y, y2 - 1))

                # Перемещаем курсор на новую позицию
                if (cursor_x != new_x) or (cursor_y != new_y):
                    pyautogui.moveTo(new_x, new_y)
                time.sleep(0.05)

        self.block_cursor_thread = threading.Thread(target=block_cursor, daemon=True)
        self.block_cursor_thread.start()

    def remove_current_profile(self):
        if not self.current_profile or self.current_profile not in self.child_profiles:
            messagebox.showerror("Ошибка", "Нет выбранного профиля для удаления.")
            return

        profile_name = self.current_profile
        profile_data = self.child_profiles[profile_name]

        password_window = tk.Toplevel(self.root)
        password_window.title("Введите пароль")
        password_window.geometry("300x150")
        password_window.resizable(False, False)

        Label(password_window, text=f"Введите пароль для профиля '{profile_name}':", font=("Arial", 12)).pack(pady=10)
        password_entry = Entry(password_window, font=("Arial", 12), show="*")
        password_entry.pack(pady=5)

        Button(
            password_window,
            text="Проверить",
            command=lambda: self.verify_password_input(
                password_entry,
                profile_data["password"],
                password_window,
                success_callback=lambda: self.delete_profile(profile_name)
            ),
            font=("Arial", 12),
            bg="lightgreen"
        ).pack(pady=10)

        password_window.transient(self.root)
        password_window.grab_set()
        self.root.wait_window(password_window)

    def delete_profile(self, profile_name):
        del self.child_profiles[profile_name]
        messagebox.showinfo("Успех", f"Профиль '{profile_name}' успешно удалён.")
        logging.info(f"Профиль '{profile_name}' удалён.")
        if self.current_profile == profile_name:
            self.current_profile = None
        if "Профиль" in self.opened_windows:
            self.opened_windows["Профиль"].destroy()
            del self.opened_windows["Профиль"]

    def verify_password_input(self, password_entry, correct_password, window, cursor_block=False, success_callback=None):
        if password_entry.get() == correct_password:
            if cursor_block:
                self.cursor_blocking_event.set()
            window.destroy()
            messagebox.showinfo("Разблокировано", "Пароль введён верно.")
            if success_callback:
                success_callback()
        else:
            messagebox.showerror("Ошибка", "Неверный пароль.")
            password_entry.delete(0, tk.END)

    def run_in_thread(self, target):
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()

    def open_monitoring_window(self):
        if not self.current_profile:
            messagebox.showerror("Ошибка", "Сначала выберите профиль.")
            return
        if "Мониторинг" not in self.opened_windows:
            self.opened_windows["Мониторинг"] = self.open_themed_window("Мониторинг", [
                {"text": "Запустить мониторинг процессов", "command": self.run_monitoring},
                {"text": "Запустить мониторинг сайтов", "command": self.run_site_monitoring}
            ])

    def run_site_monitoring(self):
        self.run_in_thread(self.parent_control.monitor_sites_console)
        messagebox.showinfo("Мониторинг сайтов", "Запущен мониторинг посещения сайтов.")

    def run_monitoring(self):
        self.run_in_thread(self.parent_control.monitor_activity)
        messagebox.showinfo("Мониторинг", "Мониторинг процессов запущен.")

    def open_applications_window(self):
        if not self.current_profile:
            messagebox.showerror("Ошибка", "Сначала выберите профиль.")
            return
        if "Приложения" not in self.opened_windows:
            self.opened_windows["Приложения"] = self.open_themed_window("Приложения", [
                {"text": "Добавить приложение", "command": self.add_blocked_application},
                {"text": "Удалить приложение", "command": self.remove_blocked_application_with_password},
                {"text": "Показать приложения", "command": self.show_blocked_applications},
                {"text": "Запустить блокировку приложений", "command": self.start_blocking_applications}
            ])

    def add_blocked_application(self):
        app_path = filedialog.askopenfilename(
            title="Выберите приложение для блокировки",
            filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
        )
        if app_path:
            app_name = os.path.basename(app_path)
            self.child_profiles[self.current_profile]["blocked_apps"].add(app_name)
            messagebox.showinfo("Приложение добавлено", f"Приложение {app_name} добавлено в список блокировки.")

    def remove_blocked_application_with_password(self):
        if not self.child_profiles[self.current_profile]["blocked_apps"]:
            messagebox.showinfo("Удаление приложения", "Список пуст.")
            return
        app = simpledialog.askstring("Удалить приложение", "Введите имя приложения для удаления:")
        if app and app in self.child_profiles[self.current_profile]["blocked_apps"]:
            self.ask_profile_password(lambda: self.remove_blocked_application(app))
        elif app:
            messagebox.showwarning("Ошибка", f"Приложение {app} не найдено.")

    def remove_blocked_application(self, app):
        self.child_profiles[self.current_profile]["blocked_apps"].remove(app)
        messagebox.showinfo("Приложение удалено", f"Приложение {app} удалено из списка блокировки.")

    def show_blocked_applications(self):
        apps = self.child_profiles[self.current_profile]["blocked_apps"]
        if apps:
            messagebox.showinfo("Заблокированные приложения", "\n".join(apps))
        else:
            messagebox.showinfo("Заблокированные приложения", "Список заблокированных приложений пуст.")

    def start_blocking_applications(self):
        def block_applications():
            while True:
                blocked_apps = self.child_profiles[self.current_profile]["blocked_apps"]
                for process in psutil.process_iter(['pid', 'name']):
                    try:
                        if process.info['name'] in blocked_apps:
                            os.kill(process.info['pid'], 9)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                time.sleep(1)

        thread = threading.Thread(target=block_applications, daemon=True)
        thread.start()
        messagebox.showinfo("Блокировка приложений", "Запущен процесс блокировки приложений.")

    def open_sites_window(self):
        if not self.current_profile:
            messagebox.showerror("Ошибка", "Сначала выберите профиль.")
            return
        if "Сайты" not in self.opened_windows:
            self.opened_windows["Сайты"] = self.open_themed_window("Сайты", [
                {"text": "Добавить сайт", "command": self.add_blocked_site},
                {"text": "Удалить сайт", "command": self.remove_blocked_site_with_password},
                {"text": "Показать сайты", "command": self.show_blocked_sites},
                {"text": "Запустить блокировку сайтов", "command": self.start_blocking_sites}
            ])

    def add_blocked_site(self):
        site = simpledialog.askstring("Добавить сайт", "Введите адрес сайта для блокировки:")
        if site:
            self.child_profiles[self.current_profile]["blocked_sites"].add(site)
            self.parent_control.add_site(site)
            messagebox.showinfo("Сайт добавлен", f"Сайт {site} добавлен в список блокировки.")

    def remove_blocked_site_with_password(self):
        if not self.child_profiles[self.current_profile]["blocked_sites"]:
            messagebox.showinfo("Удаление сайта", "Список пуст.")
            return

        site = simpledialog.askstring("Удалить сайт", "Введите адрес сайта для удаления:")
        if site and site in self.child_profiles[self.current_profile]["blocked_sites"]:
            self.ask_profile_password(lambda: self.remove_blocked_site(site))
        elif site:
            messagebox.showwarning("Ошибка", f"Сайт {site} не найден.")

    def remove_blocked_site(self, site):
        self.child_profiles[self.current_profile]["blocked_sites"].remove(site)
        self.parent_control.remove_site(site)
        messagebox.showinfo("Сайт удалён", f"Сайт {site} удалён из списка блокировки.")

    def show_blocked_sites(self):
        sites = self.child_profiles[self.current_profile]["blocked_sites"]
        if sites:
            messagebox.showinfo("Заблокированные сайты", "\n".join(sites))
        else:
            messagebox.showinfo("Заблокированные сайты", "Список заблокированных сайтов пуст.")

    def start_blocking_sites(self):
        self.run_in_thread(self.parent_control.start_blocking)
        messagebox.showinfo("Блокировка сайтов", "Блокировка сайтов активирована.")

    def ask_profile_password(self, success_callback):
        if not self.current_profile:
            return

        password_window = tk.Toplevel(self.root)
        password_window.title("Введите пароль")
        password_window.geometry("300x150")
        password_window.resizable(False, False)

        Label(password_window, text=f"Введите пароль для профиля '{self.current_profile}':", font=("Arial", 12)).pack(pady=10)
        password_entry = Entry(password_window, font=("Arial", 12), show="*")
        password_entry.pack(pady=5)

        Button(
            password_window,
            text="Проверить",
            command=lambda: self.verify_password_input(
                password_entry,
                self.child_profiles[self.current_profile]["password"],
                password_window,
                success_callback=success_callback
            ),
            font=("Arial", 12),
            bg="lightgreen"
        ).pack(pady=10)

        password_window.transient(self.root)
        password_window.grab_set()
        self.root.wait_window(password_window)

    def open_themed_window(self, title, buttons):
        if title in self.opened_windows:
            return self.opened_windows[title]

        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("800x600")
        window.resizable(True, True)

        canvas = tk.Canvas(window, width=800, height=600)
        canvas.pack(fill="both", expand=True)

        self.resize_subwindow_background(None, canvas, window)

        for i, btn_config in enumerate(buttons):
            button = tk.Button(
                window,
                text=btn_config["text"],
                command=btn_config["command"],
                bg="lightblue",
                font=("Arial", 12, "bold")
            )
            button.place(relx=0.3, rely=0.2 + i * 0.15, relwidth=0.4, relheight=0.1)

        window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(title))
        window.bind("<Configure>", lambda event: self.resize_subwindow_background(event, canvas, window))

        self.opened_windows[title] = window
        return window

    def close_window(self, title):
        if title in self.opened_windows:
            self.opened_windows[title].destroy()
            del self.opened_windows[title]

    def resize_subwindow_background(self, event, canvas, window):
        if hasattr(self, "original_background_image"):
            new_width = window.winfo_width()
            new_height = window.winfo_height()

            resized_image = self.original_background_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(resized_image)

            canvas.create_image(0, 0, image=bg_image, anchor="nw")
            canvas.image = bg_image
            canvas.config(width=new_width, height=new_height)


if __name__ == "__main__":
    root = tk.Tk()
    parent_control = ParentControl(user="admin", password="1234", check_interval=5)
    app = ParentControlGUI(root, parent_control)
    root.mainloop()

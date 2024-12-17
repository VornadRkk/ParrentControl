import tkinter as tk
from tkinter import Menu, messagebox, simpledialog, filedialog, Label, Entry, Button
from PIL import Image, ImageTk
from threading import Thread
import psutil
import os
import logging
import time
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
        self.blocked_applications = set()
        self.opened_windows = {}  # Для отслеживания открытых окон
        self.child_profiles = {}  # Хранилище профилей детей
        self.current_profile = None  # Текущий активный профиль

        # Устанавливаем Canvas для фона
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        # Загружаем изображение и сохраняем оригинал для последующего масштабирования
        try:    
            self.original_background_image = Image.open("background.jpg")
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
        Добавляет верхнее меню с функциями блокировки/разблокировки интернета, справкой и управления профилями.
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

        # Меню профилей детей
        profiles_menu = Menu(menu, tearoff=0)
        profiles_menu.add_command(label="Добавить профиль", command=self.open_add_profile_window)
        profiles_menu.add_command(label="Выбрать профиль", command=self.select_child_profile)
        profiles_menu.add_command(label="Удалить профиль", command=self.remove_child_profile)
        menu.add_cascade(label="Профили", menu=profiles_menu)

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
        """
        Отображает информацию о программе.
        """
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
        """
        Блокирует интернет.
        """
        self.run_in_thread(self.parent_control.disable_internet)
        messagebox.showinfo("Интернет", "Интернет заблокирован.")

    def enable_internet(self):
        """
        Разблокирует интернет.
        """
        self.run_in_thread(self.parent_control.enable_internet)
        messagebox.showinfo("Интернет", "Интернет разблокирован.")

    # Профили детей
    def open_add_profile_window(self):
        """
        Открывает новое окно для добавления профиля ребёнка.
        """
        add_profile_window = tk.Toplevel(self.root)
        add_profile_window.title("Добавить профиль")
        add_profile_window.geometry("800x600")
        add_profile_window.resizable(True, True)

        # Canvas для фона
        canvas = tk.Canvas(add_profile_window, width=800, height=600)
        canvas.pack(fill="both", expand=True)

        # Масштабирование и установка фона
        if hasattr(self, "original_background_image"):
            resized_image = self.original_background_image.resize((800, 600), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(resized_image)
            canvas.create_image(0, 0, image=bg_image, anchor="nw")
            canvas.image = bg_image

        # Контейнер для элементов ввода
        frame = tk.Frame(add_profile_window, bg="lightgray", bd=2, relief="flat")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Используем grid для точного размещения
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

        # Кнопка сохранения
        save_button = Button(frame, text="Сохранить", font=("Arial", 12), bg="lightgreen", cursor="hand2",
                             command=lambda: self.save_profile(
                                 profile_name_entry.get(),
                                 age_entry.get(),
                                 password_entry.get(),
                                 time_limit_entry.get(),
                                 add_profile_window
                             ))
        save_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Привязка события на изменение размера окна для фона
        add_profile_window.bind("<Configure>", lambda event: self.resize_subwindow_background(event, canvas, add_profile_window))


    def save_profile(self, name, age, password, time_limit, window):
        """
        Сохраняет профиль ребёнка после заполнения формы.
        """
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
            "allowed_sites": set(),
            "blocked_apps": set(),
            "allowed_apps": set(),
            "daily_limit": time_limit,
            "used_time": 0,
            "activity_logs": []
        }

        messagebox.showinfo("Успех", f"Профиль '{name}' успешно создан.")
        logging.info(f"Профиль '{name}' добавлен.")
        window.destroy()


    def remove_child_profile(self):
        """
        Удаляет профиль ребёнка только после проверки пароля.
        """
        if not self.child_profiles:
            messagebox.showwarning("Ошибка", "Нет доступных профилей для удаления.")
            return

        # Запрашиваем имя профиля для удаления
        profile_name = simpledialog.askstring(
            "Удалить профиль",
            f"Доступные профили:\n{', '.join(self.child_profiles.keys())}"
        )

        if profile_name in self.child_profiles:
            self.show_password_window_for_removal(profile_name)
        elif profile_name:
            messagebox.showwarning("Ошибка", "Выбранный профиль не найден.")


    def show_password_window_for_removal(self, profile_name):
        """
        Открывает окно для ввода пароля и вызывает универсальный метод для проверки.
        """
        try:
            password_window = tk.Toplevel(self.root)
            password_window.title("Введите пароль")
            password_window.geometry("300x150")
            password_window.resizable(False, False)

            # Метка с инструкцией
            Label(password_window, text=f"Введите пароль для профиля '{profile_name}':", font=("Arial", 12)).pack(pady=10)

            # Поле для ввода пароля
            password_entry = Entry(password_window, font=("Arial", 12), show="*")
            password_entry.pack(pady=5)

            # Кнопка для проверки пароля
            Button(
                password_window,
                text="Проверить",
                command=lambda: self.verify_password_input(
                    password_entry,
                    self.child_profiles[profile_name]["password"],
                    password_window,
                    lambda: self.delete_profile(profile_name)  # Удаление профиля при успехе
                ),
                font=("Arial", 12),
                bg="lightgreen"
            ).pack(pady=10)

            # Блокируем основное окно до завершения работы с окном пароля
            password_window.transient(self.root)
            password_window.grab_set()
            self.root.wait_window(password_window)
        except Exception as e:
            logging.error(f"Ошибка в show_password_window_for_removal: {e}")
            messagebox.showerror("Ошибка", "Не удалось отобразить окно для ввода пароля.")


    def delete_profile(self, profile_name):
        """
        Удаляет профиль ребёнка.
        """
        del self.child_profiles[profile_name]
        messagebox.showinfo("Успех", f"Профиль '{profile_name}' успешно удалён.")
        logging.info(f"Профиль '{profile_name}' удалён.")

    def verify_password_input(self, password_entry, correct_password, lock_window=None, success_callback=None):
        """
        Универсальный метод для проверки пароля.

        :param password_entry: Поле ввода пароля (Entry).
        :param correct_password: Правильный пароль для проверки.
        :param lock_window: Окно, которое нужно закрыть при успешной проверке (опционально).
        :param success_callback: Функция, вызываемая при успешной проверке пароля.
        """
        entered_password = password_entry.get()
        if entered_password == correct_password:
            messagebox.showinfo("Разблокировано", "Пароль введён верно.")
            if lock_window:
                lock_window.destroy()  # Закрытие окна блокировки
            if success_callback:
                success_callback()  # Вызов функции при успехе
        else:
            messagebox.showerror("Ошибка", "Неверный пароль. Попробуйте снова.")
            password_entry.delete(0, tk.END)  # Очистка поля ввода

    def show_time_exceeded_screen(self):
        """
        Отображает окно на весь экран, которое нельзя закрыть без ввода правильного пароля.
        """
        if not self.current_profile:
            return

        profile_password = self.child_profiles[self.current_profile]["password"]

        # Создаем окно, которое блокирует весь экран
        lock_window = tk.Toplevel(self.root)
        lock_window.title("Время истекло!")
        lock_window.attributes('-fullscreen', True)
        lock_window.configure(bg="black")

        # Текст на экране
        Label(lock_window, text="Время использования устройства истекло!",
            font=("Arial", 30, "bold"), fg="red", bg="black").pack(pady=100)

        Label(lock_window, text="Введите пароль для разблокировки:",
            font=("Arial", 20), fg="white", bg="black").pack(pady=20)

        # Поле для ввода пароля
        password_entry = Entry(lock_window, font=("Arial", 18), show="*", width=20, justify="center")
        password_entry.pack(pady=20)

        # Кнопка для проверки пароля
        Button(
            lock_window,
            text="Разблокировать",
            font=("Arial", 16),
            bg="green",
            fg="white",
            cursor="hand2",
            command=lambda: self.verify_password_input(
                password_entry,
                profile_password,
                lock_window
            )
        ).pack(pady=20)

        # Отключаем возможность закрыть окно стандартными средствами
        lock_window.protocol("WM_DELETE_WINDOW", lambda: None)
        lock_window.grab_set()
        lock_window.focus_set()
        self.root.wait_window(lock_window)

        
    def select_child_profile(self):
        """
        Позволяет выбрать текущий активный профиль.
        """
        if not self.child_profiles:
            messagebox.showwarning("Ошибка", "Нет доступных профилей для выбора.")
            return
        profile_name = simpledialog.askstring("Выбрать профиль", f"Доступные профили:\n{', '.join(self.child_profiles.keys())}")
        if profile_name in self.child_profiles:
            self.current_profile = profile_name
            messagebox.showinfo("Профиль выбран", f"Текущий профиль: {profile_name}")
            logging.info(f"Выбран профиль: {profile_name}")
        else:
            messagebox.showwarning("Ошибка", "Выбранный профиль не найден.")



    def run_in_thread(self, target):
        """
        Запускает функцию в отдельном потоке.
        """
        thread = Thread(target=target)
        thread.daemon = True
        thread.start()

    def open_monitoring_window(self):
        """
        Открывает окно мониторинга.
        """
        if "Мониторинг" not in self.opened_windows:
            self.opened_windows["Мониторинг"] = self.open_themed_window("Мониторинг", [
                {"text": "Запустить мониторинг процессов", "command": self.run_monitoring},
                {"text": "Запустить мониторинг сайтов", "command": self.run_site_monitoring}
            ])
    
    def run_site_monitoring(self):
        """
        Запуск мониторинга посещения сайтов.
        """
        self.run_in_thread(self.parent_control.monitor_sites_console)
        messagebox.showinfo("Мониторинг сайтов", "Запущен мониторинг посещения сайтов.")

    def open_applications_window(self):
        """
        Открывает окно управления приложениями.
        """
        if "Приложения" not in self.opened_windows:
            self.opened_windows["Приложения"] = self.open_themed_window("Приложения", [
                {"text": "Добавить приложение", "command": self.add_blocked_application},
                {"text": "Удалить приложение", "command": self.remove_blocked_application},
                {"text": "Показать приложения", "command": self.show_blocked_applications},
                {"text": "Запустить блокировку приложений", "command": self.start_blocking_applications}
            ])

    def open_sites_window(self):
        """
        Открывает окно управления сайтами.
        """
        if "Сайты" not in self.opened_windows:
            self.opened_windows["Сайты"] = self.open_themed_window("Сайты", [
                {"text": "Добавить сайт", "command": self.add_blocked_site},
                {"text": "Удалить сайт", "command": self.remove_blocked_site},
                {"text": "Показать сайты", "command": self.show_blocked_sites},
                {"text": "Запустить блокировку сайтов", "command": self.start_blocking_sites}
            ])

    def open_themed_window(self, title, buttons):
        """
        Создаёт новое окно с темой и кнопками.
        """
        if title in self.opened_windows:
            return  # Окно уже открыто

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
        """
        Запуск мониторинга процессов.
        """
        self.run_in_thread(self.parent_control.monitor_activity)
        messagebox.showinfo("Мониторинг", "Мониторинг процессов запущен.")

    def add_blocked_application(self):
        """
        Добавление приложения для блокировки.
        """
        app_path = filedialog.askopenfilename(
            title="Выберите приложение для блокировки",
            filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
        )
        if app_path:
            app_name = os.path.basename(app_path)
            self.blocked_applications.add(app_name)
            messagebox.showinfo("Приложение добавлено", f"Приложение {app_name} добавлено в список блокировки.")

    def remove_blocked_application(self):
        """
        Удаление приложения из списка блокировки.
        """
        app = simpledialog.askstring("Удалить приложение", "Введите имя приложения для удаления:")
        if app and app in self.blocked_applications:
            self.blocked_applications.remove(app)
            messagebox.showinfo("Приложение удалено", f"Приложение {app} удалено из списка блокировки.")
        elif app:
            messagebox.showwarning("Ошибка", f"Приложение {app} не найдено в списке блокировки.")

    def show_blocked_applications(self):
        """
        Показ списка заблокированных приложений.
        """
        if self.blocked_applications:
            messagebox.showinfo("Заблокированные приложения", "\n".join(self.blocked_applications))
        else:
            messagebox.showinfo("Заблокированные приложения", "Список заблокированных приложений пуст.")

    def start_blocking_applications(self):
        """
        Запуск процесса блокировки приложений.
        """
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
        """
        Добавление сайта в список блокировки.
        """
        site = simpledialog.askstring("Добавить сайт", "Введите адрес сайта для блокировки:")
        if site:
            self.parent_control.add_site(site)
            messagebox.showinfo("Сайт добавлен", f"Сайт {site} добавлен в список блокировки.")

    def remove_blocked_site(self):
        """
        Удаление сайта из списка блокировки.
        """
        site = simpledialog.askstring("Удалить сайт", "Введите адрес сайта для удаления:")
        if site:
            self.parent_control.remove_site(site)
            messagebox.showinfo("Сайт удалён", f"Сайт {site} удалён из списка блокировки.")

    def show_blocked_sites(self):
        """
        Показ списка заблокированных сайтов.
        """
        sites = self.parent_control.blocked_sites
        if sites:
            messagebox.showinfo("Заблокированные сайты", "\n".join(sites))
        else:
            messagebox.showinfo("Заблокированные сайты", "Список заблокированных сайтов пуст.")

    def start_blocking_sites(self):
        """
        Запуск процесса блокировки сайтов.
        """
        self.run_in_thread(self.parent_control.start_blocking)
        messagebox.showinfo("Блокировка сайтов", "Блокировка сайтов активирована.")
        
if __name__ == "__main__":
    root = tk.Tk()
    parent_control = ParentControl(user="admin", password="1234", check_interval=5)
    app = ParentControlGUI(root, parent_control)
    root.mainloop()

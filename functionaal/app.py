import tkinter as tk
from tkinter import Menu, messagebox, simpledialog, filedialog, Label, Entry, Button,Listbox, Scrollbar
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
        self.blocked_applications = set()
        self.opened_windows = {}  # Для отслеживания открытых окон
        self.child_profiles = {}  # Хранилище профилей детей
        self.current_profile = None  # Текущий активный профиль
        self.session_timer_id = None  # ID таймера для сессии
        self.session_remaining_time = 0
        self.session_window = None
        self.cursor_blocking_event = threading.Event()
        self.block_cursor_thread = None
        self.session_block_window = None
        

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
            "daily_limit": time_limit, # минуты
            "used_time": 0, # минуты уже использованные
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

            # Блокируем основное окно до завершения
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
            password_entry.delete(0, tk.END)

    def select_child_profile(self):
        """
        Позволяет выбрать текущий активный профиль и открывает окно с информацией о профиле.
        """
        if not self.child_profiles:
            messagebox.showwarning("Ошибка", "Нет доступных профилей для выбора.")
            return
        profile_name = simpledialog.askstring("Выбрать профиль", f"Доступные профили:\n{', '.join(self.child_profiles.keys())}")
        if profile_name in self.child_profiles:
            self.current_profile = profile_name
            logging.info(f"Выбран профиль: {profile_name}")
            self.open_profile_session_window(profile_name)
        else:
            if profile_name:
                messagebox.showwarning("Ошибка", "Выбранный профиль не найден.")

    def open_profile_session_window(self, profile_name):
        """
        Открывает окно профиля для начала сессии.
        """
        if self.session_window and tk.Toplevel.winfo_exists(self.session_window):
            self.session_window.destroy()

        profile_data = self.child_profiles[profile_name]
        remaining_time = profile_data["daily_limit"] - profile_data["used_time"]

        self.session_window = tk.Toplevel(self.root)
        self.session_window.title(f"Профиль: {profile_name}")
        self.session_window.geometry("800x600")
        self.session_window.resizable(True, True)

        # Canvas для фона
        canvas = tk.Canvas(self.session_window, width=800, height=600)
        canvas.pack(fill="both", expand=True)

        if hasattr(self, "original_background_image"):
            resized_image = self.original_background_image.resize((800, 600), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(resized_image)
            canvas.create_image(0, 0, image=bg_image, anchor="nw")
            canvas.image = bg_image

        # Фрейм для информации
        frame = tk.Frame(self.session_window, bg="lightgray", bd=2, relief="flat")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        Label(frame, text=f"Имя: {profile_name}", font=("Arial", 14, "bold"), bg="lightgray").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        Label(frame, text=f"Возраст: {profile_data['age']}", font=("Arial", 14, "bold"), bg="lightgray").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        Label(frame, text=f"Оставшееся время: {remaining_time} минут(ы)", font=("Arial", 14, "bold"), bg="lightgray").grid(row=2, column=0, padx=10, pady=10, sticky="w")

        start_button = Button(frame, text="Начать сессию", font=("Arial", 12), bg="lightgreen", cursor="hand2",
                              command=self.start_session)
        start_button.grid(row=3, column=0, pady=20)

        self.session_window.bind("<Configure>", lambda event: self.resize_subwindow_background(event, canvas, self.session_window))

    def start_session(self):
        """
        Запускает сессию для текущего профиля.
        """
        if not self.current_profile:
            messagebox.showerror("Ошибка", "Сначала выберите профиль.")
            return

        profile_data = self.child_profiles[self.current_profile]
        remaining_time = profile_data["daily_limit"] - profile_data["used_time"]

        if remaining_time <= 0:
            messagebox.showinfo("Информация", "Время для данного профиля уже исчерпано.")
            return

        # Запускаем отсчёт времени в секундах
        self.session_remaining_time = remaining_time * 60  # переводим в секунды
        self.update_session_time()

    def update_session_time(self):
        """
        Обновляет время сессии каждую секунду.
        """
        if self.session_remaining_time > 0:
            self.session_remaining_time -= 1
            # Каждую минуту обновляем used_time или только в конце?
            # Обновим used_time в конце для упрощения.
            # Можно вывести текущее оставшееся время на окно сессии:
            if self.session_window and tk.Toplevel.winfo_exists(self.session_window):
                # Найдём метку "Оставшееся время" и обновим её
                for widget in self.session_window.winfo_children():
                    # Ищем frame и label внутри
                    if isinstance(widget, tk.Frame):
                        for lbl in widget.winfo_children():
                            if isinstance(lbl, Label) and "Оставшееся время:" in lbl.cget("text"):
                                mins_left = self.session_remaining_time // 60
                                lbl.config(text=f"Оставшееся время: {mins_left} минут(ы)")
                                break
            self.session_timer_id = self.root.after(1000, self.update_session_time)
        else:
            # Время вышло
            self.end_session()

    def end_session(self):
        """
        Вызывается, когда время сессии истекает.
        Показывает блокирующее окно с вводом пароля.
        """
        if self.current_profile and self.current_profile in self.child_profiles:
            # Обновим used_time, так как вся сессия закончена
            profile_data = self.child_profiles[self.current_profile]
            profile_data["used_time"] = profile_data["daily_limit"]  # Время исчерпано

        # Откроем окно для ввода пароля, которое блокирует всё остальное
        self.show_block_window_for_time_up()

    def show_block_window_for_time_up(self):
        """
        Отображает блокирующее окно, которое фиксирует курсор и требует ввода пароля.
        """
        if self.session_block_window and tk.Toplevel.winfo_exists(self.session_block_window):
            self.session_block_window.destroy()

        self.session_block_window = tk.Toplevel(self.root)
        self.session_block_window.title("Время истекло")
        self.session_block_window.geometry("400x200")
        self.session_block_window.resizable(False, False)

        x = (self.root.winfo_screenwidth() - 400) // 2
        y = (self.root.winfo_screenheight() - 200) // 2
        self.session_block_window.geometry(f"+{x}+{y}")
        self.session_block_window.attributes("-topmost", True)
        self.session_block_window.protocol("WM_DELETE_WINDOW", lambda: None)

        tk.Label(self.session_block_window, text="Время истекло.\nВведите пароль для разблокировки:",
                font=("Arial", 12)).pack(pady=20)

        password_entry = tk.Entry(self.session_block_window, font=("Arial", 12), show="*")
        password_entry.pack(pady=10)

        tk.Button(
            self.session_block_window,
            text="Проверить",
            command=lambda: self.verify_password_input_cursor(
                password_entry,
                self.child_profiles[self.current_profile]["password"],
                self.session_block_window,
                self.unblock_after_time
            ),
            font=("Arial", 12),
            bg="lightgreen"
        ).pack(pady=10)

        self.session_block_window.focus_force()
        self.session_block_window.grab_set()
        self.start_cursor_blocking(x, y, 400, 200)

        logging.info("Блокирующее окно создано и курсор зафиксирован.")

    def start_cursor_blocking(self, window_x, window_y, width, height):
        """
        Фиксирует курсор в пределах заданного окна с использованием pyautogui.
        """
        self.cursor_blocking_event.clear()  # Сбрасываем флаг остановки

        def block_cursor():
            logging.debug("Начало блокировки курсора.")
            while not self.cursor_blocking_event.is_set():  # Проверка флага остановки
                try:
                    # Рассчитываем границы окна
                    left = window_x
                    top = window_y
                    right = window_x + width
                    bottom = window_y + height

                    # Получаем текущие координаты мыши
                    x, y = pyautogui.position()

                    # Ограничиваем движение курсора
                    if x < left:
                        pyautogui.moveTo(left, y)
                    elif x > right:
                        pyautogui.moveTo(right, y)
                    if y < top:
                        pyautogui.moveTo(x, top)
                    elif y > bottom:
                        pyautogui.moveTo(x, bottom)

                    time.sleep(0.1)  # Добавляем задержку, чтобы снизить нагрузку на CPU
                except Exception as e:  
                    logging.error(f"Ошибка в блокировке курсора: {e}")
                    break
            logging.debug("Завершение блокировки курсора.")

        # Запускаем блокировку в отдельном потоке
        self.block_cursor_thread = threading.Thread(target=block_cursor, daemon=True)
        self.block_cursor_thread.start()

    def verify_password_input_cursor(self, password_entry, correct_password, lock_window=None, success_callback=None):
        """
        Проверка введенного пароля и снятие блокировки при правильном пароле.
        """
        entered_password = password_entry.get()
        if entered_password == correct_password:
            logging.info("Пароль введён верно. Завершаем блокировку курсора и закрываем окно.")
            self.cursor_blocking_event.set()  # Устанавливаем флаг для остановки потока блокировки

            # Ждем завершения потока с таймаутом
            if self.block_cursor_thread and self.block_cursor_thread.is_alive():
                self.block_cursor_thread.join(timeout=1)
            
            # Снятие захвата и закрытие окна
            if lock_window and lock_window.winfo_exists():
                lock_window.grab_release()
                lock_window.destroy()

            # Выполнение callback
            if success_callback:
                success_callback()
        else:
            messagebox.showerror("Ошибка", "Неверный пароль. Попробуйте снова.")
            password_entry.delete(0, tk.END)

    def unblock_after_time(self):
        """
        Действия после ввода правильного пароля в блокирующем окне.
        Можно сделать так, чтобы сессия "закончилась", но при вводе пароля пользователь может продолжить работать.
        """
        messagebox.showinfo("Разблокировано", "Сеанс завершён. Вы можете продолжить работу в программе.")
        # По логике, время исчерпано, но родитель может разблокировать для каких-то дополнительных действий.
        # Здесь можно оставить всё как есть - время закончилось, но доступ к интерфейсу вернулся.

    def run_in_thread(self, target):
        """
        Запускает функцию в отдельном потоке.
        """
        thread = threading.Thread(target=target)
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

        thread = threading.Thread(target=block_applications, daemon=True)
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

import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
from threading import Thread
from control import ParentControl  # Убедитесь, что этот модуль существует

class ParentControlGUI:
    def __init__(self, root, parent_control):
        self.root = root
        self.parent_control = parent_control
        self.root.title("Родительский контроль")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Устанавливаем Canvas для фона
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        # Загружаем изображение и сохраняем оригинал для последующего масштабирования
        try:
            self.original_background_image = Image.open("background.jpg")  # Сохраняем оригинал
            self.background_image = self.original_background_image.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(self.background_image)
            self.bg_image_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        except FileNotFoundError:
            print("Файл background.jpg не найден. Убедитесь, что изображение находится в правильной папке.")

        # Обрабатываем изменение размера окна
        self.root.bind("<Configure>", self.resize_background)

        # Добавляем кнопки
        self.add_buttons()

    def add_buttons(self):
        # Размеры кнопок
        button_width = 20
        button_height = 2

        # Создаем кнопки и размещаем их
        self.add_button("Заблокировать интернет", self.disable_internet, 0.1, 0.1, button_width, button_height)
        self.add_button("Разблокировать интернет", self.enable_internet, 0.1, 0.2, button_width, button_height)
        self.add_button("Добавить сайт", self.add_blocked_site, 0.1, 0.3, button_width, button_height)
        self.add_button("Удалить сайт", self.remove_blocked_site, 0.1, 0.4, button_width, button_height)
        self.add_button("Показать сайты", self.show_blocked_sites, 0.1, 0.5, button_width, button_height)
        self.add_button("Добавить приложение", self.add_blocked_application, 0.5, 0.1, button_width, button_height)
        self.add_button("Удалить приложение", self.remove_blocked_application, 0.5, 0.2, button_width, button_height)
        self.add_button("Показать приложения", self.show_blocked_applications, 0.5, 0.3, button_width, button_height)
        self.add_button("Запустить мониторинг", self.run_monitoring, 0.5, 0.4, button_width, button_height)
        self.add_button("Блокировать сайты", self.start_blocking_sites, 0.1, 0.6, button_width, button_height)
        self.add_button("Блокировать приложения", self.start_blocking_applications, 0.5, 0.5, button_width, button_height)

    def resize_background(self, event):
        """
        Обновляет фон при изменении размеров окна.
        """
        if hasattr(self, "original_background_image"):
            # Получаем текущие размеры окна
            new_width = event.width
            new_height = event.height

            # Меняем размер исходного изображения в соответствии с текущими размерами окна
            resized_image = self.original_background_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(resized_image)

            # Обновляем фон на Canvas
            self.canvas.itemconfig(self.bg_image_id, image=self.bg_image)
            self.canvas.config(width=new_width, height=new_height)

    def add_button(self, text, command, relx, rely, width, height):
        # Функция для создания кнопок
        button = tk.Button(
            self.canvas,
            text=text,
            command=command,
            width=width,
            height=height,
            bg="lightblue",
            font=("Arial", 10, "bold")
        )
        self.canvas.create_window(relx * 800, rely * 600, window=button)
    
    # Методы для кнопок
    def disable_internet(self):
        self.run_in_thread(self.parent_control.disable_internet)
        messagebox.showinfo("Интернет", "Интернет заблокирован.")

    def enable_internet(self):
        self.run_in_thread(self.parent_control.enable_internet)
        messagebox.showinfo("Интернет", "Интернет разблокирован.")

    def add_blocked_site(self):
        site = simpledialog.askstring("Добавить сайт", "Введите адрес сайта для блокировки:")
        if site:
            self.run_in_thread(lambda: self.parent_control.add_site(site))
            messagebox.showinfo("Сайт добавлен", f"Сайт {site} добавлен в список блокировки.")

    def remove_blocked_site(self):
        site = simpledialog.askstring("Удалить сайт", "Введите адрес сайта для удаления:")
        if site:
            self.run_in_thread(lambda: self.parent_control.remove_site(site))
            messagebox.showinfo("Сайт удален", f"Сайт {site} удален из списка блокировки.")

    def show_blocked_sites(self):
        sites = self.parent_control.blocked_sites
        if sites:
            messagebox.showinfo("Заблокированные сайты", "\n".join(sites))
        else:
            messagebox.showinfo("Заблокированные сайты", "Список заблокированных сайтов пуст.")

    def add_blocked_application(self):
        app = simpledialog.askstring("Добавить приложение", "Введите имя приложения для блокировки (например, notepad.exe):")
        if app:
            self.run_in_thread(lambda: self.parent_control.add_applications(app))
            messagebox.showinfo("Приложение добавлено", f"Приложение {app} добавлено в список блокировки.")

    def remove_blocked_application(self):
        app = simpledialog.askstring("Удалить приложение", "Введите имя приложения для удаления:")
        if app:
            self.run_in_thread(lambda: self.parent_control.remove_applications(app))
            messagebox.showinfo("Приложение удалено", f"Приложение {app} удалено из списка блокировки.")

    def show_blocked_applications(self):
        apps = self.parent_control.blocked_applications
        if apps:
            messagebox.showinfo("Заблокированные приложения", "\n".join(apps))
        else:
            messagebox.showinfo("Заблокированные приложения", "Список заблокированных приложений пуст.")

    def start_blocking_sites(self):
        self.run_in_thread(self.parent_control.start_blocking)
        messagebox.showinfo("Блокировка сайтов", "Блокировка сайтов активирована.")

    def start_blocking_applications(self):
        self.run_in_thread(self.parent_control.block_applications)
        messagebox.showinfo("Блокировка приложений", "Блокировка приложений активирована.")

    def run_monitoring(self):
        self.run_in_thread(self.parent_control.monitor_activity)
        messagebox.showinfo("Мониторинг", "Мониторинг процессов запущен.")

    def run_in_thread(self, target):
        # Запуск функции в отдельном потоке
        thread = Thread(target=target)
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    parent_control = ParentControl(user="admin", password="1234", check_interval=5)  # Убедитесь, что класс ParentControl реализован
    app = ParentControlGUI(root, parent_control)
    root.mainloop()
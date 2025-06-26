import tkinter as tk
from tkinter import ttk, messagebox
import random
import string
import pyperclip
from zxcvbn import zxcvbn

class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор безопасных паролей")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        self.setup_ui()
    
    def setup_ui(self):
        style = ttk.Style()
        style.configure("TFrame", background="f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 14, "bold"))
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header_frame, 
            text="Генератор безопасных паролей", 
            style="Header.TLabel"
        ).pack()
        
        params_frame = ttk.LabelFrame(main_frame, text="Параметры генерации")
        params_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(params_frame, text="Длина пароля:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.length_var = tk.IntVar(value=12)
        length_spin = ttk.Spinbox(params_frame, from_=8, to=32, textvariable=self.length_var, width=5)
        length_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.use_digits_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            params_frame, 
            text="Использовать цифры (0-9)", 
            variable=self.use_digits_var
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        self.use_special_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            params_frame, 
            text="Использовать спецсимволы (!@$%^&*)", 
            variable=self.use_special_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        self.use_uppercase_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            params_frame, 
            text="Использовать заглавные буквы (A-Z)", 
            variable=self.use_uppercase_var
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Сгенерировать пароль", 
            command=self.generate_password
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Копировать в буфер", 
            command=self.copy_to_clipboard
        ).pack(side=tk.LEFT, padx=5)
        
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(
            main_frame, 
            textvariable=self.password_var, 
            font=("Arial", 12), 
            state="readonly"
        )
        password_entry.pack(fill=tk.X, pady=5)
        
        strength_frame = ttk.LabelFrame(main_frame, text="Анализ стойкости пароля")
        strength_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.strength_var = tk.StringVar(value="—")
        ttk.Label(strength_frame, text="Сложность:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(strength_frame, textvariable=self.strength_var, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.crack_time_var = tk.StringVar(value="—")
        ttk.Label(strength_frame, text="Время подбора:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(strength_frame, textvariable=self.crack_time_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.warnings_var = tk.StringVar(value="—")
        ttk.Label(strength_frame, text="Предупреждения:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(strength_frame, textvariable=self.warnings_var, wraplength=400).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.suggestions_var = tk.StringVar(value="—")
        ttk.Label(strength_frame, text="Рекомендации:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(strength_frame, textvariable=self.suggestions_var, wraplength=400).grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
    
    def generate_password(self):
        length = self.length_var.get()
        use_digits = self.use_digits_var.get()
        use_special = self.use_special_var.get()
        use_uppercase = self.use_uppercase_var.get()
        
        characters = string.ascii_lowercase
        if use_digits:
            characters += string.digits
        if use_special:
            characters += "!@$%^&*"
        if use_uppercase:
            characters += string.ascii_uppercase
        
        if not characters:
            messagebox.showerror("Ошибка", "Не выбрано ни одного набора символов для генерации пароля")
            return
        
        password = ''.join(random.choice(characters) for _ in range(length))
        self.password_var.set(password)
        self.analyze_password(password)
    
    def analyze_password(self, password):
        if not password:
            self.strength_var.set("—")
            self.crack_time_var.set("—")
            self.warnings_var.set("—")
            self.suggestions_var.set("—")
            return
        
        result = zxcvbn(password)
        
        strength_score = result['score']
        strength_text = {
            0: "Очень слабый",
            1: "Слабый",
            2: "Удовлетворительный",
            3: "Хороший",
            4: "Отличный"
        }.get(strength_score, "Неизвестно")
        
        self.strength_var.set(f"{strength_text} ({strength_score}/4)")
        
        crack_time = result['crack_times_display']['offline_slow_hashing_1e4_per_second']
        self.crack_time_var.set(crack_time)
        
        warnings = result['feedback']['warning'] if result['feedback']['warning'] else "Нет предупреждений"
        self.warnings_var.set(warnings)
        
        suggestions = "\n".join(result['feedback']['suggestions']) if result['feedback']['suggestions'] else "Нет рекомендаций"
        self.suggestions_var.set(suggestions)
    
    def copy_to_clipboard(self):
        password = self.password_var.get()
        if password:
            pyperclip.copy(password)
            messagebox.showinfo("Успех", "Пароль скопирован в буфер обмена")
        else:
            messagebox.showwarning("Предупреждение", "Нет пароля для копирования")

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()

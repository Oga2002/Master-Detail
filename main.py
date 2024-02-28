import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Master-Detail Tables")

        # БД
        self.conn = sqlite3.connect("documents.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS documents (
                                id INTEGER PRIMARY KEY,
                                number TEXT,
                                date TEXT,
                                amount REAL,
                                note TEXT)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS positions (
                                id INTEGER PRIMARY KEY,
                                document_id INTEGER,
                                number TEXT,
                                name TEXT,
                                amount REAL,
                                FOREIGN KEY(document_id) REFERENCES documents(id))""")
        self.conn.commit()

        # Интерфейс
        self.documents_tree = ttk.Treeview(self, columns=("Number", "Date", "Amount", "Note"))
        self.documents_tree.column("#0", width=0, stretch=tk.NO)  # Скрыть столбец ID
        self.documents_tree.heading("Number", text="Номер")
        self.documents_tree.heading("Date", text="Дата")
        self.documents_tree.heading("Amount", text="Сумма")
        self.documents_tree.heading("Note", text="Примечание")

        self.positions_tree = ttk.Treeview(self, columns=("Number", "Name", "Total"))
        self.positions_tree.column("#0", width=0, stretch=tk.NO)  # Скрыть столбец ID
        self.positions_tree.heading("Number", text="Номер")
        self.positions_tree.heading("Name", text="Наименование")
        self.positions_tree.heading("Total", text="Сумма")

        self.documents_tree.pack(expand=True, fill="both", side="top")
        self.positions_tree.pack(expand=True, fill="both", side="bottom")

        self.load_documents()
        self.documents_tree.bind("<<TreeviewSelect>>", self.on_document_select)

        # Кнопки
        self.add_document_button = tk.Button(self, text="Добавить документ", command=self.add_document)
        self.add_document_button.pack(side="left")

        self.edit_document_button = tk.Button(self, text="Редактировать документ", command=self.edit_document)
        self.edit_document_button.pack(side="left")

        self.add_position_button = tk.Button(self, text="Добавить позицию", command=self.add_position)
        self.add_position_button.pack(side="right")

        self.edit_position_button = tk.Button(self, text="Редактировать позицию", command=self.edit_position)
        self.edit_position_button.pack(side="right")

        self.remove_position_button = tk.Button(self, text="Удалить позицию", command=self.remove_position)
        self.remove_position_button.pack(side="right")

        self.remove_document_button = tk.Button(self, text="Удалить документ", command=self.remove_document)
        self.remove_document_button.pack(side="left")

    def load_documents(self):
        self.documents_tree.delete(*self.documents_tree.get_children())
        self.cursor.execute(
            "SELECT documents.id, documents.number, documents.date, SUM(positions.amount), documents.note FROM documents LEFT JOIN positions ON documents.id = positions.document_id GROUP BY documents.id")
        for row in self.cursor.fetchall():
            self.documents_tree.insert("", "end", text=row[0], values=(row[1], row[2], row[3], row[4]))

    def load_positions(self, document_id):
        self.positions_tree.delete(*self.positions_tree.get_children())
        self.cursor.execute("SELECT id, number, name, amount FROM positions WHERE document_id=?", (document_id,))
        for row in self.cursor.fetchall():
            self.positions_tree.insert("", "end", text=row[0], values=(row[1], row[2], row[3]))

    def on_document_select(self, event):
        selection = self.documents_tree.selection()
        if selection:
            document_id = self.documents_tree.item(selection[0])["text"]
            self.load_positions(document_id)

    def add_document(self):
        add_window = tk.Toplevel(self)
        add_window.title("Добавить документ")

        # Поля ввода
        labels = ["Номер", "Дата", "Примечание"]
        entries = []
        for i, label in enumerate(labels):
            tk.Label(add_window, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(add_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries.append(entry)

        def save_document():
            number = entries[0].get()
            date = entries[1].get()
            note = entries[2].get()

            self.cursor.execute("INSERT INTO documents (number, date,note) VALUES (?, ?, ?)", (number, date, note))
            self.conn.commit()
            self.load_documents()
            add_window.destroy()

        save_button = tk.Button(add_window, text="Сохранить", command=save_document)
        save_button.grid(row=len(labels), columnspan=2, padx=5, pady=10)

        add_window.grab_set()
        add_window.focus_set()
        add_window.wait_window()

    def add_position(self):
        selection = self.documents_tree.selection()
        if not selection:
            tk.messagebox.showerror("Ошибка", "Выберите документ")
            return

        document_id = self.documents_tree.item(selection[0])["text"]

        add_window = tk.Toplevel(self)
        add_window.title("Добавить позицию")

        # Поля ввода
        labels = ["Номер", "Наименование", "Сумма"]
        entries = []
        for i, label in enumerate(labels):
            tk.Label(add_window, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(add_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries.append(entry)

        def save_position():
            number = entries[0].get()
            name = entries[1].get()
            amount_str = entries[2].get()

            # Пустая ли строка amount_str
            if amount_str:
                amount = float(amount_str)
            else:
                amount = None

            self.cursor.execute("INSERT INTO positions (document_id, number, name, amount) VALUES (?, ?, ?, ?)",
                                (document_id, number, name, amount))
            self.conn.commit()
            self.load_positions(document_id)
            self.load_documents()  # Обновляем сумму
            add_window.destroy()

        save_button = tk.Button(add_window, text="Сохранить", command=save_position)
        save_button.grid(row=len(labels), columnspan=2, padx=5, pady=10)

        add_window.grab_set()
        add_window.focus_set()
        add_window.wait_window()

    def edit_document(self):
        selection = self.documents_tree.selection()
        if not selection:
            tk.messagebox.showerror("Ошибка", "Выберите документ")
            return

        document_id = self.documents_tree.item(selection[0])["text"]
        document_data = self.cursor.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()

        edit_window = tk.Toplevel(self)
        edit_window.title("Редактировать документ")

        labels = ["Номер", "Дата", "Примечание"]
        entries = []
        for i, label in enumerate(labels):
            tk.Label(edit_window, text=label + ":").grid(row=i, column=0, padx=5, pady=5)

            # Пропуск редактирования суммы
            if i == 3:
                continue

            entry = tk.Entry(edit_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry.insert(tk.END, document_data[i])
            entries.append(entry)

        def save_document():
            number = entries[0].get()
            date = entries[1].get()
            note = entries[2].get()

            self.cursor.execute("UPDATE documents SET number=?, date=?, note=? WHERE id=?",
                                (number, date, note, document_id))
            self.conn.commit()
            self.load_documents()
            edit_window.destroy()

        save_button = tk.Button(edit_window, text="Сохранить", command=save_document)
        save_button.grid(row=len(labels), columnspan=2, padx=5, pady=10)

        edit_window.grab_set()
        edit_window.focus_set()
        edit_window.wait_window()

    def edit_position(self):
        selection = self.positions_tree.selection()
        if not selection:
            tk.messagebox.showerror("Ошибка", "Выберите позицию")
            return

        position_id = self.positions_tree.item(selection[0])["text"]
        position_data = self.cursor.execute("SELECT * FROM positions WHERE id=?", (position_id,)).fetchone()

        edit_window = tk.Toplevel(self)
        edit_window.title("Редактировать позицию")

        labels = ["Номер", "Наименование", "Сумма"]
        entries = []
        for i, label in enumerate(labels):
            tk.Label(edit_window, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(edit_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry.insert(0, position_data[i + 2])  # i + 2, чтобы пропустить id и document_id
            entries.append(entry)

        def save_position():
            number = entries[0].get()
            name = entries[1].get()
            amount_str = entries[2].get()

            # Проверка на пустую строку
            if amount_str:
                amount = float(amount_str)
            else:
                amount = None

            self.cursor.execute("UPDATE positions SET number=?, name=?, amount=? WHERE id=?",
                                (number, name, amount, position_id))
            self.conn.commit()
            self.load_positions(position_data[1])  # Перезагружаем позиции
            self.load_documents()  # Обновляем сумму
            edit_window.destroy()

        save_button = tk.Button(edit_window, text="Сохранить", command=save_position)
        save_button.grid(row=len(labels), columnspan=2, padx=5, pady=10)

        edit_window.grab_set()
        edit_window.focus_set()
        edit_window.wait_window()

    def remove_position(self):
        selection = self.positions_tree.selection()
        if not selection:
            tk.messagebox.showerror("Ошибка", "Выберите позицию")
            return

        position_id = self.positions_tree.item(selection[0])["text"]
        self.cursor.execute("DELETE FROM positions WHERE id=?", (position_id,))
        self.conn.commit()

        # Обновляем таблицу позиций после удаления
        document_id = self.documents_tree.selection()[0]
        self.load_positions(document_id)
        self.load_documents()  # Обновляем сумму

    def remove_document(self):
        selection = self.documents_tree.selection()
        if not selection:
            tk.messagebox.showerror("Ошибка", "Выберите документ")
            return

        document_id = self.documents_tree.item(selection[0])["text"]
        self.cursor.execute("DELETE FROM positions WHERE document_id=?", (document_id,))
        self.cursor.execute("DELETE FROM documents WHERE id=?", (document_id,))
        self.conn.commit()
        self.load_documents()

    def __del__(self):
        self.conn.close()


if __name__ == "__main__":
    app = App()
    app.mainloop()

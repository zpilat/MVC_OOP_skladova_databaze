import sqlite3
import tkinter as tk
from tkinter import ttk, font

# Třída Model se stará o práci s databází.
class Model:
    # Inicializace modelu s připojením k databázi.
    def __init__(self, db):
        self.conn = sqlite3.connect(db)  # Připojení k databázi
        self.cursor = self.conn.cursor()  # Vytvoření kurzoru pro operace s databází

    # Metoda pro načtení názvů sloupců z dané tabulky.
    def fetch_col_names(self, table):
        query = f"SELECT * FROM {table} LIMIT 0"
        self.cursor.execute(query)
        col_names = tuple(descrip[0] for descrip in self.cursor.description)  # Získání názvů sloupců
        return col_names

    # Metoda pro načtení dat z dané tabulky.
    def fetch_data(self, table):
        query = f"SELECT * FROM {table}"
        self.cursor.execute(query)
        return self.cursor.fetchall()  # Vrátí všechna data z tabulky

    # Destruktor pro uzavření databázového připojení.
    def __del__(self):
        self.conn.close()


# Třída View se stará o zobrazení uživatelského rozhraní.
class View:
    # Inicializace GUI s nastavením hlavního okna.
    def __init__(self, root, controller):
        self.root = root
        self.root.title('Zobrazení databáze')  # Nastaví titulek okna
        self.controller = controller
        self.current_tree_view = None  # Tady uchováváme aktuální TreeView

        # Inicializace GUI
        self.initialize_frame()
        self.initialize_menu()

    # Inicializace různých Frame
    def initialize_frame(self):

        # Vytvoření Frame pro vyhledávání a filtrovací check buttony
        self.search_frame = tk.Frame(self.root)
        self.search_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
    
        # Vytvoření Frame jako kontejneru pro Treeview a Scrollbar
        self.tree_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vytvoření Frame jako kontejneru pro zobrazení skladové karty
        self.item_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.item_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        
        # Frame pro název evidenčním číslem a názvem položky
        self.title_frame = tk.Frame(self.item_frame, bg="yellow", borderwidth=2, relief="groove")
        self.title_frame.pack(side=tk.TOP,fill=tk.X, padx=2, pady=2)   
        # Frame pro zobrazení položky
        self.show_frame = tk.Frame(self.item_frame, borderwidth=2, relief="groove")
        self.show_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # Nadpis zobrazené položky - jenom pro zkoušku zobrazení
        title_label = tk.Label(self.title_frame, bg="yellow", text="ZOBRAZENÍ SKLADOVÉ KARTY")
        title_label.pack(padx=2, pady=2)


    # Inicializace menu
    def initialize_menu(self):
        # Vytvoření menu a jeho nastavení jako hlavního menu aplikace
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Přidání "Zobrazení" menu
        show_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Zobrazení", menu=show_menu)
        # Přidání položek menu
        show_menu.add_command(label="Uživatelé", command=lambda: self.controller.show_data('uzivatele'))
        show_menu.add_command(label="Psi", command=lambda: self.controller.show_data('psi'))

   
    # Metoda pro zobrazení dat v GUI.
    def show_data(self, tree_view_type, data):
         # Přepne na požadovaný TreeView
        self.switch_tree_view(tree_view_type)

        # Přidá data
        self.current_tree_view.add_data(data)

    def switch_tree_view(self, tree_view_type):
        # Odstranění aktuálního TreeView, pokud existuje
        if self.current_tree_view is not None:
            self.current_tree_view.frame.destroy()

        # Vytvoření nového TreeView podle zadaného typu
        if tree_view_type == "uzivatele":
            self.current_tree_view = UzivateleTreeView(self.tree_frame)
        elif tree_view_type == "psi":
            self.current_tree_view = PsiTreeView(self.tree_frame)
        # Přidat další podmínky pro další typy TreeView

# Základní třída na zobrazení treeview
class BaseTreeView:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(self.frame, show='headings', height=30)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")

    def setup_columns(self, col_names, col_widths=None):
        self.tree['columns'] = col_names
        for idx, col in enumerate(col_names):
            width = 100 if col_widths is None else col_widths[idx]
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=50, anchor='center')

    def add_data(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in data:
            self.tree.insert('', tk.END, values=row)


# Třídy na specializované zobrazení dle zobrazované tabulky
class UzivateleTreeView(BaseTreeView):
    def __init__(self, parent):
        super().__init__(parent)
        col_names = ["ID", "Jméno", "Bydliště", "Datum narození"]
        col_widths = [50, 100, 150, 100]  # Příklad specifických šířek sloupců
        self.setup_columns(col_names, col_widths)

class PsiTreeView(BaseTreeView):
    def __init__(self, parent):
        super().__init__(parent)
        col_names = ["ID", "Jméno", "Věk", "Majitel"]
        # Zde neuvádíme col_widths, použijí se výchozí šířky
        self.setup_columns(col_names)




# Třída Controller koordinuje Model a View.
class Controller:    
    # Inicializace controlleru s připojením k databázi a inicializací GUI.
    def __init__(self, root, db_path):
        self.root = root
        self.db_path = db_path
        self.model = Model(self.db_path)  # Instance modelu pro práci s databází
        self.view = View(self.root, self)  # Instance view pro zobrazení GUI a předání self do view


    # Metoda pro zobrazení dat z tabulky v GUI.
    def show_data(self, table):
        data = self.model.fetch_data(table)  # Načtení dat z modelu
        self.view.show_data(table, data)  # Zobrazení dat ve view
        



# Hlavní část programu pro spuštění aplikace
if __name__ == "__main__":
    root = tk.Tk()  # Vytvoření hlavního okna aplikace
    db_path = 'zkouska.db'  # Cesta k databázi
    table = 'uzivatele'  # Název první tabulky pro zobrazení při startu
    controller = Controller(root, db_path)  # Inicializace controlleru
    controller.show_data(table)  # Zobrazení dat z tabulky

    root.mainloop()  # Spuštění hlavní smyčky Tkinter GUI


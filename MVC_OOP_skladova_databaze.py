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
        col_names = tuple(descrip[0] for descrip in self.cursor.description)  
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
        self.current_tree_view = None  # Tady je uchováván aktuální TreeView        
        
        self.initialize_menu(self.root)
        self.initialize_frame(self.root)


        # Definice slovníku na přiřazení lidských názvů sloupců tabulky podle slovníku
        self.tab2hum = {'Ucetnictvi': 'Účetnictví', 'Kriticky_dil': 'Kritický díl', 'Evidencni_cislo': 'Evid. č.',
                        'Interne_cislo': 'Č. karty', 'Min_Mnozstvi_ks': 'Minimum', 'Objednano': 'Objednáno?',
                        'Nazev_dilu': 'Název dílu', 'Mnozstvi_ks_m_l': 'Akt. množství', 'Jednotky':'Jedn.',
                        'HSH': 'HSH', 'TQ8': 'TQ8', 'TQF_XL_I': 'TQF XL I', 'TQF_XL_II': 'TQF XL II',
                        'DC_XL': 'DC XL', 'DAC_XLI_a_II': 'DAC XLI a II', 'DL_XL': 'DL XL', 'DAC': 'DAC',
                        'LAC_I': 'LAC I', 'LAC_II': 'LAC II', 'IPSEN_ENE': 'IPSEN ENE', 'HSH_ENE': 'HSH ENE',
                        'XL_ENE1': 'XL ENE1', 'XL_ENE2': 'XL ENE2', 'IPSEN_W': 'IPSEN W', 'HSH_W': 'HSH W',
                        'KW': 'KW', 'KW1': 'KW1', 'KW2': 'KW2', 'KW3': 'KW3', 'Umisteni': 'Umístění',
                        'Dodavatel': 'Posl. dodavatel', 'Datum_nakupu': 'Datum nákupu',
                        'Cislo_objednavky': 'Objednávka', 'Jednotkova_cena_EUR': 'Cena EUR/ks',
                        'Celkova_cena_EUR': 'Celkem EUR', 'Poznamka': 'Poznámka', 'Zmena_mnozstvi': 'Změna množství',
                        'Cas_operace': 'Čas operace', 'Operaci_provedl': 'Operaci provedl',
                        'Typ_operace': 'Typ operace', 'Datum_vydeje': 'Datum výdeje',
                        'Pouzite_zarizeni': 'Použité zařízení'}

    # Inicializace Treeview a scrollbaru
    def initialize_treeview(self):   
        self.tree = ttk.Treeview(self.tree_frame, show='headings', height=30)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")


    # Inicializace menu
    def initialize_menu(self, root):
        # Vytvoření menu a jeho nastavení jako hlavního menu aplikace
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        # Přidání "Zobrazení" menu
        show_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Zobrazení", menu=show_menu)
        # Přidání položek menu
        show_menu.add_command(label="Sklad", command=lambda: self.controller.show_data('sklad'))
        show_menu.add_command(label="AuditLog", command=lambda: self.controller.show_data('audit_log'))


    # Inicializace různých Frame
    def initialize_frame(self, root):

        # Hlavní Frame obsahující všechny ostatní frame
        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)     

        # Vytvoření Frame pro vyhledávání a filtrovací check buttony
        self.search_frame = tk.Frame(self.frame)
        self.search_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
    
        # Vytvoření Frame jako kontejneru pro Treeview a Scrollbar
        self.tree_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
             
        # Vytvoření Frame jako kontejneru pro zobrazení skladové karty
        self.item_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.item_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        

    # Metoda na vytvoření sloupců Treeview
    def setup_columns(self, col_widths=None):
        self.tree['columns'] = self.hum_col_names
        for idx, col in enumerate(self.hum_col_names):
            width = 100 if col_widths is None else col_widths[idx]
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')


    # Metoda na vložení dat do Treeview
    def add_data(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in data:
            self.tree.insert('', tk.END, values=row)

    # Metoda pro zobrazení dat v GUI.
    def show_data(self, tree_view_type, data, col_names):
         # Přepne na požadovaný TreeView
        self.switch_tree_view(tree_view_type, col_names)
        # Přidá data
        self.current_tree_view.add_data(data)
        

    # Metoda na smazání staré a vytvoření nové instance Treeview dle vybrané tabulky databáze
    def switch_tree_view(self, tree_view_type, col_names):
        # Odstranění aktuálního TreeView, pokud existujen
        if self.current_tree_view is not None:
            self.current_tree_view.frame.destroy()
        # Vytvoření nového TreeView podle zadaného typu
        if tree_view_type == "sklad":
            self.current_tree_view = SkladView(self.root, self.controller, col_names)
        elif tree_view_type == "audit_log":
            self.current_tree_view = AuditLogView(self.root, self.controller, col_names)          
        # Přidat další podmínky pro další typy TreeView             



# Třídy na specializované zobrazení dle zobrazované tabulky
class SkladView(View):
    def __init__(self, root, controller, col_names):
        super().__init__(root, controller)
        self.col_names = col_names
        # Vytvoření lidských názvů sloupců vybrané tabulky
        self.hum_col_names = tuple(self.tab2hum[col] for col in self.col_names)
        # Inicializace Treeview a scrollbaru
        self.initialize_treeview()        

        
        # Definice sloupců, které mají být skryté
        self.hidden_columns = ('Ucetnictvi', 'Kriticky_dil', 'Objednano', 'HSH', 'TQ8', 'TQF_XL_I', 'TQF_XL_II',
                               'DC_XL', 'DAC_XLI_a_II',
                               'DL_XL', 'DAC', 'LAC_I', 'LAC_II', 'IPSEN_ENE', 'HSH_ENE', 'XL_ENE1',
                               'XL_ENE2', 'IPSEN_W', 'HSH_W', 'KW', 'KW1', 'KW2', 'KW3')

        # Definice sloupců, které mají zaškrtávací políčko (check button)
        self.check_columns = ('Ucetnictvi', 'Kriticky_dil', 'HSH', 'TQ8', 'TQF_XL_I', 'TQF_XL_II',
                              'DC_XL', 'DAC_XLI_a_II', 'DL_XL', 'DAC', 'LAC_I', 'LAC_II', 'IPSEN_ENE',
                              'HSH_ENE', 'XL_ENE1', 'XL_ENE2', 'IPSEN_W', 'HSH_W', 'KW', 'KW1', 'KW2', 'KW3')

       # Definice širokých sloupců
        self.wide_columns = ('Nazev_dilu')

        # Definice středně širokých sloupců
        self.med_columns = ('Dodavatel', 'Poznamka')

        # Definice širokých sloupců
        self.narrow_columns = ('Jednotky', 'Evidencni_cislo', 'Interne_cislo')

        # Definice a nastavení stavů filtrovacích check buttonů na False
        self.filter_columns = {col: tk.BooleanVar(value=False) for col in self.check_columns}


        # Vytvoření specifického menu a frame v `self.item_frame` z BaseTreeView
        self.initialize_specific_menu()
        self.initialize_specific_frame()

        # Vytvoření specifických parametrů zobrazení sloupců
        col_widths, col_params = self.col_parameters()
        self.setup_columns(col_widths)

    def col_parameters(self):
        col_widths = []
        col_params = []
        # Nastavení šířky sloupců a zarovnání textu, včetně skrytí vybraných sloupců
        for index, col in enumerate(self.col_names):         
            if col in self.wide_columns:                
                col_widths.append(400)
                col_params.append("w")
            elif col in self.narrow_columns:
                col_widths.append(25)
                col_params.append("center")
            elif col in self.med_columns:
                col_widths.append(150)
                col_params.append("w")                
            elif col in self.hidden_columns:
                col_widths.append(0)
                col_params.append("w") 
            else:
                col_widths.append(70)
                col_params.append("center")

        return col_widths, col_params
    

    def initialize_specific_menu(self):
        # Vytvoření specifického menu pro "Uživatele"
        users_menu = tk.Menu(self.menu_bar, tearoff=0)
        users_menu.add_command(label="Přidat položku", command=self.add_item)
        # Přidání dalších specifických položek
        self.menu_bar.add_cascade(label="Skladové položky", menu=users_menu)
        

    def initialize_specific_frame(self):
        # Frame pro název evidenčním číslem a názvem položky - zatím jenom pro zkoušku zobrazení
        self.title_frame = tk.Frame(self.item_frame, bg="yellow", borderwidth=2, relief="groove")
        self.title_frame.pack(side=tk.TOP,fill=tk.X, padx=2, pady=2)   
        # Frame pro zobrazení položky - zatím jenom pro zkoušku zobrazení
        self.show_frame = tk.Frame(self.item_frame, borderwidth=2, relief="groove")
        self.show_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # Nadpis zobrazené položky - zatím jenom pro zkoušku zobrazení
        title_label = tk.Label(self.title_frame, bg="yellow", text="ZOBRAZENÍ SKLADOVÉ KARTY")
        title_label.pack(padx=2, pady=2)

    def add_item(self):
        # Implementace
        pass

class AuditLogView(View):
    def __init__(self, root, controller, col_names):
        super().__init__(root, controller)
        self.col_names = col_names
        # Vytvoření lidských názvů sloupců vybrané tabulky
        self.hum_col_names = tuple(self.tab2hum[col] for col in self.col_names)
        # Inicializace Treeview a scrollbaru
        self.initialize_treeview() 

        # Vytvoření specifických parametrů zobrazení sloupců
        # Zde neuvádíme col_widths, použijí se výchozí šířky
        self.setup_columns()




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
        col_names = self.model.fetch_col_names(table)
        self.view.show_data(table, data, col_names)  # Zobrazení dat ve view
        



# Hlavní část programu pro spuštění aplikace
if __name__ == "__main__":
    root = tk.Tk()  # Vytvoření hlavního okna aplikace
    db_path = 'skladova_databaze.db'  # Cesta k databázi
    table = 'sklad'  # Název první tabulky pro zobrazení při startu
    controller = Controller(root, db_path)  # Inicializace controlleru
    controller.show_data(table)  # Zobrazení dat z tabulky

    root.mainloop()  # Spuštění hlavní smyčky Tkinter GUI


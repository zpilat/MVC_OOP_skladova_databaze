import sqlite3
import tkinter as tk
from tkinter import ttk, font

class Model:
    """
    Třída Model se stará o práci s databází.
    """
    def __init__(self, db):
        """
        Inicializace modelu s připojením k databázi.
        
        :param db: Cesta k databázovému souboru.
        """
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

    def fetch_col_names(self, table):
        """
        Načte názvy sloupců z dané tabulky.
        
        :param table: Název tabulky pro načtení názvů sloupců.
        :return: N-tice názvů sloupců.
        """
        query = f"SELECT * FROM {table} LIMIT 0"
        self.cursor.execute(query)
        return tuple(description[0] for description in self.cursor.description)

    def fetch_data(self, table):
        """
        Načte data z dané tabulky.
        
        :param table: Název tabulky pro načtení dat.
        :return: Všechna data z tabulky jako seznam n-tic.
        """
        query = f"SELECT * FROM {table}"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def __del__(self):
        """
        Destruktor pro uzavření databázového připojení při zániku instance.
        """
        self.conn.close()

class View:
    """
    Třída View se stará o zobrazení uživatelského rozhraní.
    """
    def __init__(self, root, controller):
        """
        Inicializace GUI a nastavení hlavního okna.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        """
        self.root = root
        self.root.title('Zobrazení databáze')
        self.controller = controller
        self.current_tree_view = None  # Aktuální TreeView pro zobrazení dat

        self.initialize_menu(self.root)
        self.initialize_frame(self.root)

        self.hidden_columns= {}
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
        
    def initialize_treeview(self, tree_frame):
        """
        Inicializace TreeView a přidruženého scrollbaru.

        :param tree_frame: Frame pro zobrazení Treeview.
        """
        self.tree = ttk.Treeview(tree_frame, show='headings', height=30)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")

    def initialize_menu(self, root):
        """
        Inicializace menu aplikace.
        
        :param root: Hlavní okno aplikace pro konfiguraci menu.
        """
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        show_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Zobrazení", menu=show_menu)

        show_menu.add_command(label="Sklad", command=lambda: self.controller.show_data('sklad'))
        show_menu.add_command(label="AuditLog", command=lambda: self.controller.show_data('audit_log'))

    def initialize_frame(self, root):
        """
        Inicializace různých frame pro uživatelské rozhraní.
        
        :param root: Hlavní okno aplikace pro umístění frame.
        """
        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)     

        self.search_frame = tk.Frame(self.frame)
        self.search_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
    
        self.tree_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
             
        self.item_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.item_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

    def setup_columns(self, col_params):
        """
        Nastavení sloupců pro TreeView.
        
        :col_params Seznam slovníků parametrů sloupců (width, minwidth, anchor, stretch...).
        """
        self.tree['columns'] = self.col_names
        for idx, col in enumerate(self.col_names):            
            self.tree.heading(col, text=self.tab2hum[col])
            self.tree.column(col, **col_params[idx])

    def add_data(self, data):
        """
        Vložení dat do TreeView.
        
        :param data: Data pro zobrazení ve formátu seznamu n-tic.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in data:
            self.tree.insert('', tk.END, values=row)

    def show_data(self, tree_view_type, data, col_names):
        """
        Zobrazení dat v GUI.
        
        :param tree_view_type: Typ zobrazení, např. "sklad".
        :param data: Data pro zobrazení.
        :param col_names: Názvy sloupců dat.
        """
        self.switch_tree_view(tree_view_type, col_names)
        self.current_tree_view.add_data(data)

    def switch_tree_view(self, tree_view_type, col_names):
        """
        Přepínání mezi různými TreeViews podle vybrané tabulky databáze.
        
        :param tree_view_type: Typ TreeView pro zobrazení.
        :param col_names: Názvy sloupců pro aktuální TreeView.
        """
        if self.current_tree_view is not None:
            self.current_tree_view.frame.destroy()

        if tree_view_type == "sklad":
            self.current_tree_view = SkladView(self.root, self.controller, col_names)
        elif tree_view_type == "audit_log":
            self.current_tree_view = AuditLogView(self.root, self.controller, col_names)
        # Přidání dalších podmínek pro nové typy zobrazení

class SkladView(View):
    """
    Třída SkladView pro specifické zobrazení dat skladu. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names):
        """
        Inicializace specifického zobrazení pro sklad.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller)
        self.col_names = col_names      
        self.initialize_treeview(self.tree_frame)

        self.check_columns = ('Ucetnictvi', 'Kriticky_dil', 'HSH', 'TQ8', 'TQF_XL_I', 'TQF_XL_II', 'DC_XL',
                               'DAC_XLI_a_II', 'DL_XL', 'DAC', 'LAC_I', 'LAC_II', 'IPSEN_ENE', 'HSH_ENE', 'XL_ENE1',
                               'XL_ENE2', 'IPSEN_W', 'HSH_W', 'KW', 'KW1', 'KW2', 'KW3')
        self.hidden_columns = self.check_columns + ('Objednano',)

        self.initialize_specific_menu()
        self.initialize_specific_frame()
        self.setup_columns(self.col_parameters())


    def col_parameters(self):
        """
        Nastavení specifických parametrů sloupců, jako jsou šířka a zarovnání.
        
        :return: Seznam slovníků parametrů sloupců k rozbalení.
        """
        col_params = []     
        for index, col in enumerate(self.col_names):
            match col:
                case 'Nazev_dilu':
                    col_params.append({"width": 400, "anchor": "w"})                
                case 'Dodavatel' | 'Poznamka':
                    col_params.append({"width": 150, "anchor": "w"})
                case 'Jednotky' | 'Evidencni_cislo' | 'Interne_cislo':
                    col_params.append({"width": 25, "anchor": "center"})
                case _ if col in self.hidden_columns:
                    col_params.append({"width": 0, "minwidth": 0, "stretch": tk.NO})
                case _:    
                    col_params.append({"width": 70, "anchor": "center"})
        return col_params      


    def initialize_specific_menu(self):
        """
        Vytvoření specifického menu pro sklad.
        """
        users_menu = tk.Menu(self.menu_bar, tearoff=0)
        users_menu.add_command(label="Přidat položku", command=self.add_item)
        self.menu_bar.add_cascade(label="Skladové položky", menu=users_menu)

    def initialize_specific_frame(self):
        """
        Vytvoření specifických frame pro zobrazení informací o skladu.
        """
        self.title_frame = tk.Frame(self.item_frame, bg="yellow", borderwidth=2, relief="groove")
        self.title_frame.pack(side=tk.TOP,fill=tk.X, padx=2, pady=2)   

        self.show_frame = tk.Frame(self.item_frame, borderwidth=2, relief="groove")
        self.show_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        title_label = tk.Label(self.title_frame, bg="yellow", text="ZOBRAZENÍ SKLADOVÉ KARTY")
        title_label.pack(padx=2, pady=2)

    def add_item(self):
        """
        Implementace funkcionality pro přidání nové položky do skladu.
        """
        pass

class AuditLogView(View):
    """
    Třída AuditLogView pro specifické zobrazení dat audit logu. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names):
        """
        Inicializace specifického zobrazení pro audit log.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller)
        self.col_names = col_names

        self.initialize_treeview(self.tree_frame)

        self.hidden_columns = {'Objednano', 'Poznamka'}

        self.initialize_specific_menu()
        self.initialize_specific_frame()
        self.setup_columns(self.col_parameters())


    def initialize_specific_menu(self):
        """
        Vytvoření specifického menu pro sklad.
        """
        pass

    def initialize_specific_frame(self):
        """
        Vytvoření specifických frame pro zobrazení informací o skladu.
        """
        pass

    def col_parameters(self):
        """
        Nastavení specifických parametrů sloupců, jako jsou šířka a zarovnání.
        
        :return: Seznam slovníků parametrů sloupců k rozbalení.
        """
        col_params = []     
        for index, col in enumerate(self.col_names):
            match col:
                case 'Nazev_dilu':
                    col_params.append({"width": 400, "anchor": "w"})                
                case 'Dodavatel' | 'Cas_operace' | 'Pouzite_zarizeni':
                    col_params.append({"width": 150, "anchor": "w"})
                case 'Jednotky' | 'Evidencni_cislo' | 'Interne_cislo':
                    col_params.append({"width": 30, "anchor": "center"})
                case _ if col in self.hidden_columns:
                    col_params.append({"width": 0, "minwidth": 0, "stretch": tk.NO})
                case _:    
                    col_params.append({"width": 80, "anchor": "center"})
        return col_params 


class Controller:
    """
    Třída Controller koordinuje Model a View.
    """
    def __init__(self, root, db_path):
        """
        Inicializace controlleru s připojením k databázi a inicializací GUI.
        
        :param root: Hlavní okno aplikace.
        :param db_path: Cesta k databázovému souboru.
        """
        self.root = root
        self.db_path = db_path
        self.model = Model(db_path)
        self.view = View(root, self)

    def show_data(self, table):
        """
        Zobrazení dat z vybrané tabulky v GUI.
        
        :param table: Název tabulky pro zobrazení.
        """
        data = self.model.fetch_data(table)
        col_names = self.model.fetch_col_names(table)
        self.view.show_data(table, data, col_names)


if __name__ == "__main__":
    root = tk.Tk()
    db_path = 'skladova_databaze.db'
    table = 'sklad'
    controller = Controller(root, db_path)
    controller.show_data(table)
    root.mainloop()

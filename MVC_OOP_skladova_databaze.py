import sqlite3
import csv
import tkinter as tk
from tkinter import ttk, font, filedialog, messagebox, simpledialog
from datetime import datetime
import os
import re

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
        
        :param root(tk.Tk): Hlavní okno aplikace.
        :param controller(Controller): Instance kontroleru pro komunikaci mezi modelem a pohledem.
        """
        self.root = root
        self.root.title('Zobrazení databáze')
        self.controller = controller
        self.current_tree_view = None  # Aktuální TreeView pro zobrazení dat
        self.sort_reverse = False  # Výchozí směr řazení je normální (False)
            
        # Definice slovníku názvy sloupců v tabulce: lidské názvy s diakritikou
        self.tab2hum = {'Ucetnictvi': 'Účetnictví', 'Kriticky_dil': 'Kritický díl', 'Evidencni_cislo': 'Evid. č.',
                        'Interne_cislo': 'Č. karty', 'Min_Mnozstvi_ks': 'Minimum', 'Objednano': 'Objednáno?',
                        'Nazev_dilu': 'Název dílu', 'Mnozstvi_ks_m_l': 'Akt. množství', 'Jednotky':'Jedn.',
                        'HSH': 'HSH', 'TQ8': 'TQ8', 'TQF_XL_I': 'TQF XL I', 'TQF_XL_II': 'TQF XL II',
                        'DC_XL': 'DC XL', 'DAC_XLI_a_II': 'DAC XLI a II', 'DL_XL': 'DL XL', 'DAC': 'DAC',
                        'LAC_I': 'LAC I', 'LAC_II': 'LAC II', 'IPSEN_ENE': 'IPSEN ENE', 'HSH_ENE': 'HSH ENE',
                        'XL_ENE1': 'XL ENE1', 'XL_ENE2': 'XL ENE2', 'IPSEN_W': 'IPSEN W', 'HSH_W': 'HSH W',
                        'KW': 'KW', 'KW1': 'KW1', 'KW2': 'KW2', 'KW3': 'KW3', 'Umisteni': 'Umístění',
                        'Dodavatel': 'Dodavatel', 'Datum_nakupu': 'Datum nákupu',
                        'Cislo_objednavky': 'Objednávka', 'Jednotkova_cena_EUR': 'Cena EUR/ks',
                        'Celkova_cena_EUR': 'Celkem EUR', 'Poznamka': 'Poznámka',
                        'Zmena_mnozstvi': 'Změna množství', 'Cas_operace': 'Čas operace',
                        'Operaci_provedl': 'Operaci provedl', 'Typ_operace': 'Typ operace',
                        'Datum_vydeje': 'Datum výdeje', 'Pouzite_zarizeni': 'Použité zařízení', 'id': 'ID'}

        
    def customize_ui(self):
        """
        Přidání specifických menu a framů a labelů pro zobrazení informací o skladu.
        """
        self.initialize_menu()
        self.initialize_frames()
        self.initialize_searching()
        specialized_menus = self.spec_menus()
        self.update_menu(specialized_menus)
        # Zjištění, zda je definována metoda 'update_frames'
        if hasattr(self.current_tree_view, 'self.update_frames'):
            self.update_frames()
        self.initialize_check_buttons()
        self.initialize_treeview(self.tree_frame)
        self.additional_gui_elements()
        # Nastavení vzhledu pro tag 'low_stock' skladové množství pod minimálním 
        self.tree.tag_configure('low_stock', background='#ffcccc', foreground='white')
        # Označení po kliknutí a vypsání položky do spodního frame:
        self.tree.bind('<<TreeviewSelect>>', lambda e: self.show_selected_item_details())


    def initialize_menu(self):
        """
        Inicializace společných menu.
        """
        # Inicializace hlavního menu aplikace
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Definování a přidání společných položek menu
        common_menus = {
            "Soubor": [
                ("Export skladu do csv", lambda: self.controller.export_csv('sklad')),
                ("Export audit_logu do csv", lambda: self.controller.export_csv('audit_log')),
                ("Export dodavatelů do csv", lambda: self.controller.export_csv('dodavatele')),
                "separator",
                ("Konec", self.root.destroy)
            ],
            "Zobrazení": [
                ("Sklad", lambda: self.controller.show_data('sklad')),
                ("Auditovací log", lambda: self.controller.show_data('audit_log')),
                ("Dodavatelé", lambda: self.controller.show_data('dodavatele'))
            ]
        }
        self.update_menu(common_menus)  

    def initialize_frames(self):        
        """
        Inicializace společných framů, proběhne až v instanci dceřínné třídy.
        """
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)     
        self.search_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.search_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.tree_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)           
        self.item_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.item_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.title_frame = tk.Frame(self.item_frame, bg="yellow", borderwidth=2, relief="groove")
        self.title_frame.pack(side=tk.TOP,fill=tk.X, padx=2, pady=2)   
        self.show_frame = tk.Frame(self.item_frame, borderwidth=2, relief="groove")
        self.show_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

    def initialize_searching(self):
        """
        Inicializace políčka a tlačítka pro vyhledávání / filtrování.
        """
        self.search_entry = tk.Entry(self.search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT)
        self.search_button = tk.Button(self.search_frame, text="Filtrovat", command=self.controller.show_data)
        self.search_button.pack(side=tk.LEFT)


    def initialize_check_buttons(self):
        """
        Nastavení specifických checkbuttonů pro filtrování zobrazených položek.
        """
        for col in self.check_columns:
            if (col == 'Ucetnictvi' or col == 'Kriticky_dil'):
                col_name = self.tab2hum[col]
                checkbutton = tk.Checkbutton(self.search_frame, text=col_name, borderwidth=3, relief="groove",
                                             variable=tk.BooleanVar(), onvalue=1, offvalue=0,
                                             command=lambda col=col: self.toggle_filter(col))
                checkbutton.pack(side='left', padx=5, pady=5)
            else:
                checkbutton = tk.Checkbutton(self.search_frame, text=col, variable=tk.BooleanVar(),
                                             onvalue=1, offvalue=0, command=lambda col=col: self.toggle_filter(col))
                checkbutton.pack(side='left', padx=3, pady=5)


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


    def update_menu(self, additional_menus):
        """
        Aktualizuje hlavní menu aplikace přidáním nových položek menu,
        včetně oddělovačů mezi některými položkami.
        
        Parametry:
            additional_menus (dict): Slovník definující položky menu k přidání.
                                     Klíč slovníku je název menu a hodnota je seznam
                                     dvojic (název položky, příkaz) nebo řetězce 'separator'
                                     pro vložení oddělovače.
        """
        for menu_name, menu_items in additional_menus.items():
            new_menu = tk.Menu(self.menu_bar, tearoff=0)
            for item in menu_items:
                if item == "separator":
                    new_menu.add_separator()
                else:
                    item_name, command = item
                    new_menu.add_command(label=item_name, command=command)
            self.menu_bar.add_cascade(label=menu_name, menu=new_menu)


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
        Vložení dat do TreeView. Změna hodnot v check_colums z 01 na NE ANO pro zobrazení.
        Třídění podle vybraného sloupce a směru třídění. Zvýraznění řádků pod minimem.
        
        :param data: Data pro zobrazení ve formátu seznamu n-tic.
        """

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in data:
            row_converted = list(row)
            for index, col in enumerate(self.col_names):
                if col in self.check_columns:
                    # Změnit ANO NE na 1 0 pro sloupce 'Ucetnictvi' i pro tabulku audit_log!
                    # Pak se může zrušit podmínka isinstace a nechat jenom část za else
                    if isinstance(row[index], str):
                        row_converted[index] = row[index]
                    else:
                        row_converted[index] = "ANO" if row[index] == 1 else "NE"               
            item_id = self.tree.insert('', tk.END, values=row_converted)


            if self.current_tree_view_type == 'sklad':                
                if int(row[7]) < int(row[4]):
                    self.tree.item(item_id, tags=('low_stock',))

        self.mark_first_item()


    def mark_first_item(self):
        """
        Označení první položky v Treeview po načtení nových dat.
        """
        first_item = self.tree.get_children()[0] if self.tree.get_children() else None
        if first_item:
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)


    def show_data(self, tree_view_type, data, col_names):
        """
        Zobrazení dat v GUI. Pokud se mění tabulka k zobrazení,
        vytvoří se nová instance podtřídy View, pokud zůstává tabulka
        stejná, pouze se aktulizují zobrazená data.
        
        :param tree_view_type: Typ zobrazení, např. "sklad".
        :param data: Data pro zobrazení.
        :param col_names: Názvy sloupců dat.
        """
        self.current_tree_view_type = tree_view_type
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
        elif tree_view_type == "dodavatele":
            self.current_tree_view = DodavateleView(self.root, self.controller, col_names)
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
        self.current_tree_view_type = 'sklad'
        self.col_names = col_names
        self.check_columns = ('Ucetnictvi', 'Kriticky_dil', 'HSH', 'TQ8', 'TQF_XL_I', 'TQF_XL_II', 'DC_XL',
                              'DAC_XLI_a_II', 'DL_XL', 'DAC', 'LAC_I', 'LAC_II', 'IPSEN_ENE', 'HSH_ENE',
                              'XL_ENE1', 'XL_ENE2', 'IPSEN_W', 'HSH_W', 'KW', 'KW1', 'KW2', 'KW3')
        self.hidden_columns = self.check_columns + ('Objednano',)

        self.customize_ui() 

        col_params = self.col_parameters()
        self.setup_columns(col_params)

        self.sort_col = 2  # Výchozí sloupec pro řazení pro sklad sloupec 2 pro Evidenční číslo        


    def spec_menus(self):
        """
        Vytvoření slovníku pro specifická menu dle typu zobrazovaných dat.
        
        :return: Slovník parametrů menu k vytvoření specifických menu.
        """
        specialized_menus = {
            "Skladové karty": [
                ("Přidat položku", self.add_item),
                ("Upravit položku", self.open_edit_window),
                "separator",
                ("Smazat položku", self.delete_row)
            ],
            "Příjem/Výdej": [
                ("Příjem zboží", lambda: self.prijem_vydej_zbozi(action='prijem')),
                ("Výdej zboží", lambda: self.prijem_vydej_zbozi(action='vydej')) 
            ],
            "Nákup": [
                ("Položky k nákupu", lambda: self.load_data(filter_low_stock=True)),
                ("Export položky k nákupu", lambda: self.controller.export_csv('sklad', filter='nakup'))
            ],
        }
        return specialized_menus


    def update_frames(self):
        """
        Nastavení specifických framů dle typu zobrazených položek.
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
                case 'Dodavatel' | 'Poznamka':
                    col_params.append({"width": 150, "anchor": "w"})
                case 'Jednotky' | 'Evidencni_cislo' | 'Interne_cislo':
                    col_params.append({"width": 25, "anchor": "center"})
                case _ if col in self.hidden_columns:
                    col_params.append({"width": 0, "minwidth": 0, "stretch": tk.NO})
                case _:    
                    col_params.append({"width": 70, "anchor": "center"})
        return col_params


    def additional_gui_elements(self):
        """
        Vytvoření zbývajících specifických prvků gui dle typu zobrazovaných dat.
        """
        self.title_label = tk.Label(self.title_frame, bg="yellow", text="ZOBRAZENÍ SKLADOVÉ KARTY")
        self.title_label.pack(padx=2, pady=2)   
   


    def open_edit_window(self):
        """
        Implementace funkcionality pro přidání nové položky do skladu.
        """
        pass

    def add_item(self):
        """
        Implementace funkcionality pro přidání nové položky do skladu.
        """
        pass

    def delete_row(self):
        """
        Implementace funkcionality pro úpravu položky do skladu.
        """
        pass

    def prijem_vydej_zbozi(self, action):
        """
        Implementace funkcionality pro příjem a výdej zboží ve skladu.
        """
        pass

    def load_data(self, filter_low_stock=False):
        """
        Implementace funkcionality nahrání dat
        Už je pro to metoda add_data - je potřeba upravit pro řízení přes kontroler.
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
        self.current_tree_view_type = 'audit_log'
        self.col_names = col_names
        
        self.hidden_columns = ('Objednano', 'Poznamka')
        self.check_columns = ('Ucetnictvi',)

        self.customize_ui()
       
        col_params = self.col_parameters()
        self.setup_columns(col_params)

        self.sort_col = 16  # Výchozí sloupec pro řazení pro audit_log sloupec 16 pro čas operace  


    def spec_menus(self):
        """
        Vytvoření slovníku pro specifická menu dle typu zobrazovaných dat.
        
        :return: Slovník parametrů menu k vytvoření specifických menu.
        """
        specialized_menus = {}
        return specialized_menus


    def additional_gui_elements(self):
        """
        Vytvoření zbývajících specifických prvků gui dle typu zobrazovaných dat.
        """
        self.title_label = tk.Label(self.title_frame, bg="yellow", text="ZOBRAZENÍ PŘÍJMU / VÝDEJE")
        self.title_label.pack(padx=2, pady=2)

        self.operation_label = tk.Label(self.search_frame, text="Typ operace:")
        self.operation_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.options = ["PŘÍJEM/VÝDEJ", "PŘÍJEM", "VÝDEJ"]
        self.operation_combobox = ttk.Combobox(self.search_frame, values=self.options)
        self.operation_combobox.pack(side=tk.LEFT, padx=5, pady=5) 

        self.operation_combobox.set("PŘÍJEM/VÝDEJ")
        self.operation_combobox.bind("<<ComboboxSelected>>", self.on_combobox_change)

    def on_combobox_change(self, event):
        selected_option = self.operation_combobox.get()
        print(f"Vybrána operace: {selected_option}")
        # Přidat později logiku na základě vybrané možnosti = filtrování dat v audit_logu

    def col_parameters(self):
        """
        Nastavení specifických parametrů sloupců, jako jsou šířka a zarovnání.
        
        :return: Seznam slovníků parametrů sloupců k rozbalení.
        """
        col_params = []     
        for index, col in enumerate(self.col_names):
            match col:
                case 'Nazev_dilu':
                    col_params.append({"width": 300, "anchor": "w"})                
                case 'Dodavatel' | 'Cas_operace' | 'Pouzite_zarizeni' | 'Operaci_provedl':
                    col_params.append({"width": 130, "anchor": "w"})
                case 'Jednotky' | 'Evidencni_cislo' | 'Interne_cislo':
                    col_params.append({"width": 30, "anchor": "center"})
                case _ if col in self.hidden_columns:
                    col_params.append({"width": 0, "minwidth": 0, "stretch": tk.NO})
                case _:    
                    col_params.append({"width": 80, "anchor": "center"})
        return col_params 


class DodavateleView(View):
    """
    Třída DodavateleView pro specifické zobrazení dat z tabulky dodavatele. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names):
        """
        Inicializace specifického zobrazení pro dodavatele.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller)
        self.current_tree_view_type = 'dodavatele'
        self.col_names = col_names
        
        self.hidden_columns = ()
        self.check_columns = ()

        self.customize_ui()
       
        col_params = self.col_parameters()
        self.setup_columns(col_params)

        self.sort_col = 0  # Výchozí sloupec pro řazení pro dodavatele sloupec 0 pro id  


    def spec_menus(self):
        """
        Vytvoření slovníku pro specifická menu dle typu zobrazovaných dat.
        
        :return: Slovník parametrů menu k vytvoření specifických menu.
        """
        specialized_menus = {}
        return specialized_menus


    def additional_gui_elements(self):
        """
        Vytvoření zbývajících specifických prvků gui dle typu zobrazovaných dat.
        """
        self.title_label = tk.Label(self.title_frame, bg="yellow", text="ZOBRAZENÍ DODAVATELŮ")
        self.title_label.pack(padx=2, pady=2)


    def col_parameters(self):
        """
        Nastavení specifických parametrů sloupců, jako jsou šířka a zarovnání.
        
        :return: Seznam slovníků parametrů sloupců k rozbalení.
        """
        col_params = []     
        for index, col in enumerate(self.col_names):
            match col:          
                case 'Dodavatel':
                    col_params.append({"width": 300, "anchor": "w"})
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
        self.current_table = None
        self.current_data = None
        self.current_col_names = None


    def show_data(self, table):
        """
        Zobrazení dat z vybrané tabulky v GUI.
        
        :param table: Název tabulky pro zobrazení.
        """
        self.current_table = table
        self.current_data = self.model.fetch_data(table)
        self.current_col_names = self.model.fetch_col_names(table)
        self.view.show_data(table, self.current_data, self.current_col_names)


    def filter_sort_show_data(self, filter_low_stock=False, sort_col=None):
        """
        Obnovení zobrazení aktuálních dat.
        """




        
        self.view.add_data(filtered_data)


    def export_csv(self, table, filter=None):
        """
        Export dat z vybrané tabulky v GUI.
        
        :param table: Název tabulky pro zobrazení.
        """
        col_names = self.model.fetch_col_names(table)
        data = self.model.fetch_data(table)

        if table == 'sklad' and filter == 'nakup':
            filtered_data =[]
            for row in data:
                if row[4] > row[7]:
                    filtered_data.append(row)                
        else:
            filtered_data = data

        csv_file_name = filedialog.asksaveasfilename(defaultextension=".csv",
                                                     filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],)
        if not csv_file_name:
            return
        
        with open(csv_file_name, mode='w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)    
            csv_writer.writerow(col_names)
            for row in filtered_data:
                csv_writer.writerow(row)
                
        tk.messagebox.showinfo("Export dokončen", f"Data byla úspěšně exportována do souboru '{csv_file_name}'.")


if __name__ == "__main__":
    root = tk.Tk()
    db_path = 'skladova_databaze.db'
    table = 'sklad' # Startovací tabulka pro zobrazení
    controller = Controller(root, db_path)
    controller.show_data(table)
    root.mainloop()

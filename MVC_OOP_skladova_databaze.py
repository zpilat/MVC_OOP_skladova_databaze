import sqlite3
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import tkinter.font as tkFont
from tkcalendar import DateEntry
from datetime import datetime, timedelta

import os
import re
import sys

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


    def fetch_item_for_editing(self, table, id_num, id_col_name):
        """
        Získání dat položky pro účely editace na základě ID.
        
        :param table: Název tabulky, ze které se položka získává.
        :param id_num: Číslo ID položky, který chceme editovat.
        :param id_col_name: Název sloupce, který obsahuje ID položky.
        :return: Řádek s daty položky nebo None, pokud položka nebyla nalezena.
        """
        query = f"SELECT * FROM {table} WHERE {id_col_name} = ?"
        self.cursor.execute(query, (id_num,))
        return self.cursor.fetchone()


    def get_max_evidencni_cislo(self):
        """
        Získá nejvyšší hodnotu ve sloupci Evidencni_cislo z tabulky sklad.
        Pokud v tabulce nejsou žádné záznamy, vrátí se 0 jako výchozí hodnota.
        
        :Return int: Nejvyšší hodnota ve sloupci Evidencni_cislo nebo 0, pokud neexistují žádné záznamy.
        """
        self.cursor.execute("SELECT MAX(Evidencni_cislo) FROM sklad")
        max_value = self.cursor.fetchone()[0]
        return max_value if max_value is not None else 0


    def get_max_interne_cislo(self):
        """
        Získá nejvyšší hodnotu ve sloupci Interne_cislo z tabulky sklad.
        Pokud v tabulce nejsou žádné záznamy, vrátí se 0 jako výchozí hodnota.
        
        :Return int: Nejvyšší hodnota ve sloupci Interne_cislo nebo 0, pokud neexistují žádné záznamy.
        """
        self.cursor.execute("SELECT MAX(Interne_cislo) FROM sklad")
        max_value = self.cursor.fetchone()[0]
        return max_value if max_value is not None else 0


    def delete_row(self, evidencni_cislo):
        """
        Smaže řádek ze skladu na základě jeho evidenčního čísla - ve sloupci Evidencni_cislo.      
        :Params evidencni_cislo (int): Evidencni_cislo řádku, který má být smazán.
        """
        self.cursor.execute("DELETE FROM sklad WHERE `Evidencni_cislo`=?", (evidencni_cislo,))
        self.conn.commit()
        

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
        self.root.title('Zobrazení databáze HPM HEAT SK - vývojová verze MVC OOP')
        self.controller = controller
        self.sort_reverse = False
        self.id_col = None
        self.id_col_name = None
        self.item_frame_show = None
            
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
        self.update_menu(self.spec_menus())
        self.update_frames()
        self.initialize_check_buttons()
        self.initialize_treeview(self.tree_frame)
        self.initialize_fonts()
        self.additional_gui_elements()
        self.selected_option = "PŘÍJEM/VÝDEJ"
        self.start_date = None
        self.tree.tag_configure('low_stock', background='#ffcccc', foreground='white')
        self.tree.bind('<<TreeviewSelect>>', self.show_selected_item)   


    def initialize_menu(self):
        """
        Inicializace hlavního společného menu.
        """
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        common_menus = {
            "Soubor": [
                ("Export aktuální databázové tabulky do csv", lambda: self.controller.export_csv(table=self.current_table)),
                "separator",
                ("Export aktuálně vyfiltrovaných dat do csv", lambda: self.controller.export_csv(tree=self.tree)),
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


    def initialize_searching(self):
        """
        Inicializace políčka a tlačítka pro vyhledávání / filtrování.
        """
        self.search_entry = tk.Entry(self.search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT)
        self.search_button = tk.Button(self.search_frame, text="Filtrovat",
                                       command=lambda: self.controller.show_data(self.current_table))
        self.search_button.pack(side=tk.LEFT)


    def initialize_check_buttons(self):
        """
        Nastavení specifických checkbuttonů pro filtrování zobrazených položek.
        """
        self.filter_columns = {col: tk.BooleanVar(value=False) for col in self.check_columns}
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


    def initialize_fonts(self):
        """
        Inicializace používaných fontů.
        """ 
        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.custom_font = self.default_font.copy()
        self.custom_font.config(size=12, weight="bold")               


    def update_menu(self, additional_menus):
        """
        Aktualizuje hlavní menu aplikace přidáním nových položek menu,
        včetně oddělovačů mezi některými položkami.
        
        Parametry:
            additional_menus (dict): Slovník definující položky menu k přidání.
                                     Klíč slovníku je název menu a hodnota je seznam
                                     dvojic (název položky, příkaz) nebo řetězec 'separator'
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


    def update_frames(self):
        """
        Aktualizuje specifické frame pro dané zobrazení.
        """
        pass

    def additional_gui_elements(self):
        """
        Vytvoření zbývajících specifických prvků gui dle typu zobrazovaných dat.
        """
        pass

    def setup_columns(self, col_params):
        """
        Nastavení sloupců pro TreeView.
        
        :col_params Seznam slovníků parametrů sloupců (width, minwidth, anchor, stretch...).
        """
        self.tree['columns'] = self.col_names
        for idx, col in enumerate(self.col_names):            
            self.tree.heading(col, text=self.tab2hum[col], command=lambda c=idx: self.on_column_click(c))
            self.tree.column(col, **col_params[idx])
   

    def add_data(self, filter_low_stock=False):
        """
        Vymazání všech dat v Treeview. Filtrace a třídění dle aktuálních hodnot parametrů.
        Vložení dat do TreeView. Změna hodnot v check_colums z 0/1 na NE/ANO pro zobrazení.
        Zvýraznění řádků pod minimem. Označení první položky v Treeview.
        Třídění podle zakliknuté hlavičky sloupce, při druhém kliknutí na stejný sloupec reverzně.
        """

        for item in self.tree.get_children():
            self.tree.delete(item)

        filtered_data = self.filter_data(self.current_data, filter_low_stock)


        sorted_data = sorted(filtered_data, key=self.sort_key, reverse=self.sort_reverse)

        for row in sorted_data:
            row_converted = list(row)
            for index, col in enumerate(self.col_names):
                if col in self.check_columns:
                    row_converted[index] = "ANO" if row[index] == 1 else "NE"               

            item_id = self.tree.insert('', tk.END, values=row_converted)

            if self.current_table == 'sklad':                
                if int(row[7]) < int(row[4]):
                    self.tree.item(item_id, tags=('low_stock',))      

        self.mark_first_item()
        

    def filter_data(self, data, filter_low_stock):
        """
        Vyfiltrování dat podle zadaných dat v search_entry ve všech tabulkách.
        V tabulce sklad navíc dle zaškrtnutých check buttonů a low stock filtru.
        V tabulce audit_log navíc dle comboboxu "PŘÍJEM/VÝDEJ" a v rozmezí datumů v date entry.

        :param data: Data pro filtraci dle search entry.
        :param filter_low_stock: Parametr pro filtraci položek pod minimálním množstvím.
        :return: Přefiltrovaná data.
        """ 
        search_query = self.search_entry.get()
        if search_query: # dle hodnoty v search entry
            filtered_data = [row for row in data if search_query.lower() in " ".join(map(str, row)).lower()]
        else:
            filtered_data = data
        
        if filter_low_stock: # dle parametru low stock
            filtered_data = [row for row in filtered_data if int(row[7]) < int(row[4])]

        if self.current_table == "audit_log": # dle vybrané položky comboboxu příjem / výdej
            if self.selected_option == "PŘÍJEM":
                filtered_data = [row for row in filtered_data if row[8] == "PŘÍJEM"]
            elif self.selected_option == "VÝDEJ":
                filtered_data = [row for row in filtered_data if row[8] == "VÝDEJ"]

        if self.start_date: # dle rozmezí datumů v date entry       
            filtered_data = [row for row in filtered_data if self.start_date <= row[12] <= self.end_date or self.start_date <= row[13] <= self.end_date]
            
        if any(value.get() for value in self.filter_columns.values()): # dle zaškrtnutých check buttonů
            filtered_data_temp = []
            for row in filtered_data:
                include_row = True  
                for col, is_filtered_var in self.filter_columns.items():
                    if is_filtered_var.get(): 
                        col_index = self.col_names.index(col)  
                        if row[col_index] != 1: 
                            include_row = False  
                            break
                if include_row:
                    filtered_data_temp.append(row)
            filtered_data = filtered_data_temp

        return filtered_data


    def toggle_filter(self, col):
        """
        Metoda pro filtraci dat v tabulce podle zaškrtnutých check buttonů
        Přepnutí stavu filtru pro daný sloupec pro tk.Boolean.Var
        a zobrazení přefiltrovaných dat.

        :param col: název sloupce (check buttonu), který byl zašrtnut / odškrtnut
        """
        current_value = self.filter_columns[col].get()
        self.filter_columns[col].set(not current_value)
        self.controller.show_data(self.current_table)


    def on_column_click(self, clicked_col):
        """
        Metoda pro třídění dat v tabulce podle kliknutí na název sloupce.
        Přepnutí stavu třídění normální / reverzní a zobrazení přefiltrovaných dat.
        
        :param clicked_col: název sloupce, na který bylo kliknuto.
        """
        if clicked_col == self.id_col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.id_col = clicked_col
            self.sort_reverse = False
        self.controller.show_data(self.current_table)

        
    def sort_key(self, row):
        """
        Funkce sloužící jako klíč pro třídění dle sloupcu.
        Pokusí se převést hodnotu na float pro řazení číselných hodnot.
        Čísla mají přednost, takže pro ně vracíme (0, number).
        Textové hodnoty dostanou nižší prioritu, vracíme (1, value.lower()).

        :param row: porovnávaný řádek / položka v datatabázi.
        """
        value = row[self.id_col]
        try:
            number = float(value)
            return (0, number)
        except ValueError:
            return (1, value.lower())

        
    def mark_first_item(self):
        """
        Označení první položky v Treeview po načtení nových dat.
        """
        first_item = self.tree.get_children()[0] if self.tree.get_children() else None
        if first_item:
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)


    def show_selected_item(self, event=None):
        """
        Metoda pro vytvoření instance pro získání dat a zobrazení vybrané položky z treeview.
        """           
        if self.item_frame_show is None:
            for widget in self.item_frame.winfo_children():
                widget.destroy()
            self.item_frame_show = ItemFrameShow(self.item_frame, self.controller, self.col_names,
                                                 self.tab2hum, self.current_table, self.check_columns)
        try:
            self.selected_item = self.tree.selection()[0]
            self.item_values = self.tree.item(self.selected_item, 'values')
            self.item_frame_show.show_selected_item_details(self.item_values)
        except Exception:
            messagebox.showwarning("Upozornění", "Žádná položka k zobrazení.")
            return


    def edit_selected_item(self):
        """
        Metoda pro získání aktuálních dat z databáze pro vybranou položku a jejich zobrazení
        pro editaci.
        """
        try:
            self.selected_item = self.tree.selection()[0]
        except Exception:
            messagebox.showwarning("Upozornění", "Žádná položka k zobrazení.")
            return
        
        for widget in self.item_frame.winfo_children():
            widget.destroy()
            
        self.item_frame_show = None
        self.id_num = self.tree.item(self.selected_item, 'values')[self.id_col]
        self.controller.show_data_for_editing(self.current_table, self.id_num, self.id_col_name,
                                              self.item_frame, self.tab2hum, self.check_columns)
            

class SkladView(View):
    """
    Třída SkladView pro specifické zobrazení dat skladu. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, data):
        """
        Inicializace specifického zobrazení pro sklad.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller)
        self.current_table = 'sklad'
        self.col_names = col_names
        self.current_data = data
        self.check_columns = ('Ucetnictvi', 'Kriticky_dil', 'HSH', 'TQ8', 'TQF_XL_I', 'TQF_XL_II', 'DC_XL',
                              'DAC_XLI_a_II', 'DL_XL', 'DAC', 'LAC_I', 'LAC_II', 'IPSEN_ENE', 'HSH_ENE',
                              'XL_ENE1', 'XL_ENE2', 'IPSEN_W', 'HSH_W', 'KW', 'KW1', 'KW2', 'KW3')
        self.hidden_columns = self.check_columns + ('Objednano',)

        self.customize_ui() 

        col_params = self.col_parameters()
        self.setup_columns(col_params)

        self.id_col = 2  # Výchozí sloupec pro třídění pro sklad podle sloupce 2 pro Evidenční číslo
        self.id_col_name = 'Evidencni_cislo'


    def spec_menus(self):
        """
        Vytvoření slovníku pro specifická menu dle typu zobrazovaných dat.
        
        :return: Slovník parametrů menu k vytvoření specifických menu.
        """
        specialized_menus = {
            "Skladové položky": [
                ("Přidat skladovou položku", self.add_item),
                ("Upravit skladovou položku", self.edit_selected_item),
                "separator",
                ("Smazat skladovou položku", self.delete_row),
            ],
            "Příjem/Výdej": [
                ("Příjem zboží", lambda: self.prijem_vydej_zbozi(action='prijem')),
                ("Výdej zboží", lambda: self.prijem_vydej_zbozi(action='vydej')), 
            ],
            "Nákup": [
                ("Položky pod minimem", lambda: self.add_data(filter_low_stock=True)),
            ],
        }
        return specialized_menus


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


    def add_item(self):
        """
        Implementace funkcionality pro přidání nové položky do skladu.
        """
        pass
 

    def delete_row(self):
        """
        Vymaže označenou položku, pokud je nulový stav.
        """
        try:
            self.selected_item = self.tree.selection()[0]
        except Exception:
            messagebox.showwarning("Upozornění", "Nebyla vybrána žádná položka k vymazání.")
            return

        last_inserted_item = self.controller.get_max_evidencni_cislo()
        evidencni_cislo = self.tree.item(self.selected_item)['values'][2]
        mnozstvi_ks_m_l = self.tree.item(self.selected_item)['values'][7]
        if mnozstvi_ks_m_l != 0 or evidencni_cislo != last_inserted_item:
            messagebox.showwarning("Varování", "Lze smazat pouze poslední zadanou položku s nulovým množstvím!")
            return           
        response = messagebox.askyesno("Potvrzení mazání", "Opravdu chcete smazat vybraný řádek?")
        if response: 
            self.controller.delete_row(evidencni_cislo)
            self.tree.delete(selected_item[0])
            messagebox.showinfo("Informace", "Vymazána poslední zadaná položka!")
        self.controller.show_data(self.current_table)
        

    def prijem_vydej_zbozi(self, action):
        """
        Implementace funkcionality pro příjem a výdej zboží ve skladu.
        """
        pass

    
class AuditLogView(View):
    """
    Třída AuditLogView pro specifické zobrazení dat audit logu. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, data):
        """
        Inicializace specifického zobrazení pro audit log.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller)
        self.current_table = 'audit_log'
        self.col_names = col_names
        self.current_data = data
        
        self.hidden_columns = ('Objednano', 'Poznamka', 'Cas_operace')
        self.check_columns = ('Ucetnictvi',)

        self.customize_ui()
       
        col_params = self.col_parameters()
        self.setup_columns(col_params)

        self.id_col = 18  # Výchozí sloupec pro řazení pro audit_log sloupec 18 id  
        self.id_col_name = 'id'

        
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
        self.operation_label = tk.Label(self.search_frame, text="Typ operace:")
        self.operation_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.options = ["PŘÍJEM/VÝDEJ", "PŘÍJEM", "VÝDEJ"]
        self.operation_combobox = ttk.Combobox(self.search_frame, values=self.options)
        self.operation_combobox.pack(side=tk.LEFT, padx=5, pady=5) 

        self.operation_combobox.set("PŘÍJEM/VÝDEJ")
        self.operation_combobox.bind("<<ComboboxSelected>>", self.on_combobox_change)

        today = datetime.now()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        self.start_date_entry_label = tk.Label(self.search_frame, text="Počáteční datum:")
        self.start_date_entry_label.pack(side=tk.LEFT, padx=5, pady=5)
        self.start_date_entry = DateEntry(self.search_frame, width=12, background='darkblue', foreground='white',
                                          borderwidth=2, year=first_day_of_month.year,
                                          month=first_day_of_month.month, day=first_day_of_month.day)
        self.start_date_entry.pack(side=tk.LEFT, padx=5, pady=5)

        self.end_date_entry_label = tk.Label(self.search_frame, text="Koncové datum:")
        self.end_date_entry_label.pack(side=tk.LEFT, padx=5, pady=5)
        self.end_date_entry = DateEntry(self.search_frame, width=12, background='darkblue', foreground='white',
                                        borderwidth=2, year=last_day_of_month.year,
                                        month=last_day_of_month.month, day=last_day_of_month.day)
        self.end_date_entry.pack(side=tk.LEFT, padx=5, pady=5)

        choice_btn = tk.Button(self.search_frame, text="Vyfiltrovat období", command=self.filter_date)
        choice_btn.pack(side=tk.LEFT, padx=5, pady=5)


    def filter_date(self):
        """
        Filtrování zobrazovaných dat v rozsahu počátečního a koncového datumu.
        """
        self.start_date = datetime.strptime(self.start_date_entry.get(), '%d.%m.%y').strftime('%Y-%m-%d')
        self.end_date = datetime.strptime(self.end_date_entry.get(), '%d.%m.%y').strftime('%Y-%m-%d')
        self.controller.show_data(self.current_table)


    def on_combobox_change(self, event):
        """
        Filtrování zobrazovaných dat podle eventu (vybraného filtru) comboboxu.
        """
        self.selected_option = self.operation_combobox.get()         
        self.controller.show_data(self.current_table)

    def col_parameters(self):
        """
        Nastavení specifických parametrů sloupců, jako jsou šířka a zarovnání.
        
        :return: Seznam slovníků parametrů sloupců k rozbalení.
        """
        col_params = []     
        for index, col in enumerate(self.col_names):
            match col:
                case 'Nazev_dilu':
                    col_params.append({"width": 230, "anchor": "w"})                
                case 'Dodavatel' | 'Pouzite_zarizeni':
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
    def __init__(self, root, controller, col_names, data):
        """
        Inicializace specifického zobrazení pro dodavatele.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller)
        self.current_table = 'dodavatele'
        self.col_names = col_names
        self.current_data = data

        self.check_columns = ()
        self.hidden_columns = ()
        
        self.customize_ui()
       
        col_params = self.col_parameters()
        self.setup_columns(col_params)

        self.id_col = 0  # Výchozí sloupec pro řazení pro dodavatele sloupec 0 pro id
        self.id_col_name = 'id'        


    def spec_menus(self):
        """
        Vytvoření slovníku pro specifická menu dle typu zobrazovaných dat.
        
        :return: Slovník parametrů menu k vytvoření specifických menu.
        """
        specialized_menus = {
            "Dodavatelé": [
                ("Přidat dodavatele", self.add_item),
                ("Upravit dodavatele", self.edit_selected_item),
            ],
        }
        return specialized_menus


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


    def add_item(self):
        """
        Implementace funkcionality pro přidání nové položky do skladu.
        """
        pass
 

class ItemFrameBase:
    """
    Třída ItemFrameBase je rodičovská třída pro práci s vybranými položkami.
    """
    def __init__(self, master, controller, col_names, tab2hum, current_table, check_columns):
        """
        Inicializace prvků v item_frame.
        
        :param master: Hlavní frame item_frame, kde se zobrazují informace o položkách.
        :param tree: Treeview, ve kterém se vybere zobrazovaná položka.
        :param col_names: Názvy sloupců zobrazované položky.
        :param dict_tab2hum: Slovník s převodem databázových názvů sloupců na lidské názvy.
        :param current_table: Aktuálně otevřená tabulka databáze.
        """
        self.master = master
        self.controller = controller
        self.col_names = col_names
        self.tab2hum = tab2hum
        self.current_table = current_table
        self.check_columns = check_columns
        self.suppliers = self.controller.fetch_suppliers()
       
        self.initialize_fonts()
        self.initialize_frames()
        self.unit_tuple = ("ks", "kg", "pár", "l", "m", "balení")
        self.table_config = {"sklad": {"order": 6, "id_col": 2}, "audit_log": {"order": 4, "id_col": 18},
                             "dodavatele": {"order": 1, "id_col": 0}}


    def initialize_fonts(self):
        """
        Inicializace používaných fontů.
        """ 
        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.custom_font = self.default_font.copy()
        self.custom_font.config(size=12, weight="bold")
        

    def initialize_frames(self):
        """
        Vytvoření framů ve frame item_frame.
        """
        self.title_frame = tk.Frame(self.master, bg="yellow", borderwidth=2, relief="groove")
        self.title_frame.pack(side=tk.TOP,fill=tk.X, padx=2, pady=2)   
        self.show_frame = tk.Frame(self.master, borderwidth=2, relief="groove")
        self.show_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)


    def update_frames(self, action):
        """
        Vytvoření a nastavení dalších framů v show_frame pro aktuální zobrazení.

        :param action: Typ akce pro tlačítko uložit - add pro přidání nebo edit pro úpravu.
        """
        self.top_frame = tk.Frame(self.show_frame)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)     
        self.left_frame = tk.Frame(self.top_frame, borderwidth=2)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.right_frame = tk.Frame(self.top_frame, borderwidth=2)
        self.right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.bottom_frame = tk.Frame(self.show_frame)
        self.bottom_frame.pack(side=tk.BOTTOM, pady=2)

        save_btn = tk.Button(self.bottom_frame, width=15, text="Uložit", command=lambda: self.check_and_save(action = action))
        save_btn.pack(side=tk.LEFT, padx=5, pady=5)
        cancel_btn = tk.Button(self.bottom_frame, width=15, text="Zrušit", command=self.current_view_instance.show_selected_item)
        cancel_btn.pack(side=tk.LEFT, padx=5, pady=5)


    def initialize_title(self):
        """
        Vytvoření nadpisu dle typu zobrazovaných dat.
        """
        self.title = self.title_dict[self.current_table]
        self.order = self.table_config[self.current_table]["order"]

        title_label = tk.Label(self.title_frame, bg="yellow", text=self.title, font=self.custom_font)
        title_label.pack(padx=2, pady=2)
        name_label = tk.Label(self.title_frame, bg="yellow", wraplength=400, font=self.custom_font,
                              text=f"{self.tab2hum[self.col_names[self.order]]}: \n {str(self.item_values[self.order])}")
        name_label.pack(padx=2, pady=2)


class ItemFrameShow(ItemFrameBase):
    """
    Třída ItemFrameShow se stará o zobrazení vybraných položek.
    """
    def __init__(self, master, controller, col_names, tab2hum, current_table, check_columns):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, tab2hum, current_table, check_columns)
        self.title_dict = {"sklad": "ZOBRAZENÍ SKLADOVÉ KARTY", "audit_log": "ZOBRAZENÍ POHYBU NA SKLADĚ",
                           "dodavatele": "ZOBRAZENÍ DODAVATELE"}


    def clear_item_frame(self):
        """
        Odstranění všech widgetů v title_frame a show_frame
        """
        for widget in self.title_frame.winfo_children():
            widget.destroy()
        for widget in self.show_frame.winfo_children():
            widget.destroy()  


    def show_selected_item_details(self, item_values):
        """
        Metoda pro zobrazení vybrané položky z Treeview ve frame item_frame
        Název položky je v title_frame, zbylé informace v show_frame
        """
        self.item_values = item_values   
        self.clear_item_frame()        
        self.initialize_title()
          
        for index, value in enumerate(self.item_values):
            if index == self.order: continue   # Vynechá název
            idx = index - 1 if index > self.order else index 
            col_num = idx % 2
            row_num = idx // 2
            col_name = self.tab2hum[self.col_names[index]]
            label_text = f"{col_name}: {value}"
            label = tk.Label(self.show_frame, text=label_text, borderwidth=2, relief="ridge", width=28, wraplength=195)
            label.grid(row=row_num, column=col_num, sticky="nsew", padx=5, pady=2)


       
class ItemFrameEdit(ItemFrameBase):
    """
    Třída ItemFrameEdit se stará o úpravu vybraných položek.
    """
    def __init__(self, master, controller, col_names, tab2hum, current_table, check_columns, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        self.current_view_instance = current_view_instance
        super().__init__(master, controller, col_names, tab2hum, current_table, check_columns)
        self.title_dict = {"sklad": "ÚPRAVA SKLADOVÉ KARTY", "dodavatele": "ÚPRAVA DODAVATELE"}

       
    def open_edit_window(self, item_values):
        """
        Metoda pro úpravu vybrané položky z Treeview.

        :params item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
        """
        self.item_values = item_values    
        self.initialize_title()
        self.update_frames(action='edit')                
        self.id_num = self.item_values[self.table_config[self.current_table]["id_col"]]
        self.checkbutton_states = {}
        self.entries = {}

        for index, col in enumerate(self.col_names):           
            if col in self.check_columns:
                frame = tk.Frame(self.right_frame)
                is_checked = self.item_values[index] == 1
                self.checkbutton_states[col] = tk.BooleanVar(value=is_checked)
                checkbutton = tk.Checkbutton(frame, text=self.tab2hum[col], variable=self.checkbutton_states[col])
                if (col == 'Ucetnictvi' or col == 'Kriticky_dil'):            
                    checkbutton.config(borderwidth=3, relief="groove")
                checkbutton.pack(side=tk.LEFT, padx=5)
            else:
                frame = tk.Frame(self.left_frame)
                label = tk.Label(frame, text=self.tab2hum[col], width=12)
                match col:
                    case 'Min_Mnozstvi_ks':
                        entry = tk.Spinbox(frame, width=28, from_=0, to='infinity')
                        if self.item_values:
                            entry.delete(0, "end")
                            entry.insert(0, self.item_values[index])                
                    case 'Jednotky':
                        entry = ttk.Combobox(frame, width=28, values=self.unit_tuple)
                        entry.set(self.item_values[index])                           
                    case 'Dodavatel' if self.current_table=='sklad':
                        entry = ttk.Combobox(frame, width=28, values=self.suppliers)
                        entry.set(self.item_values[index])                  
                    case _:
                        entry = tk.Entry(frame, width=30)
                        if self.item_values:
                            entry.insert(0, self.item_values[index])
                if ((self.current_table=='sklad' and index==2 or index==7) # Pouze ke čtení pro Evid. č. a Množství pro sklad
                    or (self.current_table=='dodavatele' and index==0 or index==1)):  # pro id a jména dodavatele pro dodavatele
                    entry.config(state='readonly')             
                label.pack(side=tk.LEFT, pady=6)
                entry.pack(side=tk.RIGHT, padx=2, pady=6)
                self.entries[col] = entry
            frame.pack(fill=tk.X)


class ItemFrameAdd(ItemFrameBase):
    """
    Třída ItemFrameAdd se stará o tvorbu nových položek.
    """
    def __init__(self, master, controller, col_names, tab2hum, current_table, check_columns):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, tab2hum, current_table, check_columns)
        self.title_dict = {"sklad": "VYTVOŘENÍ  SKLADOVÉ KARTY", "dodavatele": "VYTVOŘENÍ DODAVATELE"}
        self.entry_dict = {"sklad": {"read_only": ('Evidencni_cislo', 'Interne_cislo', 'Mnozstvi_ks_m_l', 'Datum_nakupu',
                                                   'Jednotkova_cena_EUR', 'Celkova_cena_EUR', 'Objednano', 'Cislo_objednavky'),
                                     }
                           "dodavatele": {"read_only": ('id',)
                                          }
                           }
 

    def add_item(self):
        """
        Metoda pro přidání nové položky do aktuální tabulky.
        """
        self.entries = {}
        self.checkbutton_states = {}
        self.initialize_title()
        self.update_frames(action='add')
        self.new_id = self.controller.get_max_id(self.current_table, self.table_config[self.current_table]["id_col"]) + 1
        aktualni_datum = datetime.now().strftime("%Y-%m-%d")
        
        for index, col in enumerate(self.col_names):
            if col in self.check_columns:
                frame = tk.Frame(self.right_frame)
                self.checkbutton_states[col] = tk.BooleanVar(value=True) if col == 'Ucetnictvi' else tk.BooleanVar(value=False)
                checkbutton = tk.Checkbutton(frame, text=self.tab2hum[col], variable=self.checkbutton_states[col])
                if (col == 'Ucetnictvi' or col == 'Kriticky_dil'):            
                    checkbutton.config(borderwidth=3, relief="groove")
                checkbutton.pack(side=tk.LEFT, padx=5)

            else:
                if self.current_table=='sklad':
                    self.new_interne_cislo = self.controller.get_max_interne_cislo() + 1


                elif self.current_tabel=='dodavatele':
                    

                    
                elif col == 'Min_Mnozstvi_ks':
                    frame = tk.Frame(self.left_frame)
                    label = tk.Label(frame, text=self.dict_col2humancol[col], width=12)
                    label.pack(side=tk.LEFT, pady=6)
                    entry = tk.Spinbox(frame, width=28, from_=0, to='infinity')
                elif col == 'Jednotky':
                    frame = tk.Frame(self.left_frame)
                    label = tk.Label(frame, text=self.dict_col2humancol[col], width=12)
                    label.pack(side=tk.LEFT, pady=6)
                    entry = ttk.Combobox(frame, width=28, values=self.unit_tuple)             
                    entry.set(self.unit_tuple[0])
                elif col == 'Dodavatel':
                    frame = tk.Frame(self.left_frame)
                    label = tk.Label(frame, text=self.dict_col2humancol[col], width=12)
                    label.pack(side=tk.LEFT, pady=6)
                    entry = ttk.Combobox(frame, width=28, values=self.suppliers)             
                    entry.set(self.suppliers[0])
                else:
                    frame = tk.Frame(self.left_frame)
                    label = tk.Label(frame, text=self.dict_col2humancol[col], width=12)
                label.pack(side=tk.LEFT, pady=6)
                entry.pack(side=tk.RIGHT, padx=2, pady=6)
                self.entries[col] = entry

                
                # Logika pro vložení a konfiguraci entry widgetů              
                match col:
                    case 'Evidencni_cislo':
                        entry.insert(0, str(new_evidencni_cislo))
                        entry.config(state='readonly')  # Zamezení úprav
                    case 'Nazev_dilu':
                        entry.config(background='yellow')                        
                    case 'Interne_cislo':
                        entry.insert(0, str(new_interne_cislo))
                        entry.config(state='readonly')  
                    case 'Mnozstvi_ks_m_l':
                        entry.insert(0, '0')
                        entry.config(state='readonly')  
                    case 'Datum_nakupu':
                        entry.insert(0, aktualni_datum)
                        entry.config(state='readonly')                        
                    case 'Jednotkova_cena_EUR' | 'Celkova_cena_EUR':
                        entry.insert(0, '0.0')
                        entry.config(state='readonly')  
                    case 'Objednano' | 'Cislo_objednavky':
                        entry.config(state='readonly')                      
            frame.pack(fill=tk.X)

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
        self.current_view_instance = None

    def fetch_suppliers(self):
        """
        Získání seznamu dodavatelů z tabulky 'dodavatele'.
        
        :return N-tice seřazených dodavatelů.
        """
        data = self.model.fetch_data('dodavatele')
        suppliers = []
        for row in data:
            suppliers.append(row[1])
        return tuple(sorted(suppliers))
            

    def show_data(self, table):
        """
        Získání a zobrazení dat z vybrané tabulky v GUI. Pokud se mění tabulka k zobrazení,
        vytvoří se nová instance podtřídy View, pokud zůstává tabulka
        stejná, pouze se aktulizují zobrazená data.
        
        :param table: Název tabulky pro zobrazení.
        """
        data = self.model.fetch_data(table)
        col_names = self.model.fetch_col_names(table)

        if self.current_view_instance is None:
            self.current_view_instance = SkladView(self.root, self, col_names, data)
            self.current_table = table
        else:
            if self.current_table != table:
                self.current_table = table
                self.current_view_instance.frame.destroy()
                if table == "sklad":
                    self.current_view_instance = SkladView(self.root, self, col_names, data)
                elif table == "audit_log":
                    self.current_view_instance = AuditLogView(self.root, self, col_names, data)
                elif table == "dodavatele":
                    self.current_view_instance = DodavateleView(self.root, self, col_names, data)

        self.current_view_instance.add_data()


    def show_data_for_editing(self, table, id_num, id_col_name, master, tab2hum, check_columns):
        """
        Získání dat a zobrazení vybrané položky pro úpravu. Pokud se mění tabulka k zobrazení,
        vytvoří se nová instance podtřídy ItemFrameBase, pokud zůstává tabulka stejná,
        pouze se aktulizují zobrazená data.
        
        :param table: Název tabulky pro zobrazení.
        :param id_num: Identifikační číslo položky pro zobrazení.
        """
        item_values = self.model.fetch_item_for_editing(table, id_num, id_col_name)
        col_names = self.model.fetch_col_names(table)

        self.current_item_instance = ItemFrameEdit(master, self, col_names, tab2hum, table, check_columns, self.current_view_instance)
        self.current_item_instance.open_edit_window(item_values)


    def get_max_evidencni_cislo(self):
        """
        Získání nejvyššího evidenčního čísla z tabulky 'sklad'.
        
        :return Nejvyšší hodnotu ve sloupci 'Evidencni_cislo' v tabulce sklad.
        """
        return self.model.get_max_evidencni_cislo()


    def get_max_interne_cislo(self):
        """
        Získání nejvyššího interního čísla z tabulky 'sklad'.
        
        :return Nejvyšší hodnotu ve sloupci 'Interne_cislo' v tabulce sklad.
        """
        return self.model.get_max_interne_cislo()


    def delete_row(self, evidencni_cislo):
        """
        Získání nejvyššího interního čísla z tabulky 'sklad'.
        
        :return Nejvyšší hodnotu ve sloupci 'Interne_cislo' v tabulce sklad.
        """
        self.model.delete_row(evidencni_cislo)


    def export_csv(self, table=None, tree=None):
        """
        Export dat z vybrané tabulky v GUI.
        
        :param table: Název tabulky pro zobrazení.
        """
        csv_file_name = filedialog.asksaveasfilename(defaultextension=".csv",
                                                     filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],)
        if not csv_file_name:
            return

        if tree:
            col_ids = tree["columns"]
            col_names = [tree.heading(col)["text"] for col in col_ids]
            data = [tree.item(item)["values"] for item in tree.get_children()]
        else:    
            col_names = self.model.fetch_col_names(table)
            data = self.model.fetch_data(table)


        try:
            with open(csv_file_name, mode='w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)    
                csv_writer.writerow(col_names)
                for row in data:
                    csv_writer.writerow(row)
            messagebox.showinfo("Export dokončen", f"Data byla úspěšně exportována do souboru '{csv_file_name}'.")
        except Exception as e:
            messagebox.showerror("Chyba při exportu", f"Nastala chyba při exportu dat: {e}")



if __name__ == "__main__":
    root = tk.Tk()
    if sys.platform.startswith('win'):
        root.state('zoomed')
    db_path = 'skladova_databaze.db'
    table = 'sklad' # Startovací tabulka pro zobrazení
    controller = Controller(root, db_path)
    controller.show_data(table)
    root.mainloop()

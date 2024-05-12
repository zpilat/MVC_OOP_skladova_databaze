import sqlite3
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import tkinter.font as tkFont
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


    def fetch_varianty_data(self):
        """
        Načte rozšířená data variant, včetně názvů dílů a dodavatelů z ostatních tabulek.
        
        :return: Data variant spolu s názvy dílů a dodavatelů.
        """
        query = """
        SELECT v.*, s.Nazev_dilu, d.Dodavatel
        FROM varianty v
        JOIN sklad s ON v.id_sklad = s.Evidencni_cislo
        JOIN dodavatele d ON v.id_dodavatele = d.id
        """
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


    def get_max_id(self, curr_table, id_col_name):
        """
        Vrátí nejvyšší hodnotu ID ze zadaného sloupce v zadané tabulce.

        :param curr_table: Název tabulky, ze které se má získat max ID.
        :param id_col_name: Název sloupce, ve kterém se hledá max ID.
        :return: Nejvyšší hodnota ID nebo None, pokud tabulka neobsahuje žádné záznamy.
        """
        query = f"SELECT MAX({id_col_name}) FROM {curr_table}"
        self.cursor.execute(query)
        max_id = self.cursor.fetchone()[0]
        return max_id if max_id is not None else 0


    def get_max_interne_cislo(self):
        """
        Získá nejvyšší hodnotu ve sloupci Interne_cislo z tabulky sklad.
        Pokud v tabulce nejsou žádné záznamy, vrátí se 0 jako výchozí hodnota.
        
        :Return int: Nejvyšší hodnota ve sloupci Interne_cislo nebo 0, pokud neexistují žádné záznamy.
        """
        self.cursor.execute("SELECT MAX(Interne_cislo) FROM sklad")
        max_value = self.cursor.fetchone()[0]
        return max_value if max_value is not None else 0


    def insert_item(self, table, columns, values):
        """
        Vloží novou položku do specifikované tabulky v databázi.

        :param table: Název tabulky, do které se má položka vložit.
        :param columns: Seznam sloupců, do kterých se vkládají hodnoty.
        :param values: Seznam hodnot odpovídajících sloupcům pro vkládání.
        """
        columns_str = ', '.join([f'"{col}"' for col in columns])
        placeholders = ', '.join('?' * len(columns))
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        self.cursor.execute(sql, values)
        self.conn.commit()


    def update_row(self, table, id_num, id_col_name, updated_values):
        """
        Aktualizuje řádek v zadané tabulce databáze na základě ID sloupce a jeho hodnoty.

        :param table: Název tabulky, ve které se má aktualizovat řádek.
        :param id_value: Hodnota ID, podle které se identifikuje řádek k aktualizaci.
        :param id_col_name: Název sloupce, který obsahuje ID pro identifikaci řádku.
        :param updated_values: Slovník, kde klíče jsou názvy sloupců a hodnoty jsou aktualizované hodnoty pro tyto sloupce.
        """
        set_clause = ', '.join([f"`{key}` = ?" for key in updated_values.keys()])
        values = list(updated_values.values())
        values.append(id_num)
        sql = f"UPDATE `{table}` SET {set_clause} WHERE `{id_col_name}` = ?"

        self.cursor.execute(sql, values)
        self.conn.commit()


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
    table_config = {"sklad": {"check_columns": ('Ucetnictvi', 'Kriticky_dil', 'HSH', 'TQ8', 'TQF_XL_I', 'TQF_XL_II', 'DC_XL',
                                                'DAC_XLI_a_II', 'DL_XL', 'DAC', 'LAC_I', 'LAC_II', 'IPSEN_ENE', 'HSH_ENE',
                                                'XL_ENE1', 'XL_ENE2', 'IPSEN_W', 'HSH_W', 'KW', 'KW1', 'KW2', 'KW3'),
                              "hidden_columns": ('Ucetnictvi', 'Kriticky_dil', 'HSH', 'TQ8', 'TQF_XL_I', 'TQF_XL_II', 'DC_XL',
                                                 'DAC_XLI_a_II', 'DL_XL', 'DAC', 'LAC_I', 'LAC_II', 'IPSEN_ENE', 'HSH_ENE',
                                                 'XL_ENE1', 'XL_ENE2', 'IPSEN_W', 'HSH_W', 'KW', 'KW1', 'KW2', 'KW3', 'Objednano'),
                              "special_columns": ('Ucetnictvi', 'Kriticky_dil'),
                              "id_col": 2,
                              "id_col_name": 'Evidencni_cislo',
                              },
                    "audit_log": {"check_columns": ('Ucetnictvi',),
                                  "hidden_columns": ('Objednano', 'Poznamka', 'Cas_operace', 'id'),
                                  "special_columns": ('Ucetnictvi',),
                                  "id_col": 20,
                                  "id_col_name": 'id',
                                  },
                    "dodavatele": {"id_col": 0,
                                   "id_col_name": 'id',
                                   },
                    "varianty": {"id_col": 0,
                                 "id_col_name": 'id',
                                 },
                    }


    def __init__(self, root, controller):
        """
        Inicializace GUI a nastavení hlavního okna.
        
        :param root(tk.Tk): Hlavní okno aplikace.
        :param controller(Controller): Instance kontroleru pro komunikaci mezi modelem a pohledem.
        """
        self.root = root
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
                        'Dodavatel': 'Dodavatel', 'Datum_nakupu': 'Datum nákupu', 'Cislo_objednavky': 'Objednávka',
                        'Jednotkova_cena_EUR': 'EUR/jednotka', 'Celkova_cena_EUR': 'Celkem EUR',
                        'Poznamka': 'Poznámka', 'Zmena_mnozstvi': 'Změna množství', 'Cas_operace': 'Čas operace',
                        'Operaci_provedl': 'Operaci provedl', 'Typ_operace': 'Typ operace',
                        'Datum_vydeje': 'Datum výdeje', 'Pouzite_zarizeni': 'Použité zařízení', 'id': 'ID',
                        'Kontakt': 'Kontaktní osoba', 'E-mail': 'E-mail', 'Telefon': 'Telefon',
                        'Pod_minimem': 'Pod minimem', 'id_sklad': 'Evidenční číslo', 'id_dodavatele': 'ID dodavatele',
                        'Nazev_varianty': 'Název varianty', 'Cislo_varianty': 'Číslo varianty',
                        'Dodaci_lhuta': 'Dodací lhůta', 'Min_obj_mnozstvi': 'Min. obj. množ.'}

        
    def customize_ui(self):
        """
        Přidání specifických menu a framů a labelů pro zobrazení informací o skladu.
        """
        self.curr_table_config = View.table_config[self.current_table]
        self.check_columns = self.curr_table_config.get("check_columns", [])
        self.hidden_columns = self.curr_table_config.get("hidden_columns", [])
        self.special_columns = self.curr_table_config.get("special_columns", [])
        self.id_col = self.curr_table_config["id_col"]
        self.id_col_name = self.curr_table_config["id_col_name"]     
        self.initialize_menu()
        self.initialize_frames()
        self.initialize_searching()
        self.update_menu(self.spec_menus())
        self.update_frames()
        self.initialize_check_buttons()
        self.initialize_treeview(self.tree_frame)
        self.initialize_fonts()
        self.additional_gui_elements()
        self.selected_option = "VŠE"
        self.start_date = None
        self.tree.tag_configure('evenrow', background='#FFFFFF')
        self.tree.tag_configure('oddrow', background='#F5F5F5')
        self.tree.tag_configure('low_stock', foreground='#CD5C5C')
        self.tree.bind('<<TreeviewSelect>>', self.show_selected_item)   
        self.setup_columns(self.col_parameters())    


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
                ("Varianty", lambda: self.controller.show_data('varianty')),
                ("Auditovací log", lambda: self.controller.show_data('audit_log')),
                ("Dodavatelé", lambda: self.controller.show_data('dodavatele')),
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
        self.check_buttons_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.check_buttons_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)        
        self.tree_frame = tk.Frame(self.frame, borderwidth=2, relief="groove")
        self.tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)           
        self.item_frame = tk.Frame(self.frame, width=435, borderwidth=2, relief="groove")
        self.item_frame.pack_propagate(False)
        self.item_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)


    def initialize_searching(self):
        """
        Inicializace políčka a tlačítka pro vyhledávání / filtrování.
        """
        self.search_entry = tk.Entry(self.search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind('<Return>', lambda _: self.controller.show_data(self.current_table))
        self.search_entry.bind("<Escape>", lambda _: self.search_entry.delete(0, tk.END))
        self.search_button = tk.Button(self.search_frame, text="Filtrovat",
                                       command=lambda: self.controller.show_data(self.current_table))
        self.search_button.pack(side=tk.LEFT, padx=5)


    def initialize_check_buttons(self):
        """
        Nastavení specifických checkbuttonů pro filtrování zobrazených položek.
        """
        self.filter_low_stock = tk.BooleanVar(value=False)
        self.filter_columns = {col: tk.BooleanVar(value=False) for col in self.check_columns}

        if self.current_table == 'sklad':
            low_stock_checkbutton = tk.Checkbutton(self.search_frame, text=self.tab2hum['Pod_minimem'],
                                                   variable=self.filter_low_stock, borderwidth=3, relief="groove", onvalue=True,
                                                   offvalue=False, command=lambda: self.controller.show_data(self.current_table))
            low_stock_checkbutton.pack(side='left', padx=5, pady=5)
            
        for col in self.filter_columns:
            if col in self.special_columns:
                checkbutton = tk.Checkbutton(self.search_frame, text=self.tab2hum[col], variable=self.filter_columns[col],
                                             borderwidth=3, relief="groove", onvalue=True, offvalue=False,
                                             command=lambda col=col: self.toggle_filter(col))
            else:
                checkbutton = tk.Checkbutton(self.check_buttons_frame, text=self.tab2hum[col], variable=self.filter_columns[col],
                                             onvalue=True, offvalue=False, command=lambda col=col: self.toggle_filter(col))
            checkbutton.pack(side='left', padx=5, pady=5)


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
   

    def add_data(self, current_data=None):
        """
        Vymazání všech dat v Treeview. Filtrace a třídění dle aktuálních hodnot parametrů.
        Vložení dat do TreeView. Změna hodnot v check_colums z 0/1 na NE/ANO pro zobrazení.
        Zvýraznění řádků pod minimem. Označení první položky v Treeview.
        Třídění podle zakliknuté hlavičky sloupce, při druhém kliknutí na stejný sloupec reverzně.
        """
        if current_data:
            self.current_data = current_data
            
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtered_data = self.filter_data(self.current_data)

        sorted_data = sorted(filtered_data, key=self.sort_key, reverse=self.sort_reverse)

        for idx, row in enumerate(sorted_data):
            row_converted = list(row)
            for index, col in enumerate(self.col_names):
                if col in self.check_columns:
                    row_converted[index] = "ANO" if row[index] == 1 else "NE"               

            item_id = self.tree.insert('', tk.END, values=row_converted)

            stripe_tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            if self.current_table == 'sklad' and int(row[7]) < int(row[4]):
                self.tree.item(item_id, tags=(stripe_tag, 'low_stock',))
            else: self.tree.item(item_id, tags=(stripe_tag,))

        self.mark_first_item()
        

    def filter_data(self, data):
        """
        Vyfiltrování dat podle zadaných dat v search_entry ve všech tabulkách.
        V tabulce sklad navíc dle zaškrtnutých check buttonů a low stock filtru.
        V tabulce audit_log navíc dle comboboxu "VŠE" a v rozmezí datumů v date entry.

        :param data: Data pro filtraci dle search entry.
        :return: Přefiltrovaná data.
        """ 
        search_query = self.search_entry.get()
        if search_query:
            filtered_data = [row for row in data if search_query.lower() in " ".join(map(str, row)).lower()]
        else:
            filtered_data = data

        if self.filter_low_stock.get():
            filtered_data = [row for row in filtered_data if int(row[7]) < int(row[4])]            
        
        if self.current_table == "audit_log":
            if self.selected_option == "PŘÍJEM":
                filtered_data = [row for row in filtered_data if row[8] == "PŘÍJEM"]
            elif self.selected_option == "VÝDEJ":
                filtered_data = [row for row in filtered_data if row[8] == "VÝDEJ"]

        if self.start_date:       
            filtered_data = [row for row in filtered_data if self.start_date <= (row[12] or row[13]) <= self.end_date]
            
        if any(value.get() for value in self.filter_columns.values()):          
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


    def toggle_filter(self, selected_col):
        """
        Metoda pro filtraci dat v tabulce podle zaškrtnutých check buttonů.
        Tato metoda umožňuje zaškrtnout nezávisle checkbuttony ve skupině 'special_group' 
        (Ucetnictvi, Kriticky_dil), zatímco pro ostatní checkbuttony (zařízení) zajišťuje,
        že aktivní může být maximálně jeden z nich. Při aktivaci jednoho z "normálních" 
        checkbuttonů jsou všechny ostatní "normální" checkbuttony odškrtnuty. Metoda aktualizuje 
        stav filtru pro daný sloupec a zobrazuje data podle nově aplikovaného filtru.

        :param selected_col: Název sloupce (check buttonu), který byl zaškrtnut nebo odškrtnut. 
                             Podle tohoto sloupce se určuje, který filtr bude aplikován nebo odstraněn.
        """
        status_of_chb = self.filter_columns[selected_col].get()

        if status_of_chb and selected_col not in self.special_columns:
            for col in self.filter_columns:
                if col not in self.special_columns and col != selected_col:
                    self.filter_columns[col].set(False)
                    
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


    def widget_destroy(self):
        """
        Metoda na vymazání všechn dat z item_frame.
        """
        for widget in self.item_frame.winfo_children():
            widget.destroy()


    def select_item(self, warning_message="Žádná položka k zobrazení."):
        """
        Zkontroluje, zda je ve Treeview vybrána nějaká položka.
        
        :param warning_message: Zpráva, která se zobrazí v messageboxu, pokud není vybrána žádná položka.
        :return: Vrací ID vybrané položky v Treeview, nebo None, pokud žádná položka není vybrána.
        """
        try:
            selected_item = self.tree.selection()[0]
            self.id_num = self.tree.item(selected_item, 'values')[self.id_col]
            return selected_item
        except IndexError:
            messagebox.showwarning("Upozornění", warning_message)
            return None


    def show_selected_item(self, event=None):
        """
        Metoda pro vytvoření instance pro získání dat a zobrazení vybrané položky z treeview.
        """           
        if self.item_frame_show is None:
            self.widget_destroy()
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
        selected_item = self.select_item()
        if selected_item is None: return       
        self.widget_destroy()    
        self.item_frame_show = None
        self.controller.show_data_for_editing(self.current_table, self.id_num, self.id_col_name,
                                                  self.item_frame, self.tab2hum, self.check_columns)


    def add_variant(self):
        """
        Metoda pro získání aktuálních dat z databáze pro vybranou položku a jejich zobrazení
        pro tvorbu nové varianty.
        """
        selected_item = self.select_item()
        if selected_item is None: return
        self.widget_destroy()
        self.item_frame_show = None
        varianty_table = "varianty"
        varianty_check_columns = View.table_config[varianty_table].get("check_columns", [])
        varianty_id_col_name = View.table_config[varianty_table]["id_col_name"]
        self.controller.add_variant(self.current_table, self.id_num, self.id_col_name, self.item_frame,
                                    self.tab2hum, varianty_check_columns, varianty_table, varianty_id_col_name)
      
        
    def add_item(self):
        """
        Metoda pro přidání nové položky do aktuální tabulky.
        """
        self.widget_destroy()                      
        self.item_frame_show = None
        self.id_num = None
        self.controller.add_item(self.current_table, self.id_num, self.id_col_name,
                                     self.item_frame, self.tab2hum, self.check_columns)


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
        self.current_table = 'sklad'
        self.col_names = col_names
        self.customize_ui()


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
                ("Příjem zboží", lambda: self.item_movements(action='prijem')),
                ("Výdej zboží", lambda: self.item_movements(action='vydej')), 
            ],
            "Varianty": [
                ("Přidat variantu", self.add_variant),
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


    def delete_row(self):
        """
        Vymaže označenou položku, pokud je to poslední zadaná položka a je nulový stav.
        """
        selected_item = self.select_item()
        if selected_item is None: return
        last_inserted_item = self.controller.get_max_id(self.current_table, self.id_col_name)
        evidencni_cislo = self.tree.item(self.selected_item)['values'][2]
        mnozstvi_ks_m_l = self.tree.item(self.selected_item)['values'][7]
        if mnozstvi_ks_m_l != 0 or evidencni_cislo != last_inserted_item:
            messagebox.showwarning("Varování", "Lze smazat pouze poslední zadanou položku s nulovým množstvím!")
            return           
        response = messagebox.askyesno("Potvrzení mazání", "Opravdu chcete smazat vybraný řádek?")
        if response: 
            success = self.controller.delete_row(evidencni_cislo)
            self.tree.delete(self.selected_item)
            self.mark_first_item()
            if success:
                messagebox.showinfo("Informace", "Vymazána poslední zadaná položka!")
            else:
                return
            
        self.controller.show_data(self.current_table)
        

    def item_movements(self, action):
        """
        Implementace funkcionality pro příjem a výdej zboží ve skladu.
        """
        selected_item = self.select_item()
        if selected_item is None: return
        self.widget_destroy()            
        self.item_frame_show = None
        self.controller.show_data_for_movements(self.current_table, self.id_num, self.id_col_name,
                                              self.item_frame, self.tab2hum, self.check_columns, action)

    
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
        self.current_table = 'audit_log'
        self.col_names = col_names   
        self.customize_ui()

        
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

        self.options = ["VŠE", "PŘÍJEM", "VÝDEJ"]
        self.operation_combobox = ttk.Combobox(self.search_frame, values=self.options, state="readonly")
        self.operation_combobox.pack(side=tk.LEFT, padx=5, pady=5) 

        self.operation_combobox.set("VŠE")
        self.operation_combobox.bind("<<ComboboxSelected>>", self.on_combobox_change)

        self.month_entry_label = tk.Label(self.search_frame, text="Výběr měsíce:")
        self.month_entry_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.generate_months_list()
        self.month_entry_combobox = ttk.Combobox(self.search_frame, width=12,
                                                 values=["VŠE"]+self.months_list, state="readonly")
        self.month_entry_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.month_entry_combobox.set("VŠE")
        self.month_entry_combobox.bind("<<ComboboxSelected>>", self.on_combobox_date_change)


    def generate_months_list(self):
        """
        Generuje seznam měsíců od ledna 2024 do aktuálního měsíce a roku ve formátu MM-YYYY.
        Výsledkem je seznam řetězců, kde každý řetězec reprezentuje jeden měsíc v požadovaném formátu.
        Aktuální měsíc a rok je vypočítán z aktuálního systémového času a je také zahrnut ve výsledném seznamu.
        Seznam je vhodný pro použití v uživatelském rozhraní jako hodnoty pro výběrový seznam (např. Combobox),
        umožňující uživateli vybrat specifický měsíc a rok.
        """
        current_year = datetime.now().year
        current_month = datetime.now().month
        self.months_list = []

        for year in range(2024, current_year + 1):
            for month in range(1, 13):
                if year == current_year and month > current_month:
                    break
                self.months_list.append(f"{month:02d}-{year}")
        self.months_list.reverse() 


    def on_combobox_date_change(self, event):
        """
        Filtrování zobrazovaných dat v rozsahu počátečního a koncového datumu.
        """
        selected_month_year = self.month_entry_combobox.get()
        if selected_month_year == "VŠE":
            self.start_date=None
            self.end_date=None
        else:
            start_date = datetime.strptime(f"01-{selected_month_year}", "%d-%m-%Y")
            self.start_date = start_date.strftime('%Y-%m-%d')
            month, year = map(int, selected_month_year.split("-"))
            if month == 12:
                end_date = datetime(year, month, 31)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            self.end_date = end_date.strftime('%Y-%m-%d')

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
                    col_params.append({"width": 100, "anchor": "w"})
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
        self.current_table = 'dodavatele'
        self.col_names = col_names
        self.customize_ui()   


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


class VariantyView(View):
    """
    Třída VariantyView pro specifické zobrazení dat z tabulky varianty. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names):
        """
        Inicializace specifického zobrazení pro varianty.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller)
        self.current_table = 'varianty'
        self.col_names = col_names
        self.customize_ui()   


    def spec_menus(self):
        """
        Vytvoření slovníku pro specifická menu dle typu zobrazovaných dat.
        
        :return: Slovník parametrů menu k vytvoření specifických menu.
        """
        specialized_menus = {
            "Varianty": [
                ("Upravit variantu", self.edit_selected_item),
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
                case 'Nazev_varianty':
                    col_params.append({"width": 300, "anchor": "w"})
                case "Nazev_dilu" | "Dodavatel":
                    col_params.append({"width": 200, "anchor": "w", "stretch": tk.YES})
                case _ if col in self.hidden_columns:
                    col_params.append({"width": 0, "minwidth": 0, "stretch": tk.NO})
                case _:    
                    col_params.append({"width": 80, "anchor": "center"})
        return col_params


class ItemFrameBase:
    """
    Třída ItemFrameBase je rodičovská třída pro práci s vybranými položkami.
    """
    table_config = {"sklad": {"order_of_name": 6, "id_col": 2, "id_col_name": "Evidencni_cislo",
                              "quantity_col": 7, "unit_price_col": 33, "focus": 'Nazev_dilu',},
                    "audit_log": {"order_of_name": 4, "id_col": 20, "id_col_name": "id",},
                    "dodavatele": {"order_of_name": 1, "id_col": 0, "id_col_name": "id", "focus": 'Dodavatel',},
                    "varianty": {"order_of_name": 3, "id_col": 0, "id_col_name": "id", "focus": 'Nazev_varianty',},
                    }
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
        self.logged_user = "Janarčin"
        self.unit_tuple = ("ks", "kg", "pár", "l", "m", "balení")
        self.curr_table_config = ItemFrameBase.table_config[self.current_table]


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
        self.top_frame = tk.Frame(self.show_frame, borderwidth=2, relief="groove")
        self.top_frame.pack(side=tk.TOP, fill=tk.X)     
        self.left_frame = tk.Frame(self.top_frame, borderwidth=2, relief="groove")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.right_frame = tk.Frame(self.top_frame, borderwidth=2, relief="groove")
        self.right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.bottom_frame = tk.Frame(self.show_frame)
        self.bottom_frame.pack(side=tk.BOTTOM, pady=2)

        save_btn = tk.Button(self.bottom_frame, width=15, text="Uložit", command=lambda: self.check_before_save(action=action))
        save_btn.pack(side=tk.LEFT, padx=5, pady=5)
        cancel_btn = tk.Button(self.bottom_frame, width=15, text="Zrušit", command=self.current_view_instance.show_selected_item)
        cancel_btn.pack(side=tk.LEFT, padx=5, pady=5)


    def initialize_title(self, add_name_label=True):
        """
        Vytvoření nadpisu dle typu zobrazovaných dat.
        """
        self.title = self.curr_entry_dict["title"]
        self.order_of_name = self.curr_table_config["order_of_name"]

        title_label = tk.Label(self.title_frame, bg="yellow", text=self.title, font=self.custom_font)
        title_label.pack(padx=2, pady=2)
        if add_name_label:
            name_text = f"{self.tab2hum[self.col_names[self.order_of_name]]}: \n {str(self.item_values[self.order_of_name])}"
            name_label = tk.Label(self.title_frame, bg="yellow", wraplength=400, font=self.custom_font, text=name_text)
            name_label.pack(padx=2, pady=2)


    def check_before_save(self, action): 
        """
        Metoda pro kontrolu zadání povinných dat a kontrolu správnosti dat před uložením. 

        :Params action: typ prováděné operace.
        """
        for col in self.curr_entry_dict.get("mandatory", []):
            if not self.entries[col].get():
                messagebox.showwarning("Chyba", f"Před uložením nejdříve zadejte položku {self.tab2hum[col]}")
                self.entries[col].focus()
                return
            
        for col in self.curr_entry_dict.get("not_neg_integer", []):
            entry_val = self.entries[col].get()
            if not entry_val.isdigit() or int(entry_val) < 0:
                messagebox.showwarning("Chyba", f"Položka {self.tab2hum[col]} musí být celé nezáporné číslo.")
                self.entries[col].focus()
                return
            
        for col in set(self.curr_entry_dict.get("pos_real", [])).union(self.curr_entry_dict.get("not_neg_real", [])):
            entry_val = self.entries[col].get()
            if entry_val:
                try:
                    float_entry_val = float(entry_val)
                    if col in self.curr_entry_dict.get("pos_real", []) and float_entry_val <= 0:
                        messagebox.showwarning("Chyba", f"Položka {self.tab2hum[col]} musí být kladné reálné číslo s desetinnou tečkou.")
                        return
                    if col in self.curr_entry_dict.get("not_neg_real", []) and float_entry_val < 0:
                        messagebox.showwarning("Chyba", f"Položka {self.tab2hum[col]} musí být nezáporné reálné číslo s desetinnou tečkou.")
                        return 
                except ValueError:
                    messagebox.showwarning("Chyba", f"Položka {self.tab2hum[col]} není platné reálné číslo s desetinnou tečkou.")
                    return

        if self.current_table=='varianty':
            id_sklad_value = self.entries['id_sklad'].get()
            dodavatel_value = self.entries['Dodavatel'].get()
            print(id_sklad_value, dodavatel_value)
            return
            
        self.save_item(action, self.id_num)


    def save_item(self, action, selected_item_id):
        """
        Metoda na uložení nových / upravených dat v databázi.

        :Params action: typ prováděné operace.
        :Params selected_item_id: v případě akce "edit" je to vybrané ID položky k editaci.
        """
        self.entry_values = {}
        for col, entry in self.entries.items():
            self.entry_values[col] = entry.get()
        
        self.checkbutton_values = {col: (1 if state.get() else 0) for col, state in self.checkbutton_states.items()}
        combined_values = {**self.entry_values, **self.checkbutton_values}
        values_to_insert = [combined_values[col] for col in self.col_names]
                
        if action == "add":
            success = self.controller.insert_new_item(self.current_table, self.col_names, values_to_insert)
        elif action == "edit" and selected_item_id is not None:
            success = self.controller.update_row(self.current_table, selected_item_id, self.curr_table_config["id_col_name"], combined_values)
        if not success:
            return
            
        self.controller.show_data(self.current_table)

    def show_for_editing(self):
        """
        Metoda pro zobrazení vybrané položky z Treeview ve frame item_frame pro editaci údajú.
        Název položky je v title_frame, zbylé informace v show_frame
        """        
        self.entries = {}
        self.checkbutton_states = {}
                  
        for index, col in enumerate(self.col_names):
            if col in self.check_columns:
                frame = tk.Frame(self.right_frame)
                if self.item_values:
                    self.checkbutton_states[col] = tk.BooleanVar(value=self.item_values[index] == 1)
                else:
                    self.checkbutton_states[col] = tk.BooleanVar(value=True) if col == 'Ucetnictvi' else tk.BooleanVar(value=False)
                checkbutton = tk.Checkbutton(frame, text=self.tab2hum[col], variable=self.checkbutton_states[col])
                if (col == 'Ucetnictvi' or col == 'Kriticky_dil'):            
                    checkbutton.config(borderwidth=3, relief="groove")
                checkbutton.pack(side=tk.LEFT, padx=5)
            else:
                frame = tk.Frame(self.left_frame)
                label = tk.Label(frame, text=self.tab2hum[col], width=12)
                start_value = self.item_values[index] if self.item_values else ""
                match col:                          
                    case 'Min_Mnozstvi_ks' | 'Min_obj_mnozstvi':
                        entry = tk.Spinbox(frame, width=32, from_=0, to='infinity')
                        if self.item_values:
                            entry.delete(0, "end")
                            entry.insert(0, self.item_values[index])                
                    case 'Jednotky':
                        entry = ttk.Combobox(frame, width=31, values=self.unit_tuple)
                        entry.set(start_value)                         
                    case 'Dodavatel' if self.current_table=='sklad' or self.current_table=='varianty':
                        entry = ttk.Combobox(frame, width=31, values=self.suppliers)
                        entry.set(start_value)                    
                    case _:
                        entry = tk.Entry(frame, width=34)
                        if self.item_values:
                            entry.insert(0, self.item_values[index])                                              
                label.pack(side=tk.LEFT)
                entry.pack(side=tk.LEFT, padx=2, pady=3)
                entry.bind('<Return>', lambda event: self.check_before_save(action=self.action))
                entry.bind('<Escape>', lambda event: self.current_view_instance.show_selected_item())
                self.entries[col] = entry
                if col in self.curr_entry_dict.get("mandatory", []): entry.config(background='yellow') 
                if col in self.curr_entry_dict.get("insert", []): entry.insert(0, self.curr_entry_dict["insert"][col])
                if col in self.curr_entry_dict.get("read_only", []): entry.config(state='readonly')
                if col in self.curr_entry_dict.get("pack_forget", []):
                    label.pack_forget()
                    entry.pack_forget()
            frame.pack(fill=tk.X)
        self.entries[self.curr_table_config["focus"]].focus()
  

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


    def clear_item_frame(self):
        """
        Odstranění všech widgetů v title_frame a show_frame
        """
        for widget in self.title_frame.winfo_children():
            widget.destroy()
        for widget in self.show_frame.winfo_children():
            widget.destroy()  

    def init_curr_dict(self):
        """
        Metoda pro přidání slovníku hodnotami přiřazenými dle aktuální tabulky.
        """        
        self.entry_dict = {"sklad": {"title": "ZOBRAZENÍ SKLADOVÉ KARTY"},
                           "audit_log": {"title": "ZOBRAZENÍ POHYBU NA SKLADĚ"},
                           "dodavatele": {"title": "ZOBRAZENÍ DODAVATELE"},
                           "varianty": {"title": "ZOBRAZENÍ VARIANTY"},
                           }
        self.curr_entry_dict = self.entry_dict[self.current_table]
                           

    def show_selected_item_details(self, item_values):
        """
        Metoda pro zobrazení vybrané položky z Treeview ve frame item_frame
        Název položky je v title_frame, zbylé informace v show_frame
        """
        self.item_values = item_values   
        self.clear_item_frame()
        self.init_curr_dict()
        self.initialize_title()
          
        for index, value in enumerate(self.item_values):
            if index == self.order_of_name: continue   # Vynechá název
            idx = index - 1 if index > self.order_of_name else index 
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
        super().__init__(master, controller, col_names, tab2hum, current_table, check_columns)
        self.current_view_instance = current_view_instance
        self.action = 'edit'
        self.update_frames(action=self.action)
        
       
    def init_curr_dict(self):
        """
        Metoda pro přidání slovníku hodnotami přiřazenými dle aktuální tabulky.
        """
        self.entry_dict = {"sklad": {"title": "ÚPRAVA SKLADOVÉ KARTY",
                                     "read_only": ('Evidencni_cislo', 'Mnozstvi_ks_m_l', 'Jednotky', 'Dodavatel',
                                                   'Min_Mnozstvi_ks', 'Datum_nakupu', 'Jednotkova_cena_EUR',
                                                   'Celkova_cena_EUR'),
                                     "mandatory": ('Nazev_dilu',),
                                     "not_neg_integer": ('Interne_cislo',),
                                     },
                           
                           "dodavatele": {"title": "ÚPRAVA DODAVATELE",
                                          "read_only": ('id', 'Dodavatel'),
                                          },
                           "varianty": {"title": "ÚPRAVA VARIANTY",
                                        "read_only": ('id', 'id_sklad', 'id_dodavatele',),
                                        "mandatory": ('Nazev_varianty', 'Cislo_varianty',),
                                        "pos_real":('Jednotkova_cena_EUR',),
                                        "not_neg_integer": ('Dodaci_lhuta', 'Min_obj_mnozstvi'),
                                        }
                           }
        self.curr_entry_dict = self.entry_dict[self.current_table]


    def open_edit_window(self, item_values):
        """
        Metoda pro úpravu vybrané položky z Treeview.

        :params item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
        """
        self.item_values = item_values
        self.init_curr_dict()        
        self.initialize_title()       
        self.id_num = self.item_values[self.curr_table_config["id_col"]]
        self.show_for_editing()



class ItemFrameAdd(ItemFrameBase):
    """
    Třída ItemFrameAdd se stará o tvorbu nových položek.
    """
    def __init__(self, master, controller, col_names, tab2hum, current_table, check_columns, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, tab2hum, current_table, check_columns)
        self.current_view_instance = current_view_instance
        self.id_num = None
        self.action = 'add'
        self.update_frames(action=self.action)        


    def init_curr_dict(self):
        """
        Metoda pro přidání slovníku hodnotami přiřazenými dle aktuální tabulky.
        """
        self.actual_date = datetime.now().strftime("%Y-%m-%d")
        self.entry_dict = {"sklad": {"title": "VYTVOŘENÍ  SKLADOVÉ KARTY",
                                     "read_only": ('Evidencni_cislo', 'Interne_cislo', 'Mnozstvi_ks_m_l', 'Jednotkova_cena_EUR',
                                                   'Celkova_cena_EUR', 'Objednano', 'Cislo_objednavky', 'Jednotky', 'Dodavatel',
                                                   'Min_Mnozstvi_ks'),
                                     "pack_forget": ('Objednano', 'Mnozstvi_ks_m_l', 'Datum_nakupu', 'Cislo_objednavky',
                                                     'Jednotkova_cena_EUR', 'Celkova_cena_EUR'),
                                     "insert": {'Evidencni_cislo': self.new_id, 'Interne_cislo': self.new_interne_cislo, 'Mnozstvi_ks_m_l': '0',
                                                'Jednotkova_cena_EUR': '0.0', 'Celkova_cena_EUR': '0.0'},
                                     "mandatory": ('Nazev_dilu', 'Jednotky'),
                                     },                                 
                           "dodavatele": {"title": "VYTVOŘENÍ DODAVATELE",
                                          "read_only": ('id',),
                                          "pack_forget": (),
                                          "insert": {'id': self.new_id},
                                          "mandatory": ('Dodavatel',),
                                          },
                           "varianty": {"title": "VYTVOŘENÍ VARIANTY",
                                        "read_only": ('id','Nazev_dilu', 'id_sklad', 'id_dodavatele', 'Dodavatel'),
                                        "mandatory": ('Nazev_varianty', 'Cislo_varianty'),
                                        "insert": {'Dodaci_lhuta': 0, 'Min_obj_mnozstvi':0,},
                                        "not_neg_real":('Jednotkova_cena_EUR',),
                                        "not_neg_integer": ('Dodaci_lhuta', 'Min_obj_mnozstvi'),
                                        "pack_forget": ('id_dodavatele',),
                                        "calculate": ('id_dodavatele',),
                                        },
                           }
        self.curr_entry_dict = self.entry_dict[self.current_table]


    def add_item(self, new_id, new_interne_cislo):
        """
        Metoda pro přidání nové položky do aktuální tabulky.
        """
        self.item_values = None
        self.new_id = new_id
        self.new_interne_cislo = new_interne_cislo
        self.init_curr_dict()
        self.initialize_title(add_name_label=False)
        self.show_for_editing()


    def add_variant(self, item_values):
        """
        Metoda pro vytvoření nové varianty podle vybrané položky z Treeview.
        Název položky je v title_frame, zbylé informace v show_frame

        :params item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.        
        """        
        self.entries = {}
        self.new_id = None
        self.new_interne_cislo = None
        self.item_values = item_values
        self.init_curr_dict()        
        self.initialize_title(add_name_label=False)       
        self.show_for_editing()
                

class ItemFrameMovements(ItemFrameBase):
    """
    Třída ItemFrameMovements se stará o příjem a výdej ve skladě.
    """
    def __init__(self, master, controller, col_names, tab2hum, current_table, check_columns, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, tab2hum, current_table, check_columns)
        self.current_view_instance = current_view_instance
        
       
    def init_curr_dict(self):
        """
        Metoda pro přidání slovníku hodnotami přiřazenými dle aktuální tabulky.
        """
        self.actual_date = datetime.now().strftime("%Y-%m-%d")
        self.action_dict = {
            "sklad": {"prijem": {"grid_forget": ('Nazev_dilu', 'Celkova_cena_EUR', 'Pouzite_zarizeni',
                                                 'Datum_vydeje', 'Cas_operace', 'id'),
                                 "mandatory": ('Zmena_mnozstvi', 'Umisteni', 'Dodavatel', 'Cislo_objednavky'),
                                 "date":('Datum_nakupu',),
                                 "pos_real": ('Jednotkova_cena_EUR',),
                                 "pos_integer":('Zmena_mnozstvi',),
                                 "actual_value": {'Typ_operace': "PŘÍJEM", 'Operaci_provedl': self.logged_user,
                                                  'Datum_nakupu': self.actual_date, 'Datum_vydeje': "",},
                                 "tuple_values_to_save": ('Objednano', 'Mnozstvi_ks_m_l', 'Umisteni', 'Dodavatel', 'Datum_nakupu',
                                                          'Cislo_objednavky', 'Jednotkova_cena_EUR', 'Celkova_cena_EUR', 'Poznamka'),
                                 },
                      "vydej": {"grid_forget": ('Nazev_dilu', 'Celkova_cena_EUR', 'Objednano', 'Dodavatel', 'Cas_operace',
                                                'Cislo_objednavky', 'Jednotkova_cena_EUR', 'Datum_nakupu', 'id'),
                                "mandatory": ('Zmena_mnozstvi', 'Pouzite_zarizeni', 'Umisteni'),
                                "date":('Datum_vydeje',),
                                "pos_integer":('Zmena_mnozstvi',),
                                "actual_value": {'Typ_operace': "VÝDEJ", 'Operaci_provedl': self.logged_user,
                                                  'Datum_nakupu': "", 'Datum_vydeje': self.actual_date,},
                                "tuple_values_to_save": ('Mnozstvi_ks_m_l', 'Umisteni', 'Poznamka', 'Celkova_cena_EUR'),
                                },
                      },
            }              
        self.title = self.action_dict[self.current_table][self.action]["actual_value"]['Typ_operace']
        self.entry_dict = {"sklad": {"title": f"{self.title} ZBOŽÍ",
                                     "read_only": ('Ucetnictvi', 'Evidencni_cislo', 'Interne_cislo', 'Jednotky',
                                                   'Mnozstvi_ks_m_l', 'Typ_operace', 'Operaci_provedl', 'Pouzite_zarizeni',
                                                   'Dodavatel'),
                                     "insert_item_value": ('Ucetnictvi', 'Evidencni_cislo', 'Interne_cislo', 'Jednotky',
                                                           'Mnozstvi_ks_m_l', 'Umisteni', 'Jednotkova_cena_EUR', 'Objednano',
                                                           'Poznamka', 'Nazev_dilu'),
                                     },
                           }  
        self.curr_entry_dict = self.entry_dict[self.current_table] | self.action_dict[self.current_table][self.action]
        self.devices = ('HSH', 'TQ8', 'TQF_XL_I', 'TQF_XL_II', 'DC_XL', 'DAC_XLI_a_II', 'DL_XL', 'DAC', 'LAC_I',
                        'LAC_II', 'IPSEN_ENE', 'HSH_ENE', 'XL_ENE1', 'XL_ENE2', 'IPSEN_W', 'HSH_W', 'KW', 'KW1',
                        'KW2', 'KW3', 'Ostatní')


    def enter_item_movements(self, action, item_values, audit_log_col_names):
        """
        Metoda pro příjem a výdej skladových položek.

        :params action: Parametr s názvem akce příjem nebo výdej zboží - "prijem", "vydej".
        :params item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
        """
        self.action = action
        self.item_values = item_values
        self.audit_log_col_names = audit_log_col_names
        self.init_curr_dict()
        self.initialize_title()
        self.update_frames(action=self.action)         
        self.id_num = self.item_values[self.curr_table_config["id_col"]]
        self.id_col_name = self.curr_table_config["id_col_name"]
        self.entries_al = {}
        self.actual_quantity = int(self.item_values[self.curr_table_config["quantity_col"]])
        self.actual_unit_price = float(self.item_values[self.curr_table_config["unit_price_col"]])
       
        if self.action=='vydej' and self.actual_quantity==0:
            self.current_view_instance.show_selected_item()
            messagebox.showwarning("Chyba", f"Položka aktuálně není na skladě, nelze provést výdej!")
            return
        
        for idx, col in enumerate(self.audit_log_col_names):
            if col in self.col_names:
                index = self.col_names.index(col) 
            label = tk.Label(self.left_frame, text=self.tab2hum[col], width=20)
            label.grid(row=idx, column=0, sticky="nsew", padx=5, pady=2)
            if col == 'Pouzite_zarizeni':
                entry_al = ttk.Combobox(self.left_frame, width=37, values=self.devices)             
                entry_al.set("")
            elif col == 'Dodavatel':
                entry_al = ttk.Combobox(self.left_frame, width=37, values=self.suppliers)
                entry_al.set(self.item_values[index])
            else:
                entry_al = tk.Entry(self.left_frame, width=40)                        
            entry_al.grid(row=idx, column=1, sticky="nsew", padx=5, pady=2)
            entry_al.bind('<Return>', lambda event: self.check_before_save(action=self.action))
            entry_al.bind('<Escape>', lambda event: self.current_view_instance.show_selected_item())
            
            if col in self.curr_entry_dict.get("mandatory",[]): entry_al.config(background='yellow')
            if col in self.curr_entry_dict.get("insert_item_value",[]): entry_al.insert(0, self.item_values[index])        
            if col in self.curr_entry_dict.get("actual_value",[]): entry_al.insert(0, self.curr_entry_dict["actual_value"][col])
            if col in self.curr_entry_dict.get("read_only",[]): entry_al.config(state='readonly')                
            if col in self.curr_entry_dict.get("grid_forget",[]):
                label.grid_forget()
                entry_al.grid_forget()
            self.entries_al[col] = entry_al
        self.entries_al['Zmena_mnozstvi'].focus()


    def show_warning(self, col, warning):
        """
        Metoda pro vypsání varování a zaměření pozornosti na vstupní pole s chybným zadáním.

        :parames col: název nesprávně zadané položky.
        :parames warning: text vypsaného varování.
        """
        messagebox.showwarning("Chyba", warning)
        self.entries_al[col].focus()


    def check_before_save(self, action): 
        """
        Metoda pro kontrolu zadání povinných dat a kontrolu správnosti dat před uložením. 

        :Params action: typ prováděné operace.
        """
        self.action = action
        
        for col in self.curr_entry_dict.get("mandatory", []):
            if not self.entries_al[col].get():
                self.show_warning(col, f"Před uložením nejdříve zadejte položku {self.tab2hum[col]}")
                return
            
        for col in self.curr_entry_dict.get("pos_integer", []):
            entry_val = self.entries_al[col].get()
            if not entry_val.isdigit() or int(entry_val) <= 0:
                self.show_warning(col, f"Položka {self.tab2hum[col]} musí být kladné celé číslo.")
                return

        self.quantity_change = int(self.entries_al['Zmena_mnozstvi'].get())
        self.quantity = int(self.entries_al['Mnozstvi_ks_m_l'].get())

        if self.action=='vydej' and self.quantity_change > self.quantity:
                self.show_warning('Zmena_mnozstvi', "Vydávané množství je větší než množství na skladě.")
                return

        for col in self.curr_entry_dict.get("pos_real", []):
            entry_val = self.entries_al[col].get()
            try:
                float_entry_val = float(entry_val)
                if float_entry_val <= 0:
                    self.show_warning(col, f"Položka {self.tab2hum[col]} musí být kladné reálné číslo s desetinnou tečkou.")
                    return
            except ValueError:
                self.show_warning(col, f"Položka {self.tab2hum[col]} není platné kladné reálné číslo s desetinnou tečkou.")
                return

        for col in self.curr_entry_dict.get("date", []):
            date_str = self.entries_al[col].get()
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                self.show_warning(col, "Datum nákupu musí být ve formátu RRRR-MM-DD.")
                return
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                self.show_warning(col, f"Neplatné datum: {date_str}. Zadejte prosím platné datum.")
                return
            
        self.calculate_before_save_to_audit_log() 
        self.calculate_before_save_to_sklad()
        success = self.controller.update_row("sklad", self.id_num, self.id_col_name, self.values_to_sklad)
        if not success:
            return
        success = self.controller.insert_new_item("audit_log", self.audit_log_col_names[:-1], self.values_to_audit_log[:-1])
        if not success:
            return
        messagebox.showinfo("Informace", f"Úspěšně proběhl {self.title.lower()} a zápis do audit logu!")

        self.controller.show_data(self.current_table)
        

    def calculate_before_save_to_audit_log(self):
        """
        Vypočítá hodnoty před uložením do audit logu.
        
        Tato metoda upraví hodnoty pro změnu množství, jednotkovou cenu a celkovou cenu operace,
        a také aktualizuje nové množství na skladě. Výsledné hodnoty jsou připraveny k uložení do audit logu.
        """
        self.new_unit_price = float(self.entries_al['Jednotkova_cena_EUR'].get())
        
        if self.action == 'vydej': 
            self.quantity_change = -self.quantity_change
        self.total_price = self.new_unit_price * self.quantity_change
        self.new_quantity = self.quantity + self.quantity_change

        self.values = {col: entry_al.get() for col, entry_al in self.entries_al.items()}
        self.values['Cas_operace'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")    
        self.values['Zmena_mnozstvi'] = self.quantity_change
        self.values['Celkova_cena_EUR'] = self.total_price
        self.values['Mnozstvi_ks_m_l'] = self.new_quantity
        
        self.values_to_audit_log = [self.values[col] for col in self.audit_log_col_names]
        

    def calculate_before_save_to_sklad(self):
        """
        Upravuje a připravuje hodnoty pro uložení do tabulky sklad v závislosti na provedené akci (příjem/výdej).

        Výpočet nové celkové ceny a průměrné jednotkové ceny pro příjem a aktualizace celkové ceny pro výdej.
        Změny jsou reflektovány ve slovníku `self.values`, který je poté použit pro aktualizaci záznamu v databázi.
        """
        if self.action == 'prijem':
            if self.actual_quantity > 0:
                new_total_price = round(self.actual_quantity*self.actual_unit_price+self.quantity_change*self.new_unit_price, 1)
                average_unit_price = round(new_total_price / (self.actual_quantity + self.quantity_change), 2)
                self.values['Celkova_cena_EUR'] = new_total_price
                self.values['Jednotkova_cena_EUR'] = average_unit_price
        elif self.action == 'vydej': 
            self.values['Celkova_cena_EUR'] = round(self.new_quantity * self.actual_unit_price, 1)

        self.values_to_sklad = {col: self.values[col] for col in self.curr_entry_dict["tuple_values_to_save"] if col in self.values}



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


    def get_max_id(self, curr_table, id_col_name):
        """
        Získání nejvyššího evidenčního čísla z tabulky 'sklad'.

        :param id_col: Číslo sloupce, ve kterém jsou id čísla pro danou tabulku.
        :return Nejvyšší hodnotu ve sloupci 'Evidencni_cislo' v tabulce sklad.
        """
        return self.model.get_max_id(curr_table, id_col_name)
    

    def show_data(self, table):
        """
        Získání a zobrazení dat z vybrané tabulky v GUI. Pokud se mění tabulka k zobrazení,
        vytvoří se nová instance podtřídy View, pokud zůstává tabulka
        stejná, pouze se aktulizují zobrazená data.
        
        :param table: Název tabulky pro zobrazení.
        """
        if table == 'varianty':
            data = self.model.fetch_varianty_data()
            col_names = list(self.model.fetch_col_names(table)) + ["Nazev_dilu", "Dodavatel"]
        else:
            data = self.model.fetch_data(table)
            col_names = self.model.fetch_col_names(table)

        if self.current_view_instance is None:
            self.current_view_instance = SkladView(self.root, self, col_names)
            self.current_table = table
        else:
            if self.current_table != table:
                self.current_table = table
                self.current_view_instance.frame.destroy()
                if table == "sklad":
                    self.current_view_instance = SkladView(self.root, self, col_names)
                elif table == "audit_log":
                    self.current_view_instance = AuditLogView(self.root, self, col_names)
                elif table == "dodavatele":
                    self.current_view_instance = DodavateleView(self.root, self, col_names)
                elif table == "varianty":
                    self.current_view_instance = VariantyView(self.root, self, col_names)

        self.current_view_instance.add_data(current_data=data)


    def show_data_for_editing(self, table, id_num, id_col_name, master, tab2hum, check_columns):
        """
        Získání dat a zobrazení vybrané položky pro úpravu. Vytvoří se nová instance ItemFrameEdit.
        
        :param table: Název tabulky pro zobrazení.
        :param id_num: Identifikační číslo položky pro zobrazení.
        """
        item_values = self.model.fetch_item_for_editing(table, id_num, id_col_name)
        col_names = self.model.fetch_col_names(table)
        
        self.current_item_instance = ItemFrameEdit(master, self, col_names, tab2hum, table,
                                                       check_columns, self.current_view_instance)
        self.current_item_instance.open_edit_window(item_values)    


    def show_data_for_movements(self, table, id_num, id_col_name, master, tab2hum, check_columns, action):
        """
        Získání dat a zobrazení vybrané položky pro skladový pohyb. Vytvoří se nová instance ItemFrameMovements.
        
        :param table: Název tabulky pro zobrazení.
        :param id_num: Identifikační číslo položky pro zobrazení.
        """
        item_values = self.model.fetch_item_for_editing(table, id_num, id_col_name)
        col_names = self.model.fetch_col_names(table)
        audit_log_col_names = self.model.fetch_col_names("audit_log")

        self.current_item_instance = ItemFrameMovements(master, self, col_names, tab2hum, table, check_columns, self.current_view_instance)
        self.current_item_instance.enter_item_movements(action, item_values, audit_log_col_names)


    def add_item(self, table, id_num, id_col_name, master, tab2hum, check_columns):
        """
        Získání dat a zobrazení vybrané položky pro úpravu. Pokud se mění tabulka k zobrazení,
        vytvoří se nová instance podtřídy ItemFrameBase, pokud zůstává tabulka stejná,
        pouze se aktulizují zobrazená data.
        
        :param table: Název tabulky pro zobrazení.
        :param id_num: Identifikační číslo položky pro zobrazení.
        """
        new_interne_cislo = str(self.model.get_max_interne_cislo() + 1) if table=="sklad" else None
        new_id = str(self.model.get_max_id(table, id_col_name) + 1)
        col_names = self.model.fetch_col_names(table)
        
        self.current_item_instance = ItemFrameAdd(master, self, col_names, tab2hum, table, check_columns, self.current_view_instance)
        self.current_item_instance.add_item(new_id, new_interne_cislo)


    def add_variant(self, table, id_num, id_col_name, master, tab2hum, varianty_check_columns, varianty_table, varianty_id_col_name):
        """
        Získání dat a zobrazení vybrané položky pro vytvoření nové varianty.
        
        :param table: Název tabulky pro zobrazení.
        :param id_num: Identifikační číslo položky pro zobrazení.
        """
        sklad_item_values = self.model.fetch_item_for_editing(table, id_num, id_col_name)
        sklad_col_names = self.model.fetch_col_names(table)
        sklad_values_dict = {keys: values for keys, values in zip(sklad_col_names, sklad_item_values)}
        varianty_col_names = list(self.model.fetch_col_names(varianty_table)) + ["Nazev_dilu", "Dodavatel"]
        new_id = str(self.model.get_max_id(varianty_table, varianty_id_col_name) + 1)
        varianty_item_values = [sklad_values_dict.get(col, "") for col in varianty_col_names]
        varianty_item_values[0] = new_id
        varianty_item_values[1] = sklad_values_dict['Evidencni_cislo']
                                         
        self.current_item_instance = ItemFrameAdd(master, self, varianty_col_names, tab2hum, varianty_table,
                                                   varianty_check_columns, self.current_view_instance)
        self.current_item_instance.add_variant(varianty_item_values)         


    def insert_new_item(self, table, columns, values_to_insert):
        """
        Pokusí se vložit novou položku do zadané tabulky databáze. Pokud operace selže kvůli
        porušení omezení integrity (např. pokusu o vložení položky s již existujícím
        unikátním identifikátorem), zobrazí se uživatelské varování.

        :param table: Název tabulky v databázi, do které se má vložit nová položka.
        :param columns: Seznam názvů sloupců, do kterých se mají vložit hodnoty.
        :param values_to_insert: Seznam hodnot odpovídajících názvům sloupců v `columns`, které se mají vložit.
        :return: Vrátí True, pokud byla položka úspěšně vložena. V případě, že operace selže kvůli
                 porušení omezení integrity, zobrazí varování a vrátí False.
        """
        try:
            self.model.insert_item(table, columns, values_to_insert)
        except sqlite3.IntegrityError:
            messagebox.showwarning("Varování", "Položka se zadaným evidenčním číslem už v databázi existuje.")
            return False
        return True     


    def update_row(self, table, selected_item_id, id_col_name, combined_values):
        """
        Aktualizuje položku v zadané tabulce databáze na základě jejího identifikátoru.

        :param table: Název tabulky, ve které se má aktualizovat položka.
        :param selected_item_id: Hodnota identifikátoru (ID) položky, která se má aktualizovat.
        :param id_col_name: Název sloupce, který obsahuje ID položky.
        :param combined_values: Slovník obsahující aktualizované hodnoty položky, kde klíče jsou názvy sloupců a hodnoty jsou nové hodnoty pro tyto sloupce.
        :return: Vrací True, pokud aktualizace proběhla úspěšně, jinak False.
        """
        try:
            self.model.update_row(table, selected_item_id, id_col_name, combined_values)
        except Exception as e:
            messagebox.showwarning("Varování", f"Chyba při ukládání dat do databáze: {e}!")
            return False
        return True


    def delete_row(self, evidencni_cislo):
        """
        Vymazání položky vybrané v treeview - pouze nulová poslední zadaná položka.
        """
        try:
            self.model.delete_row(evidencni_cislo)
        except Exception as e:
            messagebox.showwarning("Varování", f"Chyba při ukládání dat do databáze: {e}!")
            return False
        return True
    

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
    root.title('Zobrazení databáze HPM HEAT SK - verze 0.65 MVC OOP')
    if sys.platform.startswith('win'):
        root.state('zoomed')
    db_path = 'skladova_databaze.db'
    table = 'sklad' # Startovací tabulka pro zobrazení
    controller = Controller(root, db_path)
    controller.show_data(table)
    root.mainloop()

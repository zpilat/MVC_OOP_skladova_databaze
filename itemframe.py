import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import tkinter.font as tkFont
from datetime import datetime, timedelta

from commonresources import CommonResources

class ItemFrameBase:
    """
    Třída ItemFrameBase je rodičovská třída pro práci s vybranými položkami.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, action):
        """
        Inicializace prvků v item_frame.
        
        :param master: Hlavní frame item_frame, kde se zobrazují informace o položkách.
        :param tree: Treeview, ve kterém se vybere zobrazovaná položka.
        :param col_names: Názvy sloupců zobrazované položky.
        :param current_table: Aktuálně otevřená tabulka databáze.
        """
        self.master = master
        self.controller = controller
        self.col_names = col_names
        self.tab2hum = CommonResources.tab2hum
        self.current_table = current_table
        self.check_columns = check_columns
        self.action = action
        self.suppliers_dict = self.controller.fetch_dict("dodavatele")
        self.suppliers = tuple(sorted(self.suppliers_dict.keys()))
        self.current_user = self.controller.current_user
        self.name_of_user = self.controller.name_of_user
        self.unit_tuple = ("ks", "kg", "pár", "l", "m", "balení")
        self.curr_table_config = CommonResources.item_frame_table_config[self.current_table]
        self.special_columns = ('Ucetnictvi', 'Kriticky_dil', 'Pod_minimem')
        self.new_id = None
        self.new_interne_cislo = None
        self.actual_date = datetime.now().strftime("%Y-%m-%d")

        self.initialize_fonts()
        self.initialize_frames()


    def initialize_current_entry_dict(self):
        """
        Slovníky pro specifická menu a kontextové menu pro danou tabulku.
        """ 
        entry_dict = {
            "sklad": {
                "edit": {
                    "read_only": ('Evidencni_cislo', 'Mnozstvi_ks_m_l', 'Jednotky', 'Dodavatel',
                                  'Datum_nakupu', 'Jednotkova_cena_EUR', 'Celkova_cena_EUR'),
                    "mandatory": ('Min_Mnozstvi_ks', 'Nazev_dilu',),
                    "not_neg_integer": ('Interne_cislo', 'Min_Mnozstvi_ks',),
                    },
                "add": {
                    "read_only": ('Evidencni_cislo', 'Interne_cislo', 'Mnozstvi_ks_m_l', 'Jednotkova_cena_EUR',
                                  'Celkova_cena_EUR', 'Objednano', 'Cislo_objednavky', 'Jednotky', 'Dodavatel',),
                    "pack_forget": ('Objednano', 'Mnozstvi_ks_m_l', 'Datum_nakupu', 'Cislo_objednavky',
                                    'Jednotkova_cena_EUR', 'Celkova_cena_EUR',),
                    "insert": {'Evidencni_cislo': self.new_id, 'Interne_cislo': self.new_interne_cislo, 'Mnozstvi_ks_m_l': '0',
                               'Jednotkova_cena_EUR': '0.0', 'Celkova_cena_EUR': '0.0',},
                    "mandatory": ('Min_Mnozstvi_ks', 'Nazev_dilu', 'Jednotky',),
                    "not_neg_integer":('Min_Mnozstvi_ks',),
                    },
                "prijem": {
                    "grid_forget": ('Nazev_dilu', 'Celkova_cena_EUR', 'Pouzite_zarizeni',
                                    'Datum_vydeje', 'Cas_operace', 'id'),
                    "mandatory": ('Zmena_mnozstvi', 'Umisteni', 'Dodavatel', 'Cislo_objednavky'),
                    "date": ('Datum_nakupu',),
                    "pos_real": ('Jednotkova_cena_EUR',),
                    "pos_integer":('Zmena_mnozstvi',),
                    "actual_value": {'Typ_operace': "PŘÍJEM", 'Operaci_provedl': self.name_of_user,
                                     'Datum_nakupu': self.actual_date, 'Datum_vydeje': "",},
                    "tuple_values_to_save": ('Objednano', 'Mnozstvi_ks_m_l', 'Umisteni', 'Dodavatel', 'Datum_nakupu',
                                             'Cislo_objednavky', 'Jednotkova_cena_EUR', 'Celkova_cena_EUR', 'Poznamka'),
                    "read_only": ('Ucetnictvi', 'Evidencni_cislo', 'Interne_cislo', 'Jednotky', 'Mnozstvi_ks_m_l',
                                  'Typ_operace', 'Operaci_provedl', 'Pouzite_zarizeni', 'Dodavatel'),
                    "insert_item_value": ('Ucetnictvi', 'Evidencni_cislo', 'Interne_cislo', 'Jednotky', 'Mnozstvi_ks_m_l',
                                          'Umisteni', 'Jednotkova_cena_EUR', 'Objednano', 'Poznamka', 'Nazev_dilu'),
                    },
                "vydej": {
                    "grid_forget": ('Nazev_dilu', 'Celkova_cena_EUR', 'Objednano', 'Dodavatel', 'Cas_operace',
                                    'Cislo_objednavky', 'Jednotkova_cena_EUR', 'Datum_nakupu', 'id'),
                    "mandatory": ('Zmena_mnozstvi', 'Pouzite_zarizeni', 'Umisteni'),
                    "date":('Datum_vydeje',),
                    "pos_integer":('Zmena_mnozstvi',),
                    "actual_value": {'Typ_operace': "VÝDEJ", 'Operaci_provedl': self.name_of_user,
                                     'Datum_nakupu': "", 'Datum_vydeje': self.actual_date,},
                    "tuple_values_to_save": ('Mnozstvi_ks_m_l', 'Umisteni', 'Poznamka', 'Celkova_cena_EUR'),
                    "read_only": ('Ucetnictvi', 'Evidencni_cislo', 'Interne_cislo', 'Jednotky', 'Mnozstvi_ks_m_l',
                                  'Typ_operace', 'Operaci_provedl', 'Pouzite_zarizeni', 'Dodavatel'),
                    "insert_item_value": ('Ucetnictvi', 'Evidencni_cislo', 'Interne_cislo', 'Jednotky', 'Mnozstvi_ks_m_l',
                                          'Umisteni', 'Jednotkova_cena_EUR', 'Objednano', 'Poznamka', 'Nazev_dilu'),
                    },
                },
            "dodavatele": {
                "edit": {
                    "read_only": ('id', 'Dodavatel'),
                    "mandatory": ('Jazyk',),
                    },
                "add": {
                    "read_only": ('id',),
                    "insert": {'id': self.new_id},
                    "mandatory": ('Dodavatel', 'Jazyk',),
                    },
                },
            "zarizeni": {
                "edit": {
                    "read_only": ('id', 'Zarizeni'),
                    "mandatory": ('Zarizeni', 'Nazev_zarizeni', 'Umisteni', 'Typ_zarizeni',),
                    },
                "add": {
                    "read_only": ('id',),
                    "insert": {'id': self.new_id},
                    "mandatory": ('Zarizeni', 'Nazev_zarizeni', 'Umisteni', 'Typ_zarizeni',),
                    },
                },
            "varianty": {
                "edit": {
                    "read_only": ('id', 'id_sklad', 'id_dodavatele',),
                    "mandatory": ('Nazev_varianty', 'Cislo_varianty',),
                    "not_neg_real":('Jednotkova_cena_EUR',),
                    "not_neg_integer": ('Dodaci_lhuta', 'Min_obj_mnozstvi'),
                    },
                "add": {
                    "read_only": ('id','Nazev_dilu', 'id_sklad', 'Dodavatel', 'id_dodavatele',),
                    "mandatory": ('Nazev_varianty', 'Cislo_varianty', 'Dodavatel', 'Jednotkova_cena_EUR',),
                    "insert": {'Dodaci_lhuta': 0, 'Min_obj_mnozstvi':0,},
                    "not_neg_real":('Jednotkova_cena_EUR',),
                    "not_neg_integer": ('Dodaci_lhuta', 'Min_obj_mnozstvi'),
                    "calculate": 'id_dodavatele',
                    },
                },
            "uzivatele": {
                "edit": {
                    "read_only": ('id', 'username'),
                    "mandatory": ('password_hash', 'name', 'role',),
                    },
                "add": {
                    "read_only": ('id',),
                    "insert": {'id': self.new_id},
                    "mandatory": ('username', 'password_hash', 'name', 'role',),
                    },
                },
            }

        self.title_action_dict = {"show": 'ZOBRAZENÍ ', "edit": 'ÚPRAVA ', "add": 'VYTVOŘENÍ ',
                                  "prijem": 'PŘÍJEM ', "vydej": 'VÝDEJ ', "inquiry": 'POPTÁVKA ', }
            
        self.current_table_entry_dict = entry_dict.get(self.current_table, {})


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
        self.top_frame = tk.Frame(self.show_frame, borderwidth=2, relief="groove")
        self.top_frame.pack(side=tk.TOP, fill=tk.X)     
        self.left_frame = tk.Frame(self.top_frame, borderwidth=2, relief="groove")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.right_common_frame = tk.Frame(self.top_frame, borderwidth=2, relief="groove")
        self.right_common_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=2, pady=2)
        self.right_top_frame = tk.Frame(self.right_common_frame, borderwidth=2, relief="groove")
        self.right_top_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=2, pady=2)        
        self.right_frame = tk.Frame(self.right_common_frame, borderwidth=2, relief="groove")
        self.right_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=2, pady=2)        




    def clear_item_frame(self):
        """
        Odstranění všech widgetů v title_frame a show_frame
        """
        for widget in self.title_frame.winfo_children():
            widget.destroy()
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        for widget in self.right_top_frame.winfo_children():
            widget.destroy()           
        for widget in self.left_frame.winfo_children():
            widget.destroy()


    def update_frames(self):
        """
        Vytvoření a nastavení dalších framů v show_frame pro aktuální zobrazení.

        :param action: Typ akce pro tlačítko uložit - add pro přidání nebo edit pro úpravu, None - žádné.
        """
        self.bottom_frame = tk.Frame(self.show_frame)
        self.bottom_frame.pack(side=tk.BOTTOM, pady=2)        
        save_btn = tk.Button(self.bottom_frame, width=15, text="Uložit",
                             command=lambda: self.check_before_save(action=self.action))
        save_btn.pack(side=tk.LEFT, padx=5, pady=5)
        cancel_btn = tk.Button(self.bottom_frame, width=15, text="Zrušit",
                               command=self.current_view_instance.show_selected_item)
        cancel_btn.pack(side=tk.LEFT, padx=5, pady=5)


    def initialize_title(self, add_name_label=True):
        """
        Vytvoření nadpisu dle typu zobrazovaných dat.
        """
        self.order_of_name = self.curr_table_config["order_of_name"]
        title_label = tk.Label(self.title_frame, bg="yellow", text=self.title, font=self.custom_font)
        title_label.pack(padx=2, pady=2)
        if add_name_label:
            name_text = f"{self.tab2hum[self.col_names[self.order_of_name]]}: \n {str(self.item_values[self.order_of_name])}"
            name_label = tk.Label(self.title_frame, bg="yellow", wraplength=400, font=self.custom_font, text=name_text)
            name_label.pack(padx=2, pady=2)


    def init_curr_dict(self):
        """
        Metoda pro přidání slovníku hodnotami přiřazenými dle aktuální tabulky.
        """
        self.curr_entry_dict = self.current_table_entry_dict.get(self.action, {})
        title_action = self.title_action_dict[self.action]
        self.title = title_action + str(self.curr_table_config["name"])        

            
    def check_before_save(self, action): 
        """
        Metoda pro kontrolu zadání povinných dat a kontrolu správnosti dat před uložením. 

        :Params action: typ prováděné operace.
        """
        for col in self.curr_entry_dict.get("mandatory", []):
            if not self.entries[col].get():
                messagebox.showwarning("Chyba", f"Před uložením nejdříve zadejte položku {self.tab2hum.get(col, col)}")
                self.entries[col].focus()
                return
            
        for col in self.curr_entry_dict.get("not_neg_integer", []):
            entry_val = self.entries[col].get()
            if not entry_val.isdigit() or int(entry_val) < 0:
                messagebox.showwarning("Chyba", f"Položka {self.tab2hum.get(col, col)} musí být celé nezáporné číslo.")
                self.entries[col].focus()
                return
            
        for col in set(self.curr_entry_dict.get("pos_real", [])).union(self.curr_entry_dict.get("not_neg_real", [])):
            entry_val = self.entries[col].get()
            if entry_val:
                try:
                    float_entry_val = float(entry_val)
                    if col in self.curr_entry_dict.get("pos_real", []) and float_entry_val <= 0:
                        messagebox.showwarning("Chyba", f"Položka {self.tab2hum.get(col, col)} musí být kladné reálné číslo s desetinnou tečkou.")
                        return
                    if col in self.curr_entry_dict.get("not_neg_real", []) and float_entry_val < 0:
                        messagebox.showwarning("Chyba", f"Položka {self.tab2hum.get(col, col)} musí být nezáporné reálné číslo s desetinnou tečkou.")
                        return 
                except ValueError:
                    messagebox.showwarning("Chyba", f"Položka {self.tab2hum.get(col, col)} není platné reálné číslo s desetinnou tečkou.")
                    return

        if action=="add":
            if self.current_table=="zarizeni":
                success = self.check_length()
                if not success: return
               
            if self.current_table=='varianty':
                success = self.check_variant_existence()
                if not success: return
            
        self.save_item(action)


    def check_length(self):
        """
        Metoda pro kontrolu délky normalizované zkratky názvu zařízení.
        """
        col = "Zarizeni"
        entry_val = self.entries[col].get()
        normalized = unicodedata.normalize('NFKD', entry_val).encode('ASCII', 'ignore').decode('ASCII')
        final_val = normalized.upper().replace(" ", "_")
        self.entries[col].delete(0, "end")
        self.entries[col].insert(0, final_val)
        if len(final_val) > 8:
            messagebox.showwarning("Varování", f"Zkratka zařízení po normalizaci:\n{final_val}\n je delší než 10 znaků.")
            self.entries[col].focus()
            return False
        self.new_col_name = final_val
        return True


    def check_variant_existence(self):
        """
        Metoda pro kontrolu existence ukládané varianty.
        """
        id_sklad_value = self.entries['id_sklad'].get()
        id_dodavatele_value = self.entries['id_dodavatele'].get()
        exists_variant = self.controller.check_existence_of_variant(id_sklad_value, id_dodavatele_value, self.current_table)
        if exists_variant:
            messagebox.showerror("Chyba", "Tato varianta již existuje.")
            self.entries["Dodavatel"].focus()
            return False
        return True


    def save_item(self, action):
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
                      
        if action == "add":
            if self.current_table == "varianty":
                col_names_to_save = self.col_names[:-2]
            else:
                col_names_to_save = self.col_names
            values_to_insert = [combined_values[col] for col in col_names_to_save]
            if self.current_table == 'zarizeni':
                success = self.controller.add_column_and_set_default(self.new_col_name)
                if not success: return
            success = self.controller.insert_new_item(self.current_table, col_names_to_save, values_to_insert)
            if not success: return
            self.id_num = int(self.new_id)
        elif action == "edit" and self.id_num is not None:
            success = self.controller.update_row(self.current_table, self.id_num, self.id_col_name, combined_values)
            if not success: return
        self.controller.show_data(self.current_table, self.id_num)


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
                if col in self.special_columns:
                    frame = tk.Frame(self.right_top_frame)
                    checkbutton = tk.Checkbutton(frame, text=self.tab2hum.get(col, col), borderwidth=3,
                                                 relief="groove", variable=self.checkbutton_states[col])
                else:
                    frame = tk.Frame(self.right_frame)
                    checkbutton = tk.Checkbutton(frame, text=self.tab2hum.get(col, col),
                                                 variable=self.checkbutton_states[col])
                checkbutton.pack(side=tk.LEFT, padx=5)
            else:
                frame = tk.Frame(self.left_frame)
                label = tk.Label(frame, text=self.tab2hum.get(col, col), width=12)
                label.pack(side=tk.LEFT)
                start_value = self.item_values[index] if self.item_values else ""
                match col:                          
                    case 'Min_Mnozstvi_ks' | 'Min_obj_mnozstvi':
                        entry = tk.Spinbox(frame, from_=0, to='infinity')
                        if self.item_values:
                            entry.delete(0, "end")
                            entry.insert(0, self.item_values[index])
                    case 'Jednotky':
                        entry = ttk.Combobox(frame, values=self.unit_tuple)
                        entry.set(start_value)                         
                    case 'Dodavatel' if self.current_table in ['sklad', 'varianty']:
                        entry = ttk.Combobox(frame, values=self.suppliers)
                        entry.set(start_value)
                        if self.current_table=='varianty':
                            entry.bind("<<ComboboxSelected>>", lambda event, entry=entry: self.supplier_number(entry))
                    case _:
                        entry = tk.Entry(frame)
                        if self.item_values:
                            entry.insert(0, self.item_values[index])                                              
                entry.pack(fill=tk.X, padx=2, pady=3)
                entry.bind('<Return>', lambda event: self.check_before_save(action=self.action))
                entry.bind('<KP_Enter>', lambda event: self.check_before_save(action=self.action))                               
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


    def supplier_number(self, entry=None):
        """
        Metoda na vložení čísla dodavatele do entry pro id_dodavatele dle vybraného dodavatele v comboboxu.
        """
        supplier_id = self.suppliers_dict[entry.get()]
        idd = "id_dodavatele"
        self.entries[idd].config(state='normal')
        self.entries[idd].delete(0, 'end')
        self.entries[idd].insert(0, supplier_id)
        self.entries[idd].config(state='readonly')


class ItemFrameShow(ItemFrameBase):
    """
    Třída ItemFrameShow se stará o zobrazení vybraných položek.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, action):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns, action)
                           

    def show_selected_item_details(self, item_values):
        """
        Metoda pro zobrazení vybrané položky z Treeview ve frame item_frame
        Název položky je v title_frame, zbylé informace v show_frame.

        :param item_values: n-tice řetězců obsahující hodnoty sloupců označené položky.
        """
        self.item_values = item_values
        self.clear_item_frame()
        self.initialize_current_entry_dict()
        self.init_curr_dict()
        self.initialize_title()
        self.checkbutton_states = {}
 
        for index, col in enumerate(self.col_names):
            if index == self.order_of_name: continue   # Vynechá název
            item_value = self.item_values[index]
            item_text = self.tab2hum.get(col, col)
            if col in self.check_columns:
                item_state = int(item_value) == 1
                self.checkbutton_states[col] = tk.BooleanVar(value=item_state)
                if col in self.special_columns:
                    frame = tk.Frame(self.right_top_frame)
                    checkbutton = tk.Checkbutton(frame, text=item_text, borderwidth=3, relief="groove",
                                                 variable=self.checkbutton_states[col])
                else:
                    frame = tk.Frame(self.right_frame)
                    checkbutton = tk.Checkbutton(frame, text=item_text, variable=self.checkbutton_states[col])
                checkbutton.pack(side=tk.LEFT, padx=5)
                checkbutton.bind("<Enter>", lambda event, cb=checkbutton: cb.config(state="disabled"))
                checkbutton.bind("<Leave>", lambda event, cb=checkbutton: cb.config(state="normal"))
            else:
                frame = tk.Frame(self.left_frame)
                label_text = f"{item_text}:\n{item_value}"
                label = tk.Label(frame, text=label_text, borderwidth=2, relief="ridge", wraplength=250)
                label.pack(fill=tk.X)
            frame.pack(fill=tk.X)              


class ItemFrameInquiry(ItemFrameBase):
    """
    Třída ItemFrameInquiry se stará o zobrazení vyfiltrovaných variant pro poptávku.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, action, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns, action)
        self.current_view_instance = current_view_instance
        self.update_frames()
                          

    def create_inquiry_form(self, tree):
        """
        Metoda pro zobrazení vybrané položky z Treeview ve frame item_frame
        Název položky je v title_frame, zbylé informace v show_frame.

        :param item_values: n-tice řetězců obsahující hodnoty sloupců označené položky.
        """
        self.initialize_current_entry_dict()
        self.init_curr_dict()
##        self.initialize_title()
        self.entries_inq = {}

        self.left_frame.columnconfigure(0, weight=1)

        for index, col in enumerate(["Nazev_varianty", "Cislo_varianty"]):
            item_text = self.tab2hum.get(col, col)
            label = tk.Label(self.left_frame, text=item_text)
            label.grid(row=0, column=index, sticky="ew", padx=5, pady=2)            
            
        for index1, item in enumerate(tree.get_children()):
            idx = 0
            item_values = tree.item(item, 'values')
            for index2, col in enumerate(self.col_names):
                if col in ["Nazev_varianty", "Cislo_varianty"]:
                    item_value = item_values[index2]
                    entry_inq = tk.Entry(self.left_frame)
                    entry_inq.grid(row=index1+1, column=idx, sticky="ew", padx=5, pady=2)
                    entry_inq.delete(0, "end")
                    entry_inq.insert(0, item_value)
                    self.entries_inq[col] = entry_inq
                    idx += 1

      
class ItemFrameEdit(ItemFrameBase):
    """
    Třída ItemFrameEdit se stará o úpravu vybraných položek.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, action, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns, action)
        self.current_view_instance = current_view_instance
        self.update_frames()


    def open_edit_window(self, item_values):
        """
        Metoda pro úpravu vybrané položky z Treeview.

        :params item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
        """
        self.item_values = item_values
        self.initialize_current_entry_dict()         
        self.init_curr_dict()        
        self.initialize_title()       
        self.id_num = self.item_values[0]
        self.id_col_name = self.curr_table_config.get("id_col_name", "id")
        self.show_for_editing()


class ItemFrameAdd(ItemFrameBase):
    """
    Třída ItemFrameAdd se stará o tvorbu nových položek.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, action, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns, action)
        self.current_view_instance = current_view_instance
        self.update_frames()


    def add_item(self, new_id, new_interne_cislo):
        """
        Metoda pro přidání nové položky do aktuální tabulky.
        """
        self.item_values = None
        self.new_id = new_id
        self.new_interne_cislo = new_interne_cislo
        self.initialize_current_entry_dict()        
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
        self.new_id = item_values[0]
        self.item_values = item_values
        dodavatel_value = self.item_values[-1]
        if dodavatel_value:
            id_dodavatele_value = self.suppliers_dict[dodavatel_value]
            self.item_values[2] = id_dodavatele_value
        self.initialize_current_entry_dict()              
        self.init_curr_dict()        
        self.initialize_title(add_name_label=False)       
        self.show_for_editing()
                

class ItemFrameMovements(ItemFrameBase):
    """
    Třída ItemFrameMovements se stará o příjem a výdej ve skladě.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, action, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns, action)
        self.current_view_instance = current_view_instance
        self.update_frames()
        
       
    def init_curr_dict(self):
        """
        Metoda pro přidání slovníku hodnotami přiřazenými dle aktuální tabulky.
        """
        title_action = self.title_action_dict[self.action]    
        self.title = f"{title_action} ZBOŽÍ"       
        self.curr_entry_dict = self.current_table_entry_dict.get(self.action, {})
        self.devices = tuple(self.controller.fetch_dict("zarizeni").keys())


    def init_item_movements(self, item_values, audit_log_col_names):
        """
        Metoda pro inicializace proměnných pro příjem a výdej skladových položek.

        :params action: Parametr s názvem akce příjem nebo výdej zboží - "prijem", "vydej".
                item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
                audit_log_col_names: N-tice názvů sloupců tabulky audit_log.      
        """
        self.item_values = item_values
        self.audit_log_col_names = audit_log_col_names
        self.initialize_current_entry_dict()          
        self.init_curr_dict()
        self.initialize_title()        
        self.id_num = self.item_values[0]
        self.id_col_name = self.curr_table_config.get("id_col_name", "id")
        self.entries_al = {}
        self.actual_quantity = int(self.item_values[self.curr_table_config["quantity_col"]])
        self.actual_unit_price = float(self.item_values[self.curr_table_config["unit_price_col"]])


    def enter_item_movements(self, item_values, audit_log_col_names):
        """
        Metoda pro příjem a výdej skladových položek.

        :params action: Parametr s názvem akce příjem nebo výdej zboží - "prijem", "vydej".
                item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
                audit_log_col_names: N-tice názvů sloupců tabulky audit_log.    
        """
        self.init_item_movements(item_values, audit_log_col_names)
        
        if self.action=='vydej' and self.actual_quantity==0:
            self.current_view_instance.show_selected_item()
            messagebox.showwarning("Chyba", f"Položka aktuálně není na skladě, nelze provést výdej!")
            return

        self.left_frame.columnconfigure(1, weight=1)
        for idx, col in enumerate(self.audit_log_col_names):
            if col in self.col_names:
                index = self.col_names.index(col)
            label = tk.Label(self.left_frame, text=self.tab2hum.get(col, col))
            label.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)
            if col == 'Pouzite_zarizeni':
                entry_al = ttk.Combobox(self.left_frame,values=self.devices+("Neuvedeno",))             
                entry_al.set("")
            elif col == 'Dodavatel':
                entry_al = ttk.Combobox(self.left_frame, values=self.suppliers)
                entry_al.set(self.item_values[index])
            else:
                entry_al = tk.Entry(self.left_frame)                        
            entry_al.grid(row=idx, column=1, sticky="ew", padx=5, pady=2)
            entry_al.bind('<Return>', lambda event: self.check_before_save(action=self.action))
            entry_al.bind('<KP_Enter>', lambda event: self.check_before_save(action=self.action))                        
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
                self.show_warning(col, f"Před uložením nejdříve zadejte položku {self.tab2hum.get(col, col)}")
                return
            
        for col in self.curr_entry_dict.get("pos_integer", []):
            entry_val = self.entries_al[col].get()
            if not entry_val.isdigit() or int(entry_val) <= 0:
                self.show_warning(col, f"Položka {self.tab2hum.get(col, col)} musí být kladné celé číslo.")
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
                    self.show_warning(col, f"Položka {self.tab2hum.get(col, col)} musí být kladné reálné číslo s desetinnou tečkou.")
                    return
            except ValueError:
                self.show_warning(col, f"Položka {self.tab2hum.get(col, col)} není platné kladné reálné číslo s desetinnou tečkou.")
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

        self.calculate_and_save(action)


    def calculate_and_save(self, action): 
        """
        Metoda uložení dat výpočet hodnot před uložením do skladu a audit_logu a pro uložení
        změn do tabulky sklad a nového zápisu do tabulky audit_log. Pokud je při příjmu zjištěno,
        že ještě neexistuje varianta skladové položky se zadaným dodavatelem, tak připraví okno na
        vytvoření nové varianty.
        
        :Params action: typ prováděné operace.
        """           
        self.calculate_before_save_to_audit_log() 
        self.calculate_before_save_to_sklad()
        
        success = self.controller.update_row("sklad", self.id_num, self.id_col_name, self.values_to_sklad)
        if not success:
            return
        success = self.controller.insert_new_item("audit_log", self.audit_log_col_names[1:], self.values_to_audit_log[1:])
        if not success:
            return
        messagebox.showinfo("Informace", f"Úspěšně proběhl {self.title.lower()} a zápis do audit logu!")

        if self.action == "prijem":
            id_sklad_value = self.id_num
            dodavatel_value = self.values_to_sklad["Dodavatel"]
            id_dodavatele_value = self.suppliers_dict[dodavatel_value]
            exists_variant = self.controller.check_existence_of_variant(id_sklad_value, id_dodavatele_value, "varianty")
            if not exists_variant:
                messagebox.showinfo("Informace", "Varianta s tímto dodavatelem ještě neexistuje, prosím, vytvořte ji.")
                self.current_view_instance.add_variant(curr_unit_price=self.new_unit_price)
                return
            else:
                pass # uložit aktuální jednotkovou cenu do varianty

        self.controller.show_data(self.current_table, self.id_num)
        

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


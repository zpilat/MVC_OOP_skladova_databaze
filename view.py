import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import tkinter.font as tkFont
from datetime import datetime, timedelta
import re
import sys
import unicodedata
import hashlib

class View:
    """
    Třída View se stará o zobrazení uživatelského rozhraní.
    """  
    def __init__(self, root, controller, col_names, current_table):
        """
        Inicializace GUI a nastavení hlavního okna.
        
        :param root(tk.Tk): Hlavní okno aplikace.
        :param controller(Controller): Instance kontroleru pro komunikaci mezi modelem a pohledem.
        """
        self.root = root
        self.controller = controller
        self.col_names = col_names
        self.current_table = current_table
        self.sort_reverse = True
        self.item_frame_show = None         
        self.tab2hum = CommonResources.tab2hum
        self.suppliers_dict = self.controller.fetch_dict("dodavatele")
        self.suppliers = tuple(sorted(self.suppliers_dict.keys()))
        self.item_names_dict = self.controller.fetch_dict("sklad")
        self.item_names = tuple(sorted(self.item_names_dict.keys()))
        self.selected_option = "VŠE"
        self.selected_supplier = "VŠE"
        self.selected_item_name = "VŠE"
        self.start_date = None
        self.context_menu_list = []         
        self.curr_table_config = CommonResources.view_table_config.get(self.current_table, {})
        if self.current_table == "sklad":
            devices = tuple(self.controller.fetch_dict("zarizeni").keys())
            self.curr_table_config['check_columns'] = self.curr_table_config['check_columns'] + devices
            self.curr_table_config['hidden_columns'] = self.curr_table_config['hidden_columns'] + devices
        self.mnozstvi_col = self.curr_table_config.get("quantity_col", [])
        self.check_columns = self.curr_table_config.get("check_columns", [])
        self.hidden_columns = self.curr_table_config.get("hidden_columns", [])
        self.special_columns = self.curr_table_config.get("special_columns", [])
        self.col_params_dict = self.curr_table_config.get('col_params_dict', {})
        self.default_params = self.curr_table_config.get('default_params', {"width": 80, "anchor": "center"})
        self.hidden_params = self.curr_table_config.get('hidden_params', {"width": 0, "minwidth": 0, "stretch": tk.NO})
        self.filter_columns = {col: tk.BooleanVar(value=False) for col in self.check_columns}
        self.id_col = 0
        self.click_col = 0
        self.id_col_name = self.curr_table_config.get("id_col_name", 'id')            


    def customize_ui(self):
        """
        Přidání specifických menu a framů a labelů pro zobrazení informací o skladu.
        """
        self.initialize_menus_dict()
        self.initialize_fonts()
        self.initialize_menu()
        self.initialize_frames()
        self.initialize_searching()
        self.update_menu(self.specialized_menu_list)
        self.update_context_menu()
        self.update_frames()
        self.initialize_check_buttons()
        self.initialize_treeview()
        self.initialize_bindings()
        self.additional_gui_elements()
        self.setup_columns()    


    def initialize_menus_dict(self):
        """
        Slovníky pro specifická menu a kontextové menu pro danou tabulku.
        """ 
        menus_dict = {
            "sklad":{
                "specialized_menu_dict": {
                    "Skladové položky": [("Přidat skladovou položku", self.add_item),
                                         ("Upravit skladovou položku", self.edit_selected_item),
                                         "separator",
                                         ("Smazat skladovou položku", self.delete_row),],
                    "Příjem/Výdej": [("Příjem zboží", lambda: self.item_movements(action='prijem')),
                                     ("Výdej zboží", lambda: self.item_movements(action='vydej')),],
                    "Varianty": [("Přidat variantu", self.add_variant),],
                    },
                "context_menu_list": [
                    ("Upravit skladovou položku", self.edit_selected_item),
                    ("Smazat skladovou položku", self.delete_row),
                    "separator",
                    ("Příjem zboží", lambda: self.item_movements(action='prijem')),
                    ("Výdej zboží", lambda: self.item_movements(action='vydej')),
                    "separator",
                    ("Přidat variantu", self.add_variant),
                    "separator",
                    ("Zrušit", self.hide_context_menu)
                    ],
                },
            "dodavatele": {
                "specialized_menu_dict": {
                    "Dodavatelé": [("Přidat dodavatele", self.add_item),
                                   ("Upravit dodavatele", self.edit_selected_item),],
                    },
                "context_menu_list": [
                    ("Upravit dodavatele", self.edit_selected_item),
                    "separator",
                    ("Zrušit", self.hide_context_menu)
                    ],
                },
            "zarizeni": {
                "specialized_menu_dict": {
                    "Zařízení": [("Přidat zařízení", self.add_item),
                                 ("Upravit zařízení", self.edit_selected_item),],
                    },
                "context_menu_list": [
                    ("Upravit zařízení", self.edit_selected_item),
                    "separator",
                    ("Zrušit", self.hide_context_menu)
                    ],
                },
            "varianty": {
                "specialized_menu_dict": {
                    "Varianty": [("Upravit variantu", self.edit_selected_item),],
                    },
                "context_menu_list": [
                    ("Upravit variantu", self.edit_selected_item),
                    "separator",
                    ("Zrušit", self.hide_context_menu)
                    ],
                },
            }
        current_menus_dict = menus_dict.get(self.current_table, {})

        self.specialized_menu_list = current_menus_dict.get("specialized_menu_dict", {})
        self.context_menu_list = current_menus_dict.get("context_menu_list", [])
        

    def initialize_fonts(self):
        """
        Inicializace používaných fontů.
        """ 
        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.custom_font = self.default_font.copy()
        self.custom_font.config(size=12, weight="bold") 


    def initialize_menu(self):
        """
        Inicializace hlavního společného menu.
        """
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        common_menus = {
            "Soubor": [
                (f"Export databáze {self.current_table} do csv", lambda: self.controller.export_csv(table=self.current_table)),
                ("Export aktuálně vyfiltrovaných dat do csv", lambda: self.controller.export_csv(tree=self.tree)),
                "separator",
                ("Konec", self.root.destroy)
            ],
        }
        common_radiobutton_menus = CommonResources.common_radiobutton_menus
        
        self.update_menu(common_menus)
        self.view_var = tk.StringVar()
        self.view_var.set(self.current_table)
        self.update_radiobuttons_menu(common_radiobutton_menus, self.view_var)


    def on_view_change(self):
        """
        Přepnutí pohledu na tabulku v menu pomocí radiobuttonů.
        """
        selected_view = self.view_var.get()
        self.controller.show_data(selected_view)


    def initialize_frames(self):
        """
        Inicializace společných framů, proběhne až v instanci dceřínné třídy.
        """
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.top_frames_container = tk.Frame(self.frame)
        self.top_frames_container.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.search_frame = tk.LabelFrame(self.top_frames_container, text="Vyhledávání",
                                          borderwidth=2, relief="groove")
        self.search_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        self.filter_buttons_frame = tk.LabelFrame(self.top_frames_container, text="Filtrování dle výběru",
                                                  borderwidth=2, relief="groove")
        self.filter_buttons_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.check_buttons_frame = tk.LabelFrame(self.frame, text="Filtrování dle zařízení",
                                                 borderwidth=2, relief="groove")
        self.check_buttons_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.left_frames_container = tk.Frame(self.frame)
        self.left_frames_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)        


    def initialize_searching(self):
        """
        Inicializace políčka a tlačítka pro vyhledávání / filtrování.
        """
        self.search_entry = tk.Entry(self.search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        self.search_entry.bind('<Return>', lambda _: self.controller.show_data(self.current_table))
        self.search_entry.bind('<KP_Enter>', lambda _: self.controller.show_data(self.current_table))
        self.search_entry.bind("<Escape>", lambda _: self.search_entry.delete(0, tk.END))
        self.search_button = tk.Button(self.search_frame, text="Filtrovat",
                                       command=lambda: self.controller.show_data(self.current_table))
        self.search_button.pack(side=tk.LEFT, padx=5)


    def initialize_check_buttons(self):
        """
        Nastavení specifických checkbuttonů pro filtrování zobrazených položek.
        """         
        for col in self.filter_columns:
            if col in self.special_columns:
                checkbutton = tk.Checkbutton(self.filter_buttons_frame, text=self.tab2hum.get(col, col), variable=self.filter_columns[col],
                                             borderwidth=3, relief="groove", onvalue=True, offvalue=False, 
                                             command=lambda col=col: self.toggle_filter(col))
                checkbutton.pack(side='left', padx=5, pady=5)
            else:
                checkbutton = tk.Checkbutton(self.check_buttons_frame, text=self.tab2hum.get(col, col), variable=self.filter_columns[col],
                                             onvalue=True, offvalue=False, command=lambda col=col: self.toggle_filter(col))
                checkbutton.pack(side='left', pady=5)


    def initialize_treeview(self):
        """
        Inicializace TreeView a přidruženého scrollbaru.

        :param tree_frame: Frame pro zobrazení Treeview.
        """
        self.tree = ttk.Treeview(self.tree_frame, show='headings', height=30)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")

        self.tree.tag_configure('evenrow', background='#FFFFFF')
        self.tree.tag_configure('oddrow', background='#F5F5F5')
        self.tree.tag_configure('low_stock', foreground='#CD5C5C')    


    def initialize_bindings(self):
        """
        Vytvoření společených provázání na události.
        """
        self.tree.bind('<<TreeviewSelect>>', self.show_selected_item)  
        self.root.bind('<Button-1>', self.global_click)
        self.tree.bind('<Button-3>', self.on_right_click)
    

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
          

    def update_radiobuttons_menu(self, additional_radiobutton_menus, str_variable):
        """
        Aktualizuje hlavní menu aplikace přidáním nových radiobutton menu.

        Parametry:
            additional_radiobuttons_menus (dict): Slovník definující radiobuttony menu k přidání.
                                                  Klíč slovníku je název menu a hodnota je seznam
                                                  dvojic (název položky, tabulka).
        """
        for menu_name, menu_items in additional_radiobutton_menus.items():
            new_menu = tk.Menu(self.menu_bar, tearoff=0)
            for item in menu_items:
                item_name, table = item
                new_menu.add_radiobutton(label=item_name, variable=str_variable,
                                         value=table, command=self.on_view_change)
            self.menu_bar.add_cascade(label=menu_name, menu=new_menu)


    def update_context_menu(self):
        """
        Vytvoří kontextové menu aplikace při kliknutí pravým tlačítkem na položku v Treeview.
        """
        self.context_menu = tk.Menu(self.root, tearoff=0)
        for item in self.context_menu_list:
            if item == "separator":
                self.context_menu.add_separator()
            else:
                item_name, command = item
                self.context_menu.add_command(label=item_name, command=command)       


    def hide_context_menu(self):
        """
        Metoda pro schování kontextového menu.
        """
        self.context_menu.unpost()        


    def update_frames(self):
        """
        Aktualizuje specifické frame pro dané zobrazení.
        """
        self.item_frame = tk.LabelFrame(self.frame, width=435, text="Zobrazení detailu položky",
                                        borderwidth=2, relief="groove")
        self.item_frame.pack_propagate(False)
        self.item_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.tree_frame = tk.LabelFrame(self.left_frames_container, text="Zobrazení vyfiltrovaných položek",
                                        borderwidth=2, relief="groove")
        self.tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)        


    def additional_gui_elements(self):
        """
        Vytvoření zbývajících specifických prvků gui dle typu zobrazovaných dat.
        """
        pass


    def setup_columns(self):
        """
        Nastavení parametrů sloupců pro TreeView.
        """              
        self.tree['columns'] = self.col_names
        for idx, col in enumerate(self.col_names):
            if col in self.hidden_columns:
                col_params = self.hidden_params
            else:
                col_params = self.col_params_dict.get(col, self.default_params)           
            self.tree.heading(col, text=self.tab2hum.get(col, col), command=lambda c=idx: self.on_column_click(c))
            self.tree.column(col, **col_params)


    def on_combobox_change(self, event, attribute_name):
        """
        Aktualizuje příslušný atribut na základě vybrané hodnoty v comboboxu
        a filtruje zobrazovaná data podle aktuálních vybraných hodnot.
        """
        setattr(self, attribute_name, event.widget.get())
        self.controller.show_data(self.current_table)


    def delete_tree(self):
        """
        Vymaže všechny položky v Treeview.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)


    def on_right_click(self, event):
        """
        Vybere položku a zobrazí kontextové menu po kliknutím pravým tlačítkem na položku v Treeview.
        """        
        treeview_item_id = self.tree.identify_row(event.y)
        if treeview_item_id:
            self.tree.selection_set(treeview_item_id)
            self.selected_item = treeview_item_id
            self.id_num = int(self.tree.item(self.selected_item, 'values')[self.id_col])
            self.context_menu.post(event.x_root, event.y_root)
        else:
            self.hide_context_menu()        


    def global_click(self, event):
        """
        Pokud je otevřeno kontextové menu a klikne se myší jinam, tak se kontextové menu zavře.
        """
        widget = event.widget
        if widget != self.context_menu:
            self.hide_context_menu()


    def add_data(self, current_data, current_id_num=None):
        """
        Vymazání všech dat v Treeview. Filtrace a třídění dle aktuálních hodnot parametrů.
        Vložení dat do TreeView. Změna hodnot v check_colums z 0/1 na NE/ANO pro zobrazení.
        Zvýraznění řádků pod minimem. Označení první položky v Treeview.
        Třídění podle zakliknuté hlavičky sloupce, při druhém kliknutí na stejný sloupec reverzně.

        :param current_data: aktuální data získaná z aktuální tabulky.
        :param current_id_num: id číslo aktuální položky k označení, pokud None, tak se označí první.        
        """          
        self.delete_tree()

        if self.current_table == "item_variants":
            sorted_data = current_data
        else:
            filtered_data = self.filter_data(current_data)
            sorted_data = sorted(filtered_data, key=self.sort_key, reverse=self.sort_reverse)
        
        treeview_item_ids = {}
        for idx, row in enumerate(sorted_data):      
            treeview_item_id = self.tree.insert('', tk.END, values=row)
            treeview_item_ids[row[0]] = treeview_item_id
            stripe_tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            if self.current_table in ('sklad', 'varianty') and int(row[-1])==1:
                self.tree.item(treeview_item_id, tags=(stripe_tag, 'low_stock',))
            else: 
                self.tree.item(treeview_item_id, tags=(stripe_tag,))

        if current_id_num and current_id_num in treeview_item_ids:
            choosen_item = treeview_item_ids[current_id_num]
            self.mark_first_or_choosen_item(item=choosen_item)
        else:
            self.mark_first_or_choosen_item(item=None)
            

    def mark_first_or_choosen_item(self, item):
        """
        Označení první nebo vybrané položky v Treeview po načtení nových dat.
        """
        if not item:
            children = self.tree.get_children()
            if children:
                item = children[0]
            else: return
        self.tree.selection_set(item)
        self.tree.see(item)
        self.tree.focus(item)           
        

    def filter_data(self, data):
        """
        Vyfiltrování dat podle zadaných dat v search_entry ve všech tabulkách.
        V tabulce sklad navíc dle zaškrtnutých check buttonů a low stock filtru.
        V tabulce audit_log navíc dle comboboxu typ akce a v rozmezí datumů v date entry.
        V tabulce varianty dle comboboxu dodavatelé.

        :param data: Data pro filtraci dle search entry.
        :return: Přefiltrovaná data.
        """ 
        search_query = self.search_entry.get()
        if search_query:
            filtered_data = [row for row in data if search_query.lower() in " ".join(map(str, row)).lower()]
        else:
            filtered_data = data
    
        if self.current_table == "audit_log":
            if self.selected_option != "VŠE":
                filtered_data = [row for row in filtered_data if row[9] == self.selected_option]

        if self.current_table == "varianty":
            if self.selected_supplier != "VŠE":
                filtered_data = [row for row in filtered_data if row[-2] == self.selected_supplier]
            if self.selected_item_name != "VŠE":
                filtered_data = [row for row in filtered_data if row[-3] == self.selected_item_name]                

        if self.start_date:       
            filtered_data = [row for row in filtered_data if self.start_date <= (row[13] or row[14]) <= self.end_date]
            
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
        if clicked_col == self.click_col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.click_col = clicked_col
            self.sort_reverse = False
        self.controller.show_data(self.current_table, self.id_num)

        
    def sort_key(self, row):
        """
        Funkce sloužící jako klíč pro třídění dle sloupcu.
        Pokusí se převést hodnotu na float pro řazení číselných hodnot.
        Čísla mají přednost, takže pro ně vracíme (0, number).
        Textové hodnoty dostanou nižší prioritu, vracíme (1, value.lower()).

        :param row: porovnávaný řádek / položka v datatabázi.
        """
        value = row[self.click_col]
        try:
            number = float(value)
            return (0, number)
        except ValueError:
            return (1, value.lower())

        
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
            self.id_num = int(self.tree.item(selected_item, 'values')[self.id_col])
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
                                                 self.current_table, self.check_columns)
            
        children = self.tree.get_children()
        if not children:
            messagebox.showwarning("Upozornění", "Nejsou žádné položky k zobrazení.")
            return

        self.selected_item = self.select_item(warning_message="Není vybrána žádná položka k zobrazení.")
        if self.selected_item is None:
            return  
       
        try:        
            item_values = self.tree.item(self.selected_item, 'values')
            self.item_frame_show.show_selected_item_details(item_values)
        except Exception as e:
            messagebox.showwarning("Upozornění", f"Při zobrazování došlo k chybě {e}.")
            return


    def edit_selected_item(self):
        """
        Metoda pro získání aktuálních dat z databáze pro vybranou položku a jejich zobrazení
        pro editaci.
        """
        self.selected_item = self.select_item()
        if self.selected_item is None:
            return       
        self.widget_destroy()    
        self.item_frame_show = None
        self.controller.show_data_for_editing(self.current_table, self.id_num, self.id_col_name,
                                                  self.item_frame, self.check_columns)


    def add_variant(self, curr_unit_price=None):
        """
        Metoda pro získání aktuálních dat z databáze pro vybranou položku a jejich zobrazení
        pro tvorbu nové varianty.
        """
        self.selected_item = self.select_item()
        if self.selected_item is None: return
        self.widget_destroy()
        self.item_frame_show = None
        varianty_table = "varianty"
        varianty_table_config = View.table_config.get(varianty_table, {})
        varianty_check_columns = varianty_table_config.get("check_columns", [])
        varianty_id_col_name = varianty_table_config.get("id_col_name", "id")
        self.controller.add_variant(self.current_table, self.id_num, self.id_col_name, self.item_frame,
                                    varianty_check_columns, varianty_table, varianty_id_col_name,
                                    curr_unit_price)
      
        
    def add_item(self):
        """
        Metoda pro přidání nové položky do aktuální tabulky.
        """
        self.widget_destroy()                      
        self.item_frame_show = None
        self.id_num = None
        self.controller.add_item(self.current_table, self.id_num, self.id_col_name,
                                     self.item_frame, self.check_columns)


    def delete_row(self):
        """
        Vymaže označenou položku, pokud je to poslední zadaná položka a je nulový stav.
        """
        # Zatím funguje pouze pro SkladView, určit, zda má smysl i pro ostatní pohledy!
        self.selected_item = self.select_item()
        if self.selected_item is None:
            return
        last_inserted_item = self.controller.get_max_id(self.current_table, self.id_col_name)
        mnozstvi = self.tree.item(self.selected_item)['values'][self.mnozstvi_col]
        if mnozstvi != 0 or self.id_num != last_inserted_item:
            messagebox.showwarning("Varování", "Lze smazat pouze poslední zadanou položku s nulovým množstvím!")
            return           
        response = messagebox.askyesno("Potvrzení mazání", "Opravdu chcete smazat vybraný řádek?")
        if response: 
            success = self.controller.delete_row(self.id_num)
            self.tree.delete(self.selected_item)
            self.mark_first_or_choosen_item(item=None)
            if success:
                messagebox.showinfo("Informace", "Vymazána poslední zadaná položka!")
            else:
                return
            
        self.controller.show_data(self.current_table)        


    def hash_password(self, password):
        """
        Vypočítá a vrátí hash zadaného hesla pomocí algoritmu SHA-256.

        Tato funkce je určena pro bezpečné ukládání hesel v databázi. Místo uložení
        čitelného hesla se uloží jeho hash, což zvyšuje bezpečnost uchování hesel.

        :param password: Heslo, které má být zahashováno.
        :return: Zahashované heslo ve formátu hexadecimálního řetězce.
        """
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash


class LoginView(View):
    """
    Třída LoginView pro přihlášení uživatele. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, current_table):
        """
        Inicializace specifického zobrazení pro dodavatele.
        
        :param root: Tkinter root widget, hlavní okno aplikace.
        :param controller: Instance třídy Controller.
        :param col_names: Seznam názvů sloupců (v tomto případě prázdný, protože se nepoužívá).
        """
        super().__init__(root, controller, col_names, current_table)
        self.additional_gui_elements()

    def place_window(self, window_width, window_height):
        """
        Metoda na umístění okna do středu obrazovky a stanovení velikosti okna dle zadaných parametrů.

        :params window_width, window_height - rozměry okna aplikace.
        """
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int((screen_width/2) - (window_width/2))
        center_y = int((screen_height/2) - (window_height/2))

        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')


    def additional_gui_elements(self):
        """
        Vytvoření a umístění prvků GUI pro přihlašovací formulář.
        """
        self.place_window(410, 340)
        
        self.frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        login_label = tk.Label(self.frame , text="Přihlášení uživatele", font=("TkDefaultFont", 20))
        username_label = tk.Label(self.frame , text="Uživatelské jméno", font=("TkDefaultFont", 14))
        self.username_entry = tk.Entry(self.frame , font=("TkDefaultFont", 14))
        self.password_entry = tk.Entry(self.frame , show="*", font=("TkDefaultFont", 14))
        password_label = tk.Label(self.frame , text="Heslo", font=("TkDefaultFont", 14))
        login_button = tk.Button(self.frame , text="Login", bg='#333333', fg="#FFFFFF", borderwidth=2,
                                 relief="groove", font=("TkDefaultFont", 16), command=self.attempt_login)

        login_label.grid(row=0, column=0, columnspan=2, sticky="news", padx=5, pady=40)
        username_label.grid(row=1, column=0, padx=5)
        self.username_entry.grid(row=1, column=1, padx=5, pady=20)
        password_label.grid(row=2, column=0, padx=5)
        self.password_entry.grid(row=2, column=1, padx=5, pady=20)
        login_button.grid(row=3, column=0, columnspan=2, pady=30)

        self.password_entry.bind('<Return>', lambda _: self.attempt_login())
        self.password_entry.bind('<KP_Enter>', lambda _: self.attempt_login())               

        self.username_entry.focus()


    def attempt_login(self):
        """
        Přihlášení uživatele do systému.
        """
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showinfo("Upozornění", "Nebylo zadáno uživatelské jméno nebo heslo")
            return

        password_hash = self.hash_password(password)

        self.controller.attempt_login(username, password_hash)

        
    def handle_failed_login(self):
        """
        Zobrazí dialogové okno s možností opakování přihlášení nebo ukončení aplikace
        po neúspěšném pokusu o přihlášení.
        """
        result = messagebox.askretrycancel("Přihlášení selhalo",
                                           "Nesprávné uživatelské jméno nebo heslo. Chcete to zkusit znovu?")
        if result:
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.username_entry.focus()
        else:
            self.root.destroy()


    def start_main_window(self):
        """
        Metoda pro start tabulky sklad a vytvoření hlavního okna po úspěšném přihlášení.
        """
        title = CommonResources.main_window_title
        root.title(title)
        
        if sys.platform.startswith('win'):
            root.state('zoomed')
        else:
            self.place_window(1920, 1080)
        
        self.controller.show_data("sklad")      
     

class SkladView(View):
    """
    Třída SkladView pro specifické zobrazení dat skladu. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, current_table):
        """
        Inicializace specifického zobrazení pro sklad.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller, col_names, current_table)
        self.customize_ui()


    def additional_gui_elements(self):
        """
        Vytvoření zbývajících specifických prvků gui dle typu zobrazovaných dat.
        """
        self.tree.bind('<<TreeviewSelect>>', self.show_item_and_variants)  
        
        self.item_variants_frame = tk.LabelFrame(self.left_frames_container, height=180,
                                                 text="Varianty", borderwidth=2, relief="groove")
        self.item_variants_frame.pack_propagate(False)
        self.item_variants_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)        


    def item_movements(self, action):
        """
        Implementace funkcionality pro příjem a výdej zboží ve skladu.
        """
        if self.selected_item is None:
            return
        self.widget_destroy()            
        self.item_frame_show = None
        self.controller.show_data_for_movements(self.current_table, self.id_num, self.id_col_name,
                                              self.item_frame, self.check_columns, action)


    def show_item_and_variants(self, event=None):
        """
        Metoda pro zobrazení označené položky z treeview v item frame a zobrazení variant
        vybrané položky v item_variants_frame.
        """
        self.show_selected_item()
        self.controller.show_item_variants(self.id_num, self.item_variants_frame)  

    
class AuditLogView(View):
    """
    Třída AuditLogView pro specifické zobrazení dat audit logu. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, current_table):
        """
        Inicializace specifického zobrazení pro audit log.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller, col_names, current_table)    
        self.customize_ui()


    def additional_gui_elements(self):
        """
        Vytvoření zbývajících specifických prvků gui dle typu zobrazovaných dat.
        """
        self.operation_label = tk.Label(self.filter_buttons_frame, text="Typ operace:")
        self.operation_label.pack(side=tk.LEFT, padx=5, pady=5)

        options = ["VŠE", "PŘÍJEM", "VÝDEJ"]
        self.operation_combobox = ttk.Combobox(self.filter_buttons_frame, values=options, state="readonly")
        self.operation_combobox.pack(side=tk.LEFT, padx=5, pady=5) 
        self.operation_combobox.bind("<<ComboboxSelected>>",
                                     lambda event, attr='selected_option': self.on_combobox_change(event, attr))

        self.month_entry_label = tk.Label(self.filter_buttons_frame, text="Výběr měsíce:")
        self.month_entry_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.generate_months_list()
        self.month_entry_combobox = ttk.Combobox(self.filter_buttons_frame, width=12,
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


class DodavateleView(View):
    """
    Třída DodavateleView pro specifické zobrazení dat z tabulky dodavatele. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, current_table):
        """
        Inicializace specifického zobrazení pro dodavatele.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller, col_names, current_table)     
        self.click_col = 1
        self.sort_reverse = False
        self.customize_ui()


class ZarizeniView(View):
    """
    Třída ZarizeniView pro specifické zobrazení dat z tabulky zarizeni. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, current_table):
        """
        Inicializace specifického zobrazení pro dodavatele.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller, col_names,current_table)     
        self.sort_reverse = False
        self.customize_ui()


class VariantyView(View):
    """
    Třída VariantyView pro specifické zobrazení dat z tabulky varianty. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, current_table):
        """
        Inicializace specifického zobrazení pro varianty.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller, col_names, current_table)
        self.customize_ui()


    def additional_gui_elements(self):
        """
        Vytvoření zbývajících specifických prvků gui dle typu zobrazovaných dat.
        """   
        self.supplier_label = tk.Label(self.filter_buttons_frame, text="Dodavatel:")
        self.supplier_label.pack(side=tk.LEFT, padx=5, pady=5)

        options = ("VŠE",) + self.suppliers
        self.supplier_combobox = ttk.Combobox(self.filter_buttons_frame, values=options, state="readonly")
        self.supplier_combobox.pack(side=tk.LEFT, padx=5, pady=5) 

        self.supplier_combobox.set("VŠE")
        self.supplier_combobox.bind("<<ComboboxSelected>>",
                                     lambda event, attr='selected_supplier': self.on_combobox_change(event, attr))
        
        self.item_name_label = tk.Label(self.filter_buttons_frame, text="Skladová položka")
        self.item_name_label.pack(side=tk.LEFT, padx=5, pady=5)

        options = ("VŠE",) + self.item_names
        self.item_name_combobox = ttk.Combobox(self.filter_buttons_frame, values=options, width=50, state="readonly")
        self.item_name_combobox.pack(side=tk.LEFT, padx=5, pady=5) 

        self.item_name_combobox.set("VŠE")
        self.item_name_combobox.bind("<<ComboboxSelected>>",
                                     lambda event, attr='selected_item_name': self.on_combobox_change(event, attr))           


class ItemVariantsView(View):
    """
    Třída VariantyView pro specifické zobrazení dat z tabulky varianty. Dědí od třídy View.
    """
    def __init__(self, root, controller, col_names, current_table):
        """
        Inicializace specifického zobrazení pro varianty.
        
        :param root: Hlavní okno aplikace.
        :param controller: Instance třídy Controller pro komunikaci mezi modelem a pohledem.
        :param col_names: Názvy sloupců pro aktuální zobrazení.
        """
        super().__init__(root, controller, col_names, current_table)
        self.customize_ui()


    def customize_ui(self):
        """
        Přidání specifických menu a framů a labelů pro zobrazení informací o skladu.
        """
        self.initialize_frames()
        self.update_frames()
        self.initialize_treeview()
        self.initialize_bindings()
        self.setup_columns()
        

    def initialize_bindings(self):
        """
        Vytvoření společených provázání na události.
        """
        self.tree.bind('<Double-1>', self.on_item_double_click)


    def update_frames(self):
        """
        Aktualizuje specifické frame pro dané zobrazení.
        """
        self.tree_frame = tk.Frame(self.left_frames_container, borderwidth=2, relief="groove")
        self.tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)    
            

    def on_column_click(self, clicked_col):
        """
        Přebití metody on_column_click, zde není potřeba.
        """
        pass


    def on_item_double_click(self, event):
        """
        Vybere dvojklikem variantu v podokně Varianty a zobrazí označenou variantu v tabulce Varianty.
        """        
        treeview_item_id = self.tree.identify_row(event.y)
        if treeview_item_id:
            self.tree.selection_set(treeview_item_id)
            self.id_num = int(self.tree.item(treeview_item_id, 'values')[self.id_col])
            table="varianty"
            self.controller.show_data(table, self.id_num) 
           

class ItemFrameBase:
    """
    Třída ItemFrameBase je rodičovská třída pro práci s vybranými položkami.
    """
    table_config = {
        "sklad": {"order_of_name": 6, "id_col_name": "Evidencni_cislo", "quantity_col": 7,
                  "unit_price_col": 13, "focus": 'Nazev_dilu', "name": "SKLADOVÉ KARTY",},
        "audit_log": {"order_of_name": 5, "name": "POHYBU NA SKLADĚ",},
        "dodavatele": {"order_of_name": 1, "focus": 'Dodavatel', "name": "DODAVATELE",},
        "varianty": {"order_of_name": 3, "focus": 'Nazev_varianty', "name": "VARIANTY",},
        "zarizeni": {"order_of_name": 1, "focus": 'Zarizeni', "name": "ZAŘÍZENÍ",},
        }

    def __init__(self, master, controller, col_names, current_table, check_columns):
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
        self.suppliers_dict = self.controller.fetch_dict("dodavatele")
        self.suppliers = tuple(sorted(self.suppliers_dict.keys()))
        self.current_user = self.controller.current_user
        self.name_of_user = self.controller.name_of_user
        self.unit_tuple = ("ks", "kg", "pár", "l", "m", "balení")
        self.curr_table_config = ItemFrameBase.table_config[self.current_table]
        self.special_columns = ('Ucetnictvi', 'Kriticky_dil', 'Pod_minimem')

        self.initialize_fonts()
        self.initialize_frames()


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

        :param action: Typ akce pro tlačítko uložit - add pro přidání nebo edit pro úpravu, None - žádné.
        """
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

        if action:        
            self.bottom_frame = tk.Frame(self.show_frame)
            self.bottom_frame.pack(side=tk.BOTTOM, pady=2)
            save_btn = tk.Button(self.bottom_frame, width=15, text="Uložit",
                                 command=lambda: self.check_before_save(action=action))
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
    def __init__(self, master, controller, col_names, current_table, check_columns):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns)


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
        self.entry_dict = {}
        self.curr_entry_dict = self.entry_dict.get(self.current_table, {})
        self.title = "ZOBRAZENÍ " + str(self.curr_table_config["name"])
                           

    def show_selected_item_details(self, item_values):
        """
        Metoda pro zobrazení vybrané položky z Treeview ve frame item_frame
        Název položky je v title_frame, zbylé informace v show_frame.

        :param item_values: n-tice řetězců obsahující hodnoty sloupců označené položky.
        """
        self.item_values = item_values
        self.clear_item_frame()
        self.init_curr_dict()
        self.initialize_title()
        self.update_frames(action=None)
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

       
class ItemFrameEdit(ItemFrameBase):
    """
    Třída ItemFrameEdit se stará o úpravu vybraných položek.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns)
        self.current_view_instance = current_view_instance
        self.action = 'edit'
        self.update_frames(action=self.action)
        
       
    def init_curr_dict(self):
        """
        Metoda pro přidání slovníku hodnotami přiřazenými dle aktuální tabulky.
        """
        self.entry_dict = {"sklad": {"read_only": ('Evidencni_cislo', 'Mnozstvi_ks_m_l', 'Jednotky', 'Dodavatel',
                                                   'Datum_nakupu', 'Jednotkova_cena_EUR', 'Celkova_cena_EUR'),
                                     "mandatory": ('Min_Mnozstvi_ks', 'Nazev_dilu',),
                                     "not_neg_integer": ('Interne_cislo', 'Min_Mnozstvi_ks',),
                                     },
                           "dodavatele": {"read_only": ('id', 'Dodavatel'),
                                          },
                           "zarizeni": {"read_only": ('id', 'Zarizeni'),
                                        "mandatory": ('Zarizeni', 'Nazev_zarizeni', 'Umisteni', 'Typ_zarizeni',),
                                        },                           
                           "varianty": {"read_only": ('id', 'id_sklad', 'id_dodavatele',),
                                        "mandatory": ('Nazev_varianty', 'Cislo_varianty',),
                                        "not_neg_real":('Jednotkova_cena_EUR',),
                                        "not_neg_integer": ('Dodaci_lhuta', 'Min_obj_mnozstvi'),
                                        }
                           }
        self.curr_entry_dict = self.entry_dict.get(self.current_table, {})
        self.title = "ÚPRAVA " + str(self.curr_table_config["name"])        


    def open_edit_window(self, item_values):
        """
        Metoda pro úpravu vybrané položky z Treeview.

        :params item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
        """
        self.item_values = item_values
        self.init_curr_dict()        
        self.initialize_title()       
        self.id_num = self.item_values[0]
        self.id_col_name = self.curr_table_config.get("id_col_name", "id")
        self.show_for_editing()


class ItemFrameAdd(ItemFrameBase):
    """
    Třída ItemFrameAdd se stará o tvorbu nových položek.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns)
        self.current_view_instance = current_view_instance
        self.action = 'add'
        self.update_frames(action=self.action)        


    def init_curr_dict(self):
        """
        Metoda pro přidání slovníku hodnotami přiřazenými dle aktuální tabulky.
        """
        self.actual_date = datetime.now().strftime("%Y-%m-%d")
        self.entry_dict = {"sklad": {"read_only": ('Evidencni_cislo', 'Interne_cislo', 'Mnozstvi_ks_m_l', 'Jednotkova_cena_EUR',
                                                   'Celkova_cena_EUR', 'Objednano', 'Cislo_objednavky', 'Jednotky', 'Dodavatel',),
                                     "pack_forget": ('Objednano', 'Mnozstvi_ks_m_l', 'Datum_nakupu', 'Cislo_objednavky',
                                                     'Jednotkova_cena_EUR', 'Celkova_cena_EUR',),
                                     "insert": {'Evidencni_cislo': self.new_id, 'Interne_cislo': self.new_interne_cislo, 'Mnozstvi_ks_m_l': '0',
                                                'Jednotkova_cena_EUR': '0.0', 'Celkova_cena_EUR': '0.0',},
                                     "mandatory": ('Min_Mnozstvi_ks', 'Nazev_dilu', 'Jednotky',),
                                     "not_neg_integer":('Min_Mnozstvi_ks',),
                                     },                                 
                           "dodavatele": {"read_only": ('id',),
                                          "insert": {'id': self.new_id},
                                          "mandatory": ('Dodavatel',),
                                          },
                           "zarizeni": {"read_only": ('id',),
                                        "insert": {'id': self.new_id},
                                        "mandatory": ('Zarizeni', 'Nazev_zarizeni', 'Umisteni', 'Typ_zarizeni',),
                                        },                            
                           "varianty": {"read_only": ('id','Nazev_dilu', 'id_sklad', 'Dodavatel', 'id_dodavatele',),
                                        "mandatory": ('Nazev_varianty', 'Cislo_varianty', 'Dodavatel', 'Jednotkova_cena_EUR',),
                                        "insert": {'Dodaci_lhuta': 0, 'Min_obj_mnozstvi':0,},
                                        "not_neg_real":('Jednotkova_cena_EUR',),
                                        "not_neg_integer": ('Dodaci_lhuta', 'Min_obj_mnozstvi'),
                                        "calculate": 'id_dodavatele',
                                        },
                           }
        self.curr_entry_dict = self.entry_dict.get(self.current_table, {})
        self.title = "VYTVOŘENÍ " + str(self.curr_table_config["name"])        


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
        self.new_id = item_values[0]
        self.new_interne_cislo = None
        self.item_values = item_values
        dodavatel_value = self.item_values[-1]
        if dodavatel_value:
            id_dodavatele_value = self.suppliers_dict[dodavatel_value]
            self.item_values[2] = id_dodavatele_value
        self.init_curr_dict()        
        self.initialize_title(add_name_label=False)       
        self.show_for_editing()
                

class ItemFrameMovements(ItemFrameBase):
    """
    Třída ItemFrameMovements se stará o příjem a výdej ve skladě.
    """
    def __init__(self, master, controller, col_names, current_table, check_columns, current_view_instance):
        """
        Inicializace prvků v item_frame.
        
        :param: Inicializovány v rodičovské třídě.
        """
        super().__init__(master, controller, col_names, current_table, check_columns)
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
                                 "actual_value": {'Typ_operace': "PŘÍJEM", 'Operaci_provedl': self.name_of_user,
                                                  'Datum_nakupu': self.actual_date, 'Datum_vydeje': "",},
                                 "tuple_values_to_save": ('Objednano', 'Mnozstvi_ks_m_l', 'Umisteni', 'Dodavatel', 'Datum_nakupu',
                                                          'Cislo_objednavky', 'Jednotkova_cena_EUR', 'Celkova_cena_EUR', 'Poznamka'),
                                 },
                      "vydej": {"grid_forget": ('Nazev_dilu', 'Celkova_cena_EUR', 'Objednano', 'Dodavatel', 'Cas_operace',
                                                'Cislo_objednavky', 'Jednotkova_cena_EUR', 'Datum_nakupu', 'id'),
                                "mandatory": ('Zmena_mnozstvi', 'Pouzite_zarizeni', 'Umisteni'),
                                "date":('Datum_vydeje',),
                                "pos_integer":('Zmena_mnozstvi',),
                                "actual_value": {'Typ_operace': "VÝDEJ", 'Operaci_provedl': self.name_of_user,
                                                  'Datum_nakupu': "", 'Datum_vydeje': self.actual_date,},
                                "tuple_values_to_save": ('Mnozstvi_ks_m_l', 'Umisteni', 'Poznamka', 'Celkova_cena_EUR'),
                                },
                      },
            }              
        self.title = self.action_dict[self.current_table][self.action]["actual_value"]['Typ_operace']
        self.entry_dict = {"sklad": {"read_only": ('Ucetnictvi', 'Evidencni_cislo', 'Interne_cislo', 'Jednotky',
                                                   'Mnozstvi_ks_m_l', 'Typ_operace', 'Operaci_provedl', 'Pouzite_zarizeni',
                                                   'Dodavatel'),
                                     "insert_item_value": ('Ucetnictvi', 'Evidencni_cislo', 'Interne_cislo', 'Jednotky',
                                                           'Mnozstvi_ks_m_l', 'Umisteni', 'Jednotkova_cena_EUR', 'Objednano',
                                                           'Poznamka', 'Nazev_dilu'),
                                     },
                           }
        self.title = f"{self.title} ZBOŽÍ"       
        self.curr_entry_dict = self.entry_dict[self.current_table] | self.action_dict[self.current_table][self.action]
        self.devices = tuple(self.controller.fetch_dict("zarizeni").keys())


    def init_item_movements(self, action, item_values, audit_log_col_names):
        """
        Metoda pro inicializace proměnných pro příjem a výdej skladových položek.

        :params action: Parametr s názvem akce příjem nebo výdej zboží - "prijem", "vydej".
                item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
                audit_log_col_names: N-tice názvů sloupců tabulky audit_log.      
        """
        self.action = action
        self.item_values = item_values
        self.audit_log_col_names = audit_log_col_names
        self.init_curr_dict()
        self.initialize_title()
        self.update_frames(action=self.action)         
        self.id_num = self.item_values[0]
        self.id_col_name = self.curr_table_config.get("id_col_name", "id")
        self.entries_al = {}
        self.actual_quantity = int(self.item_values[self.curr_table_config["quantity_col"]])
        self.actual_unit_price = float(self.item_values[self.curr_table_config["unit_price_col"]])


    def enter_item_movements(self, action, item_values, audit_log_col_names):
        """
        Metoda pro příjem a výdej skladových položek.

        :params action: Parametr s názvem akce příjem nebo výdej zboží - "prijem", "vydej".
                item_values: Aktuální hodnoty z databázové tabulky dle id vybrané položky z Treeview.
                audit_log_col_names: N-tice názvů sloupců tabulky audit_log.    
        """
        self.init_item_movements(action, item_values, audit_log_col_names)
        
        if self.action=='vydej' and self.actual_quantity==0:
            self.current_view_instance.show_selected_item()
            messagebox.showwarning("Chyba", f"Položka aktuálně není na skladě, nelze provést výdej!")
            return
        
        for idx, col in enumerate(self.audit_log_col_names):
            if col in self.col_names:
                index = self.col_names.index(col)
            self.left_frame.columnconfigure(1, weight=1)
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


class CommonResources:
    """
    Třída uchovávající všechna konfigurační data, slovníky, seznamy, n-tice a metody pro přístup
    k specifickým podskupinám těchto dat.
    """
    main_window_title = 'Skladová databáze HPM HEAT SK - verze 1.40 MVC OOP'
    
    tab2hum = {
        'Ucetnictvi': 'Účetnictví', 'Kriticky_dil': 'Kritický díl', 'Evidencni_cislo': 'Evid. č.',
        'Interne_cislo': 'Č. karty', 'Min_Mnozstvi_ks': 'Minimum', 'Objednano': 'Objednáno?',
        'Nazev_dilu': 'Název dílu', 'Mnozstvi_ks_m_l': 'Akt. množství', 'Jednotky':'Jedn.',
        'Umisteni': 'Umístění', 'Dodavatel': 'Dodavatel', 'Datum_nakupu': 'Datum nákupu',
        'Cislo_objednavky': 'Objednávka', 'Jednotkova_cena_EUR': 'EUR/jednotka',
        'Celkova_cena_EUR': 'Celkem EUR', 'Poznamka': 'Poznámka', 'Zmena_mnozstvi': 'Změna množství',
        'Cas_operace': 'Čas operace', 'Operaci_provedl': 'Operaci provedl', 'Typ_operace': 'Typ operace',
        'Datum_vydeje': 'Datum výdeje', 'Pouzite_zarizeni': 'Použité zařízení', 'id': 'ID',
        'Kontakt': 'Kontaktní osoba', 'E-mail': 'E-mail', 'Telefon': 'Telefon',
        'id_sklad': 'Evidenční číslo', 'id_dodavatele': 'ID dodavatele', 'Nazev_varianty': 'Název varianty',
        'Cislo_varianty': 'Číslo varianty', 'Dodaci_lhuta': 'Dod. lhůta dnů',
        'Min_obj_mnozstvi': 'Min. obj. množ.', 'Zarizeni': 'Zařízení', 'Nazev_zarizeni': 'Název zařízení',
        'Umisteni': 'Umístění', 'Typ_zarizeni': 'Typ zařízení', 'Pod_minimem': 'Pod minimem'
        }

    common_radiobutton_menus = {"Zobrazení":
                                [("Sklad", 'sklad'),
                                 ("Varianty", 'varianty'),
                                 ("Auditovací log", 'audit_log'),
                                 ("Dodavatelé", 'dodavatele'),
                                 ("Zařízení", 'zarizeni'),],
                                }

    view_table_config = {
        "sklad": {"check_columns": ('Pod_minimem', 'Ucetnictvi', 'Kriticky_dil',),
                  "hidden_columns": ('Pod_minimem', 'Ucetnictvi', 'Kriticky_dil', 'Objednano',),
                  "special_columns": ('Pod_minimem', 'Ucetnictvi', 'Kriticky_dil',),
                  "id_col_name": 'Evidencni_cislo',
                  "quantity_col": 7,
                  "default_params": {"width": 70, "anchor": "center"},                  
                  "col_params_dict": {
                      'Nazev_dilu': {"width": 400, "anchor": "w"},
                      'Dodavatel': {"width": 150, "anchor": "w"},
                      'Poznamka': {"width": 150, "anchor": "w"},
                      'Jednotky': {"width": 25, "anchor": "center"},
                      'Evidencni_cislo': {"width": 25, "anchor": "center"},
                      'Interne_cislo': {"width": 25, "anchor": "center"},
                      },
                  },
        "audit_log": {"check_columns": ('Ucetnictvi',),
                      "hidden_columns": ('Objednano', 'Poznamka', 'Cas_operace',),
                      "special_columns": ('Ucetnictvi',),
                      "col_params_dict": {
                          'Nazev_dilu': {"width": 230, "anchor": "w"},
                          'Dodavatel': {"width": 100, "anchor": "w"},
                          'Pouzite_zarizeni': {"width": 100, "anchor": "w"},
                          'Jednotky': {"width": 30, "anchor": "center"},
                          'Evidencni_cislo': {"width": 30, "anchor": "center"},
                          'Interne_cislo': {"width": 30, "anchor": "center"},
                          },
                      },
        "dodavatele": {"col_params_dict": {
                           'Nazev_zarizeni': {"width": 300, "anchor": "w"},
                           },
                       "default_params": {"width": 80, "anchor": "center"},
                       },
                "dodavatele": {"col_params_dict": {
                           'Dodavatel': {"width": 300, "anchor": "w"},
                           },
                       },       
        "varianty": {"check_columns": ('Pod_minimem',),
                     "hidden_columns": ('Pod_minimem',),
                     "special_columns": ('Pod_minimem',),
                     "col_params_dict": {
                         'Dodavatel': {"width": 100, "anchor": "w"},
                         'Nazev_varianty': {"width": 300, "anchor": "w"},
                         'Nazev_dilu': {"width": 200, "anchor": "w", "stretch": tk.YES},
                         },
                     },
        "item_variants": {"col_params_dict": {
                              'Nazev_varianty': {"width": 300, "anchor": "w"},
                              'Nazev_dilu': {"width": 200, "anchor": "w", "stretch": tk.YES},  
                              'Dodavatel': {"width": 100, "anchor": "w", "stretch": tk.YES},
                              },
                          },
        }

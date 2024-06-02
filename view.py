import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import tkinter.font as tkFont
from datetime import datetime, timedelta
import re
import sys
import unicodedata
import hashlib

from commonresources import CommonResources
from itemframe import *

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
        self.current_user = self.controller.current_user
        self.name_of_user = self.controller.name_of_user        
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
        self.initialize_logged_user_label()
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
        self.logged_user_frame = tk.LabelFrame(self.top_frames_container, text="Přihlášený uživatel",
                                                  borderwidth=2, relief="groove")
        self.logged_user_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False)        
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


    def initialize_logged_user_label(self):
        """
        Inicializace labelu se zobrazením přihlášeného uživatel.
        """
        self.logged_user_label = tk.Label(self.logged_user_frame, text=self.name_of_user)
        self.logged_user_label.pack(pady=3, padx=2)


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
        varianty_table_config = CommonResources.view_table_config.get(varianty_table, {})
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
           


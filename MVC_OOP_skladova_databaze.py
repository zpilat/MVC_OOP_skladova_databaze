import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import sqlite3
import webbrowser
import urllib.parse

from model import Model
from view import *
    

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
        self.varianty_view_instance = None
        self.current_user = None
        self.name_of_user = None        
        self.current_role = None


    def fetch_dict(self, table):
        """
        Získání seznamu dodavatelů nebo zařízení'.

        :param table: pro výběr tabulky, ze které se získávají data.
        :return slovník dodavatelů nebo zařízení s jejich id jako hodnotou.
        """
        data = self.model.fetch_data(table)
        if table == "sklad":
            name=6
        else: name=1
        return {row[name]: row[0] for row in data}


    def get_max_id(self, curr_table, id_col_name):
        """
        Získání nejvyššího evidenčního čísla z tabulky 'sklad'.

        :param id_col: Číslo sloupce, ve kterém jsou id čísla pro danou tabulku.
        :return Nejvyšší hodnotu ve sloupci 'Evidencni_cislo' v tabulce sklad.
        """
        return self.model.get_max_id(curr_table, id_col_name)
    

    def show_data(self, table, current_id_num=None):
        """
        Získání a zobrazení dat z vybrané tabulky v GUI. Pokud se mění tabulka k zobrazení,
        vytvoří se nová instance podtřídy View, pokud zůstává tabulka
        stejná, pouze se aktulizují zobrazená data.
        
        :param table: Název tabulky pro zobrazení.
        """     
        if table == 'varianty':
            data = self.model.fetch_varianty_data()
            col_names = list(self.model.fetch_col_names(table)) + ["Nazev_dilu", "Dodavatel", "Pod_minimem"]
        elif table == 'sklad':
            data = self.model.fetch_sklad_data()
            col_names = list(self.model.fetch_col_names(table)) + ["Pod_minimem"]
        else:
            data = self.model.fetch_data(table)
            col_names = self.model.fetch_col_names(table)

        if self.current_table != table:
            self.current_table = table
            self.current_view_instance.frame.destroy()
            if table == "sklad":
                self.current_view_instance = SkladView(self.root, self, col_names, self.current_table)
            elif table == "audit_log":
                self.current_view_instance = AuditLogView(self.root, self, col_names, self.current_table)
            elif table == "dodavatele":
                self.current_view_instance = DodavateleView(self.root, self, col_names, self.current_table)
            elif table == "varianty":
                self.current_view_instance = VariantyView(self.root, self, col_names, self.current_table)
            elif table == "zarizeni":
                self.current_view_instance = ZarizeniView(self.root, self, col_names, self.current_table)
            elif table == "uzivatele":
                self.current_view_instance = UzivateleView(self.root, self, col_names, self.current_table)                
            else:
                messagebox.showwarning("Varování", "Nebyla vytvořena nová instance třídy View.")
                return
        
        if current_id_num:
            self.current_view_instance.add_data(data, current_id_num=current_id_num)
        else:
            self.current_view_instance.add_data(data)


    def show_data_for_editing(self, table, id_num, id_col_name, master, check_columns):
        """
        Získání dat a zobrazení vybrané položky pro úpravu. Vytvoří se nová instance ItemFrameEdit.
        
        :param table: Název tabulky pro zobrazení.
        :param id_num: Identifikační číslo položky pro zobrazení.
        """
        item_values = self.model.fetch_item_for_editing(table, id_num, id_col_name)
        col_names = self.model.fetch_col_names(table)

        action="edit"
        self.current_item_instance = ItemFrameEdit(master, self, col_names, table, check_columns,
                                                   action, self.current_view_instance)
        self.current_item_instance.open_edit_window(item_values)


    def start_login(self):
        """
        Metoda pro spuštění přihlašování uživatele. Vytvoří se nová instance LoginView.
        """
        # při programov;ání pro přeskočení přihlašování, potom vyměnit za okomentovaný kód
        self.current_user = "pilat"
        self.name_of_user = "Zdeněk Pilát"
        self.current_role = "admin"
        self.current_table = "sklad"
        data = self.model.fetch_sklad_data()
        col_names = list(self.model.fetch_col_names(self.current_table)) + ["Pod_minimem"]
        self.current_view_instance = SkladView(self.root, self, col_names, self.current_table)
        self.current_view_instance.add_data(data)
        if sys.platform.startswith('win'):
            self.root.state('zoomed')
        else:
            window_width=1920
            window_height=1080
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            center_x = int((screen_width/2) - (window_width/2))
            center_y = int((screen_height/2) - (window_height/2))
            self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        
##        self.current_table = "login"
##        col_names = []            
##        self.current_view_instance = LoginView(self.root, self, col_names, self.current_table)


    def attempt_login(self, username, password_hash):
        """
        Zkusí přihlásit uživatele se zadanými přihlašovacími údaji.
        
        :param username: Uživatelské jméno.
        :param password_hash: Zahashované heslo.
        """        
        if self.model.verify_user_credentials(username, password_hash):
            self.current_user = username
            self.name_of_user, self.current_role = self.model.get_user_info(self.current_user)
            self.current_view_instance.start_main_window()
        else:
            self.current_view_instance.handle_failed_login()


    def show_data_for_movements(self, table, id_num, id_col_name, master, check_columns, action):
        """
        Získání dat a zobrazení vybrané položky pro skladový pohyb. Vytvoří se nová instance ItemFrameMovements.
        
        :param table: Název tabulky pro zobrazení.
        :param id_num: Identifikační číslo položky pro zobrazení.
        """
        item_values = self.model.fetch_item_for_editing(table, id_num, id_col_name)
        col_names = self.model.fetch_col_names(table)
        audit_log_col_names = self.model.fetch_col_names("audit_log")

        
        self.current_item_instance = ItemFrameMovements(master, self, col_names, table, check_columns,
                                                        action, self.current_view_instance)
        self.current_item_instance.enter_item_movements(item_values, audit_log_col_names)


    def add_item(self, table, id_num, id_col_name, master, check_columns):
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

        action="add"        
        self.current_item_instance = ItemFrameAdd(master, self, col_names, table, check_columns,
                                                  action, self.current_view_instance)
        self.current_item_instance.add_item(new_id, new_interne_cislo)


    def add_variant(self, table, id_num, id_col_name, master, varianty_check_columns,
                    varianty_table, varianty_id_col_name, curr_unit_price):
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
        varianty_item_values[5] = curr_unit_price if curr_unit_price else ""

        action="add"                                         
        self.current_item_instance = ItemFrameAdd(master, self, varianty_col_names, varianty_table,
                                                  varianty_check_columns, action, self.current_view_instance)
        self.current_item_instance.add_variant(varianty_item_values)


    def show_item_variants(self, id_num, frame):
        """
        Metoda, která získá data variant dvojklikem vybrané skladové položky a
        pošle je k zobrazení do item_frame.

        :param id_num: evideční číslo dvojklikem vybrané skladové položky.
        :return 
        """
        table = "varianty"
        id_col_name = "id_sklad"
        if self.varianty_view_instance:
            self.varianty_view_instance.frame.destroy()
        try:
            variants_data = self.model.fetch_item_variants(table, id_num, id_col_name)
            col_names = list(self.model.fetch_col_names(table)) + ["Dodavatel"]
        except Exception as e:
            messagebox.showwarning("Varování", f"Nebyla získána data variant z důvodu chyby:\n {e}")
            return
        if not variants_data:
            return
        current_table = "item_variants"
        self.varianty_view_instance = ItemVariantsView(frame, self, col_names, current_table)
        self.varianty_view_instance.add_data(variants_data)  


    def check_existence_of_variant(self, id_sklad_value, id_dodavatele_value, current_table):
        """
        Metoda, která ověří, zda varianta už neexistuje před uložením nové.

        :return True, když varianta už v tabulce "varianty" existuje, jinak False.
        """
        try:
            exists_variant = self.model.check_existence(id_sklad_value, id_dodavatele_value, current_table)
        except Exception as e:
            messagebox.showwarning("Varování", f"Nebyla získána data variant z důvodu chyby:\n {e}")
            return False           
        return exists_variant


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
            messagebox.showwarning("Varování", "Položka se zadaným ID číslem, uživatelem nebo jménem už v databázi existuje.")
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


    def add_column_and_set_default(self, new_col_name):
        """
        Řídí proces přidání nového sloupce do tabulky 'sklad' a nastavení jeho výchozích hodnot.

        :param new_col_name: Název nového sloupce, který má být přidán.
        """
        try:
            self.model.add_integer_column_with_default(new_col_name)
            messagebox.showinfo("Informace",
                                f"Sloupec {new_col_name} byl úspěšně přidán do tabulky sklad s výchozími hodnotami 0.")
        except Exception as e:
            messagebox.showerror("Chyba", f"Nastala chyba při přidávání sloupce {new_col_name}: {e}")
            return False
        return True


    def fetch_data_for_inquiry(self, ids):
        """
        Načte specifická data na základě ID z tabulky varianty a získá odpovídající data ze tabulek varianty a sklad.

        :param ids: Seznam nebo n-tice ID položek z tabulky varianty.
        :return: Seznam n-tic s hodnotami rozdíl 'Min_Mnozstvi_ks' - 'Mnozstvi_ks_m_l', jednotky ,
                 název varianty, číslo varianty pro každou odpovídající položku.
        """
        
        try:
            data_for_inquiry = self.model.fetch_data_for_inquiry(ids)
        except Exception as e:
            messagebox.showwarning("Varování", f"Chyba při načítání dat z databáze: {e}!")
            return False
        return data_for_inquiry


    def fetch_supplier_for_inquiry(self, id_name):
        """
        Získání dat dodavatele, pro kterého se tvoří poptávka, na základě získaného jména dodavatel.
        
        :param id_num: Jméno dodavatele pro zobrazení.
        :return slovník s klíči názvy sloupců a hodnotami pro dodavatele s jménem id_name.
        """
        table="dodavatele"
        col_name="Dodavatel"

        col_names = self.model.fetch_col_names(table)        
        item_values = self.model.fetch_item_for_editing(table, id_name, col_name)

        return dict(zip(col_names, item_values))


    def open_email_client(self, recipient, subject, body):
        """
        Otevře nový email výchozího emailového klienta s předvyplněnými údaji (emailová adresa, předmět a tělo zprávy).

        :params recipient: E-mailová adresa příjemce.
                subject: Předmět e-mailu.
                body: Tělo e-mailu - vytvořená poptávka.
        """     
        subject_encoded = urllib.parse.quote(subject)
        body_encoded = urllib.parse.quote(body)

        mailto_link = f"mailto:{recipient}?subject={subject_encoded}&body={body_encoded}"
        
        webbrowser.open(mailto_link)    
    

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
        elif table:    
            col_names = self.model.fetch_col_names(table)
            data = self.model.fetch_data(table)
        else:
            messagebox.showwarning("Upozornění", "Nebyla vybrána tabulka ani tree pro export.")
            return

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
    root.title('Skladová databáze HPM HEAT SK')
    db_path = '.'                                                 #Z:\Údržba\Sklad\Skladová databáze'
    db_file = os.path.join( db_path , 'skladova_databaze_EC0.db') # Změňte na aktuální název souboru DB včetně cesty    
    controller = Controller(root, db_file)
    controller.start_login()
    root.mainloop()

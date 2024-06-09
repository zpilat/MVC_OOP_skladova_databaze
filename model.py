import sqlite3

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


    def fetch_sklad_data(self):
        """
        Načte rozšířená data z tabulky sklad včetně sloupce s informací, zda je množství pod minimem.
        
        :return: Data variant spolu s názvy dílů a dodavatelů.
        """
        query = """
        SELECT *,
               CASE 
                   WHEN Mnozstvi_ks_m_l < Min_Mnozstvi_ks THEN 1
                   ELSE 0
               END AS 'Pod_minimem' FROM sklad
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()


    def fetch_varianty_data(self):
        """
        Načte rozšířená data variant, včetně názvů dílů a dodavatelů z ostatních tabulek a indikaci Pod minimem.
        
        :return: Data variant spolu s názvy dílů a dodavatelů a informací, zda je množství pod minimálním množstvím.
        """
        query = """
        SELECT v.*, s.Nazev_dilu, d.Dodavatel,
               CASE 
                   WHEN s.Mnozstvi_ks_m_l < s.Min_Mnozstvi_ks THEN 1
                   ELSE 0
               END AS 'Pod_minimem'
        FROM varianty v
        JOIN sklad s ON v.id_sklad = s.Evidencni_cislo
        JOIN dodavatele d ON v.id_dodavatele = d.id
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()


    def fetch_item_variants(self, table, id_num, id_col_name):
        """
        Získání dat variant položky pro na základě ID pro zobrazení ve spodním frame.

        :param table: Název tabulky, ze které se položka získává.
        :param id_num: Číslo ID položky, ke které chceme získat varianty.
        :param id_col_name: Název sloupce, který obsahuje ID položky.
        :return: Seznam n-tic s daty variant položky a sloupcem Dodavatel z tabulky dodavatele
                 nebo None, pokud položka nebyla nalezena.
        """
        query = f"""
        SELECT v.*, d.Dodavatel
        FROM {table} AS v
        JOIN dodavatele AS d ON v.id_dodavatele = d.id
        WHERE v.{id_col_name} = ?
        """
        self.cursor.execute(query, (id_num,))
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


    def fetch_data_for_inquiry(self, ids):
        """
        Načte specifická data na základě ID z tabulky varianty a získá odpovídající data ze tabulky sklad.

        :param ids: Seznam ID položek z tabulky varianty.
        :return: Seznam n-tic s hodnotami: rozdíl 'Min_Mnozstvi_ks' - 'Mnozstvi_ks_m_l',
                 jednotky, název varianty, číslo varianty pro každou odpovídající položku.
        """
        ids_placeholder = ','.join('?' for _ in ids)
        
        query = f"""
        SELECT (s.Min_Mnozstvi_ks - s.Mnozstvi_ks_m_l) AS Rozdil, s.Jednotky, v.Cislo_varianty, v.Nazev_varianty
        FROM sklad s
        JOIN varianty v ON s.Evidencni_cislo = v.id_sklad
        WHERE v.id IN ({ids_placeholder})
        """
        self.cursor.execute(query, ids)
        return self.cursor.fetchall()


    def check_existence(self, id_sklad_value, id_dodavatele_value, current_table):
        """
        SQL dotaz pro ověření existence varianty před uložením nové.
        """
        query = f"""SELECT EXISTS(
                        SELECT 1 FROM {current_table} 
                        WHERE id_sklad = ? AND id_dodavatele = ?
                    )"""
        self.cursor.execute(query, (id_sklad_value, id_dodavatele_value))

        return self.cursor.fetchone()[0] == 1    


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
        :param updated_values: Slovník, kde klíče jsou názvy sloupců a hodnoty
                               jsou aktualizované hodnoty pro tyto sloupce.
        """
        set_clause = ', '.join([f"`{key}` = ?" for key in updated_values.keys()])
        values = list(updated_values.values())
        values.append(id_num)
        sql = f"UPDATE `{table}` SET {set_clause} WHERE `{id_col_name}` = ?"

        self.cursor.execute(sql, values)
        self.conn.commit()


    def add_integer_column_with_default(self, new_col_name):
        """
        Přidá nový sloupec typu Integer do tabulky 'sklad' s výchozí hodnotou 0.
        
        :param new_col_name: Název nového sloupce, který má být přidán.
        """
        alter_table_query = f"ALTER TABLE sklad ADD COLUMN {new_col_name} INTEGER DEFAULT 0"
        self.cursor.execute(alter_table_query)
        self.conn.commit() 


    def delete_row(self, evidencni_cislo):
        """
        Smaže řádek ze skladu na základě jeho evidenčního čísla - ve sloupci Evidencni_cislo.      
        :Params evidencni_cislo (int): Evidencni_cislo řádku, který má být smazán.
        """
        self.cursor.execute("DELETE FROM sklad WHERE `Evidencni_cislo`=?", (evidencni_cislo,))
        self.conn.commit()


    def verify_user_credentials(self, username, password_hash):
        """
        Ověří, zda zadané uživatelské jméno a hash hesla odpovídají údajům v databázi.

        :param username: Uživatelské jméno k ověření.
        :param password_hash: Hash hesla k ověření.
        :return: True, pokud údaje odpovídají; jinak False.
        """
        query = "SELECT password_hash FROM uzivatele WHERE username = ?"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        if result:
            stored_password_hash = result[0]
            return stored_password_hash == password_hash
        else:
            return False        
        

    def get_user_info(self, username):
        """
        Získá jméno a roli uživatele z databáze na základě jeho uživatelského jména.

        Tato metoda vyhledá v databázi v tabulce "uzivatele" řádek, který odpovídá
        zadanému uživatelskému jménu, a vrátí jméno uživatele a jeho roli
        z odpovídajících sloupců "name" a "role".

        :param username: Uživatelské jméno, pro které má být informace získána.
        :return: Tuple obsahující jméno uživatele a jeho roli nebo (None, None),
                 pokud uživatel s takovým uživatelským jménem neexistuje.
        """
        try:
            self.cursor.execute("SELECT name, role FROM uzivatele WHERE username = ?", (username,))
            result = self.cursor.fetchone()
            if result:
                return result
            else:
                return (None, None)
        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba při získávání informací o uživateli: {e}")
            return (None, None)


    def __del__(self):
        """
        Destruktor pro uzavření databázového připojení při zániku instance.
        """
        self.conn.close()

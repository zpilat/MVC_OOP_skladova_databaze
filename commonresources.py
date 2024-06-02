import tkinter as tk

class CommonResources:
    """
    Třída uchovávající všechna konfigurační data, slovníky, seznamy, n-tice a metody pro přístup
    k specifickým podskupinám těchto dat.
    """   
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

    item_frame_table_config = {
        "sklad": {"order_of_name": 6,
                  "id_col_name": "Evidencni_cislo", "quantity_col": 7,
                  "unit_price_col": 13,
                  "focus": 'Nazev_dilu',
                  "name": "SKLADOVÉ KARTY",
                  },
        "audit_log": {"order_of_name": 5,
                      "name": "POHYBU NA SKLADĚ",
                      },
        "dodavatele": {"order_of_name": 1,
                       "focus": 'Dodavatel',
                       "name": "DODAVATELE",
                       },
        "varianty": {"order_of_name": 3,
                     "focus": 'Nazev_varianty',
                     "name": "VARIANTY",
                     },
        "zarizeni": {"order_of_name": 1,
                     "focus": 'Zarizeni',
                     "name": "ZAŘÍZENÍ",
                     },
        }    

    main_window_title = 'Skladová databáze HPM HEAT SK - verze 1.39 MVC OOP'

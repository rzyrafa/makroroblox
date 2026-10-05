# gui.py — Menedżer i interfejs graficzny Makroblox Sniper
import sys
import os
import json
import time
import subprocess
import threading
import queue
import urllib.request
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox

class _NullWriter:
    def write(self, s):
        pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = _NullWriter()
if sys.stderr is None:
    sys.stderr = _NullWriter()

# Rejestracja katalogów DLL dla Windows (zwłaszcza w środowisku PyInstaller)
if hasattr(sys, '_MEIPASS'):
    os.environ['PATH'] = sys._MEIPASS + ';' + os.path.join(sys._MEIPASS, 'tesserocr') + ';' + os.environ.get('PATH', '')
    if hasattr(os, 'add_dll_directory'):
        for p in [sys._MEIPASS, os.path.join(sys._MEIPASS, 'tesserocr')]:
            if os.path.exists(p):
                try:
                    os.add_dll_directory(p)
                except Exception:
                    pass

# Import modułu makro w głównym wątku (wymagane przez tesserocr / cysignals na Windows!)
import makro

# Ścieżka do pliku konfiguracyjnego
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
MAKRO_SCRIPT = os.path.join(BASE_DIR, "makro.py")
PYTHON_EXE = sys.executable

DEFAULT_CONFIG = {
    "resolution": "1440p",
    "stop_after_buy": False,
    "ntfy_topic": "botdorestaracji2115",
    "discord_webhook": "",
    "whatsapp_phone": "",
    "whatsapp_apikey": "",
    "timers": {
        "lead_time": 1.5,
        "wait_results": 0.30,
        "wait_open": 0.30,
        "wait_refresh": 0.50,
        "wait_back": 0.20,
        "price_timeout": 3.5,
        "start_delay": 3
    },
    "targets": [
        {"name": "Davy Jones Chair", "query": "davy jones chair", "max": 200, "refresh_wait": 10},
        {"name": "Davy Jones Table", "query": "davy jones table", "max": 100, "refresh_wait": 10},
        {"name": "Sunken Chair",     "query": "sunken chair",     "max": 70,  "refresh_wait": 10},
        {"name": "Sunken Table",     "query": "sunken table",     "max": 60,  "refresh_wait": 10},
        {"name": "Celestial Chair",  "query": "celestial chair",  "max": 200, "refresh_wait": 10}
    ],
    "profiles": {
        "1440p": {
            "label": "2560x1440 (Komputer stacjonarny)",
            "search_box": [1777, 448],
            "item_1": [1050, 608],
            "refresh_btn": [1668, 326],
            "buy_btn": [1714, 1041],
            "back_btn": [726, 461],
            "popup_confirm_btn": [1082, 887],
            "popup_cancel_btn": [1478, 886],
            "popup_select_item_x": [1818, 358],
            "market_buy_tab": [750, 580],
            "market_sell_tab": [750, 470],
            "item_price": {"top": 1030, "left": 1573, "width": 280, "height": 50},
            "item_header_region": {"top": 435, "left": 770, "width": 650, "height": 55},
            "popup_text_region": {"top": 680, "left": 860, "width": 840, "height": 80},
            "failsafe_popup_x_check": {"top": 350, "left": 1785, "width": 30, "height": 25},
            "failsafe_sell_tab_check": {"top": 460, "left": 740, "width": 20, "height": 20}
        },
        "1080p": {
            "label": "1920x1080 (Laptop)",
            "search_box": [1348, 327],
            "item_1": [800, 420],
            "refresh_btn": [1277, 226],
            "buy_btn": [1252, 791],
            "back_btn": [526, 330],
            "popup_confirm_btn": [800, 669],
            "popup_cancel_btn": [1106, 666],
            "popup_select_item_x": [1108, 202],
            "market_buy_tab": [530, 427],
            "market_sell_tab": [522, 327],
            "item_price": {"top": 773, "left": 1216, "width": 189, "height": 41},
            "item_header_region": {"top": 308, "left": 591, "width": 303, "height": 40},
            "popup_text_region": {"top": 508, "left": 649, "width": 537, "height": 60},
            "failsafe_popup_x_check": {"top": 100, "left": 100, "width": 1, "height": 1},
            "failsafe_sell_tab_check": {"top": 100, "left": 100, "width": 1, "height": 1}
        }
    }
}

class SniperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Roblox Sniper Macro Manager v1.0")
        self.geometry("900x700")
        self.minsize(820, 600)

        self.proc = None
        self.log_reader_thread = None
        self.config_data = self.load_config()
        # Tkinter nie jest thread-safe — wątek makra tylko wrzuca do kolejki, a główny wątek ją opróżnia
        self.ui_queue = queue.Queue()

        self._init_styles()
        self._build_ui()
        self.populate_data()
        self._drain_ui_queue()

    def _drain_ui_queue(self):
        chunks = []
        try:
            while True:
                item = self.ui_queue.get_nowait()
                if callable(item):
                    if chunks:
                        self.log_raw("".join(chunks))
                        chunks = []
                    item()
                else:
                    chunks.append(item)
        except queue.Empty:
            pass
        if chunks:
            self.log_raw("".join(chunks))
        self.after(50, self._drain_ui_queue)

    def _init_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        self.style.configure(".", font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"))
        self.style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))
        self.style.configure("Start.TButton", font=("Segoe UI", 11, "bold"), foreground="green")
        self.style.configure("Stop.TButton", font=("Segoe UI", 11, "bold"), foreground="red")

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                # Uzupełnij ewentualne brakujące klucze z domyślnych
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                return data
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się odczytać config.json: {e}")
        return json.loads(json.dumps(DEFAULT_CONFIG))

    def save_config(self, show_msg=True):
        self.collect_data_from_ui()
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            if show_msg:
                messagebox.showinfo("Sukces", "Konfiguracja została pomyślnie zapisana w config.json!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać config.json: {e}")

    def _build_ui(self):
        # Górny pasek z profilem ekranu i statusem
        top_frame = ttk.Frame(self, padding=(10, 8, 10, 8))
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="🖥️ Profil rozdzielczości:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.res_var = tk.StringVar(value=self.config_data.get("resolution", "1440p"))
        self.res_combo = ttk.Combobox(
            top_frame,
            textvariable=self.res_var,
            values=["1440p (2560x1440 - PC)", "1080p (1920x1080 - Laptop)"],
            state="readonly",
            width=28
        )
        self.res_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.res_combo.bind("<<ComboboxSelected>>", self.on_res_change)

        self.status_lbl = ttk.Label(top_frame, text="● Makro zatrzymane", foreground="#666666", style="Status.TLabel")
        self.status_lbl.pack(side=tk.RIGHT, padx=10)

        # Główne zakładki
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        # 1. Zakładka Przedmioty (Targets)
        self.tab_targets = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_targets, text=" 🎯 Przedmioty (Targets) ")
        self._build_targets_tab()

        # 2. Zakładka Timery i Powiadomienia
        self.tab_settings = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_settings, text=" ⚙️ Ustawienia & Timery ")
        self._build_settings_tab()

        # 3. Zakładka Koordynaty (1440p / 1080p)
        self.tab_coords = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_coords, text=" 📍 Koordynaty UI ")
        self._build_coords_tab()

        # 4. Zakładka Konsola & Start
        self.tab_console = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_console, text=" 🚀 Uruchamianie & Logi ")
        self._build_console_tab()

        # Dolny pasek akcji
        bottom_frame = ttk.Frame(self, padding=(10, 6, 10, 8))
        bottom_frame.pack(fill=tk.X)

        self.btn_save = ttk.Button(bottom_frame, text="💾 Zapisz konfigurację", command=lambda: self.save_config(True))
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.btn_start = ttk.Button(bottom_frame, text="▶ URUCHOM MAKRO", style="Start.TButton", command=self.start_macro)
        self.btn_start.pack(side=tk.RIGHT, padx=5)

        self.btn_stop = ttk.Button(bottom_frame, text="⏹ ZATRZYMAJ (F8 / ESC)", style="Stop.TButton", command=self.stop_macro, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.RIGHT, padx=5)

    def _build_targets_tab(self):
        # Tabela przedmiotów
        cols = ("name", "query", "max", "refresh_wait")
        self.tree_targets = ttk.Treeview(self.tab_targets, columns=cols, show="headings", height=9, selectmode="browse")
        self.tree_targets.heading("name", text="Nazwa przedmiotu")
        self.tree_targets.heading("query", text="Fraza w szukajce")
        self.tree_targets.heading("max", text="Maksymalna cena (💎)")
        self.tree_targets.heading("refresh_wait", text="Cooldown (s)")

        self.tree_targets.column("name", width=220)
        self.tree_targets.column("query", width=220)
        self.tree_targets.column("max", width=140, anchor="center")
        self.tree_targets.column("refresh_wait", width=110, anchor="center")

        tree_scroll = ttk.Scrollbar(self.tab_targets, orient=tk.VERTICAL, command=self.tree_targets.yview)
        self.tree_targets.configure(yscrollcommand=tree_scroll.set)

        self.tree_targets.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        tree_scroll.place(in_=self.tree_targets, relx=1.0, relheight=1.0, bordermode="outside")

        self.tree_targets.bind("<<TreeviewSelect>>", self.on_target_select)

        # Formularz edycji
        edit_frame = ttk.LabelFrame(self.tab_targets, text="Dodaj / Edytuj przedmiot", padding=10)
        edit_frame.pack(fill=tk.X, pady=(10, 0))

        r1 = ttk.Frame(edit_frame)
        r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text="Nazwa:", width=12).pack(side=tk.LEFT)
        self.ent_target_name = ttk.Entry(r1)
        self.ent_target_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))

        ttk.Label(r1, text="Fraza:", width=8).pack(side=tk.LEFT)
        self.ent_target_query = ttk.Entry(r1)
        self.ent_target_query.pack(side=tk.LEFT, fill=tk.X, expand=True)

        r2 = ttk.Frame(edit_frame)
        r2.pack(fill=tk.X, pady=4)
        ttk.Label(r2, text="Max cena 💎:", width=12).pack(side=tk.LEFT)
        self.ent_target_max = ttk.Entry(r2, width=15)
        self.ent_target_max.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(r2, text="Cooldown (s):", width=12).pack(side=tk.LEFT)
        self.ent_target_cooldown = ttk.Entry(r2, width=15)
        self.ent_target_cooldown.insert(0, "10")
        self.ent_target_cooldown.pack(side=tk.LEFT)

        btn_row = ttk.Frame(edit_frame)
        btn_row.pack(fill=tk.X, pady=(8, 2))

        ttk.Button(btn_row, text="➕ Dodaj nowy", command=self.add_target).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row, text="✏️ Zaktualizuj zaznaczony", command=self.update_target).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row, text="🗑️ Usuń zaznaczony", command=self.remove_target).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row, text="🧹 Wyczyść pola", command=self.clear_target_fields).pack(side=tk.LEFT, padx=3)

    def _build_settings_tab(self):
        # Powiadomienia
        notify_box = ttk.LabelFrame(self.tab_settings, text="📲 Powiadomienia na telefon (Push)", padding=10)
        notify_box.pack(fill=tk.X, pady=(0, 10))

        r_ntfy = ttk.Frame(notify_box)
        r_ntfy.pack(fill=tk.X, pady=2)
        ttk.Label(r_ntfy, text="Temat ntfy.sh:", width=16).pack(side=tk.LEFT)
        self.ent_ntfy = ttk.Entry(r_ntfy, width=30)
        self.ent_ntfy.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(r_ntfy, text="🔔 Wyślij test na telefon", command=self.test_ntfy).pack(side=tk.LEFT)

        ttk.Label(notify_box, text="Darmowa aplikacja 'ntfy' na Android/iOS — wpisz w niej dokładnie ten sam temat.", foreground="#555555").pack(anchor=tk.W, pady=(2, 0))

        # Timery
        timers_box = ttk.LabelFrame(self.tab_settings, text="⏱️ Timery i prędkość działania (sekundy)", padding=10)
        timers_box.pack(fill=tk.X, pady=(0, 10))

        self.timer_entries = {}
        timer_defs = [
            ("lead_time",    "Lead Time (wcześniejszy start szukania):"),
            ("wait_results", "Wait Results (czas po wpisaniu do szukajki):"),
            ("wait_open",    "Wait Open (czas otwierania oferty):"),
            ("wait_refresh", "Wait Refresh (czas po refreshu przed OCR):"),
            ("wait_back",    "Wait Back (czas powrotu wstecz):"),
            ("price_timeout","Price Timeout (max czas czekania na cenę):"),
            ("start_delay",  "Start Delay (odliczanie przed startem):")
        ]

        for k, label_txt in timer_defs:
            row = ttk.Frame(timers_box)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label_txt, width=42).pack(side=tk.LEFT)
            ent = ttk.Entry(row, width=12)
            ent.insert(0, str(DEFAULT_CONFIG["timers"][k]))
            ent.pack(side=tk.LEFT)
            self.timer_entries[k] = ent

        # Zachowanie po zakupie
        behav_box = ttk.LabelFrame(self.tab_settings, text="🛡️ Zachowanie", padding=10)
        behav_box.pack(fill=tk.X)

        self.stop_after_buy_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(
            behav_box,
            text="Zatrzymaj makro natychmiast po udanym zakupie (odznaczone = polowanie w nieskończoność)",
            variable=self.stop_after_buy_var
        )
        chk.pack(anchor=tk.W)

    def _build_coords_tab(self):
        info_lbl = ttk.Label(
            self.tab_coords,
            text="Współrzędne klikania i ramki OCR dla aktywnego profilu ekranu.\n"
                 "Wartości są automatycznie przełączane zależnie od wybranego profilu na górnym pasku.",
            foreground="#333333"
        )
        info_lbl.pack(anchor=tk.W, pady=(0, 8))

        canvas = tk.Canvas(self.tab_coords, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_coords, orient=tk.VERTICAL, command=canvas.yview)
        self.coords_container = ttk.Frame(canvas)

        self.coords_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.coords_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.coord_entries = {}
        coord_defs = [
            ("search_box",          "Pasek wyszukiwania (Search Box):", "X, Y"),
            ("item_1",              "Pierwszy slot przedmiotu (Item 1):", "X, Y"),
            ("refresh_btn",         "Przycisk Odśwież (Refresh):", "X, Y"),
            ("buy_btn",             "Przycisk Kup (Buy - główny):", "X, Y"),
            ("back_btn",            "Przycisk Wstecz (<):", "X, Y"),
            ("popup_confirm_btn",   "Popup - Zielony przycisk 'Buy':", "X, Y"),
            ("popup_cancel_btn",    "Popup - Czerwony przycisk 'Cancel':", "X, Y"),
            ("popup_select_item_x", "Fail-safe: Czerwony [X] w 'Select an Item!':", "X, Y"),
            ("market_buy_tab",      "Fail-safe: Zakładka 'Buy' w Markecie:", "X, Y"),
            ("market_sell_tab",     "Fail-safe: Zakładka 'Sell' w Markecie:", "X, Y"),
            ("item_price",          "Ramka OCR Ceny:", "top, left, width, height"),
            ("item_header_region",  "Ramka OCR Nagłówka oferty:", "top, left, width, height"),
            ("popup_text_region",   "Ramka OCR Tekstu w popupie:", "top, left, width, height"),
            ("failsafe_popup_x_check",  "Fail-safe: Detekcja okienka popup [X]:", "top, left, width, height"),
            ("failsafe_sell_tab_check", "Fail-safe: Detekcja zakładki Sell:", "top, left, width, height")
        ]

        for k, label_txt, hint in coord_defs:
            row = ttk.Frame(self.coords_container)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label_txt, width=38).pack(side=tk.LEFT)
            ent = ttk.Entry(row, width=36)
            ent.pack(side=tk.LEFT, padx=(0, 6))
            ttk.Label(row, text=f"({hint})", foreground="#888888").pack(side=tk.LEFT)
            self.coord_entries[k] = ent

        btn_row = ttk.Frame(self.coords_container)
        btn_row.pack(fill=tk.X, pady=(10, 5))
        ttk.Button(btn_row, text="📋 Wklej profil z JSON (ze schowka)", command=self.paste_profile_json).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_row, text="📂 Wczytaj ponownie z config.json", command=self.reload_config_from_file).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_row, text="🔄 Przywróć domyślne współrzędne profilu", command=self.reset_profile_coords).pack(side=tk.LEFT)

    def _build_console_tab(self):
        top_c = ttk.Frame(self.tab_console)
        top_c.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(top_c, text="Podgląd konsoli makra na żywo:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        ttk.Button(top_c, text="🧹 Wyczyść logi", command=self.clear_console).pack(side=tk.RIGHT)

        self.txt_console = tk.Text(self.tab_console, bg="#111111", fg="#00FF66", font=("Consolas", 9), wrap=tk.WORD)
        scroll_c = ttk.Scrollbar(self.tab_console, orient=tk.VERTICAL, command=self.txt_console.yview)
        self.txt_console.configure(yscrollcommand=scroll_c.set)

        self.txt_console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_c.pack(side=tk.RIGHT, fill=tk.Y)

    def populate_data(self):
        # 1. Profil rozdzielczości
        cur_res = self.config_data.get("resolution", "1440p")
        if cur_res == "1080p":
            self.res_combo.set("1080p (1920x1080 - Laptop)")
        else:
            self.res_combo.set("1440p (2560x1440 - PC)")

        # 2. Przedmioty
        for row in self.tree_targets.get_children():
            self.tree_targets.delete(row)
        for t in self.config_data.get("targets", []):
            self.tree_targets.insert("", tk.END, values=(t.get("name", ""), t.get("query", ""), t.get("max", ""), t.get("refresh_wait", 10)))

        # 3. Ustawienia
        self.ent_ntfy.delete(0, tk.END)
        self.ent_ntfy.insert(0, self.config_data.get("ntfy_topic", "botdorestaracji2115"))

        self.stop_after_buy_var.set(self.config_data.get("stop_after_buy", False))

        timers = self.config_data.get("timers", {})
        for k, ent in self.timer_entries.items():
            if k in timers:
                ent.delete(0, tk.END)
                ent.insert(0, str(timers[k]))

        # 4. Koordynaty profilu
        self.load_coords_for_current_res()

    def get_selected_res_key(self):
        sel = self.res_combo.get() if hasattr(self, "res_combo") and self.res_combo.get() else self.res_var.get()
        return "1080p" if "1080p" in sel else "1440p"

    def load_coords_for_current_res(self):
        res_key = self.get_selected_res_key()
        profiles = self.config_data.get("profiles", {})
        prof = profiles.get(res_key, DEFAULT_CONFIG["profiles"].get(res_key, {}))

        for k, ent in self.coord_entries.items():
            ent.delete(0, tk.END)
            val = prof.get(k)
            if isinstance(val, (list, tuple)):
                ent.insert(0, f"{val[0]}, {val[1]}")
            elif isinstance(val, dict):
                # top, left, width, height
                ent.insert(0, f"{val.get('top', 0)}, {val.get('left', 0)}, {val.get('width', 0)}, {val.get('height', 0)}")

    def on_res_change(self, event=None):
        res_key = self.get_selected_res_key()
        self.config_data["resolution"] = res_key
        self.load_coords_for_current_res()

    def reset_profile_coords(self):
        res_key = self.get_selected_res_key()
        if messagebox.askyesno("Potwierdzenie", f"Czy na pewno przywrócić domyślne koordynaty dla {res_key}?"):
            def_prof = DEFAULT_CONFIG["profiles"][res_key]
            self.config_data["profiles"][res_key] = json.loads(json.dumps(def_prof))
            self.load_coords_for_current_res()

    def reload_config_from_file(self):
        self.config_data = self.load_config()
        self.populate_data()
        messagebox.showinfo("Sukces", "Pomyślnie wczytano dane z pliku config.json!")

    def paste_profile_json(self):
        raw = ""
        try:
            raw = self.clipboard_get().strip()
        except Exception:
            raw = ""

        if not raw or not ("{" in raw and "}" in raw):
            dialog = tk.Toplevel(self)
            dialog.title("Wklej profil JSON")
            dialog.geometry("520x360")
            dialog.transient(self)
            dialog.grab_set()

            ttk.Label(dialog, text="Wklej poniżej fragment JSON profilu (np. z kalibratora):").pack(anchor=tk.W, padx=10, pady=(10, 5))
            txt = tk.Text(dialog, wrap=tk.NONE, height=13)
            txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            def apply_paste():
                content = txt.get("1.0", tk.END).strip()
                if self._apply_json_data(content):
                    dialog.destroy()

            ttk.Button(dialog, text="✅ Zastosuj koordynaty", command=apply_paste).pack(pady=8)
            return

        self._apply_json_data(raw)

    def _apply_json_data(self, raw_str):
        raw_str = raw_str.strip()
        if raw_str.startswith('"1080p"') or raw_str.startswith('"1440p"'):
            raw_str = "{" + raw_str + "}"

        try:
            parsed = json.loads(raw_str)
        except Exception as e:
            messagebox.showerror("Błąd", f"Niepoprawny format JSON:\n{e}")
            return False

        res_key = self.get_selected_res_key()
        target_prof = None

        if "profiles" in parsed and res_key in parsed["profiles"]:
            target_prof = parsed["profiles"][res_key]
        elif res_key in parsed:
            target_prof = parsed[res_key]
        elif "search_box" in parsed:
            target_prof = parsed

        if not target_prof:
            for k in ["1080p", "1440p"]:
                if k in parsed:
                    target_prof = parsed[k]
                    self.res_var.set("1080p (1920x1080 - Laptop)" if k == "1080p" else "1440p (2560x1440 - PC)")
                    res_key = k
                    break

        if not target_prof:
            messagebox.showerror("Błąd", "Nie znaleziono danych profilu w podanym JSON!")
            return False

        if "profiles" not in self.config_data:
            self.config_data["profiles"] = {}
        if res_key not in self.config_data["profiles"]:
            self.config_data["profiles"][res_key] = {}

        self.config_data["profiles"][res_key].update(target_prof)
        self.load_coords_for_current_res()
        self.save_config(show_msg=False)
        messagebox.showinfo("Sukces", f"Pomyślnie załadowano i zapisano koordynaty dla profilu {res_key}!")
        return True

    def on_target_select(self, event=None):
        sel = self.tree_targets.selection()
        if not sel:
            return
        vals = self.tree_targets.item(sel[0], "values")
        if vals:
            self.ent_target_name.delete(0, tk.END)
            self.ent_target_name.insert(0, vals[0])

            self.ent_target_query.delete(0, tk.END)
            self.ent_target_query.insert(0, vals[1])

            self.ent_target_max.delete(0, tk.END)
            self.ent_target_max.insert(0, vals[2])

            self.ent_target_cooldown.delete(0, tk.END)
            self.ent_target_cooldown.insert(0, vals[3])

    def clear_target_fields(self):
        self.ent_target_name.delete(0, tk.END)
        self.ent_target_query.delete(0, tk.END)
        self.ent_target_max.delete(0, tk.END)
        self.ent_target_cooldown.delete(0, tk.END)
        self.ent_target_cooldown.insert(0, "10")
        self.tree_targets.selection_remove(self.tree_targets.selection())

    def add_target(self):
        name = self.ent_target_name.get().strip()
        query = self.ent_target_query.get().strip()
        max_p = self.ent_target_max.get().strip()
        cd = self.ent_target_cooldown.get().strip() or "10"

        if not name or not query or not max_p:
            messagebox.showwarning("Uwaga", "Wypełnij nazwę, frazę oraz maksymalną cenę!")
            return

        try:
            max_int = int(max_p)
            cd_int = int(cd)
        except ValueError:
            messagebox.showerror("Błąd", "Cena i cooldown muszą być liczbami całkowitymi!")
            return

        self.tree_targets.insert("", tk.END, values=(name, query, max_int, cd_int))
        self.clear_target_fields()

    def update_target(self):
        sel = self.tree_targets.selection()
        if not sel:
            messagebox.showwarning("Uwaga", "Zaznacz najpierw przedmiot na liście do aktualizacji!")
            return

        name = self.ent_target_name.get().strip()
        query = self.ent_target_query.get().strip()
        max_p = self.ent_target_max.get().strip()
        cd = self.ent_target_cooldown.get().strip() or "10"

        if not name or not query or not max_p:
            messagebox.showwarning("Uwaga", "Wypełnij nazwę, frazę oraz maksymalną cenę!")
            return

        try:
            max_int = int(max_p)
            cd_int = int(cd)
        except ValueError:
            messagebox.showerror("Błąd", "Cena i cooldown muszą być liczbami!")
            return

        self.tree_targets.item(sel[0], values=(name, query, max_int, cd_int))

    def remove_target(self):
        sel = self.tree_targets.selection()
        if not sel:
            messagebox.showwarning("Uwaga", "Zaznacz przedmiot na liście do usunięcia!")
            return
        for s in sel:
            self.tree_targets.delete(s)
        self.clear_target_fields()

    def collect_data_from_ui(self):
        # 1. Resolution
        res_key = self.get_selected_res_key()
        self.config_data["resolution"] = res_key

        # 2. Targets
        new_targets = []
        for item_id in self.tree_targets.get_children():
            vals = self.tree_targets.item(item_id, "values")
            new_targets.append({
                "name": str(vals[0]),
                "query": str(vals[1]),
                "max": int(vals[2]),
                "refresh_wait": int(vals[3])
            })
        self.config_data["targets"] = new_targets

        # 3. Settings
        self.config_data["ntfy_topic"] = self.ent_ntfy.get().strip()
        self.config_data["stop_after_buy"] = bool(self.stop_after_buy_var.get())

        timers = {}
        for k, ent in self.timer_entries.items():
            try:
                timers[k] = float(ent.get().strip())
            except ValueError:
                pass
        self.config_data["timers"] = timers

        # 4. Active Profile Coords
        if "profiles" not in self.config_data:
            self.config_data["profiles"] = {}
        if res_key not in self.config_data["profiles"]:
            self.config_data["profiles"][res_key] = {}

        prof = self.config_data["profiles"][res_key]
        for k, ent in self.coord_entries.items():
            txt = ent.get().strip()
            parts = [p.strip() for p in txt.split(",") if p.strip()]
            if len(parts) == 2:
                try:
                    prof[k] = [int(parts[0]), int(parts[1])]
                except ValueError:
                    pass
            elif len(parts) == 4:
                try:
                    prof[k] = {
                        "top": int(parts[0]),
                        "left": int(parts[1]),
                        "width": int(parts[2]),
                        "height": int(parts[3])
                    }
                except ValueError:
                    pass

    def test_ntfy(self):
        topic = self.ent_ntfy.get().strip()
        if not topic:
            messagebox.showwarning("Uwaga", "Podaj temat ntfy.sh!")
            return

        try:
            payload = json.dumps({
                "topic": topic,
                "title": "Roblox Sniper - Test",
                "message": "Powiadomienia testowe z GUI działają perfekcyjnie! 🚀",
                "priority": 4,
                "tags": ["tada", "bell"]
            }).encode('utf-8')
            req = urllib.request.Request(
                "https://ntfy.sh",
                data=payload,
                headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    messagebox.showinfo("Sukces", f"Powiadomienie testowe wysłane na temat: {topic}\nSprawdź swój telefon!")
                else:
                    messagebox.showwarning("Status", f"Odpowiedź serwera: {resp.status}")
        except Exception as e:
            messagebox.showerror("Błąd ntfy", f"Nie udało się wysłać powiadomienia: {e}")

    def clear_console(self):
        self.txt_console.delete("1.0", tk.END)

    def log(self, text):
        self.txt_console.insert(tk.END, text + "\n")
        self.txt_console.see(tk.END)

    def log_raw(self, text):
        self.txt_console.insert(tk.END, text)
        self.txt_console.see(tk.END)

    def start_macro(self):
        if getattr(self, "is_macro_running", False):
            messagebox.showwarning("Uwaga", "Makro już jest uruchomione!")
            return

        self.save_config(show_msg=False)
        self.notebook.select(self.tab_console)
        self.log("\n" + "=" * 50)
        self.log(f"🚀 URUCHAMIANIE MAKRA (Profil: {self.get_selected_res_key()})...")
        self.log("=" * 50)

        self.is_macro_running = True
        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self.status_lbl.configure(text="● MAKRO AKTYWNE (F8/ESC=Stop)", foreground="#00AA00")

        def run_thread():
            class Redirector:
                def __init__(self, cb):
                    self.cb = cb
                def write(self, s):
                    if s:
                        self.cb(s)
                def flush(self):
                    pass

            old_stdout = sys.stdout
            old_stderr = sys.stderr

            try:
                redirector = Redirector(self.ui_queue.put)
                sys.stdout = redirector
                sys.stderr = redirector
                makro.running = True
                makro.load_config()
                makro.main()
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                self.ui_queue.put(f"⚠️ Błąd wykonania makra:\n{tb}\n")
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                self.ui_queue.put(self._on_macro_exit)

        self.macro_thread = threading.Thread(target=run_thread, daemon=True)
        self.macro_thread.start()

    def _on_macro_exit(self):
        self.is_macro_running = False
        self.btn_start.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.DISABLED)
        self.status_lbl.configure(text="● Makro zatrzymane", foreground="#666666")
        self.log("\n⏹ Makro zostało zatrzymane.\n")

    def stop_macro(self):
        if getattr(self, "is_macro_running", False):
            self.log("🛑 Zatrzymywanie makra...")
            try:
                makro.running = False
            except Exception:
                pass

if __name__ == "__main__":
    app = SniperApp()
    app.mainloop()

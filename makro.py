# sniper.py — v6.6 (TRYB TURBO: błyskawiczne przechodzenie między przedmiotami)
import sys
import os
import time
import random
import re
import urllib.request
import urllib.parse
import json
import mss
import mss.tools
import cv2
import numpy as np
import keyboard
import pydirectinput as pai
import pyperclip
from PIL import Image

# Obsługa UTF-8 dla konsoli Windows
if sys.stdout and getattr(sys.stdout, 'encoding', None) and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

# --- OCR: tesserocr (ultra szybki, ~4ms) z fallbackiem na pytesseract ---
# --- OCR: tesserocr (ultra szybki, ~4ms) z fallbackiem na pytesseract ---
TESS_WHITELIST = "0123456789"
HAS_FAST_TESS = False
_tess = None
_tess_line = None
_tess_digits_line = None
_tess_word = None
_tess_char = None

NORM_MAP = {
    'B': '8', 'O': '0', 'o': '0', 'D': '0',
    'I': '1', 'l': '1', '|': '1', '/': '1', ']': '1', '[': '1', 'i': '1',
    'S': '5', 's': '5',
    'Z': '2', 'z': '2',
    'g': '9', 'q': '9',
    'b': '6',
    '?': '7', 'T': '7',
    'A': '4'
}

def _get_tessdata_path():
    # 1. Wewnątrz paczki PyInstaller (_MEIPASS)
    if hasattr(sys, '_MEIPASS'):
        bundle_td = os.path.join(sys._MEIPASS, "tessdata")
        if os.path.exists(bundle_td):
            return bundle_td
    # 2. Obok pliku exe / skryptu
    if getattr(sys, 'frozen', False):
        exe_td = os.path.join(os.path.dirname(sys.executable), "tessdata")
        if os.path.exists(exe_td):
            return exe_td
    local_td = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tessdata")
    if os.path.exists(local_td):
        return local_td
    # 3. Systemowa instalacja
    if os.path.exists(r'C:\Program Files\Tesseract-OCR\tessdata'):
        return r'C:\Program Files\Tesseract-OCR\tessdata'
    return None

TESS_PATH = _get_tessdata_path()

_tess_status_msg = ""
_tess_error = None

try:
    from tesserocr import PyTessBaseAPI, PSM
    # _tess_line: BEZ WHITELISTY — do czytania nagłówków ofert i popupów tekstowych (litery + cyfry)
    _tess_line = PyTessBaseAPI(psm=PSM.SINGLE_LINE, path=TESS_PATH)

    # _tess_digits_line: TYLKO CYFRY — do odczytu całej linii ceny w decode_price_from_boxes
    _tess_digits_line = PyTessBaseAPI(psm=PSM.SINGLE_LINE, path=TESS_PATH)
    _tess_digits_line.SetVariable("tessedit_char_whitelist", TESS_WHITELIST)

    _tess_word = PyTessBaseAPI(psm=PSM.SINGLE_WORD, path=TESS_PATH)
    _tess_word.SetVariable("tessedit_char_whitelist", TESS_WHITELIST)
    _tess_char = PyTessBaseAPI(psm=PSM.SINGLE_CHAR, path=TESS_PATH)
    _tess_char.SetVariable("tessedit_char_whitelist", TESS_WHITELIST)
    _tess = _tess_char
    HAS_FAST_TESS = True
    _tess_status_msg = f"⚡ tesserocr aktywny — ultra szybki OCR (~4ms) [baza: {TESS_PATH}]"
    print(_tess_status_msg)
except Exception as e:
    HAS_FAST_TESS = False
    _tess_error = f"{type(e).__name__}: {e}"
    _tess_status_msg = f"ℹ️ tesserocr niedostępny ({_tess_error}) — fallback na pytesseract"
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    print(_tess_status_msg)

pai.FAILSAFE = False  # Zapobiega wywalaniu bota przy krawędziach ekranów / wielu monitorach
pai.PAUSE = 0.005  # Minimalny narzut pydirectinput

# ============ TARGETY ============
TARGETS = [
    {"name": "Davy Jones Chair", "query": "davy jones chair", "max": 200, "refresh_wait": 10},
    {"name": "Davy Jones Table", "query": "davy jones table", "max": 100, "refresh_wait": 10},
    {"name": "Sunken Chair",     "query": "sunken chair",     "max": 70,  "refresh_wait": 10},
    {"name": "Sunken Table",     "query": "sunken table",     "max": 60,  "refresh_wait": 10}
]

STOP_AFTER_BUY = False         # False = bot nie zatrzymuje się po zakupie, tylko poluje bez przerwy!
PROFILE = True

# ============ POWIADOMIENIA NA TELEFON ============
# Opcja 1: WhatsApp (CallMeBot — w 100% darmowe API)
# Jak aktywować w 30 sekund:
# 1. Dodaj w WhatsApp numer: +34 644 59 74 42 (CallMeBot)
# 2. Wyślij do niego wiadomość: "I allow callmebot to send me messages"
# 3. Otrzymasz w odpowiedzi swój klucz API (apikey).
# 4. Wpisz swój numer (z kodem kraju np. "+48123456789") i apikey poniżej:
WHATSAPP_PHONE  = ""           # np. "+48123456789" (zostaw puste "" jeśli wyłączone)
WHATSAPP_APIKEY = ""           # np. "1234567" (zostaw puste "" jeśli wyłączone)

# Opcja 2: Discord Webhook (działa od razu z powiadomieniami na telefonie)
DISCORD_WEBHOOK = ""           # np. "https://discord.com/api/webhooks/..." (zostaw puste "" jeśli wyłączone)

# Opcja 3: ntfy.sh (błyskawiczny push bez żadnych kont — darmowa apka 'ntfy' na Android/iOS)
NTFY_TOPIC      = "botdorestaracji2115"  # Twój temat w ntfy

# ============ DEBUG & DIAGNOSTYKA ============
DEBUG_MODE = False             # Wyłączone zapisywanie zrzutów diagnostycznych
DEBUG_VERBOSE = False          # Czysta konsola bez spamu logami
DEBUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug")
saved_crops = set()
debug_saved = set()

# ============ TIMING (TRYB TURBO) ============
LEAD_TIME     = 1.5        # Wcześniejszy start szukania (zanim minie cooldown, bot już wpisuje i wchodzi)
WAIT_RESULTS  = 0.40       # Czas po wpisaniu do szukajki na odświeżenie listy
WAIT_OPEN     = 0.30      # Krótki delay po kliknięciu (reszta to dynamiczne czekanie na nagłówek)
WAIT_REFRESH  = 0.7       # Czas po kliknięciu refresh przed odczytem ceny
WAIT_BACK     = 0.35       # Czas po kliknięciu wstecz
PRICE_TIMEOUT = 3.5        # Max czas czekania na cenę (gdy serwer gry ma laga)
PRICE_POLL    = 0.03       # Sprawdzanie ceny co 30ms
EMPTY_SKIP    = 35         # Po tylu pustych klatkach bez przycisku (~1.1s) uznajemy brak oferty
MIN_WHITE     = 150
START_DELAY   = 3          # Odliczanie na start (sekundy)

# ============ WSPÓŁRZĘDNE ============
SEARCH_BOX  = (1777, 448)
ITEM_1      = (1050, 608)
REFRESH_BTN = (1668, 326)
BUY_BTN     = (1714, 1041)
BACK_BTN    = (726, 461)

ITEM_PRICE = {"top": 1030, "left": 1573, "width": 280, "height": 50}
ITEM_HEADER_REGION = {"top": 435, "left": 770, "width": 650, "height": 55}

# Okienko potwierdzenia zakupu ("Hey! Are you sure? Buy 1x ...")
POPUP_TEXT_REGION  = {"top": 680, "left": 860, "width": 840, "height": 80}
POPUP_CONFIRM_BTN  = (1082, 887)   # Zielony przycisk 'Buy' w okienku
POPUP_CANCEL_BTN   = (1478, 886)   # Czerwony przycisk 'Cancel' w okienku

# Fail-safe: Naprawa przypadkowego wejścia w zakładkę Sell lub okienko 'Select an Item!'
POPUP_SELECT_ITEM_X = (1818, 358)   # Środek czerwonego 'X' okienka 'Select an Item!'
MARKET_BUY_TAB      = (750, 580)    # Przycisk zakładki 'Buy' (Kupno) w Markecie
MARKET_SELL_TAB     = (750, 470)    # Przycisk zakładki 'Sell' (Sprzedaż) w Markecie

FAILSAFE_POPUP_X_CHECK  = {"top": 350, "left": 1785, "width": 30, "height": 25}
FAILSAFE_SELL_TAB_CHECK = {"top": 460, "left": 740, "width": 20, "height": 20}
CURRENT_RES = "1440p"

if getattr(sys, 'frozen', False):
    CONFIG_PATH = os.path.join(os.path.dirname(sys.executable), "config.json")
else:
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    global TARGETS, STOP_AFTER_BUY, NTFY_TOPIC, DISCORD_WEBHOOK, WHATSAPP_PHONE, WHATSAPP_APIKEY
    global LEAD_TIME, WAIT_RESULTS, WAIT_OPEN, WAIT_REFRESH, WAIT_BACK, PRICE_TIMEOUT, START_DELAY
    global SEARCH_BOX, ITEM_1, REFRESH_BTN, BUY_BTN, BACK_BTN
    global POPUP_CONFIRM_BTN, POPUP_CANCEL_BTN, POPUP_SELECT_ITEM_X, MARKET_BUY_TAB, MARKET_SELL_TAB
    global ITEM_PRICE, ITEM_HEADER_REGION, POPUP_TEXT_REGION
    global FAILSAFE_POPUP_X_CHECK, FAILSAFE_SELL_TAB_CHECK, CURRENT_RES

    if not os.path.exists(CONFIG_PATH):
        return

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        if "targets" in cfg and cfg["targets"]:
            TARGETS = cfg["targets"]
        if "stop_after_buy" in cfg:
            STOP_AFTER_BUY = cfg["stop_after_buy"]
        if "ntfy_topic" in cfg:
            NTFY_TOPIC = cfg["ntfy_topic"]
        if "discord_webhook" in cfg:
            DISCORD_WEBHOOK = cfg["discord_webhook"]
        if "whatsapp_phone" in cfg:
            WHATSAPP_PHONE = cfg["whatsapp_phone"]
        if "whatsapp_apikey" in cfg:
            WHATSAPP_APIKEY = cfg["whatsapp_apikey"]

        if "timers" in cfg:
            tm = cfg["timers"]
            LEAD_TIME     = float(tm.get("lead_time", LEAD_TIME))
            WAIT_RESULTS  = float(tm.get("wait_results", WAIT_RESULTS))
            WAIT_OPEN     = float(tm.get("wait_open", WAIT_OPEN))
            WAIT_REFRESH  = float(tm.get("wait_refresh", WAIT_REFRESH))
            WAIT_BACK     = float(tm.get("wait_back", WAIT_BACK))
            PRICE_TIMEOUT = float(tm.get("price_timeout", PRICE_TIMEOUT))
            START_DELAY   = int(tm.get("start_delay", START_DELAY))

        CURRENT_RES = cfg.get("resolution", "1440p")
        profiles = cfg.get("profiles", {})
        prof = profiles.get(CURRENT_RES, profiles.get("1440p"))
        if prof:
            SEARCH_BOX          = tuple(prof.get("search_box", SEARCH_BOX))
            ITEM_1              = tuple(prof.get("item_1", ITEM_1))
            REFRESH_BTN         = tuple(prof.get("refresh_btn", REFRESH_BTN))
            BUY_BTN             = tuple(prof.get("buy_btn", BUY_BTN))
            BACK_BTN            = tuple(prof.get("back_btn", BACK_BTN))
            POPUP_CONFIRM_BTN   = tuple(prof.get("popup_confirm_btn", POPUP_CONFIRM_BTN))
            POPUP_CANCEL_BTN    = tuple(prof.get("popup_cancel_btn", POPUP_CANCEL_BTN))
            POPUP_SELECT_ITEM_X = tuple(prof.get("popup_select_item_x", POPUP_SELECT_ITEM_X))
            MARKET_BUY_TAB      = tuple(prof.get("market_buy_tab", MARKET_BUY_TAB))
            MARKET_SELL_TAB     = tuple(prof.get("market_sell_tab", MARKET_SELL_TAB))

            ITEM_PRICE          = prof.get("item_price", ITEM_PRICE)
            ITEM_HEADER_REGION  = prof.get("item_header_region", ITEM_HEADER_REGION)
            POPUP_TEXT_REGION   = prof.get("popup_text_region", POPUP_TEXT_REGION)
            FAILSAFE_POPUP_X_CHECK  = prof.get("failsafe_popup_x_check", FAILSAFE_POPUP_X_CHECK)
            FAILSAFE_SELL_TAB_CHECK = prof.get("failsafe_sell_tab_check", FAILSAFE_SELL_TAB_CHECK)
    except Exception as e:
        print(f"⚠️ Błąd wczytywania config.json: {e}")

load_config()
# ==========================================

SKIP_TEXT = "TEXT"

sct = mss.mss()
running = True

# ============ STATYSTYKI SESJI ============
STATS = {
    "start_time": 0.0,
    "checks_total": 0,           # Łączna liczba sprawdzonych ofert
    "buy_attempts": 0,          # Liczba prób zakupu (kliknięć Buy)
    "bought_items": [],         # Lista kupionych przedmiotów
    "popup_cancelled": 0,       # Liczba anulowań w oknie potwierdzenia
    "blocks_wrong_item": 0,     # Liczba zablokowanych pomyłek (np. Wooden Chair)
    "fail_safe_recoveries": 0,  # Liczba automatycznych napraw (okienko Select an Item / Sell tab)
}

def _kill():
    global running
    running = False
    print("\n🛑 KILL SWITCH AKTYWOWANY!")

keyboard.add_hotkey('f8', _kill)
keyboard.add_hotkey('esc', _kill)

def safe_sleep(seconds):
    end = time.time() + seconds
    while running and time.time() < end:
        time.sleep(0.005)

def hotkey(*keys):
    for k in keys:
        pai.keyDown(k)
    time.sleep(0.01)
    for k in reversed(keys):
        pai.keyUp(k)

def click(x, y, delay=0.03, label=""):
    """
    Kliknięcie z mikro-drganiem (jitter).
    Roblox wymaga zdarzenia ruchu kursora (hover), aby zarejestrować kliknięcie w przycisk UI.
    """
    if label:
        print(f"   🖱️ [{label}] -> ({x}, {y})")
    pai.moveTo(x, y)
    time.sleep(0.01)
    jx, jy = random.randint(2, 4), random.randint(-2, 2)
    pai.moveRel(jx, jy)
    time.sleep(0.01)
    pai.moveRel(-jx, -jy)
    time.sleep(0.01)
    pai.mouseDown()
    time.sleep(0.025)
    pai.mouseUp()
    if delay > 0:
        safe_sleep(delay)

def _grab_bgr(region):
    img = sct.grab(region)
    return cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)

def save_annotated_screen(filename, note="", status_color=(0, 255, 0)):
    """
    Zapisuje pełnoekranowy zrzut z naniesionymi wszystkimi koordynatami i ramkami.
    Pozwala na 100% pewną weryfikację bez wróżenia z fusów!
    """
    try:
        shot = sct.grab(sct.monitors[0])
        img = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
        h, w = img.shape[:2]

        # 1. ITEM_HEADER_REGION (Zielona ramka)
        hr = ITEM_HEADER_REGION
        cv2.rectangle(img, (hr["left"], hr["top"]), (hr["left"] + hr["width"], hr["top"] + hr["height"]), (0, 255, 0), 2)
        cv2.putText(img, "ITEM_HEADER_REGION", (hr["left"], max(25, hr["top"] - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        # 2. ITEM_PRICE (Błękitna ramka)
        pr = ITEM_PRICE
        cv2.rectangle(img, (pr["left"], pr["top"]), (pr["left"] + pr["width"], pr["top"] + pr["height"]), (255, 255, 0), 2)
        cv2.putText(img, "ITEM_PRICE", (pr["left"], max(25, pr["top"] - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)

        # 3. Punkty kliknięć
        points = [
            ("SEARCH_BOX", SEARCH_BOX, (255, 0, 255)),
            ("ITEM_1", ITEM_1, (0, 255, 255)),
            ("REFRESH_BTN", REFRESH_BTN, (255, 128, 0)),
            ("BUY_BTN", BUY_BTN, (0, 0, 255)),
            ("BACK_BTN", BACK_BTN, (0, 165, 255)),
        ]
        for label, (px, py), color in points:
            cv2.circle(img, (px, py), 8, color, -1)
            cv2.circle(img, (px, py), 12, (255, 255, 255), 1)
            cv2.putText(img, f"{label} ({px},{py})", (px + 15, py + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # 4. Górny pasek diagnostyczny z notatką
        if note:
            cv2.rectangle(img, (15, 15), (min(w - 15, 1200), 75), (20, 20, 20), -1)
            cv2.rectangle(img, (15, 15), (min(w - 15, 1200), 75), status_color, 2)
            cv2.putText(img, note, (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.75, status_color, 2)

        path = os.path.join(DEBUG_DIR, filename)
        cv2.imwrite(path, img)
        return path
    except Exception as e:
        print(f"⚠️ Błąd zapisu annotated screen: {e}")
        return None

def save_crop_debug(name, img_bgr, mask=None):
    """Zapisuje wycinek BGR i opcjonalną maskę do folderu debug."""
    try:
        p1 = os.path.join(DEBUG_DIR, f"{name}.png")
        cv2.imwrite(p1, img_bgr)
        if mask is not None:
            p2 = os.path.join(DEBUG_DIR, f"{name}_mask.png")
            cv2.imwrite(p2, mask)
    except Exception as e:
        print(f"⚠️ Błąd zapisu crop debug: {e}")

def component_report(mask):
    """Pomocniczy raport komponentów dla debugu."""
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    kept, parts = 0, []
    for i in range(1, num):
        x, y, w, h, area = stats[i]
        if 12 <= h <= 70 and 2 <= w <= 60 and area >= 20:
            kept += 1
            parts.append(f"[x={x} w={w} h={h} a={area}]")
    return num - 1, kept, parts

def decode_price_from_boxes(mask, boxes):
    """
    Hybrydowy, odporny dekoder ceny z komponentów maski:
    1. Obsługuje pojedyncze cyfry (np. 9, 8, 7...) z uwzględnieniem wąskiej '1'.
    2. Obsługuje wielocyfrowe liczby (np. 17, 18, 19, 410, 497) za pomocą odczytu całego bloku (SINGLE_LINE / SINGLE_WORD).
    3. Posiada per-character fallback bez restrykcyjnego whitelistu z normalizacją liter (np. B->8, O->0, l->1, q/g->9).
    """
    if not boxes:
        return None
    boxes.sort(key=lambda b: b[0])
    num_boxes = len(boxes)

    min_x = boxes[0][0]
    max_x = boxes[-1][0] + boxes[-1][2]
    min_y = min(b[1] for b in boxes)
    max_y = max(b[1] + b[3] for b in boxes)

    combined = mask[min_y:max_y, min_x:max_x]
    inv_c = cv2.bitwise_not(combined)

    # A. Pojedyncza cyfra (np. 9, 8, 7, 1...)
    if num_boxes == 1:
        x, y, w, h = boxes[0][:4]
        # Wąski kształt o małym stosunku w/h to zawsze '1'
        if w <= 8 and h >= 10 and (w / h) <= 0.55:
            return 1

        pad = 6
        padded_single = cv2.copyMakeBorder(inv_c, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
        scaled_single = cv2.resize(padded_single, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        pil_s = Image.fromarray(scaled_single)

        if HAS_FAST_TESS and _tess_word is not None and _tess_digits_line is not None and _tess_char is not None:
            _tess_word.SetImage(pil_s)
            tw = ''.join(c for c in _tess_word.GetUTF8Text() if c.isdigit())
            if len(tw) == 1:
                return int(tw)

            _tess_digits_line.SetImage(pil_s)
            tl = ''.join(c for c in _tess_digits_line.GetUTF8Text() if c.isdigit())
            if len(tl) == 1:
                return int(tl)

            _tess_char.SetImage(pil_s)
            raw = _tess_char.GetUTF8Text().strip()
            mapped = ''.join(NORM_MAP.get(c, c) for c in raw)
            dc = ''.join(c for c in mapped if c.isdigit())
            if len(dc) == 1:
                return int(dc)
        else:
            try:
                tw = pytesseract.image_to_string(
                    scaled_single,
                    config=f'--psm 8 -c tessedit_char_whitelist={TESS_WHITELIST}').strip()
                dw = ''.join(c for c in tw if c.isdigit())
                if len(dw) == 1:
                    return int(dw)
            except Exception:
                pass
        return None

    # B. Wiele cyfr (np. 17, 18, 19, 410, 497...)
    # Krok 1: Combined Line / Word OCR (cała liczba jako spójny blok)
    padded_c = cv2.copyMakeBorder(inv_c, 8, 8, 14, 14, cv2.BORDER_CONSTANT, value=255)
    scaled_c = cv2.resize(padded_c, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    pil_c = Image.fromarray(scaled_c)

    digits_line = ""
    if HAS_FAST_TESS and _tess_digits_line is not None:
        _tess_digits_line.SetImage(pil_c)
        t_line = _tess_digits_line.GetUTF8Text().strip()
        digits_line = ''.join(c for c in t_line if c.isdigit())
        if len(digits_line) == num_boxes:
            return int(digits_line)

        if _tess_word is not None:
            _tess_word.SetImage(pil_c)
            t_word = _tess_word.GetUTF8Text().strip()
            digits_word = ''.join(c for c in t_word if c.isdigit())
            if len(digits_word) == num_boxes:
                return int(digits_word)
    else:
        try:
            t_line = pytesseract.image_to_string(
                scaled_c,
                config=f'--psm 7 -c tessedit_char_whitelist={TESS_WHITELIST}').strip()
            digits_line = ''.join(c for c in t_line if c.isdigit())
            if len(digits_line) == num_boxes:
                return int(digits_line)
        except Exception:
            digits_line = ""

    # Krok 2: Per-character fallback z unconstrained char OCR + normalizacja
    per_char = []
    for b in boxes:
        x, y, w, h = b[:4]
        if w <= 8 and h >= 10 and (w / h) <= 0.55:
            per_char.append('1')
            continue

        glyph = mask[y:y+h, x:x+w]
        inv = cv2.bitwise_not(glyph)
        pad = 6
        padded = cv2.copyMakeBorder(inv, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
        scaled = cv2.resize(padded, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        pil_g = Image.fromarray(scaled)

        found_digit = None
        if HAS_FAST_TESS and _tess_word is not None and _tess_char is not None:
            _tess_word.SetImage(pil_g)
            tw = ''.join(c for c in _tess_word.GetUTF8Text() if c.isdigit())
            if len(tw) == 1:
                found_digit = tw

            if not found_digit:
                _tess_char.SetImage(pil_g)
                raw = _tess_char.GetUTF8Text().strip()
                mapped = ''.join(NORM_MAP.get(c, c) for c in raw)
                dc = ''.join(c for c in mapped if c.isdigit())
                if len(dc) >= 1:
                    found_digit = dc[0]
        else:
            try:
                tw = pytesseract.image_to_string(
                    scaled,
                    config=f'--psm 8 -c tessedit_char_whitelist={TESS_WHITELIST}').strip()
                dw = ''.join(c for c in tw if c.isdigit())
                if len(dw) == 1:
                    found_digit = dw
            except Exception:
                pass

        if found_digit:
            per_char.append(found_digit)
        else:
            per_char.append('?')

    if len(per_char) == num_boxes and all(c.isdigit() for c in per_char):
        return int(''.join(per_char))

    # Krok 3: Rekompensacja wąskiej jedynki na początku (np. '17' gdzie linia odczytała tylko '7')
    if len(digits_line) == num_boxes - 1 and boxes[0][2] <= 8:
        candidate = "1" + digits_line
        return int(candidate)

    if digits_line and len(digits_line) >= 1:
        return int(digits_line)

    return None

def ocr_region(img_bgr, mask, item_name=""):
    """
    Błyskawiczna ekstrakcja i odczyt OCR cyfra po cyfrze oraz liniowo (hybryda).
    Rozpoznaje walutę: DIAMOND (💎) vs CASH ($).
    Zwraca: (cena, 'DIAMOND' | 'CASH') | (SKIP_TEXT, None) | (None, None).
    """
    # 1. Wykrycie obecności niebieskiego diamentu w przycisku (ikona ma ~350-500 niebieskich px)
    blue_mask = cv2.inRange(img_bgr, (180, 80, 10), (255, 240, 110))
    blue_px = cv2.countNonZero(blue_mask)
    is_diamond = (blue_px >= 100)

    # 2. Wykrycie komponentów tekstu
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)

    boxes = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        # Cyfry i znaki w Roblox mają h ~ 10-25, w ~ 2-25, area >= 12
        if 8 <= h <= 70 and 2 <= w <= 60 and area >= 12:
            boxes.append((x, y, w, h))

    if not boxes:
        return None, None

    # Jeśli jest 7+ komponentów -> napis słowny (np. 'Your listing')
    if len(boxes) >= 7:
        if DEBUG_VERBOSE:
            print(f"   ℹ️ [DEBUG OCR] Wykryto napis słowny ({len(boxes)} komponentów)")
        return SKIP_TEXT, None

    # Sortowanie cyfr od lewej do prawej
    boxes.sort(key=lambda b: b[0])

    # Zbyt szeroki obszar -> napis słowny
    if (boxes[-1][0] + boxes[-1][2] - boxes[0][0]) > 170:
        if DEBUG_VERBOSE:
            print(f"   ℹ️ [DEBUG OCR] Zbyt szeroki obszar ({boxes[-1][0] + boxes[-1][2] - boxes[0][0]}px) -> napis słowny")
        return SKIP_TEXT, None

    # Diament vs Gotówka (CASH)
    if is_diamond:
        currency = "DIAMOND"
        digit_boxes = boxes
    else:
        currency = "CASH"
        digit_boxes = boxes[1:] if len(boxes) > 1 else boxes

    if not digit_boxes:
        return None, None

    final_val = decode_price_from_boxes(mask, digit_boxes)
    if final_val is None:
        if DEBUG_VERBOSE:
            print(f"   ⚠️ [DEBUG OCR] Nie udało się zdekodować ceny z {len(digit_boxes)} komponentów")
        return None, None

    if DEBUG_VERBOSE:
        symbol = "💎" if currency == "DIAMOND" else "$"
        print(f"   🔬 [DEBUG OCR] Odczytano: {final_val} {symbol} (niebieskie px: {blue_px}, boxy: {len(boxes)})")

    return final_val, currency

def wait_for_price(item_name=""):
    """
    Dynamiczne czekanie na odświeżenie ceny przez serwer gry.
    Ignoruje chwilowy biały flash po refreshu i natychmiast odczytuje cenę oraz walutę.
    Zwraca: (cena, 'DIAMOND' | 'CASH', próby, last_nz) | (SKIP_TEXT, None, tries, nz)
    """
    end = time.time() + PRICE_TIMEOUT
    total_px = ITEM_PRICE["width"] * ITEM_PRICE["height"]
    tries = 0
    empty = 0
    last_nz = 0
    last_mask = None
    last_bgr = None
    safe_name = item_name.replace(" ", "_").lower()

    while running and time.time() < end:
        img_bgr = _grab_bgr(ITEM_PRICE)
        mask = cv2.inRange(img_bgr, np.array([200, 200, 200]), np.array([255, 255, 255]))
        nz = cv2.countNonZero(mask)
        last_nz = max(last_nz, nz)
        last_mask = mask
        last_bgr = img_bgr

        # Wykrycie białego flasha przejścia gry (animacja odświeżania)
        if nz >= total_px * 0.85:
            if DEBUG_VERBOSE and empty == 0:
                print(f"   ⚡ [DEBUG CENA] Biały flash przeładowania gry ({nz}/{total_px} px)")
            empty = 0  # Flash oznacza, że gra dopiero przeładowuje — resetujemy licznik
            time.sleep(PRICE_POLL)
            continue

        result = None
        currency = None
        if MIN_WHITE <= nz:
            tries += 1
            result, currency = ocr_region(img_bgr, mask, item_name)

        # Jak tylko OCR poprawnie odczyta cenę -> zwracamy natychmiast!
        if result is not None:
            if DEBUG_MODE and safe_name not in debug_saved:
                debug_saved.add(safe_name)
                save_crop_debug(f"price_{safe_name}", img_bgr, mask)
                if DEBUG_VERBOSE:
                    print(f"   📸 [DEBUG] Zapisano wzorzec ceny: debug/price_{safe_name}.png")
            return result, currency, tries, last_nz

        # Zliczamy puste klatki TYLKO gdy na ekranie nie ma przycisku (np. serwer ładuje lub brak ofert)
        if nz < MIN_WHITE:
            empty += 1
            if empty >= EMPTY_SKIP:
                if DEBUG_MODE and safe_name not in debug_saved:
                    debug_saved.add(safe_name)
                    save_crop_debug(f"empty_{safe_name}", last_bgr, last_mask)
                    if DEBUG_VERBOSE:
                        print(f"   📸 [DEBUG] Zapisano pusty widok oferty: debug/empty_{safe_name}.png")
                return SKIP_TEXT, None, tries, last_nz

        time.sleep(PRICE_POLL)

    # W razie timeoutu ceny
    if DEBUG_MODE:
        ts = time.strftime("%H%M%S")
        save_annotated_screen(f"TIMEOUT_price_{safe_name}_{ts}.png", f"TIMEOUT CENY: {item_name} (max px: {last_nz})", status_color=(0, 165, 255))
        if last_bgr is not None:
            save_crop_debug(f"TIMEOUT_price_{safe_name}_{ts}", last_bgr, last_mask)
        print(f"   📸 [DEBUG] Zapisano zrzut timeoutu: debug/TIMEOUT_price_{safe_name}_{ts}.png")

    return None, None, tries, last_nz

def read_title(item_name=""):
    """Odczytuje tekst z nagłówka otwartej oferty ('Listings - <Item Name>')."""
    img_bgr = _grab_bgr(ITEM_HEADER_REGION)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    title = ""
    if HAS_FAST_TESS and _tess_line is not None:
        _tess_line.SetImage(Image.fromarray(scaled))
        title = _tess_line.GetUTF8Text().strip().lower()
        if not title:
            # Fallback z maską białego tekstu w razie słabego kontrastu
            mask = cv2.inRange(img_bgr, np.array([170, 170, 170]), np.array([255, 255, 255]))
            inv = cv2.bitwise_not(mask)
            scaled_inv = cv2.resize(inv, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
            _tess_line.SetImage(Image.fromarray(scaled_inv))
            title = _tess_line.GetUTF8Text().strip().lower()
    else:
        try:
            title = pytesseract.image_to_string(scaled, config='--psm 7').strip().lower()
        except Exception:
            title = ""

    if DEBUG_MODE and item_name:
        safe_name = item_name.replace(" ", "_").lower()
        if safe_name not in saved_crops:
            saved_crops.add(safe_name)
            save_crop_debug(f"header_{safe_name}", img_bgr)
            if DEBUG_VERBOSE:
                print(f"   📸 [DEBUG] Zapisano wycinek nagłówka: debug/header_{safe_name}.png")

    if DEBUG_VERBOSE and title:
        print(f"   🏷️  [DEBUG NAGŁÓWEK] Odczytano: '{title}'")

    return title

def check_title_match(target_name, title):
    """
    Sprawdza czy odczytany tytuł odpowiada targetowi.
    Zwraca True tylko wtedy, gdy pasują słowa kluczowe i nie ma konfliktu (np. Wooden Chair / Chair vs Table).
    """
    if not title:
        return False
    tgt_low = target_name.lower()
    title_low = title.lower()

    # 1. Bezwzględna blokada dla Wooden Chair (zawsze śmieć)
    if "wooden" in title_low and "wooden" not in tgt_low:
        if DEBUG_VERBOSE:
            print(f"   🛑 [DEBUG WERYFIKACJA] ODRZUCONO! Wykryto słowo 'wooden' w nagłówku: '{title}'")
        return False

    # 2. Konflikt Chair vs Table
    if "chair" in tgt_low and "table" in title_low and "table" not in tgt_low:
        if DEBUG_VERBOSE:
            print(f"   🛑 [DEBUG WERYFIKACJA] ODRZUCONO! Szukano chair, a w tytule jest table: '{title}'")
        return False
    if "table" in tgt_low and "chair" in title_low and "chair" not in tgt_low:
        if DEBUG_VERBOSE:
            print(f"   🛑 [DEBUG WERYFIKACJA] ODRZUCONO! Szukano table, a w tytule jest chair: '{title}'")
        return False

    # 3. Sprawdzenie unikalnych słów kluczowych serii (np. davy, sunken, celestial)
    words = [w for w in tgt_low.split() if w not in ("chair", "table", "the", "a", "an")]
    if words:
        matched = [w for w in words if w in title_low]
        if not matched:
            if DEBUG_VERBOSE:
                print(f"   🛑 [DEBUG WERYFIKACJA] ODRZUCONO! Brak słów {words} w tytule: '{title}'")
            return False
        if DEBUG_VERBOSE:
            print(f"   ✅ [DEBUG WERYFIKACJA] ZATWIERDZONO! Pasujące słowa kluczowe: {matched} w '{title}'")

    return True

def wait_for_valid_title(target_name, timeout=0.40):
    """
    Dynamiczne czekanie na nagłówek otwartej oferty (np. 'Listings - Davy Jones Chair').
    Zwraca (is_valid, title_text). W razie Wooden Chair natychmiast przerywa i blokuje!
    """
    end = time.time() + timeout
    last_title = ""
    tries = 0
    t_start = time.time()
    while running and time.time() < end:
        tries += 1
        title = read_title(target_name)
        if title:
            last_title = title
            # Jeśli widać Wooden Chair -> natychmiastowa blokada bez czekania!
            if "wooden" in title and "wooden" not in target_name.lower():
                dt = (time.time() - t_start) * 1000
                if DEBUG_VERBOSE:
                    print(f"   🛑 [DEBUG] Natychmiastowe wykrycie Wooden Chair po {dt:.1f}ms (próba #{tries})")
                return False, title
            if check_title_match(target_name, title):
                dt = (time.time() - t_start) * 1000
                if DEBUG_VERBOSE:
                    print(f"   ✅ [DEBUG] Poprawny nagłówek '{title}' po {dt:.1f}ms (próba #{tries})")
                return True, title
        time.sleep(0.02)
    return False, last_title

def read_popup_text():
    """Odczytuje treść pytania potwierdzającego zakup z okienka 'Hey! Are you sure?'."""
    img_bgr = _grab_bgr(POPUP_TEXT_REGION)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    if HAS_FAST_TESS and _tess_line is not None:
        _tess_line.SetImage(Image.fromarray(scaled))
        text = _tess_line.GetUTF8Text().strip()
    else:
        try:
            text = pytesseract.image_to_string(scaled, config='--psm 7').strip()
        except Exception:
            text = ""
    return text

def verify_popup_text(target_name, max_price, currency_type, text):
    """
    Weryfikuje treść wyskakującego okienka:
    np. 'Buy 1x Rusty Stove from Yahirrueda989 for 2 Diamonds?'
    Zwraca (is_valid, reason).
    """
    if not text or len(text) < 5:
        return False, "Brak lub zbyt krótki tekst w popupie"

    text_low = text.lower()
    tgt_low = target_name.lower()

    # 1. Bezwzględna blokada dla Wooden Chair
    if "wooden" in text_low and "wooden" not in tgt_low:
        return False, "Wykryto 'wooden' w popupie"

    # 2. Konflikt Chair vs Table
    if "chair" in tgt_low and "table" in text_low and "table" not in tgt_low:
        return False, "Niezgodność: szukano chair, a w popupie jest table"
    if "table" in tgt_low and "chair" in text_low and "chair" not in tgt_low:
        return False, "Niezgodność: szukano table, a w popupie jest chair"

    # 3. Słowa kluczowe serii (np. davy, sunken, celestial itp.)
    words = [w for w in tgt_low.split() if w not in ("chair", "table", "the", "a", "an", "1x")]
    if words:
        if not any(w in text_low for w in words):
            return False, f"Brak słów kluczowych {words} w popupie"

    # 4. Sprawdzenie ceny w tekście jeśli udało się sparsować
    m_price = re.search(r'for\s+[\$]?(\d+)\s*(diamonds|cash|\$)?', text_low)
    if m_price:
        price_in_popup = int(m_price.group(1))
        if currency_type == "DIAMOND" and price_in_popup > max_price:
            return False, f"Cena w popupie ({price_in_popup} 💎) > max ({max_price} 💎)"

    return True, "Zgodne z ofertą"

def send_notification(message, title="Roblox Sniper"):
    """Wysyła powiadomienie na telefon (WhatsApp / Discord / ntfy)."""
    # 1. WhatsApp (CallMeBot)
    if WHATSAPP_PHONE and WHATSAPP_APIKEY:
        try:
            encoded_text = urllib.parse.quote(f"*{title}*\n{message}")
            clean_phone = WHATSAPP_PHONE.replace("+", "").replace(" ", "").replace("-", "")
            url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded_text}&apikey={WHATSAPP_APIKEY}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                print("   📲 [WHATSAPP] Powiadomienie wysłane na telefon!")
        except Exception as e:
            print(f"   ⚠️ Błąd wysyłania powiadomienia na WhatsApp: {e}")

    # 2. Discord Webhook
    if DISCORD_WEBHOOK:
        try:
            payload = json.dumps({"content": f"🎯 **{title}**\n{message}"}).encode('utf-8')
            req = urllib.request.Request(DISCORD_WEBHOOK, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                print("   📲 [DISCORD] Powiadomienie wysłane!")
        except Exception as e:
            print(f"   ⚠️ Błąd wysyłania powiadomienia na Discord: {e}")

    # 3. ntfy.sh (błyskawiczny push na apkę w telefonie bez zakładania konta)
    if NTFY_TOPIC:
        try:
            payload = json.dumps({
                "topic": NTFY_TOPIC,
                "title": title,
                "message": message,
                "priority": 4,
                "tags": ["tada", "moneybag"]
            }).encode('utf-8')
            req = urllib.request.Request(
                "https://ntfy.sh",
                data=payload,
                headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"   📲 [NTFY] Powiadomienie push wysłane na telefon! (temat: {NTFY_TOPIC})")
        except Exception as e:
            print(f"   ⚠️ Błąd wysyłania powiadomienia na ntfy: {e}")

def confirm_and_finalize_purchase(target, currency, result):
    """
    Czeka na wyskoczenie okienka 'Hey! Are you sure?', weryfikuje linijkę tekstu
    i klika 'Buy' (zielony) lub 'Cancel' (czerwony w razie niezgodności).
    Zwraca True jeśli zakup został pomyślnie potwierdzony.
    """
    end = time.time() + 1.2
    popup_text = ""
    while running and time.time() < end:
        popup_text = read_popup_text()
        if popup_text and len(popup_text) >= 10:
            break
        time.sleep(0.04)

    is_ok, reason = verify_popup_text(target["name"], target["max"], currency, popup_text)

    if is_ok:
        print(f"   🛡️ [POPUP POTWIERDZENIE] '{popup_text}' — ZGADZA SIĘ! KLIKAM BUY!")
        click(*POPUP_CONFIRM_BTN, delay=0.3)
        STATS["bought_items"].append({"name": target["name"], "price": result, "currency": currency})
        return True
    else:
        print(f"   🛑 [POPUP ANULOWANIE] '{popup_text or 'Brak okienka'}' ({reason}) — KLIKAM CANCEL!")
        click(*POPUP_CANCEL_BTN, delay=0.3)
        STATS["popup_cancelled"] += 1
        return False

def recover_market_state():
    """
    Fail-safe: Sprawdza czy nie otworzyło się okienko 'Select an Item!'
    albo czy Market nie przełączył się przypadkowo na zakładkę 'Sell'.
    Automatycznie klika [X] i przycisk 'Buy', przywracając pełną gotowość do snajpienia.
    Zwraca True jeśli nastąpiła którakolwiek naprawa.
    """
    recovered = False

    # 1. Sprawdzenie czy okienko 'Select an Item!' jest otwarte
    crop_x = _grab_bgr(FAILSAFE_POPUP_X_CHECK)
    b_x, g_x, r_x = crop_x[:,:,0].astype(int), crop_x[:,:,1].astype(int), crop_x[:,:,2].astype(int)
    red_count = np.sum((r_x - g_x > 40) & (r_x - b_x > 40) & (r_x > 160))
    if red_count > 50:
        print("   🛡️ [FAIL-SAFE] Wykryto okienko 'Select an Item!' — zamykam [X]!")
        click(*POPUP_SELECT_ITEM_X, delay=0.25)
        STATS["fail_safe_recoveries"] += 1
        recovered = True

    # 2. Sprawdzenie czy Market jest na zakładce 'Sell'
    crop_sell = _grab_bgr(FAILSAFE_SELL_TAB_CHECK)
    b_s, g_s, r_s = crop_sell[:,:,0].astype(int), crop_sell[:,:,1].astype(int), crop_sell[:,:,2].astype(int)
    blue_count = np.sum((b_s > 180) & (g_s > 120) & (r_s < 110))
    if blue_count > 50:
        print("   🛡️ [FAIL-SAFE] Wykryto zakładkę 'Sell' — przełączam na 'Buy'!")
        click(*MARKET_BUY_TAB, delay=0.25)
        STATS["fail_safe_recoveries"] += 1
        recovered = True

    return recovered

def visit(target):
    t0 = time.time()
    prof = []
    def lap(name):
        prof.append(f"{name} {time.time()-t0:.2f}s")

    # Fail-safe: upewnij się, że jesteśmy w 'Buy' i brak blokujących okienek
    recover_market_state()

    STATS["checks_total"] += 1
    print(f"\n➡️ {target['name']}")

    # 1. Błyskawiczne i pewne czyszczenie szukajki (fokus + Ctrl+A + Backspace + wklejenie)
    if DEBUG_VERBOSE:
        print(f"   🔍 [DEBUG SZUKAJ] Wpisuję do szukajki: '{target['query']}'")
    click(*SEARCH_BOX, delay=0.06, label="Szukajka")
    hotkey('ctrl', 'a')
    time.sleep(0.01)
    pai.press('backspace')
    time.sleep(0.01)
    pyperclip.copy(target["query"].lower())
    hotkey('ctrl', 'v')
    time.sleep(0.02)
    pai.press('enter')
    safe_sleep(WAIT_RESULTS)
    lap("search")

    # 2. Otwarcie itemu
    if DEBUG_VERBOSE:
        print(f"   🖱️ [DEBUG OPEN] Kliknięcie w pierwszy slot: ITEM_1 {ITEM_1}")
    click(*target.get("item_pos", ITEM_1), delay=WAIT_OPEN, label="Item 1")
    lap("open")

    # 3. WERYFIKACJA OTWARTEGO PRZEDMIOTU (Tarcza anty-Wooden Chair)
    is_correct, opened_title = wait_for_valid_title(target["name"], timeout=0.40)
    if not is_correct:
        STATS["blocks_wrong_item"] += 1
        ts = time.strftime("%H%M%S")
        safe_name = target['name'].replace(" ", "_").lower()
        reason = f"BLOKADA: Otwarto '{opened_title or 'brak tekstu'}' zamiast '{target['name']}'"
        print(f"   🛑 {reason} — ANULUJĘ!")
        if DEBUG_MODE:
            save_annotated_screen(f"BLOCKED_{safe_name}_{ts}.png", reason, status_color=(0, 0, 255))
            header_crop = _grab_bgr(ITEM_HEADER_REGION)
            save_crop_debug(f"BLOCKED_header_{safe_name}_{ts}", header_crop)
            print(f"   📸 [DEBUG] Zapisano pełny zrzut z naniesionymi ramkami: debug/BLOCKED_{safe_name}_{ts}.png")

        # Jeśli to było okienko 'Select an Item!' lub zakładka Sell — napraw to natychmiast
        did_recover = recover_market_state()

        # Klikamy wstecz TYLKO jeśli faktycznie otworzył się inny przedmiot (np. Wooden Chair).
        # Jeśli nic się nie otworzyło (brak ofert), jesteśmy nadal na liście Marketu,
        # więc kliknięcie BACK_BTN wbiłoby nas niepotrzebnie w zakładkę Sell!
        if not did_recover and opened_title:
            click(*BACK_BTN, delay=WAIT_BACK, label="Wstecz")

        lap("back_wrong_item")
        _print_profile(prof)
        return False

    # 4. Refresh — upewnij się, że cooldown gry minął (ochrona przy LEAD_TIME)
    rem = (target["last_refresh"] + target["refresh_wait"]) - time.time()
    if rem > 0:
        safe_sleep(rem)
    if DEBUG_VERBOSE:
        print(f"   🔄 [DEBUG REFRESH] Kliknięcie REFRESH_BTN {REFRESH_BTN}")
    click(*REFRESH_BTN, delay=WAIT_REFRESH, label="Odśwież")
    target["last_refresh"] = time.time()
    lap("refresh")

    # 5. Sprawdzenie ceny i waluty
    result, currency, tries, nz = wait_for_price(target['name'])
    lap(f"ocr({tries})")

    if result == SKIP_TEXT:
        print(f"   ℹ️ brak ceny / Twoja oferta — skip")
    elif result is None:
        print(f"   ⚠️ brak odczytu ceny | próby: {tries} | max px: {nz}")
    elif currency == "CASH":
        # Podwójna blokada bezpieczeństwa przed kliknięciem BUY
        if not check_title_match(target["name"], read_title(target["name"])):
            print(f"   🛑 BLOKADA PRZED KUPNEM: Nagłówek nie pasuje do '{target['name']}' — ANULUJĘ!")
            click(*BACK_BTN, delay=WAIT_BACK, label="Wstecz")
            return False
        STATS["buy_attempts"] += 1
        print(f"   🔥 MEGA STEAL! {target['name']} za KASĘ (${result}) — Otwieram potwierdzenie...")
        click(*BUY_BTN, delay=0.1, label="Kup")

        # Ostateczna tarcza: Potwierdzenie w okienku modalnym
        if confirm_and_finalize_purchase(target, currency, result):
            msg = f"Kupiono {target['name']} za KASĘ (${result})!"
            print(f"   🏆 SUKCES! {msg}")
            send_notification(msg, title="🔥 MEGA STEAL KUPIONY!")
            _print_profile(prof)
            return True
        else:
            click(*BACK_BTN, delay=WAIT_BACK, label="Wstecz")
            _print_profile(prof)
            return False

    elif result <= target["max"]:
        # Podwójna blokada bezpieczeństwa przed kliknięciem BUY
        if not check_title_match(target["name"], read_title(target["name"])):
            print(f"   🛑 BLOKADA PRZED KUPNEM: Nagłówek nie pasuje do '{target['name']}' — ANULUJĘ!")
            click(*BACK_BTN, delay=WAIT_BACK, label="Wstecz")
            return False
        STATS["buy_attempts"] += 1
        print(f"   🎯 {result} 💎 ≤ {target['max']} 💎 — Otwieram potwierdzenie...")
        click(*BUY_BTN, delay=0.1, label="Kup")

        # Ostateczna tarcza: Potwierdzenie w okienku modalnym
        if confirm_and_finalize_purchase(target, currency, result):
            msg = f"Kupiono {target['name']} za {result} 💎!"
            print(f"   🏆 SUKCES! {msg}")
            send_notification(msg, title="🎯 PRZEDMIOT KUPIONY!")
            _print_profile(prof)
            return True
        else:
            click(*BACK_BTN, delay=WAIT_BACK, label="Wstecz")
            _print_profile(prof)
            return False
    else:
        print(f"   ❌ {result} 💎 — za drogo (max {target['max']} 💎) | próby: {tries}")

    # 6. Błyskawiczny powrót
    click(*BACK_BTN, delay=WAIT_BACK, label="Wstecz")
    lap("back")
    _print_profile(prof)
    return False

def _print_profile(prof):
    if PROFILE:
        print(f"   ⏱️  " + " | ".join(prof))

def print_session_summary():
    """Wypisuje czytelne podsumowanie statystyk sesji."""
    elapsed = time.time() - STATS["start_time"] if STATS["start_time"] else 0
    m, s = divmod(int(elapsed), 60)
    print("\n" + "=" * 60)
    print("📊 PODSUMOWANIE DZIAŁANIA MAKRA:")
    print(f"   ⏱️  Czas trwania sesji: {m}m {s}s")
    print(f"   🔍 Przeszukane oferty: {STATS['checks_total']}")
    print(f"   🛒 Podjęte próby zakupu: {STATS['buy_attempts']}")
    if STATS["bought_items"]:
        print(f"   🏆 Udane zakupy ({len(STATS['bought_items'])}):")
        for it in STATS["bought_items"]:
            symbol = "💎" if it["currency"] == "DIAMOND" else "$"
            print(f"      • {it['name']} za {it['price']} {symbol}")
    else:
        print("   🏆 Udane zakupy: 0")
    if STATS["popup_cancelled"]:
        print(f"   ⚠️  Anulowane w oknie potwierdzenia: {STATS['popup_cancelled']}")
    if STATS["blocks_wrong_item"]:
        print(f"   🛡️  Zablokowane pomyłki (np. Wooden Chair): {STATS['blocks_wrong_item']}")
    if STATS["fail_safe_recoveries"]:
        print(f"   🔧  Automatyczne naprawy UI (okienka / powrót do Buy): {STATS['fail_safe_recoveries']}")
    print("=" * 60 + "\n")

def main():
    load_config()
    for t in TARGETS:
        t["last_refresh"] = 0.0
        t["bought"] = False

    STATS["start_time"] = time.time()

    print("=" * 60)
    print(f"🎯 MULTI-SNIPER (TRYB TURBO | PROFIL: {CURRENT_RES.upper()})")
    print(f"   📍 Koordynaty: Szukajka {SEARCH_BOX} | Slot 1 {ITEM_1} | Refresh {REFRESH_BTN} | Kup {BUY_BTN} | Wstecz {BACK_BTN}")
    if _tess_status_msg:
        print(f"   {_tess_status_msg}")
    for t in TARGETS:
        print(f"   • {t['name']}: max {t['max']} 💎")
    print("🛑 KILL SWITCH: F8 / ESC")
    if DEBUG_MODE:
        print(f"📁 FOLDER DIAGNOSTYCZNY: {DEBUG_DIR}")
    print("=" * 60)
    print(f"⏳ Start za {START_DELAY}s — przełącz na okno Roblox!")
    safe_sleep(START_DELAY)
    if not running:
        print_session_summary()
        return

    # Fail-safe na starcie: upewnij się, że okno gry jest na zakładce 'Buy'
    recover_market_state()

    # Zrzut kalibracyjny zaraz po przełączeniu na okno Roblox
    if DEBUG_MODE:
        calib_path = save_annotated_screen("00_start_calibration.png", "KALIBRACJA: Pozycja okna Roblox w momencie startu bota")
        if calib_path:
            print(f"\n📸 [DEBUG KALIBRACJA] Zapisano zrzut: debug/00_start_calibration.png")
            print(f"   (Możesz otworzyć ten plik, aby sprawdzić czy wszystkie ramki i punkty leżą idealnie na UI gry!)\n")

    try:
        while running:
            now = time.time()
            candidates = [t for t in TARGETS
                          if not t["bought"] and now - t["last_refresh"] >= (t["refresh_wait"] - LEAD_TIME)]
            if not candidates:
                upcoming = [t["last_refresh"] + (t["refresh_wait"] - LEAD_TIME) for t in TARGETS if not t["bought"]]
                if not upcoming:
                    print("\n🏆 Wszystkie przedmioty kupione!")
                    return
                safe_sleep(0.02)
                continue

            target = max(candidates, key=lambda t: now - t["last_refresh"])
            if visit(target):
                if STOP_AFTER_BUY:
                    target["bought"] = True
                    print("\n🏆 Sukces! Przedmiot kupiony — zatrzymuję bota.")
                    return
                print(f"✅ {target['name']} kupiony — poluję dalej bez zatrzymywania!")
    finally:
        print_session_summary()

if __name__ == "__main__":
    main()
    print("Zakończono działanie makro.")
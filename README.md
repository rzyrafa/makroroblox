# 🎯 Roblox Market Sniper (Makroblox)

Zaawansowany, wielowątkowy i ultra-szybki bot / makro snajperskie do automatycznego monitorowania rynku w **Roblox**, natychmiastowego wykrywania okazji cenowych i błyskawicznego skupowania przedmiotów.

Aplikacja wyposażona jest w dedykowany silnik **OCR czasu rzeczywistego (~4ms)**, wielostopniowe **tarcze bezpieczeństwa** przed pomyłkami (anty-Wooden Chair), interfejs graficzny (GUI) w **Tkinter**, wsparcie profili rozdzielczości (1440p / 1080p) oraz **powiadomienia push na telefon** (WhatsApp, Discord, ntfy.sh).

---

## ⚡ Kluczowe Możliwości

1. **Ultra-szybki silnik OCR (~4ms)**:
   - Integracja z biblioteką `tesserocr` (C++ API Tesseract) z automatycznym fallbackiem na `pytesseract`.
   - **Podwójny rurociąg rozpoznawania tekstu**:
     - **Ceny**: Silnik dostosowany do oficjalnego kroju cyfr Roblox (*Builder Sans Bold*) z rozpoznawaniem liczb jedno- i wielocyfrowych (w tym trudnych cyfr takich jak `9`, `17`, `18`, `19`, `90`, `497`).
     - **Nagłówki i pytania**: Dedykowany silnik dopasowany do standardowego kroju interfejsu Roblox (*Source Sans*).

2. **Wielostopniowe Tarcze Bezpieczeństwa (Fail-Safe)**:
   - **Tarcza anty-pomyłkowa (Anti-Wooden Chair)**: Dynamiczne sprawdzanie nagłówka otwartej oferty (`read_title`). Blokuje zakup, gdy na skutek laga wyszukiwarki otworzy się niepożądana oferta.
   - **Weryfikacja okienka popup ("Hey! Are you sure?")**: Odczyt i parsowanie tekstu modalnego przed ostatecznym potwierdzeniem transakcji (sprawdzenie nazwy i maksymalnej ceny w walucie 💎 Diamonds / $ Cash).
   - **Auto-naprawa stanu interfejsu gry**: Samoczynne wykrywanie i zamykanie niepożądanego okienka *"Select an Item!"* oraz powrót z zakładki *"Sell"* do *"Buy"*.

3. **Tryb Turbo i inteligentna kolejka**:
   - Przeszukiwanie wielu przedmiotów z niezależnymi czasami odświeżania (`cooldown`).
   - Mechanizm wcześniejszego przygotowania zapytania (`LEAD_TIME`), redukujący czas reakcji do ułamków sekund.

4. **Wieloplatformowe powiadomienia na telefon**:
   - **ntfy.sh**: Darmowe powiadomienia push bez rejestracji konta na telefon (Android / iOS).
   - **Discord**: Webhook z powiadomieniami na dowolny kanał i wzmianką na smartfonie.
   - **WhatsApp**: Darmowe API przez CallMeBot.

5. **Wygodny Panel GUI (Tkinter)**:
   - Proste dodawanie i edycja celów (nazwa, fraza, cena maksymalna, czas odświeżania).
   - Przełączanie w locie między profilami rozdzielczości (`1440p (2560x1440)` oraz `1080p (1920x1080)`).
   - Interaktywny podgląd i edycja koordynatów oraz ramek pikseli OCR.
   - Podgląd konsoli na żywo z czytelnym logowaniem każdego kliknięcia myszy.

---

## 📂 Struktura Projektu — Co robi co?

| Plik / Katalog | Rola i opis działania |
| :--- | :--- |
| **`makro.py`** | **Główny silnik automatyzacji bota**. Zawiera całą logikę pętli snajpienia, kolejkowanie celów, sterowanie kursorem i klawiaturą (`pydirectinput`), przetwarzanie obrazu (`cv2`, `mss`), ultra-szybki OCR (`tesserocr`), systemy weryfikacji nagłówków/popupów oraz wysyłanie powiadomień. |
| **`gui.py`** | **Graficzny menedżer bota (GUI)**. Zbudowany w `tkinter` / `ttk`. Umożliwia edycję przedmiotów do kupienia, ustawianie timerów, kalibrację koordynatów profili ekranu, testowanie webhooków oraz uruchamianie i zatrzymywanie bota z konsolą na żywo. |
| **`config.json`** | **Plik konfiguracyjny**. Przechowuje listę celów (`targets`), timery opóźnień (`timers`), konfigurację powiadomień (`ntfy_topic`, `discord_webhook`, `whatsapp`) oraz kompletne profile współrzędnych i ramek OCR (`profiles.1440p`, `profiles.1080p`). |
| **`RobloxSniper.spec`** | **Konfiguracja PyInstaller**. Skrypt do kompilacji całego projektu w pojedynczy, autonomiczny plik `.exe`. Pakuje biblioteki DLL C++, model `tessdata`, konfigurację oraz ikony. |
| **`kalibrator.ps1`** / **`kalibrator.bat`** | **Narzędzie do kalibracji**. Skrypt PowerShell z nakładką GUI do łatwego wyznaczania współrzędnych kliknięć $(X, Y)$ oraz ramek pikseli OCR $(\text{top}, \text{left}, \text{width}, \text{height})$ pod dowolne niestandardowe monitory i okna gry. |
| **`start_gui.bat`** | Skrypt wsadowy Windows uruchamiający panel graficzny GUI bota w środowisku wirtualnym `venv`. |
| **`start.bat`** | Skrypt wsadowy Windows uruchamiający bezpośrednio silnik makra w konsoli CMD. |
| **`requirements.txt`** | Lista zależności Pythona potrzebnych do uruchomienia i kompilacji projektu. |
| **`tessdata/eng.traineddata`** | Baza językowa modelu sieci neuronowej Tesseract OCR (język angielski), używana do odczytu tekstu i cyfr w grze. |
| **`.gitignore`** | Reguły wykluczające z repozytorium zbędne pliki tymczasowe, środowisko `venv`, pliki kompilacji `build/`, `dist/` oraz duże binaria `.exe`. |

---

## 🛠️ Instalacja i Wymagania

### Wymagania systemowe
- **System**: Windows 10 lub Windows 11 (64-bit)
- **Python**: 3.10+
- **Tesseract-OCR**: Zainstalowany w systemie lub dostarczony w pakiecie `tesserocr`

### Krok po kroku:
1. Sklonuj repozytorium:
   ```bash
   git clone <URL_TWOJEGO_REPOZYTORIUM>
   cd makroblox
   ```

2. Utwórz i aktywuj środowisko wirtualne:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Zainstaluj wymagane pakiety:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🚀 Uruchomienie

### Sposób 1: Przez Interfejs Graficzny (Zalecane)
Uruchom plik `start_gui.bat` lub w konsoli wpisz:
```powershell
python gui.py
```
1. Wybierz swój profil rozdzielczości (np. `1440p (2560x1440)` lub `1080p (1920x1080)`).
2. Sprawdź i ustaw przedmioty oraz ich maksymalne ceny w zakładce **🎯 Przedmioty (Targets)**.
3. Kliknij **▶ URUCHOM MAKRO** i przełącz się na okno Roblox.

### Sposób 2: Bezpośrednio w konsoli
Uruchom `start.bat` lub wpisz:
```powershell
python makro.py
```

### 🛑 Awaryjne Zatrzymanie (Kill Switch)
W dowolnym momencie możesz natychmiast zatrzymać bota wciskając klawisz **`F8`** lub **`ESC`**.

---

## 📦 Budowanie pliku wykonywalnego (.exe)

Aby wygenerować samodzielny plik `.exe` niepotrzebujący zainstalowanego Pythona:
```powershell
pyinstaller RobloxSniper.spec --noconfirm
```
Skompilowany plik pojawi się w folderze `dist/RobloxSniper.exe`.

---

## ⚙️ Konfiguracja Powiadomień na Telefon

### 1. ntfy.sh (Najprostsza — 1 minuta konfiguracji)
1. Zainstaluj darmową aplikację **ntfy** na swój telefon ([Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [App Store](https://apps.apple.com/app/ntfy/id1625396347)).
2. W aplikacji kliknij `+` (Subskrybuj temat) i wpisz dowolną unikalną nazwę, np. `twojbot2115`.
3. Wpisz tę samą nazwę tematu w polu **ntfy topic** w GUI bota i kliknij *Test powiadomienia*.

### 2. Discord Webhook
1. Na swoim serwerze Discord wejdź w: *Ustawienia kanału -> Integracje -> Webhooki -> Nowy webhook*.
2. Skopiuj adres URL webhooka i wklej go w pliku `config.json` w polu `"discord_webhook"`.

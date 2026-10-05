# kalibrator.ps1 — Szybki kalibrator koordynatow dla Makroblox Sniper (Klawisz X)
# Dziala natywnie na kazdym Windowsie bez instalowania Pythona!

Add-Type -AssemblyName System.Windows.Forms

$winApiCode = @"
using System;
using System.Runtime.InteropServices;

public class MouseTracker {
    [DllImport("user32.dll")]
    public static extern short GetAsyncKeyState(int vKey);

    [DllImport("user32.dll")]
    public static extern bool GetCursorPos(out POINT lpPoint);

    [StructLayout(LayoutKind.Sequential)]
    public struct POINT {
        public int X;
        public int Y;
    }

    public static POINT GetPos() {
        POINT p;
        GetCursorPos(out p);
        return p;
    }

    public static bool IsXKeyDown() {
        return (GetAsyncKeyState(0x58) & 0x8000) != 0; // Klawisz X
    }

    public static bool IsF2Down() {
        return (GetAsyncKeyState(0x71) & 0x8000) != 0; // Klawisz F2 opcjonalnie
    }

    public static bool IsEscDown() {
        return (GetAsyncKeyState(0x1B) & 0x8000) != 0; // Klawisz ESC
    }
}
"@

Add-Type -TypeDefinition $winApiCode

function Beep-Ok {
    try { [Console]::Beep(1200, 90) } catch {}
}

function Beep-Done {
    try { 
        [Console]::Beep(1000, 100)
        [Console]::Beep(1500, 150)
    } catch {}
}

function Wait-For-Click-Or-Key {
    while ([MouseTracker]::IsXKeyDown() -or [MouseTracker]::IsF2Down()) {
        Start-Sleep -Milliseconds 20
    }

    while ($true) {
        if ([MouseTracker]::IsEscDown()) {
            return $null
        }
        if ([MouseTracker]::IsXKeyDown() -or [MouseTracker]::IsF2Down()) {
            $pt = [MouseTracker]::GetPos()
            Beep-Ok
            while ([MouseTracker]::IsXKeyDown() -or [MouseTracker]::IsF2Down()) {
                Start-Sleep -Milliseconds 20
            }
            Start-Sleep -Milliseconds 80
            return $pt
        }
        Start-Sleep -Milliseconds 15
    }
}

Clear-Host
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SZYBKI KALIBRATOR KOORDYNATOW (KLAWISZ 'X')" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Program dziala w tle, gdy masz wlaczone i aktywne okno Roblox!" -ForegroundColor White
Write-Host " Wystarczy najechac myszka na element i nacisnac klawisz [X]!" -ForegroundColor Green
Write-Host " (Myszka nic nie klika w grze - brak przypadkowych klikniec)" -ForegroundColor Gray
Write-Host ""
Write-Host " [1] KREATOR KALIBRACJI — KROK PO KROKU (Zalecany do snajpera)" -ForegroundColor Green
Write-Host " [2] PODGLAD NA ZYWO (Wypisuje pozycje po kazdym wcisnieciu X)" -ForegroundColor White
Write-Host ""
Write-Host " Wybierz tryb [1 lub 2] i wcisnij ENTER: " -NoNewline -ForegroundColor Yellow

$choice = Read-Host

if ($choice -eq "2") {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " TRYB PODGLADU NA ZYWO (Klawisz X)" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " - Przelacz sie na okno Roblox." -ForegroundColor White
    Write-Host " - Najedz kursorem myszy na dowolny punkt i wcisnij [X] na klawiaturze." -ForegroundColor Yellow
    Write-Host " - Dzwiek BEEP potwierdza zapisanie punktu." -ForegroundColor Green
    Write-Host " - Koordynaty sa automatycznie kopiowane do schowka!" -ForegroundColor Green
    Write-Host " - Aby zakonczyc, wcisnij klawisz [ESC]." -ForegroundColor Red
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray

    $count = 1
    while ($true) {
        $pt = Wait-For-Click-Or-Key
        if ($null -eq $pt) {
            Write-Host "`nZakonczono nasluchiwanie (ESC)." -ForegroundColor Yellow
            break
        }
        $coordStr = "[$($pt.X), $($pt.Y)]"
        [System.Windows.Forms.Clipboard]::SetText($coordStr)
        Write-Host " [#$count] X = $($pt.X.ToString().PadLeft(4)), Y = $($pt.Y.ToString().PadLeft(4))   -->   $coordStr (skopiowano)" -ForegroundColor Green
        $count++
    }
    Write-Host "`nNacisnij dowolny klawisz, aby zamknac..." -ForegroundColor Gray
    [Console]::ReadKey($true) | Out-Null
    exit
}

Clear-Host
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " KREATOR KALIBRACJI PROFILU MAKRA" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Instrukcja:" -ForegroundColor White
Write-Host " 1. Przelacz sie na okno Roblox (program czeka w tle)." -ForegroundColor White
Write-Host " 2. Najedz kursorem myszy na wskazany przycisk i WCISNIJ [X]." -ForegroundColor Yellow
Write-Host " 3. Uslyszysz dzwiek BEEP - znak zapisania punktu!" -ForegroundColor Green
Write-Host " 4. Klawisz [ESC] w dowolnym momencie anuluje kalibracje." -ForegroundColor Red
Write-Host "------------------------------------------------------------`n" -ForegroundColor Gray

$steps = @(
    @{ Key = "search_box";           Label = "1. POLE WYSZUKIWANIA (lupka/pole Search u gory po prawej)" },
    @{ Key = "item_1";               Label = "2. PIERWSZY KAFELEK OFERTY (srodek 1. przedmiotu na liscie)" },
    @{ Key = "refresh_btn";          Label = "3. PRZYCISK REFRESH (niebieski przycisk odswiezania)" },
    @{ Key = "buy_btn";              Label = "4. PRZYCISK BUY (zielony przycisk z cena diamentow w panelu)" },
    @{ Key = "back_btn";             Label = "5. PRZYCISK BACK (strzalka powrotu w lewym gornym rogu targu)" },
    @{ Key = "market_sell_tab";      Label = "6. ZAKLADKA 'SELL' (po lewej stronie okna Market)" },
    @{ Key = "market_buy_tab";       Label = "7. ZAKLADKA 'BUY' (po lewej stronie okna Market)" },
    @{ Key = "popup_confirm_btn";    Label = "8. PRZYCISK BUY W OKNIE 'Are you sure?' (zielony)" },
    @{ Key = "popup_cancel_btn";     Label = "9. PRZYCISK CANCEL W OKNIE 'Are you sure?' (czerwony)" },
    @{ Key = "popup_select_item_x";  Label = "10. CZERWONY IKS [X] okienka zamykajacego" }
)

$resMap = @{}

foreach ($s in $steps) {
    Write-Host " --> Najedz na $($s.Label) i wcisnij [X]... " -ForegroundColor Yellow -NoNewline
    $pt = Wait-For-Click-Or-Key
    if ($null -eq $pt) {
        Write-Host "`nKalibracja przerwana przez uzytkownika (ESC)." -ForegroundColor Red
        exit
    }
    $resMap[$s.Key] = @($pt.X, $pt.Y)
    Write-Host "OK! -> [$($pt.X), $($pt.Y)]" -ForegroundColor Green
}

Write-Host "`n------------------------------------------------------------" -ForegroundColor Gray
Write-Host " KALIBRACJA RAMEK TEKSTOWYCH (Najedz i wcisnij [X])" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

Write-Host " --> [RAMKA TYTULU] Najedz na LEWY GORNY rog napisu 'Listings - ...' i wcisnij [X]: " -ForegroundColor Yellow -NoNewline
$ptTopLeft = Wait-For-Click-Or-Key
if ($null -eq $ptTopLeft) { exit }
Write-Host "OK ($($ptTopLeft.X), $($ptTopLeft.Y))" -ForegroundColor Green

Write-Host " --> [RAMKA TYTULU] Najedz na PRAWY DOLNY rog napisu 'Listings - ...' i wcisnij [X]: " -ForegroundColor Yellow -NoNewline
$ptBottomRight = Wait-For-Click-Or-Key
if ($null -eq $ptBottomRight) { exit }
Write-Host "OK ($($ptBottomRight.X), $($ptBottomRight.Y))" -ForegroundColor Green

$hdr_top    = [Math]::Min($ptTopLeft.Y, $ptBottomRight.Y)
$hdr_left   = [Math]::Min($ptTopLeft.X, $ptBottomRight.X)
$hdr_width  = [Math]::Abs($ptBottomRight.X - $ptTopLeft.X)
$hdr_height = [Math]::Abs($ptBottomRight.Y - $ptTopLeft.Y)
$resMap["item_header_region"] = @{ top = $hdr_top; left = $hdr_left; width = $hdr_width; height = $hdr_height }

Write-Host "`n --> [RAMKA CENY] Najedz na LEWY GORNY rog zielonego przycisku z cena i wcisnij [X]: " -ForegroundColor Yellow -NoNewline
$prTopLeft = Wait-For-Click-Or-Key
if ($null -eq $prTopLeft) { exit }
Write-Host "OK ($($prTopLeft.X), $($prTopLeft.Y))" -ForegroundColor Green

Write-Host " --> [RAMKA CENY] Najedz na PRAWY DOLNY rog zielonego przycisku z cena i wcisnij [X]: " -ForegroundColor Yellow -NoNewline
$prBottomRight = Wait-For-Click-Or-Key
if ($null -eq $prBottomRight) { exit }
Write-Host "OK ($($prBottomRight.X), $($prBottomRight.Y))" -ForegroundColor Green

$pr_top    = [Math]::Min($prTopLeft.Y, $prBottomRight.Y)
$pr_left   = [Math]::Min($prTopLeft.X, $prBottomRight.X)
$pr_width  = [Math]::Abs($prBottomRight.X - $prTopLeft.X)
$pr_height = [Math]::Abs($prBottomRight.Y - $prTopLeft.Y)
$resMap["item_price"] = @{ top = $pr_top; left = $pr_left; width = $pr_width; height = $pr_height }

$resMap["failsafe_sell_tab_check"] = @{ top = ($resMap["market_sell_tab"][1] - 10); left = ($resMap["market_sell_tab"][0] - 10); width = 20; height = 20 }
$resMap["failsafe_popup_x_check"]  = @{ top = ($resMap["popup_select_item_x"][1] - 12); left = ($resMap["popup_select_item_x"][0] - 12); width = 25; height = 25 }
$resMap["popup_text_region"]       = @{ top = ($resMap["popup_confirm_btn"][1] - 162); left = ($resMap["popup_confirm_btn"][0] - 159); width = 620; height = 66 }

Beep-Done

Clear-Host
Write-Host "============================================================" -ForegroundColor Green
Write-Host " KALIBRACJA ZAKONCZONA POMYSLNIE!" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green

$sb = $resMap["search_box"]
$i1 = $resMap["item_1"]
$rf = $resMap["refresh_btn"]
$by = $resMap["buy_btn"]
$bk = $resMap["back_btn"]
$pc = $resMap["popup_confirm_btn"]
$px = $resMap["popup_cancel_btn"]
$sx = $resMap["popup_select_item_x"]
$mb = $resMap["market_buy_tab"]
$ms = $resMap["market_sell_tab"]
$ip = $resMap["item_price"]
$ih = $resMap["item_header_region"]
$pt = $resMap["popup_text_region"]
$fx = $resMap["failsafe_popup_x_check"]
$fs = $resMap["failsafe_sell_tab_check"]

$lines = @(
    '        "1080p": {',
    '            "label": "1920x1080 (Laptop)",',
    "            `"search_box`": [$($sb[0]), $($sb[1])],",
    "            `"item_1`": [$($i1[0]), $($i1[1])],",
    "            `"refresh_btn`": [$($rf[0]), $($rf[1])],",
    "            `"buy_btn`": [$($by[0]), $($by[1])],",
    "            `"back_btn`": [$($bk[0]), $($bk[1])],",
    "            `"popup_confirm_btn`": [$($pc[0]), $($pc[1])],",
    "            `"popup_cancel_btn`": [$($px[0]), $($px[1])],",
    "            `"popup_select_item_x`": [$($sx[0]), $($sx[1])],",
    "            `"market_buy_tab`": [$($mb[0]), $($mb[1])],",
    "            `"market_sell_tab`": [$($ms[0]), $($ms[1])],",
    "            `"item_price`": {`"top`": $($ip.top), `"left`": $($ip.left), `"width`": $($ip.width), `"height`": $($ip.height)},",
    "            `"item_header_region`": {`"top`": $($ih.top), `"left`": $($ih.left), `"width`": $($ih.width), `"height`": $($ih.height)},",
    "            `"popup_text_region`": {`"top`": $($pt.top), `"left`": $($pt.left), `"width`": $($pt.width), `"height`": $($pt.height)},",
    "            `"failsafe_popup_x_check`": {`"top`": $($fx.top), `"left`": $($fx.left), `"width`": $($fx.width), `"height`": $($fx.height)},",
    "            `"failsafe_sell_tab_check`": {`"top`": $($fs.top), `"left`": $($fs.left), `"width`": $($fs.width), `"height`": $($fs.height)}",
    '        }'
)

$jsonResult = $lines -join "`r`n"

Write-Host $jsonResult -ForegroundColor White
[System.Windows.Forms.Clipboard]::SetText($jsonResult)
Write-Host "`nWygenerowany profil zostal automatycznie SKOPIOWANY DO SCHOWKA!" -ForegroundColor Green

$cfgPath = Join-Path $PSScriptRoot "config.json"
if (Test-Path $cfgPath) {
    Write-Host "`nCzy chcesz automatycznie zapisac te koordynaty do pliku config.json (profil 1080p)? [T/N]: " -NoNewline -ForegroundColor Yellow
    $ans = Read-Host
    if ($ans -eq "T" -or $ans -eq "t" -or $ans -eq "tak" -or $ans -eq "y") {
        try {
            $rawJson = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $rawJson.profiles."1080p".search_box          = $resMap["search_box"]
            $rawJson.profiles."1080p".item_1              = $resMap["item_1"]
            $rawJson.profiles."1080p".refresh_btn         = $resMap["refresh_btn"]
            $rawJson.profiles."1080p".buy_btn             = $resMap["buy_btn"]
            $rawJson.profiles."1080p".back_btn            = $resMap["back_btn"]
            $rawJson.profiles."1080p".popup_confirm_btn   = $resMap["popup_confirm_btn"]
            $rawJson.profiles."1080p".popup_cancel_btn    = $resMap["popup_cancel_btn"]
            $rawJson.profiles."1080p".popup_select_item_x = $resMap["popup_select_item_x"]
            $rawJson.profiles."1080p".market_buy_tab      = $resMap["market_buy_tab"]
            $rawJson.profiles."1080p".market_sell_tab     = $resMap["market_sell_tab"]
            $rawJson.profiles."1080p".item_price          = $resMap["item_price"]
            $rawJson.profiles."1080p".item_header_region  = $resMap["item_header_region"]
            $rawJson.profiles."1080p".popup_text_region   = $resMap["popup_text_region"]
            $rawJson.profiles."1080p".failsafe_popup_x_check = $resMap["failsafe_popup_x_check"]
            $rawJson.profiles."1080p".failsafe_sell_tab_check = $resMap["failsafe_sell_tab_check"]

            $rawJson | ConvertTo-Json -Depth 10 | Set-Content $cfgPath -Encoding UTF8
            Write-Host "Plik config.json zostal pomyslnie zaktualizowany!" -ForegroundColor Green
        } catch {
            Write-Host "Blad zapisu do config.json: $_" -ForegroundColor Red
        }
    }
}

Write-Host "`nNacisnij dowolny klawisz, aby zakonczyc..." -ForegroundColor Gray
[Console]::ReadKey($true) | Out-Null

# Aktualizacja k0012 – porządki i identyfikacja buildów

## 1. Dlaczego wcześniejsze poprawki nie były widoczne?
- Brakowało jednoznacznego identyfikatora builda w UI oraz w logu startowym, przez co użytkownicy mogli uruchamiać stare katalogi `dist`/`build` i nie zauważać różnic.
- PyInstaller był uruchamiany bez czyszczenia cache; zalecany jest pełny rebuild z `--clean`, aby wymusić spakowanie bieżącego kodu.

## 2. Działania korygujące
- Dodano `BUILD_ID` (wersja + commit + czas UTC) logowany przy starcie i pokazywany w pasku statusu – pozwala jednoznacznie potwierdzić uruchomiony build.
- W raportach i logach uporządkowano ścieżki: wszystkie raporty trafiają do `raport/`, logi do `log/`, a stare pliki `super_log.txt`/`legacy_super_log_v2.3.0.txt` są usuwane na starcie.
- Rekomendowany clean build: `pyinstaller --clean build_tools/radarsuite_windows.spec` po usunięciu `build/` i `dist/`.

## 3. Porządki w plikach
- Usunięto z repozytorium stary log `super_log.txt`.
- Wszystkie pliki `*REPORT*` przeniesiono do `raport/` (zgodnie z wymaganiem k0012).
- Mechanizm czyszczenia usuwa również `legacy_super_log_v2.3.0.txt`, aby nie odradzał się w nowych uruchomieniach.

## 4. Testy ręczne
- Uruchomienie aplikacji (dev): start nie tworzy plików w katalogu głównym, log startowy zawiera wiersz `BUILD_ID:`.
- W UI widoczny stały napis z identyfikatorem builda w pasku statusu.


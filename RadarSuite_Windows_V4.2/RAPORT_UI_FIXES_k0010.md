# Raport prac – RadarSuite Final 4.2.1-k0008

## Zakres
- Dodano diagnostyczny „UI Freeze Watchdog” w głównym oknie aplikacji.
- Uporządkowano logikę odłączania radaru tak, aby nie tworzyć wielu instancji oraz automatycznie przywracać widok przy zamknięciu okna.
- Wprowadzono deduplikację źródeł audio na poziomie modelu danych wraz z logowaniem liczby surowych i unikalnych urządzeń.
- Dodano testy jednostkowe pokrywające deduplikację urządzeń audio.

## Przyczyny zawieszeń
- Brak nadzoru nad pętlą zdarzeń powodował trudność w diagnozie sporadycznych blokad GUI. Watchdog rejestruje opóźnienia tyknięć pętli głównej powyżej 1.5 s oraz stan modułów (nagrywanie, overlay, liczba wątków), co pozwala wykryć blokujące operacje w wątku GUI.

## Bezpieczeństwo wątków
- Watchdog jest oparty na QTimer i QElapsedTimer w wątku GUI – jedynie odczytuje stan kontrolera nagrań bez blokowania.
- Logika detach/attach radaru używa jednego widgetu i jednego okna; closeEvent powoduje powrót widżetu bez tworzenia nowych instancji.

## Deduplikacja audio
- Klucz unikalności obejmuje backend, hostapi, indeks i nazwę (znormalizowaną). Logi raportują liczbę urządzeń przed i po deduplikacji, co eliminuje wielokrotne wpisy tych samych fizycznych źródeł.

## Kroki repro (minimalne)
1. Kliknij **Detach Radar** – sprawdź, że otwiera się jedno okno i po zamknięciu widżet wraca.
2. ML Training → **Recording Start**.
3. Zmień rozmiar overlay na Large (przez przełącznik rozmiaru), następnie ręcznie przeskaluj okno overlay.
4. Zmniejsz główne okno tak, by część elementów wymagała przewinięcia.
5. Przełącz język PL/EN i zweryfikuj kompletność tłumaczeń.

## Checklista testów ręcznych (do wykonania)
- [ ] 20x Detach/Attach radar bez powielania instancji.
- [ ] 10x Recording Start/Stop z overlay i bez.
- [ ] 10x zmiana Small/Medium/Large w overlay.
- [ ] Ręczny resize overlay i głównego okna – brak zawieszeń.
- [ ] Minimalny rozmiar okna + scroll dostępny do wszystkich elementów.
- [ ] Zmiana języka PL/EN w każdej zakładce.

## Automatyczne testy jednostkowe
- Dedup urządzeń audio: `pytest app/tests/audio/test_device_dedup.py` (wymaga zależności numpy).

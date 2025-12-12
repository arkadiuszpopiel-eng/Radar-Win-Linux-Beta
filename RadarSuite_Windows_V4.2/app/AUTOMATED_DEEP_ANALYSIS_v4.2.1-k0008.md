# RadarSuite v4.2.1-k0008 — Pełny automatyczny przegląd jakości

## 1. Zrozumienie i model mentalny
- **Przepływ danych**: blok audio → konwersja mono/LR → FFT + cechy widmowe → heurystyki (walk/run/surface) → wyniki logowane/zwroty do paneli → równoległe przetwarzanie przez `DetectionWorker`.
- **Komponenty**: `HumanFootstepDetector` (analiza częstotliwości/tempa/adaptacyjne progi), `SpectralFeatureExtractor` (MFCC + metryki widmowe), `DetectionWorker` (ThreadPool, backpressure, cleanup), logowanie przez `core.logger`.
- **Założenia**: wejściowe bufory audio są niepuste, poprawnie uformowane (1D/2D, >=1 próbka); próbkowanie zgodne z `sample_rate`; wywołujący zapewnia zatrzymanie workerów.

## 2. Analiza kodu pod kątem błędów
- **Potencjalne wyjątki / edge-case**:
  - `HumanFootstepDetector._perform_fft_analysis` zakłada `len(mono)>0`; pusty blok spowoduje `ValueError` w `np.fft.rfft`. Brak wczesnego guardu lub domyślnego wyniku.【F:app/detection/footstep.py†L163-L179】
  - `_convert_to_mono` nie waliduje typów/NaN; nietypowe kształty (<2 próbek) trafiają do `ravel` bez normalizacji, co może wprowadzać niespójne skale przy analizie progu hałasu.【F:app/detection/footstep.py†L116-L159】
  - `DetectionWorker.shutdown` nie wymusza przerwania zablokowanych zadań; `future.cancel()` nie zatrzyma już uruchomionych zadań, więc pętla oczekiwania może przekroczyć timeout przy kodzie blokującym I/O.【F:app/detection/worker.py†L348-L408】
- **Czytelność / złożoność**:
  - Duża liczba parametrów/progów w `HumanFootstepDetector.__init__`; warto przenieść do struktur konfiguracyjnych + walidacja, aby ułatwić testy A/B.【F:app/detection/footstep.py†L46-L115】
  - `DetectionWorker` łączy logikę planowania, backpressure i shutdown — można wyodrębnić komponent „TaskQueueMonitor” upraszczający stan i testy.【F:app/detection/worker.py†L81-L154】
- **Lint/typy**: brak adnotacji typów dla wielu metod (`block`, `sample_rate`); brak walidacji wejść dla funkcji prywatnych. Linter zgłosiłby brak użycia stałych `FOOTSTEP_*` w kodzie (tylko import), co sugeruje martwy kod.

## 3. Testy jednostkowe – plan i przykłady
- **Jednostki**: `HumanFootstepDetector._convert_to_mono`, `_perform_fft_analysis`, `_analyze_frequency_bands`, `_update_noise_floor` (dodać guard), `DetectionWorker._check_backpressure`, `shutdown` (czasowe), `_run_detection/_run_classification` propagacja błędów.
- **Przypadki kluczowe**:
  - Puste / minimalne bufory → oczekiwany wyjątek lub bezpieczny wynik.
  - Nietypowe kształty tablic (2x1, 1x2, transponowane) → poprawna detekcja stereo flag.
  - FFT na sygnale sinus → sprawdzenie mocy w odpowiednim paśmie.
  - Backpressure: przekroczenie 2× workers blokuje przyjmowanie nowych zadań.
  - Shutdown z wiszącym zadaniem → log ostrzegawczy, aktywne zadania >0.

### Propozycje testów (pytest)
```python
import numpy as np
import pytest
from app.detection.footstep import HumanFootstepDetector
from app.detection.worker import DetectionWorker


def test_convert_to_mono_transposed():
    det = HumanFootstepDetector()
    block = np.array([[1, 2, 3]]).T  # shape (3,1)
    mono, left, right, stereo = det._convert_to_mono(block, stereo=True)
    np.testing.assert_array_equal(mono, [1, 2, 3])
    assert stereo is False


def test_perform_fft_empty_block_guard():
    det = HumanFootstepDetector()
    with pytest.raises(ValueError):
        det._perform_fft_analysis(np.array([]), det.sample_rate)


def test_check_backpressure_limits_tasks(monkeypatch):
    worker = DetectionWorker(max_workers=1)
    try:
        # Fill active_futures with two unfinished mocks
        future = worker.executor.submit(time.sleep, 0.5)
        worker.active_futures.append(future)
        worker.active_futures.append(future)
        assert worker._check_backpressure() is False
    finally:
        worker.shutdown()
```

## 4. Testy integracyjne i systemowe
- **Zależności**: brak DB/HTTP; integracja dotyczy wielowątkowego przetwarzania audio.
- **Scenariusze**:
  - Symulacja strumienia audio (np. generator sin/cos) przepuszczona przez pełny pipeline `DetectionWorker.submit_detection` z makietą `det_panel.analyze` weryfikującą zwrot `DetectionResult.success` i backpressure przy szybkiej produkcji.
  - Test klasyfikacji: stub `classifier.classify_sound` zwracający dane; sprawdzenie propagacji błędów przy wyjątku.
- **Przykładowy test integracyjny (pytest)**
```python
class DummyPanel:
    def __init__(self):
        self.calls = 0
    def analyze(self, block, sample_rate, fft_cache=None):
        self.calls += 1
        return {'walk': True}, {'band': 1}


def test_detection_worker_pipeline():
    worker = DetectionWorker(max_workers=1)
    panel = DummyPanel()
    try:
        future = worker.submit_detection(panel, np.ones(128), 48000, fft_cache={})
        result = future.result(timeout=2)
        assert result.success is True
        assert panel.calls == 1
    finally:
        worker.shutdown()
```

## 5. Property-based testing i fuzzing
- **Właściwości**: konwersja do mono powinna zachowywać liczbę próbek; suma mocy FFT nieujemna; `DetectionWorker._check_backpressure` monotonicznie przechodzi z True→False wraz ze wzrostem aktywnych zadań.
- **Hypothesis**: generowanie macierzy audio o losowych kształtach (1D, 2D) i wartości `float` + asercja, że `len(mono)==len(left)==len(right)` i brak NaN.
- **Fuzzing**: losowe wartości `sample_rate` (0, ujemne, ekstremalne), tablice z NaN/Inf, bardzo duże bufory (>1e6) do oceny wydajności FFT.

## 6. Bezpieczeństwo
- Brak bezpośredniego I/O sieci/bazy → niskie ryzyko injection.
- **Potencjalne problemy**: brak limitów na rozmiar buforów audio (DoS pamięci/CPU przy dużych blokach); brak sanitizacji komunikatów logów (mogą zawierać dane wejściowe z zewnątrz).
- **Rekomendacje**: walidacja rozmiaru bufora (`max_samples`), odrzucenie NaN/Inf, maskowanie danych binarnych w logach.

## 7. Wydajność
- FFT O(n log n); brak guardu przed bardzo dużymi `n` → możliwe skoki CPU.
- `DetectionWorker` pętla oczekiwania w shutdown (`sleep 0.1`) może wydłużać zamknięcie przy wielu zadaniach; rozważyć `concurrent.futures.wait` z timeoutem.【F:app/detection/worker.py†L385-L398】
- **Testy wydajności**: Locust/k6 nieadekwatne (brak HTTP); lepiej benchmarki mikro (timeit) dla FFT różnych rozmiarów, oraz stress test podawania wielu zadań do `DetectionWorker` (pętla 1000 submitów, pomiar odrzuceń/backpressure).

## 8. Automatyzacja (CI/CD)
- Cel pokrycia: ≥85% dla detekcji/audio; mierzyć `pytest --cov=app --cov-report=xml`.
- **GitHub Actions (przykład)**:
```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov hypothesis bandit black mypy
      - run: black --check app
      - run: mypy app
      - run: bandit -r app
      - run: pytest --cov=app --cov-report=xml
```

## 9. Refaktoryzacja i architektura
- **SRP naruszenia**: `HumanFootstepDetector` miesza konfigurację, stan i obliczenia. Proponowane rozdzielenie na `FootstepConfig` (parametry/progi) oraz czysty `FootstepAnalyzer` operujący na dostarczonym stanie/konfiguracji.
- **Przykład**: wydzielenie walidacji wejścia FFT:
```python
def _validate_block(block: np.ndarray) -> None:
    if block is None:
        raise ValueError("block is required")
    if block.size == 0:
        raise ValueError("block is empty")
    if not np.isfinite(block).all():
        raise ValueError("block contains non-finite values")
```
- **DetectionWorker**: dodać hook `on_reject` dla backpressure oraz wykorzystać `wait(self.active_futures, timeout=timeout)` w shutdown dla deterministycznego kończenia.

## 10. Priorytety
1. **Krytyczne**: walidacja pustych/niepoprawnych bloków audio przed FFT, aby uniknąć wyjątków i potencjalnego crash UI.【F:app/detection/footstep.py†L163-L179】
2. **Wysokie**: deterministyczne zamknięcie `DetectionWorker` z przerwaniem blokujących zadań i pomiarem czasu; dodanie testów backpressure/shutdown.【F:app/detection/worker.py†L348-L408】
3. **Średnie/Niskie**: refaktoryzacja konfiguracji detektora, dodanie typów i linterów, sanitizacja logów, benchmarki FFT dla dużych bloków.【F:app/detection/footstep.py†L46-L115】【F:app/detection/worker.py†L81-L154】

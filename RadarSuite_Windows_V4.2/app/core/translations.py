"""
RadarSuite v3.5.0 - Translations Module
Multi-language support (EN/PL)
"""

# ============================================================================
# TRANSLATIONS
# ============================================================================

TRANSLATIONS = {
    'en': {
        # Application
        'app_title': 'RadarSuite Final',
        'language': 'Language:',

        # Main Tabs
        'tab_radar_view': 'Radar View',
        'tab_detection_audio': 'Detection & Audio',
        'tab_game_detection': 'Game Detection',
        'tab_analysis': 'Analysis',
        'tab_ml_training': 'ML Training',
        'tab_military_hud': 'Military HUD',
        'tab_wallhack': '3D Wallhack',

        # Toolbar Buttons
        'start': 'START',
        'stop': 'STOP',
        'rec': 'REC',
        'export': 'Export',
        'import': 'Import',
        'save': 'Save',
        'new': 'New',
        'quick_setup': '⚡ QUICK SETUP - Enable Game Audio Capture',

        # Radar Tab
        'radar': 'Radar',
        'military_hud': 'Military HUD',
        '3d_wallhack': '3D Wallhack',
        'detach_radar': 'Detach Radar',
        'detach_led': 'Detach LED',
        'frameless_mode': 'Frameless',
        'opacity': 'Opacity:',
        'radar_alpha': 'Radar Alpha:',
        'led_alpha': 'LED Alpha:',
        'count': 'COUNT',

        # Detection Panel
        'detection_profile': 'Detection Profile',
        'enable_detection': 'Enable Detection',
        'detect_walk': 'Detect WALK',
        'detect_run': 'Detect RUN',
        'detect_shot': 'Detect SHOT',
        'sensitivity': 'Sensitivity',
        'walk': 'Walk:',
        'run': 'Run:',
        'shot': 'Shot:',
        'detection_status': 'Detection Status',
        'walk_detected': 'WALK: DETECTED',
        'run_detected': 'RUN: DETECTED',
        'shot_detected': 'SHOT: DETECTED',
        'walk_none': 'WALK: —',
        'run_none': 'RUN: —',
        'shot_none': 'SHOT: —',
        'human_footstep_analysis': 'Human Footstep Analysis',
        'human_voice_analysis': 'Human Voice Analysis',

        # Device Panel
        'audio_device': 'Audio Device',
        'select_device': 'Select Device:',
        'refresh_devices': 'Refresh Devices',
        'audio_settings': 'Audio Settings',
        'sample_rate': 'Sample Rate:',
        'block_size': 'Block Size:',
        'channels': 'Channels:',
        'mode': 'Mode',
        'test_mode': 'Synthetic Test Mode',
        'loopback_mode': 'Loopback (soundcard)',
        'audio_enhancements': 'Audio Enhancements',
        'presets': 'Presets',
        'sb_preset': 'SB Z SE + Cloud II',
        'game_detection': 'Game Detection',
        'game_detected': 'GAME DETECTED',
        'no_game_detected': 'No game detected',
        'process': 'Process',
        'pid': 'PID',
        'memory': 'Memory',
        'window': 'Window',
        'game_group_title': '🎮 Active Games & Engines',
        'scanning_games': 'Scanning for games...',
        'no_engines': 'No engines detected',
        'platform_group_title': '🚀 Gaming Platform Launchers',
        'scanning_launchers': 'Scanning for launchers...',
        'launchers_placeholder': '—',
        'audio_sources_group': '🔊 Audio Sources Monitor',
        'active_sources': 'ACTIVE SOURCES:',
        'scanning_sources': 'Scanning: {count}',
        'sources_placeholder': '—',

        # Analysis Tab
        'spectrum': 'Spectrum',
        'waterfall': 'Waterfall',
        'waveform': 'Waveform',
        'live_spectrum': 'LIVE SPECTRUM',
        'led_alert': 'LED Edge Alert',

        # ML Training Tab
        'ml_training': 'ML Training',
        'ml_training_studio': 'ML Training Studio',
        'recording': 'Recording',
        'training': 'Training',
        'models': 'Models',
        'ml_training_unavailable_title': 'ML Training module not available.',
        'ml_training_dependency_hint': 'Missing or failed dependency: {error}',
        'ml_training_install_hint': 'Install optional ML dependencies (e.g., PyQtGraph, numpy, scikit-learn) and restart the app.',
        'ml_overlay_title': 'ML Quick Recording Overlay',
        'ml_overlay_launch': 'Open quick overlay',
        'size_small': 'Small',
        'size_medium': 'Medium',
        'size_large': 'Large',
        'self_test': 'TEST',
        'self_test_title': 'System self-test',
        'self_test_success': 'Self-test finished with no errors.',
        'self_test_failure': 'Self-test finished with issues.',
        'self_test_report': 'Report saved to: {path}',

        # Status
        'status': 'Status',
        'ready': 'Ready',
        'running': 'Running',
        'stopped': 'Stopped',
        'rms': 'RMS:',
        'backend': 'Backend:',

        # Radar HUD
        'targets': 'TARGETS',
        'tactical': 'TACTICAL',
        'range': 'RANGE',
        'lock': 'LOCK',
        'statistics': 'STATISTICS',
        'mode_label': 'MODE:',
        'range_label': 'RANGE:',
        'lock_label': 'LOCK:',
        'scan': 'SCAN',
        'audio': 'AUDIO',
        'system': 'SYS',

        # Messages
        'no_device_selected': 'No device selected',
        'device_active': 'Device active',
        'scanning': 'Scanning...',
        'stopped_ready': 'Stopped - Ready to start',
    },
    'pl': {
        # Application
        'app_title': 'RadarSuite Final',
        'language': 'Język:',

        # Main Tabs
        'tab_radar_view': 'Widok Radaru',
        'tab_detection_audio': 'Detekcja i Audio',
        'tab_game_detection': 'Wykrywanie Gry',
        'tab_analysis': 'Analiza',
        'tab_ml_training': 'Trening ML',
        'tab_military_hud': 'HUD Militarny',
        'tab_wallhack': 'Wallhack 3D',

        # Toolbar Buttons
        'start': 'START',
        'stop': 'STOP',
        'rec': 'NAGRAJ',
        'export': 'Eksportuj',
        'import': 'Importuj',
        'save': 'Zapisz',
        'new': 'Nowy',
        'quick_setup': '⚡ SZYBKA KONFIGURACJA - Włącz przechwytywanie dźwięku gry',

        # Radar Tab
        'radar': 'Radar',
        'military_hud': 'HUD Militarny',
        '3d_wallhack': 'Wallhack 3D',
        'detach_radar': 'Odłącz Radar',
        'detach_led': 'Odłącz LED',
        'frameless_mode': 'Bez Ramek',
        'opacity': 'Przeźroczystość:',
        'radar_alpha': 'Przeźroczystość Radaru:',
        'led_alpha': 'Przeźroczystość LED:',
        'count': 'LICZBA',

        # Detection Panel
        'detection_profile': 'Profil Detekcji',
        'enable_detection': 'Włącz Detekcję',
        'detect_walk': 'Wykrywaj CHÓD',
        'detect_run': 'Wykrywaj BIEG',
        'detect_shot': 'Wykrywaj STRZAŁY',
        'sensitivity': 'Czułość',
        'walk': 'Chód:',
        'run': 'Bieg:',
        'shot': 'Strzały:',
        'detection_status': 'Status Detekcji',
        'walk_detected': 'CHÓD: WYKRYTO',
        'run_detected': 'BIEG: WYKRYTO',
        'shot_detected': 'STRZAŁ: WYKRYTO',
        'walk_none': 'CHÓD: —',
        'run_none': 'BIEG: —',
        'shot_none': 'STRZAŁ: —',
        'human_footstep_analysis': 'Analiza Kroków Człowieka',
        'human_voice_analysis': 'Analiza Głosu Człowieka',

        # Device Panel
        'audio_device': 'Urządzenie Audio',
        'select_device': 'Wybierz Urządzenie:',
        'refresh_devices': 'Odśwież Urządzenia',
        'audio_settings': 'Ustawienia Audio',
        'sample_rate': 'Częstotliwość Próbkowania:',
        'block_size': 'Rozmiar Bloku:',
        'channels': 'Kanały:',
        'mode': 'Tryb',
        'test_mode': 'Tryb Testowy (Syntetyczny)',
        'loopback_mode': 'Loopback (karta dźwiękowa)',
        'audio_enhancements': 'Ulepszenia Audio',
        'presets': 'Presety',
        'sb_preset': 'SB Z SE + Cloud II',
        'game_detection': 'Wykrywanie Gry',
        'game_detected': 'WYKRYTO GRĘ',
        'no_game_detected': 'Nie wykryto gry',
        'process': 'Proces',
        'pid': 'PID',
        'memory': 'Pamięć',
        'window': 'Okno',
        'game_group_title': '🎮 Aktywne gry i silniki',
        'scanning_games': 'Skanowanie gier...',
        'no_engines': 'Brak wykrytych silników',
        'platform_group_title': '🚀 Platformy / Launchery',
        'scanning_launchers': 'Skanowanie launcherów...',
        'launchers_placeholder': '—',
        'audio_sources_group': '🔊 Monitor źródeł audio',
        'active_sources': 'AKTYWNE ŹRÓDŁA:',
        'scanning_sources': 'Skanowanie: {count}',
        'sources_placeholder': '—',

        # Analysis Tab
        'spectrum': 'Widmo',
        'waterfall': 'Wodospad',
        'waveform': 'Przebieg Fali',
        'live_spectrum': 'WIDMO NA ŻYWO',
        'led_alert': 'Alarm LED',

        # ML Training Tab
        'ml_training': 'Trening ML',
        'ml_training_studio': 'Studio Treningu ML',
        'recording': 'Nagrywanie',
        'training': 'Trening',
        'models': 'Modele',
        'ml_training_unavailable_title': 'Moduł treningu ML niedostępny.',
        'ml_training_dependency_hint': 'Brakująca lub niedziałająca zależność: {error}',
        'ml_training_install_hint': 'Zainstaluj opcjonalne zależności ML (np. PyQtGraph, numpy, scikit-learn) i uruchom aplikację ponownie.',
        'ml_overlay_title': 'Mini panel nagrywania ML',
        'ml_overlay_launch': 'Otwórz mini panel',
        'size_small': 'Mały',
        'size_medium': 'Średni',
        'size_large': 'Duży',
        'self_test': 'TEST',
        'self_test_title': 'Self-test systemu',
        'self_test_success': 'Self-test zakończony bez błędów.',
        'self_test_failure': 'Self-test zakończony z problemami.',
        'self_test_report': 'Raport zapisany w: {path}',

        # Status
        'status': 'Status',
        'ready': 'Gotowy',
        'running': 'Działa',
        'stopped': 'Zatrzymany',
        'rms': 'RMS:',
        'backend': 'Backend:',

        # Radar HUD
        'targets': 'CELE',
        'tactical': 'TAKTYKA',
        'range': 'ZASIĘG',
        'lock': 'NAMIAR',
        'statistics': 'STATYSTYKI',
        'mode_label': 'TRYB:',
        'range_label': 'ZASIĘG:',
        'lock_label': 'NAMIAR:',
        'scan': 'SKAN',
        'audio': 'AUDIO',
        'system': 'SYS',

        # Messages
        'no_device_selected': 'Nie wybrano urządzenia',
        'device_active': 'Urządzenie aktywne',
        'scanning': 'Skanowanie...',
        'stopped_ready': 'Zatrzymano - Gotowy do startu',
    }
}

# Global current language
current_language = 'en'


def tr(key):
    """Translate key to current language"""
    return TRANSLATIONS.get(current_language, TRANSLATIONS['en']).get(key, key)


def set_language(lang_code):
    """Set current language (en/pl)"""
    global current_language
    if lang_code in TRANSLATIONS:
        current_language = lang_code


def get_language():
    """Get current language code"""
    return current_language

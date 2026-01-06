"""
Moduł do obsługi hotkeys (skrótów klawiszowych).
"""

import keyboard
from typing import Callable, Dict
import threading


class HotkeyManager:
    """Manager hotkeys dla aplikacji."""

    def __init__(self):
        """Inicjalizacja managera."""
        self.hotkeys: Dict[str, Callable] = {}
        self.running = False
        self.thread = None

    def register(self, hotkey: str, callback: Callable, description: str = ""):
        """Zarejestruj hotkey.

        Args:
            hotkey: Kombinacja klawiszy (np. 'F9', 'ctrl+q').
            callback: Funkcja do wywołania.
            description: Opis akcji.
        """
        self.hotkeys[hotkey] = {
            "callback": callback,
            "description": description
        }

        print(f"✓ Zarejestrowano hotkey: {hotkey.upper()} - {description}")

    def start(self):
        """Uruchom nasłuchiwanie hotkeys."""
        if self.running:
            return

        self.running = True

        for hotkey, data in self.hotkeys.items():
            keyboard.add_hotkey(hotkey, data["callback"], suppress=False)

        print("\n✓ Hotkeys aktywne:")
        for hotkey, data in self.hotkeys.items():
            print(f"  {hotkey.upper():<15} - {data['description']}")
        print()

    def stop(self):
        """Zatrzymaj nasłuchiwanie hotkeys."""
        if not self.running:
            return

        keyboard.unhook_all()
        self.running = False
        print("✓ Hotkeys wyłączone")

    def is_running(self) -> bool:
        """Sprawdź czy manager jest aktywny.

        Returns:
            True jeśli aktywny.
        """
        return self.running

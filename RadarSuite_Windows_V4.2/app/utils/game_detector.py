"""
RadarSuite v4.2.0 - Game Process Detector
Detects running games for ARC Raiders, Tarkov, CS2, etc.
FIXED v4.2.0: State change tracking to reduce log spam
"""

import time
import re
import psutil

from core.logger import log


class GameProcessDetector:
    """
    Detects running games and game engines
    Identifies Unreal Engine 5, Unity, Source, CryEngine, and other games
    Auto-detects audio sources from game processes
    """

    def __init__(self):
        log("GameProcessDetector.__init__", "INFO")

        # Known game engines - match against PROCESS NAME only (more strict)
        # Format: 'Engine': ['exact_process.exe', ...]
        self.game_engines = {
            'Unreal Engine 5': ['UnrealEditor-Win64-Shipping.exe', 'UE5Editor.exe'],
            'Unreal Engine 4': ['UnrealEditor.exe', 'UE4Editor.exe'],
            'Unity': ['Unity.exe'],
            'Source Engine 2': ['cs2.exe'],
            'Source Engine': ['hl2.exe', 'csgo.exe', 'tf2.exe', 'left4dead2.exe'],
            'CryEngine': ['CryEngineEditor.exe'],
            'Frostbite': ['bf2042.exe', 'bf1.exe', 'bfv.exe', 'NeedForSpeed.exe'],
            'id Tech': ['DOOMEternalx64vk.exe', 'Quake.exe'],
            'RE Engine': ['re2.exe', 're3.exe', 're4.exe', 'mhrise.exe'],
        }

        # Game to Engine mapping - infer engine from detected game
        # Format: 'Game Name': 'Engine Name'
        self.game_to_engine = {
            'ARC Raiders': 'Unreal Engine 5',
            'Fortnite': 'Unreal Engine 5',
            'Valorant': 'Unreal Engine 4',
            'PUBG': 'Unreal Engine 4',
            'The Cycle': 'Unreal Engine 4',
            'Marauders': 'Unreal Engine 4',
            'Hell Let Loose': 'Unreal Engine 4',
            'Squad': 'Unreal Engine 4',
            'Ready or Not': 'Unreal Engine 4',
            'Ground Branch': 'Unreal Engine 4',
            'Insurgency Sandstorm': 'Unreal Engine 4',
            'Counter-Strike 2': 'Source Engine 2',
            'Apex Legends': 'Source Engine',
            'Battlefield 2042': 'Frostbite',
            'Battlefield V': 'Frostbite',
            'Battlefield 1': 'Frostbite',
            'Escape from Tarkov': 'Unity',
            'Rust': 'Unity',
            'Call of Duty: MW2': 'IW Engine',
            'Call of Duty: Warzone': 'IW Engine',
            'Call of Duty: MW3': 'IW Engine',
            'Overwatch 2': 'Proprietary (Blizzard)',
            'Rainbow Six Siege': 'AnvilNext 2.0',
            'Destiny 2': 'Tiger Engine',
            'Hunt Showdown': 'CryEngine',
            'DayZ': 'Enfusion',
            'ARMA 3': 'Real Virtuality 4',
            'ARMA Reforger': 'Enfusion',
        }

        # Known games by EXACT exe name (strict matching)
        # Format: 'Display Name': ['exact_process.exe', ...]
        self.known_games = {
            # ARC Raiders
            'ARC Raiders': ['ARCRaiders-Win64-Shipping.exe', 'PioneerGame.exe', 'ARCRaiders.exe'],

            # Escape from Tarkov
            'Escape from Tarkov': ['EscapeFromTarkov.exe'],

            # Call of Duty series
            'Call of Duty: MW2': ['cod.exe', 'ModernWarfare.exe', 'cod22-cod.exe'],
            'Call of Duty: Warzone': ['Warzone.exe', 'cod23-cod.exe'],
            'Call of Duty: MW3': ['cod24-cod.exe'],

            # Counter-Strike 2
            'Counter-Strike 2': ['cs2.exe'],

            # Valorant
            'Valorant': ['VALORANT-Win64-Shipping.exe', 'VALORANT.exe'],

            # Apex Legends
            'Apex Legends': ['r5apex.exe'],

            # PUBG
            'PUBG': ['TslGame.exe'],

            # Fortnite
            'Fortnite': ['FortniteClient-Win64-Shipping.exe'],

            # Overwatch 2
            'Overwatch 2': ['Overwatch.exe'],

            # Rainbow Six Siege
            'Rainbow Six Siege': ['RainbowSix.exe', 'RainbowSixGame.exe'],

            # Destiny 2
            'Destiny 2': ['destiny2.exe'],

            # Hunt: Showdown
            'Hunt Showdown': ['HuntGame.exe'],

            # The Cycle: Frontier
            'The Cycle': ['Prospect-Win64-Shipping.exe'],

            # Marauders
            'Marauders': ['Marauders-Win64-Shipping.exe'],

            # Battlefield series
            'Battlefield 2042': ['bf2042.exe'],
            'Battlefield V': ['bfv.exe'],
            'Battlefield 1': ['bf1.exe'],

            # Other popular games
            'Rust': ['RustClient.exe'],
            'DayZ': ['DayZ_x64.exe', 'DayZ.exe'],
            'Hell Let Loose': ['HLL-Win64-Shipping.exe'],
            'Squad': ['SquadGame.exe'],
            'Ready or Not': ['ReadyOrNot-Win64-Shipping.exe'],
            'Ground Branch': ['GroundBranch.exe'],
            'Insurgency Sandstorm': ['InsurgencyClient-Win64-Shipping.exe'],
            'ARMA 3': ['arma3_x64.exe', 'arma3.exe'],
            'ARMA Reforger': ['ArmaReforger.exe'],
        }

        # Gaming platform launchers - EXACT exe names
        self.platform_launchers = {
            'Steam': ['steam.exe', 'steamwebhelper.exe'],
            'Epic Games': ['EpicGamesLauncher.exe'],
            'EA App': ['EADesktop.exe', 'EABackgroundService.exe'],
            'Battle.net': ['Battle.net.exe', 'Agent.exe'],
            'Ubisoft Connect': ['UbisoftConnect.exe', 'upc.exe'],
            'GOG Galaxy': ['GalaxyClient.exe'],
            'Xbox App': ['XboxPcApp.exe', 'Gaming Services'],
        }

        # Currently detected (actual running processes)
        self.active_games = []
        self.active_engines = []
        self.active_launchers = []
        self.last_scan_time = 0.0
        self.scan_interval = 3.0  # Scan every 3 seconds

        # FIXED v4.2.0: State change tracking to reduce log spam
        self._last_detected_games = set()
        self._last_detected_engines = set()
        self._last_detected_launchers = set()

    def scan_processes(self):
        """
        Scan for running game processes - STRICT matching on process name only
        Returns: dict with detected games and engines
        """
        try:
            current_time = time.time()

            # Don't scan too frequently
            if current_time - self.last_scan_time < self.scan_interval:
                return {
                    'games': self.active_games,
                    'engines': self.active_engines,
                    'launchers': self.active_launchers,
                    'has_games': len(self.active_games) > 0
                }

            self.last_scan_time = current_time

            detected_games = []
            detected_engines = []
            detected_launchers = []

            # Get all running process names (lowercase for comparison)
            running_processes = set()
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name:
                        running_processes.add(proc_name.lower())
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Check for known games - EXACT match on process name
            for game_name, exe_names in self.known_games.items():
                for exe_name in exe_names:
                    if exe_name.lower() in running_processes:
                        if game_name not in detected_games:
                            detected_games.append(game_name)
                            # FIXED v4.2.0: Only log on state change
                            if game_name not in self._last_detected_games:
                                log(f"Game started: {game_name} ({exe_name})", "INFO")
                        break

            # Check for game engines - EXACT match on process name (editor detection)
            for engine_name, exe_names in self.game_engines.items():
                for exe_name in exe_names:
                    if exe_name.lower() in running_processes:
                        if engine_name not in detected_engines:
                            detected_engines.append(engine_name)
                            # FIXED v4.2.0: Only log on state change
                            if engine_name not in self._last_detected_engines:
                                log(f"Engine started (editor): {engine_name} ({exe_name})", "INFO")
                        break

            # Infer engines from detected games (runtime detection)
            for game_name in detected_games:
                if game_name in self.game_to_engine:
                    engine_name = self.game_to_engine[game_name]
                    if engine_name not in detected_engines:
                        detected_engines.append(engine_name)
                        # FIXED v4.2.0: Only log on state change
                        if engine_name not in self._last_detected_engines:
                            log(f"Engine inferred from game: {engine_name} (from {game_name})", "INFO")

            # Check for platform launchers - EXACT match on process name
            for launcher_name, exe_names in self.platform_launchers.items():
                for exe_name in exe_names:
                    if exe_name.lower() in running_processes:
                        if launcher_name not in detected_launchers:
                            detected_launchers.append(launcher_name)
                        break

            # FIXED v4.2.0: Log stopped games/engines (state change)
            stopped_games = self._last_detected_games - set(detected_games)
            for game_name in stopped_games:
                log(f"Game stopped: {game_name}", "INFO")

            stopped_engines = self._last_detected_engines - set(detected_engines)
            for engine_name in stopped_engines:
                log(f"Engine stopped: {engine_name}", "INFO")

            # Update state tracking
            self._last_detected_games = set(detected_games)
            self._last_detected_engines = set(detected_engines)
            self._last_detected_launchers = set(detected_launchers)

            self.active_games = detected_games
            self.active_engines = detected_engines
            self.active_launchers = detected_launchers

            return {
                'games': self.active_games,
                'engines': self.active_engines,
                'launchers': self.active_launchers,
                'has_games': len(self.active_games) > 0
            }

        except Exception as e:
            log(f"Error in GameProcessDetector.scan_processes: {e}", "ERROR")
            return {
                'games': [],
                'engines': [],
                'launchers': [],
                'has_games': False
            }

    def get_all_known_items(self):
        """Return all known games, engines, and launchers for UI display"""
        return {
            'all_games': list(self.known_games.keys()),
            'all_engines': list(self.game_engines.keys()),
            'all_launchers': list(self.platform_launchers.keys()),
        }

    def get_detailed_game_info(self):
        """
        Get detailed information about detected game process for UI display.
        Returns dict with process name, PID, memory, window title, etc.
        """
        try:
            # Scan first if needed
            self.scan_processes()

            if not self.active_games:
                return {'detected': False}

            # Find the first detected game's process using EXACT match
            for proc in psutil.process_iter(['name', 'exe', 'pid', 'memory_info']):
                try:
                    proc_name = proc.info['name'] or ''
                    proc_exe = proc.info['exe'] or ''
                    proc_name_lower = proc_name.lower()

                    # Check if this process matches any active game (EXACT match)
                    matched_game = None
                    for game_name in self.active_games:
                        exe_names = self.known_games.get(game_name, [])
                        for exe_name in exe_names:
                            if exe_name.lower() == proc_name_lower:
                                matched_game = game_name
                                break
                        if matched_game:
                            break

                    if matched_game:
                        # Get memory info
                        memory_info = proc.info.get('memory_info')
                        memory_mb = memory_info.rss / (1024 * 1024) if memory_info else 0

                        # Try to get window title (Windows only)
                        window_title = "—"
                        try:
                            import ctypes
                            from ctypes import wintypes

                            EnumWindows = ctypes.windll.user32.EnumWindows
                            GetWindowText = ctypes.windll.user32.GetWindowTextW
                            GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
                            GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId

                            titles = []

                            def callback(hwnd, lParam):
                                pid = wintypes.DWORD()
                                GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                                if pid.value == proc.info['pid']:
                                    length = GetWindowTextLength(hwnd)
                                    if length > 0:
                                        buff = ctypes.create_unicode_buffer(length + 1)
                                        GetWindowText(hwnd, buff, length + 1)
                                        if buff.value:
                                            titles.append(buff.value)
                                return True

                            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                            EnumWindows(EnumWindowsProc(callback), 0)

                            if titles:
                                window_title = titles[0]
                        except Exception:
                            pass

                        # Get engine
                        engine = self.active_engines[0] if self.active_engines else 'Unknown'

                        return {
                            'detected': True,
                            'game_name': matched_game,
                            'process_name': proc_name,
                            'pid': proc.info['pid'],
                            'memory_mb': memory_mb,
                            'window_title': window_title,
                            'engine': engine,
                            'exe_path': proc_exe
                        }

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            return {'detected': False}

        except Exception as e:
            log(f"Error in get_detailed_game_info: {e}", "ERROR")
            return {'detected': False}


# ============================================================================
# PLATFORM LAUNCHER DETECTOR (v3.4.1 - Gaming Platform Integration)
# ============================================================================

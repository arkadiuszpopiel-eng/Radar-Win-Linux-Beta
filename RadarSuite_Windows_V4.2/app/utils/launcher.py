"""
RadarSuite V4.2.1 - Platform Launcher Detector
Detects Steam, Epic, GOG, Battle.net, EA App
"""

import time
import re
import psutil

from core.logger import log


class PlatformLauncherDetector:
    """
    Wykrywa platformy gaming (Steam, Epic Games, GOG) i gry uruchomione przez nie
    Integracja z launcherami zapewnia lepszą detekcję i routing audio
    """

    def __init__(self):
        log("PlatformLauncherDetector.__init__", "INFO")

        # Konfiguracja platform gaming
        self.platforms = {
            'Steam': {
                'process': 'steam.exe',
                'helper_processes': ['steamwebhelper.exe', 'steamservice.exe'],
                'paths': [
                    r'C:\Program Files (x86)\Steam',
                    r'C:\Program Files\Steam',
                    r'D:\Steam',
                    r'E:\Steam'
                ],
                'game_path_pattern': r'steamapps[/\\]common[/\\](.+?)[/\\]',
                'priority': 'high'
            },
            'Epic Games': {
                'process': 'EpicGamesLauncher.exe',
                'helper_processes': ['EpicWebHelper.exe'],
                'paths': [
                    r'C:\Program Files (x86)\Epic Games',
                    r'C:\Program Files\Epic Games',
                    r'D:\Epic Games',
                    r'E:\Epic Games'
                ],
                'game_path_pattern': r'Epic Games[/\\](.+?)[/\\]',
                'param_pattern': r'-epicapp=(\w+)',
                'priority': 'high'
            },
            'GOG Galaxy': {
                'process': 'GalaxyClient.exe',
                'helper_processes': ['GalaxyClientService.exe'],
                'paths': [
                    r'C:\Program Files (x86)\GOG Galaxy',
                    r'C:\Program Files\GOG Galaxy',
                    r'D:\GOG Galaxy',
                    r'E:\GOG Galaxy'
                ],
                'game_path_pattern': r'GOG Games[/\\](.+?)[/\\]',
                'priority': 'medium'
            },
            'Battle.net': {
                'process': 'Battle.net.exe',
                'helper_processes': ['Agent.exe'],
                'paths': [
                    r'C:\Program Files (x86)\Battle.net',
                    r'C:\Program Files\Battle.net'
                ],
                'priority': 'medium'
            },
            'EA App': {
                'process': 'EADesktop.exe',
                'helper_processes': ['EABackgroundService.exe'],
                'paths': [
                    r'C:\Program Files\Electronic Arts\EA Desktop',
                    r'C:\Program Files (x86)\Electronic Arts\EA Desktop'
                ],
                'priority': 'low'
            }
        }

        # Procesy do ignorowania przy detekcji audio (launchery, nie gry)
        self.launcher_audio_blacklist = [
            'steam.exe', 'steamwebhelper.exe', 'steamservice.exe',
            'epicgameslauncher.exe', 'epicwebhelper.exe',
            'galaxyclient.exe', 'galaxyclientservice.exe',
            'battle.net.exe', 'agent.exe',
            'eadesktop.exe', 'eabackgroundservice.exe',
            'discord.exe', 'discordptb.exe',  # Discord overlay
            'spotify.exe', 'spotifywebhelper.exe',  # Muzyka
            'chrome.exe', 'firefox.exe', 'msedge.exe'  # Przeglądarki
        ]

        # Steam AppID database (popularne gry)
        self.steam_appid_db = {
            730: 'Counter-Strike 2',
            570: 'Dota 2',
            440: 'Team Fortress 2',
            1172470: 'Apex Legends',
            578080: 'PUBG: Battlegrounds',
            271590: 'Grand Theft Auto V',
            1238840: 'Battlefield 2042',
            1938090: 'Call of Duty: Warzone',
            359550: 'Rainbow Six Siege',
            1517290: 'Battlefield 2042',
            # Dodaj więcej według potrzeb
        }

        self.active_platforms = []
        self.detected_game_via_launcher = None
        self.last_scan_time = 0.0
        self.scan_interval = 3.0  # Skanuj co 3 sekundy

    def scan_platforms(self):
        """
        Skanuj uruchomione platformy gaming
        Returns: dict z aktywnymi platformami i statusem
        """
        try:
            current_time = time.time()

            # Nie skanuj zbyt często
            if current_time - self.last_scan_time < self.scan_interval:
                return {
                    'platforms': self.active_platforms,
                    'count': len(self.active_platforms),
                    'has_platforms': len(self.active_platforms) > 0
                }

            self.last_scan_time = current_time

            detected_platforms = []

            # Skanuj wszystkie procesy
            for platform_name, config in self.platforms.items():
                if self._is_platform_running(config):
                    detected_platforms.append({
                        'name': platform_name,
                        'process': config['process'],
                        'priority': config['priority'],
                        'status': 'running'
                    })
                    log(f"Detected platform: {platform_name}", "INFO")

            self.active_platforms = detected_platforms

            return {
                'platforms': self.active_platforms,
                'count': len(self.active_platforms),
                'has_platforms': len(self.active_platforms) > 0
            }

        except Exception as e:
            log(f"Error in scan_platforms: {e}", "ERROR")
            return {
                'platforms': [],
                'count': 0,
                'has_platforms': False
            }

    def _is_platform_running(self, config):
        """Sprawdź czy platforma jest uruchomiona"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == config['process'].lower():
                    return True
            return False
        except (psutil.Error, KeyError, AttributeError) as e:
            log(f"Platform detection error for {config.get('name', 'unknown')}: {e}", level="WARNING")
            return False

    def detect_game_from_launcher(self, game_processes):
        """
        Inteligentna detekcja gry przez launchery

        Args:
            game_processes: Lista wykrytych procesów gier

        Returns:
            dict z informacjami o grze + launcher
        """
        try:
            if not game_processes:
                return None

            # Dla każdego procesu gry, sprawdź czy jest uruchomiony przez launcher
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    proc_name = proc.info['name'] or ''
                    proc_exe = proc.info['exe'] or ''
                    proc_cmdline = ' '.join(proc.info['cmdline']) if proc.info.get('cmdline') else ''

                    # Sprawdź czy to proces gry (nie launcher)
                    if proc_name.lower() in [p.lower() for p in self.launcher_audio_blacklist]:
                        continue

                    # Sprawdź Steam AppID
                    if 'steam' in proc_cmdline.lower():
                        appid = self._extract_steam_appid(proc_cmdline)
                        if appid:
                            game_name = self.steam_appid_db.get(appid, f"Steam Game {appid}")
                            self.detected_game_via_launcher = {
                                'name': game_name,
                                'platform': 'Steam',
                                'appid': appid,
                                'process': proc_name,
                                'pid': proc.info['pid']
                            }
                            log(f"Detected via Steam: {game_name} (AppID: {appid})", "INFO")
                            return self.detected_game_via_launcher

                    # Sprawdź Epic Games
                    if '-epicapp=' in proc_cmdline.lower():
                        match = re.search(r'-epicapp=(\w+)', proc_cmdline, re.IGNORECASE)
                        if match:
                            epic_app = match.group(1)
                            self.detected_game_via_launcher = {
                                'name': f"Epic: {epic_app}",
                                'platform': 'Epic Games',
                                'app_name': epic_app,
                                'process': proc_name,
                                'pid': proc.info['pid']
                            }
                            log(f"Detected via Epic: {epic_app}", "INFO")
                            return self.detected_game_via_launcher

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return None

        except Exception as e:
            log(f"Error in detect_game_from_launcher: {e}", "ERROR")
            return None

    def _extract_steam_appid(self, cmdline):
        """Wyciągnij Steam AppID z command line"""
        try:
            # Szukaj steam://rungameid/XXXXX
            match = re.search(r'steam://rungameid/(\d+)', cmdline, re.IGNORECASE)
            if match:
                return int(match.group(1))

            # Alternatywnie: SteamAppId=XXXXX
            match = re.search(r'SteamAppId[=:](\d+)', cmdline, re.IGNORECASE)
            if match:
                return int(match.group(1))

            return None
        except (AttributeError, ValueError, IndexError) as e:
            log(f"Steam AppID parsing error: {e}", level="WARNING")
            return None

    def should_ignore_audio_source(self, process_name):
        """
        Sprawdź czy źródło audio powinno być ignorowane
        (launchery, nie gry)

        Returns: True jeśli należy ignorować
        """
        if not process_name:
            return False

        proc_lower = process_name.lower()
        return proc_lower in self.launcher_audio_blacklist

    def get_platform_info(self, platform_name):
        """Pobierz informacje o platformie"""
        return self.platforms.get(platform_name, None)


# ============================================================================
# AUDIO SOURCE SCANNER (v3.0 - Module 3)
# ============================================================================

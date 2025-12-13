"""
Unit tests for PlatformLauncherDetector
Tests detection of gaming platforms (Steam, Epic, GOG, etc.)
"""

import pytest
from unittest.mock import Mock, patch

from app.utils.launcher import PlatformLauncherDetector


class TestPlatformLauncherDetector:
    """Test suite for PlatformLauncherDetector class"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector instance for each test"""
        return PlatformLauncherDetector()

    def test_initialization(self, detector):
        """Test that detector initializes correctly"""
        assert detector.platforms is not None
        assert detector.launcher_audio_blacklist is not None

        # Check known platforms
        assert 'Steam' in detector.platforms
        assert 'Epic Games' in detector.platforms
        assert 'GOG Galaxy' in detector.platforms
        assert 'Battle.net' in detector.platforms
        assert 'EA App' in detector.platforms

    def test_steam_configuration(self, detector):
        """Test Steam platform configuration"""
        steam_config = detector.platforms['Steam']

        assert steam_config['process'] == 'steam.exe'
        assert 'steamwebhelper.exe' in steam_config['helper_processes']
        assert steam_config['priority'] == 'high'
        assert len(steam_config['paths']) > 0

    def test_epic_games_configuration(self, detector):
        """Test Epic Games platform configuration"""
        epic_config = detector.platforms['Epic Games']

        assert epic_config['process'] == 'EpicGamesLauncher.exe'
        assert 'EpicWebHelper.exe' in epic_config['helper_processes']
        assert epic_config['priority'] == 'high'
        assert 'param_pattern' in epic_config

    def test_gog_galaxy_configuration(self, detector):
        """Test GOG Galaxy platform configuration"""
        gog_config = detector.platforms['GOG Galaxy']

        assert gog_config['process'] == 'GalaxyClient.exe'
        assert gog_config['priority'] == 'medium'

    def test_battlenet_configuration(self, detector):
        """Test Battle.net platform configuration"""
        battlenet_config = detector.platforms['Battle.net']

        assert battlenet_config['process'] == 'Battle.net.exe'
        assert 'Agent.exe' in battlenet_config['helper_processes']

    def test_ea_app_configuration(self, detector):
        """Test EA App platform configuration"""
        ea_config = detector.platforms['EA App']

        assert ea_config['process'] == 'EADesktop.exe'
        assert ea_config['priority'] == 'low'

    def test_launcher_blacklist(self, detector):
        """Test launcher audio blacklist"""
        blacklist = detector.launcher_audio_blacklist

        # Should contain common launchers
        assert 'steam.exe' in blacklist
        assert 'epicgameslauncher.exe' in blacklist
        assert 'discord.exe' in blacklist
        assert 'chrome.exe' in blacklist

    def test_steam_appid_database(self, detector):
        """Test Steam AppID database"""
        appid_db = detector.steam_appid_db

        # Check some known games
        assert 730 in appid_db  # CS2/CSGO
        assert appid_db[730] == 'Counter-Strike 2'

        assert 570 in appid_db  # Dota 2
        assert appid_db[570] == 'Dota 2'

    def test_platform_priorities(self, detector):
        """Test platform priority levels"""
        # High priority platforms
        assert detector.platforms['Steam']['priority'] == 'high'
        assert detector.platforms['Epic Games']['priority'] == 'high'

        # Medium priority platforms
        assert detector.platforms['GOG Galaxy']['priority'] == 'medium'
        assert detector.platforms['Battle.net']['priority'] == 'medium'

        # Low priority platforms
        assert detector.platforms['EA App']['priority'] == 'low'

    def test_platform_paths_exist(self, detector):
        """Test that all platforms have path configurations"""
        for platform_name, platform_config in detector.platforms.items():
            assert 'paths' in platform_config
            assert len(platform_config['paths']) > 0

    def test_helper_processes_exist(self, detector):
        """Test that all platforms have helper process configurations"""
        for platform_name, platform_config in detector.platforms.items():
            assert 'helper_processes' in platform_config
            assert isinstance(platform_config['helper_processes'], list)

    def test_blacklist_lowercase(self, detector):
        """Test that blacklist entries are lowercase"""
        for entry in detector.launcher_audio_blacklist:
            assert entry == entry.lower(), f"{entry} should be lowercase"

    def test_path_patterns(self, detector):
        """Test path pattern configurations"""
        # Steam should have game path pattern
        assert 'game_path_pattern' in detector.platforms['Steam']

        # Epic should have both game path and param patterns
        assert 'game_path_pattern' in detector.platforms['Epic Games']
        assert 'param_pattern' in detector.platforms['Epic Games']

    def test_all_platforms_have_process(self, detector):
        """Test that all platforms have a main process defined"""
        for platform_name, platform_config in detector.platforms.items():
            assert 'process' in platform_config
            assert len(platform_config['process']) > 0

    def test_blacklist_includes_browsers(self, detector):
        """Test that blacklist includes common browsers"""
        blacklist = detector.launcher_audio_blacklist

        assert 'chrome.exe' in blacklist
        assert 'firefox.exe' in blacklist
        assert 'msedge.exe' in blacklist

    def test_blacklist_includes_music_apps(self, detector):
        """Test that blacklist includes music applications"""
        blacklist = detector.launcher_audio_blacklist

        assert 'spotify.exe' in blacklist

    def test_steam_appid_types(self, detector):
        """Test that Steam AppIDs are correct types"""
        for appid, game_name in detector.steam_appid_db.items():
            assert isinstance(appid, int)
            assert isinstance(game_name, str)
            assert len(game_name) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

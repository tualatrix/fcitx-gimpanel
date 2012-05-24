import os
import unittest

from gimpanel.config import ConfigSetting, fcitx_config
from gimpanel.common import CONFIG_ROOT


class TestConfigSettingFunctions(unittest.TestCase):
    def setUp(self):
        self.config_profile = ConfigSetting(os.path.join(CONFIG_ROOT, 'profile'))

    def test_config(self):
        self.assertEqual('wubi', self.config_profile.get_value('Profile', 'IMName'))
        self.assertEqual(['fcitx-keyboard-us', 'wubi', 'wbpy'], fcitx_config.get_enabled_ims())


if __name__ == '__main__':
    unittest.main()

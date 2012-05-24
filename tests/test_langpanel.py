import unittest

from gimpanel.langpanel import LangPanel


class TestLangPanelFunctions(unittest.TestCase):
    def setUp(self):
        self.langpanel = LangPanel()

    def test_langpanel(self):
        self.assertTrue(self.langpanel.is_default_im())


if __name__ == '__main__':
    unittest.main()

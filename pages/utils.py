from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pages.page_manager import PageManager
    from pages.main_page import MainPage
    from pages.settings import SettingsPage




def page_resized(e, self: Union['PageManager', 'MainPage', 'SettingsPage']):
    self.current_content.width = self.page.window.width
    self.current_content.height = self.page.window.height
    self.page.update()
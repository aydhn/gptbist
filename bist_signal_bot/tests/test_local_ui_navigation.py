import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.navigation import LocalUINavigationController
from bist_signal_bot.local_ui.layout import LocalUILayoutBuilder

def test_next_previous_page():
    builder = LocalUILayoutBuilder(Settings())
    layout = builder.build_layout()
    nav = LocalUINavigationController(Settings())

    first_page_id = layout.navigation_order[0]
    second_page_id = layout.navigation_order[1]

    next_page = nav.next_page(layout, first_page_id)
    assert next_page is not None
    assert next_page.page_id == second_page_id

    prev_page = nav.previous_page(layout, second_page_id)
    assert prev_page is not None
    assert prev_page.page_id == first_page_id

def test_get_page_not_found():
    builder = LocalUILayoutBuilder(Settings())
    layout = builder.build_layout()
    nav = LocalUINavigationController(Settings())
    assert nav.get_page(layout, "NON_EXISTENT") is None

def test_nav_menu_widget():
    builder = LocalUILayoutBuilder(Settings())
    layout = builder.build_layout()
    nav = LocalUINavigationController(Settings())

    widget = nav.nav_menu(layout)
    assert widget.kind.value == "NAV_MENU"
    assert len(widget.content["items"]) == len(layout.pages)

from __future__ import annotations

from importlib import resources

from ordocor.ui.design_config import BUTTON, FONT, INPUT, LIST, SCROLLBAR, TABLE, TAB

from .palettes import BASE_THEME, DEFAULT_THEME, PALETTES

_active_theme = DEFAULT_THEME


def _asset_url(filename: str) -> str:
    return str(resources.files("ordocor").joinpath("assets", filename)).replace("\\", "/")


BASE_STYLESHEET = f"""
* {{
    color: #EDE1C5;
    font-family: {FONT["family"]};
    font-size: {FONT["base_size"]}px;
}}

QMainWindow,
QWidget {{
    background: #191518;
}}

QLabel {{
    background: transparent;
}}

QPushButton {{
    background: #33292D;
    border: {BUTTON["border_width"]}px solid #665451;
    border-radius: {BUTTON["radius"]}px;
    color: #F7EDCF;
    font-weight: {BUTTON["font_weight"]};
    min-height: {BUTTON["min_height"]}px;
    padding: {BUTTON["padding_vertical"]}px {BUTTON["padding_horizontal"]}px;
}}

QPushButton:hover {{
    background: #3B2D32;
    border: {BUTTON["border_width"]}px solid #C0A361;
    color: #F3E7C9;
}}

QPushButton:pressed {{
    background: #675735;
    padding-top: {BUTTON["pressed_padding_top"]}px;
    padding-bottom: {BUTTON["pressed_padding_bottom"]}px;
}}

QPushButton:focus {{
    border: {BUTTON["border_width"]}px solid #C0A361;
}}

QPushButton:disabled {{
    background: #33292D;
    border: {BUTTON["border_width"]}px solid #665451;
    color: #9B8F83;
}}

QListWidget {{
    background: #191518;
    border: {LIST["border_width"]}px solid #665451;
    border-radius: {LIST["radius"]}px;
    outline: 0;
}}

QListWidget::item {{
    border-radius: {LIST["radius"]}px;
    color: #C7B99F;
    margin: {LIST["item_margin_vertical"]}px {LIST["item_margin_horizontal"]}px;
    padding: {LIST["item_padding_vertical"]}px {LIST["item_padding_horizontal"]}px;
}}

QListWidget::item:hover {{
    background: #2D2428;
    color: #F3E7C9;
}}

QListWidget::item:selected {{
    background: #3B2D32;
    color: #F3E7C9;
    border-left: {LIST["selected_border_width"]}px solid #9A8250;
}}

QTabWidget::pane {{
    border: {TAB["border_width"]}px solid #665451;
    border-radius: {TAB["radius"]}px;
    background: #231C20;
    top: -1px;
}}

QTabBar {{
    background: transparent;
}}

QTabBar::tab {{
    background: #191518;
    border: {TAB["border_width"]}px solid #665451;
    border-radius: {TAB["radius"]}px;
    color: #C7B99F;
    font-weight: {TAB["font_weight"]};
    margin-right: {TAB["margin_right"]}px;
    margin-bottom: {TAB["margin_bottom"]}px;
    min-width: {TAB["min_width"]}px;
    padding: {TAB["padding_vertical"]}px {TAB["padding_horizontal"]}px;
}}

QTabBar::tab:hover {{
    background: #2D2428;
    border: {TAB["border_width"]}px solid #C0A361;
    color: #F3E7C9;
}}

QTabBar::tab:selected {{
    background: #44363B;
    border: {TAB["border_width"]}px solid #C0A361;
    color: #F3E7C9;
    margin-bottom: {TAB["selected_margin_bottom"]}px;
    padding-bottom: {TAB["selected_padding_bottom"]}px;
}}

QTabBar::tab:disabled {{
    color: #9B8F83;
    background: #231C20;
    border: {TAB["border_width"]}px solid #665451;
}}

QLineEdit,
QTextEdit,
QComboBox,
QDateEdit,
QDoubleSpinBox,
QSpinBox {{
    background: #191518;
    border: {INPUT["border_width"]}px solid #665451;
    border-radius: {INPUT["radius"]}px;
    color: #F3E7C9;
    padding: {INPUT["padding"]}px;
}}

QDateEdit,
QDoubleSpinBox,
QSpinBox {{
    padding-right: 30px;
}}

QLineEdit:focus,
QTextEdit:focus,
QComboBox:focus,
QDateEdit:focus,
QDoubleSpinBox:focus,
QSpinBox:focus {{
    border: {INPUT["border_width"]}px solid #C0A361;
}}

QDateEdit::drop-down,
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: {INPUT["border_width"]}px solid #665451;
    border-top-right-radius: {INPUT["radius"]}px;
    border-bottom-right-radius: {INPUT["radius"]}px;
    background: #2D2428;
}}

QDateEdit::drop-down:hover,
QComboBox::drop-down:hover {{
    background: #3B2D32;
}}

QComboBox::down-arrow {{
    image: url("{_asset_url("chevron_down.svg")}");
    width: 10px;
    height: 10px;
}}

QDateEdit::down-arrow {{
    image: url("{_asset_url("calendar.svg")}");
    width: 14px;
    height: 14px;
}}

QDoubleSpinBox::up-button,
QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    border-left: {INPUT["border_width"]}px solid #665451;
    border-bottom: {INPUT["border_width"]}px solid #665451;
    border-top-right-radius: {INPUT["radius"]}px;
    background: #2D2428;
}}

QDoubleSpinBox::down-button,
QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 24px;
    border-left: {INPUT["border_width"]}px solid #665451;
    border-bottom-right-radius: {INPUT["radius"]}px;
    background: #2D2428;
}}

QDoubleSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover,
QSpinBox::down-button:hover {{
    background: #3B2D32;
}}

QDoubleSpinBox::up-arrow,
QSpinBox::up-arrow {{
    image: url("{_asset_url("arrow_up.svg")}");
    width: 9px;
    height: 9px;
}}

QDoubleSpinBox::down-arrow,
QSpinBox::down-arrow {{
    image: url("{_asset_url("arrow_down.svg")}");
    width: 9px;
    height: 9px;
}}

QCalendarWidget QWidget {{
    alternate-background-color: #191518;
    background: #191518;
    color: #F3E7C9;
}}

QCalendarWidget QAbstractItemView {{
    alternate-background-color: #191518;
    background: #191518;
    color: #F3E7C9;
    selection-background-color: #66513F;
    selection-color: #F3E7C9;
}}

QTableWidget {{
    background: #191518;
    border: {TABLE["border_width"]}px solid #665451;
    border-radius: {TABLE["radius"]}px;
    gridline-color: #665451;
    selection-background-color: #66513F;
}}

QTableWidget::item {{
    padding: {TABLE["cell_padding"]}px;
}}

QHeaderView::section {{
    background: #2D2428;
    border: 0;
    border-right: {TABLE["border_width"]}px solid #665451;
    border-bottom: {TABLE["border_width"]}px solid #665451;
    color: #E2D4B7;
    font-weight: {TABLE["header_weight"]};
    padding: {TABLE["header_padding"]}px;
}}

QDialog {{
    background: #191518;
}}

QScrollArea {{
    background: transparent;
    border: 0;
}}

QScrollBar:vertical {{
    background: #191518;
    width: {SCROLLBAR["width"]}px;
}}

QScrollBar::handle:vertical {{
    background: #76635E;
    border-radius: {SCROLLBAR["radius"]}px;
}}
"""


def set_active_theme(theme_name: str) -> None:
    global _active_theme

    _active_theme = theme_name


def stylesheet_for(theme_name: str) -> str:
    return _replace_palette(BASE_STYLESHEET, BASE_THEME, theme_name)


def themed_stylesheet(stylesheet: str) -> str:
    return _replace_palette(stylesheet, BASE_THEME, _active_theme)


def theme_color(token: str) -> str:
    return PALETTES[_active_theme][token]


def _replace_palette(text: str, source_theme: str, target_theme: str) -> str:
    source = PALETTES[source_theme]
    target = PALETTES[target_theme]
    for token, source_color in source.items():
        text = text.replace(source_color, target[token])
    return text


APP_STYLESHEET = stylesheet_for(DEFAULT_THEME)

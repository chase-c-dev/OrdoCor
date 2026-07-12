from __future__ import annotations

FONT = {
    "family": '"Segoe UI", Arial, sans-serif',
    "base_size": 14,
    "caption_size": 12,
    "body_weight": 400,
    "control_weight": 700,
    "heading_weight": 800,
}

RADIUS = {
    "small": 4,
    "medium": 6,
    "large": 7,
}

SPACING = {
    "control_vertical": 9,
    "control_horizontal": 15,
    "control_pressed_top": 9,
    "control_pressed_bottom": 9,
    "field_padding": 8,
    "table_cell_padding": 6,
    "header_padding": 8,
    "list_item_vertical": 11,
    "list_item_horizontal": 12,
    "tab_vertical": 10,
    "tab_horizontal": 16,
    "selected_tab_bottom": 10,
}

BUTTON = {
    "border_width": 1,
    "radius": RADIUS["large"],
    "font_weight": FONT["control_weight"],
    "min_height": 20,
    "padding_vertical": SPACING["control_vertical"],
    "padding_horizontal": SPACING["control_horizontal"],
    "pressed_padding_top": SPACING["control_pressed_top"],
    "pressed_padding_bottom": SPACING["control_pressed_bottom"],
}

TAB = {
    "border_width": 1,
    "radius": RADIUS["large"],
    "font_weight": FONT["control_weight"],
    "min_width": 72,
    "margin_right": 6,
    "margin_bottom": 8,
    "selected_margin_bottom": 8,
    "padding_vertical": SPACING["tab_vertical"],
    "padding_horizontal": SPACING["tab_horizontal"],
    "selected_padding_bottom": SPACING["selected_tab_bottom"],
}

ANIMATION = {
    "page_fade_ms": 180,
    "welcome_fade_ms": 260,
    "welcome_slide_ms": 520,
    "welcome_unlock_ms": 260,
    "welcome_enter_delay_ms": 240,
    "button_feedback_ms": 150,
    "button_feedback_opacity_start": 0.68,
    "opacity_start": 0.0,
    "opacity_end": 1.0,
}

INPUT = {
    "border_width": 1,
    "radius": RADIUS["medium"],
    "padding": SPACING["field_padding"],
}

TABLE = {
    "border_width": 1,
    "radius": RADIUS["large"],
    "cell_padding": SPACING["table_cell_padding"],
    "header_padding": SPACING["header_padding"],
    "header_weight": FONT["control_weight"],
}

LIST = {
    "border_width": 1,
    "radius": RADIUS["small"],
    "item_margin_vertical": 2,
    "item_margin_horizontal": 0,
    "item_padding_vertical": SPACING["list_item_vertical"],
    "item_padding_horizontal": SPACING["list_item_horizontal"],
    "selected_border_width": 3,
}

SCROLLBAR = {
    "width": 12,
    "radius": RADIUS["small"],
}

CALENDAR_DAY_BUTTON = {
    "width": 34,
    "height": 28,
    "border_width": 1,
    "radius": RADIUS["small"],
    "font_weight": FONT["heading_weight"],
    "padding": 0,
}

"""Chord ring of the arms flows of one year, with a country card (custom component, st.components.v2).

Same picture as chordView() in app/site/flows.js and flowCard() in app/site/adc.html: suppliers on the left half
in fixed slots (the top 6 suppliers over the whole period plus "Other suppliers"), the year's top 8 recipients plus
"Other recipients" on the right half, arcs and ribbons linear in the share of the year's TIV. Python computes all
numbers (data.py); chord.js only draws them, tweens between years and shows a country card on hover or when pinned.

    res = chord_ring(year, pinned="r:IND", key="wm_chord", on_pin=..., on_close=...)

Events back to Python (triggers, one rerun each): "pin" (a card key, sent when a country node is clicked) and
"close" (the × of a pinned card).
"""

from pathlib import Path

import streamlit as st

from . import data as cd

_HERE = Path(__file__).resolve().parent
_COMPONENT = st.components.v2.component(
    "adc_chord_ring",
    html='<div class="chr-root"></div>',
    css=(_HERE / "chord.css").read_text(encoding="utf8"),
    js=(_HERE / "chord.js").read_text(encoding="utf8"),
)


def chord_ring(year, *, pinned=None, height=440, tween_ms=800, key=None, on_pin=None, on_close=None):
    """Draw the ring for `year`. `pinned` is a card key ("r:ISO3" for a country as recipient, "s:Supplier name"
    for a supplier) whose card is shown with a close button. Returns the component result (.pin, .close)."""
    payload = {
        "year": int(year),
        "ring": cd.ring(int(year)),
        "cards": cd.cards(int(year), pinned),
        "pinned": pinned,
        "height": int(height),
        "tween": int(tween_ms),
    }
    return _COMPONENT(data=payload, key=key, height=height,
                      on_pin_change=on_pin or (lambda: None), on_close_change=on_close or (lambda: None))

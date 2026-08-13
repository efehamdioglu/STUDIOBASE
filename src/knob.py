import os

import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "components", "knob")
)
_knob_func = components.declare_component("studiobase_knob", path=_COMPONENT_DIR)


def range_knob(label: str, min_value: int, max_value: int, value: int, key: str) -> int:
    """Fare ile sürüklenerek (ya da tekerlekle) döndürülen sayısal bir knob.
    Gerçek bir potansiyometre gibi -135° ile +135° arasında döner."""
    result = _knob_func(
        mode="range",
        label=label,
        min=min_value,
        max=max_value,
        value=value,
        options=[],
        key=key,
        default=value,
        height=110,
    )
    if result is None:
        return value
    return int(result)


def select_knob(label: str, options: list[str], value: str, key: str) -> str:
    """Ayrık seçenekler arasında döner bir seçim anahtarı (rotary switch)
    gibi davranan knob. Döndürüldükçe seçenekler arasında sırayla geçer."""
    safe_value = value if value in options else options[0]
    result = _knob_func(
        mode="select",
        label=label,
        min=0,
        max=len(options) - 1,
        value=safe_value,
        options=options,
        key=key,
        default=options.index(safe_value),
        height=110,
    )
    if result is None:
        return safe_value
    idx = int(result)
    if 0 <= idx < len(options):
        return options[idx]
    return safe_value

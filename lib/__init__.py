"""Launch Control XL 3 SysEx Template Generator Library.

This package provides tools for generating and customizing MIDI templates
for the Novation Launch Control XL 3.
"""

from .sysex_generator import SysExTemplateGenerator, ChannelMode, CCMode
from .led_mapper import LEDColorMapper
from .constants import (
    COLOR_MAP, COLOR_NAMES, COLOR_ABBREV, CONTROLS, DEVICE_LAYOUT,
    MAX_CC_VALUE, MIN_CC_VALUE, DEFAULT_MIN_CC_VALUE, MAX_MIDI_CHANNEL, MIN_MIDI_CHANNEL,
    DEFAULT_TEMPLATE_COUNT
)

__version__ = "1.0.0"
__all__ = [
    "SysExTemplateGenerator", "LEDColorMapper", "ChannelMode", "CCMode",
    "COLOR_MAP", "COLOR_NAMES", "COLOR_ABBREV", "CONTROLS", "DEVICE_LAYOUT",
    "MAX_CC_VALUE", "MIN_CC_VALUE", "DEFAULT_MIN_CC_VALUE", "MAX_MIDI_CHANNEL", "MIN_MIDI_CHANNEL", 
    "DEFAULT_TEMPLATE_COUNT"
]
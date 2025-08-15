#!/usr/bin/env python3

from pathlib import Path
import argparse
import logging
from typing import List, Tuple, Optional
import sys
from enum import Enum

# Constants
MAX_CC_VALUE = 127  
MIN_CC_VALUE = 1
MAX_MIDI_CHANNEL = 16
MIN_MIDI_CHANNEL = 1
MAX_INTERNAL_CHANNEL = 15
MIN_INTERNAL_CHANNEL = 0
DEFAULT_TEMPLATE_COUNT = 16

class ChannelMode(Enum):
    """Channel assignment modes."""
    PER_TEMPLATE = "per-template"  # T01=Ch1, T02=Ch2, etc. (default)
    GLOBAL = "global"              # All templates use same channel

class CCMode(Enum):
    """CC numbering strategies."""
    RESTART_PER_TEMPLATE = "restart"    # Each template starts at CC 1 (default)
    CONTINUOUS = "continuous"           # CCs 1-127 continuous across templates

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Embedded SysEx messages 
EMBEDDED_MSGS = [
    b"\xf0\x00\x20\x29\x02\x15\x05\x00\x45\x00\x7f\x20\x10\x2a\x4e\x65\x77\x20\x43\x75\x73\x74\x6f\x6d\x20\x4d\x6f\x64\x65\x49\x10\x02\x05\x00\x01\x40\x00\x0d\x7f\x00\x49\x11\x02\x05\x00\x01\x40\x00\x0e\x7f\x00\x49\x12\x02\x05\x00\x01\x40\x00\x0f\x7f\x00\x49\x13\x02\x05\x00\x01\x40\x00\x10\x7f\x00\x49\x14\x02\x05\x00\x01\x40\x00\x11\x7f\x00\x49\x15\x02\x05\x00\x01\x40\x00\x12\x7f\x00\x49\x16\x02\x05\x00\x01\x40\x00\x13\x7f\x00\x49\x17\x02\x05\x00\x01\x40\x00\x14\x7f\x00\x49\x18\x02\x09\x00\x01\x40\x00\x15\x7f\x00\x49\x19\x02\x09\x00\x01\x40\x00\x16\x7f\x00\x49\x1a\x02\x09\x00\x01\x40\x00\x17\x7f\x00\x49\x1b\x02\x09\x00\x01\x40\x00\x18\x7f\x00\x49\x1c\x02\x09\x00\x01\x40\x00\x19\x7f\x00\x49\x1d\x02\x09\x00\x01\x40\x00\x1a\x7f\x00\x49\x1e\x02\x09\x00\x01\x40\x00\x1b\x7f\x00\x49\x1f\x02\x09\x00\x01\x40\x00\x1c\x7f\x00\x49\x20\x02\x0d\x00\x01\x40\x00\x1d\x7f\x00\x49\x21\x02\x0d\x00\x01\x40\x00\x1e\x7f\x00\x49\x22\x02\x0d\x00\x01\x40\x00\x1f\x7f\x00\x49\x23\x02\x0d\x00\x01\x40\x00\x20\x7f\x00\x49\x24\x02\x0d\x00\x01\x40\x00\x21\x7f\x00\x49\x25\x02\x0d\x00\x01\x40\x00\x22\x7f\x00\x49\x26\x02\x0d\x00\x01\x40\x00\x23\x7f\x00\x49\x27\x02\x0d\x00\x01\x40\x00\x24\x7f\x00\x60\x10\x60\x11\x60\x12\x60\x13\x60\x14\x60\x15\x60\x16\x60\x17\x60\x18\x60\x19\x60\x1a\x60\x1b\x60\x1c\x60\x1d\x60\x1e\x60\x1f\x60\x20\x60\x21\x60\x22\x60\x23\x60\x24\x60\x25\x60\x26\x60\x27\xf7",
    b"\xf0\x00\x20\x29\x02\x15\x05\x00\x45\x03\x7f\x20\x10\x2a\x4e\x65\x77\x20\x43\x75\x73\x74\x6f\x6d\x20\x4d\x6f\x64\x65\x49\x28\x02\x00\x00\x01\x40\x00\x05\x7f\x00\x49\x29\x02\x00\x00\x01\x40\x00\x06\x7f\x00\x49\x2a\x02\x00\x00\x01\x40\x00\x07\x7f\x00\x49\x2b\x02\x00\x00\x01\x40\x00\x08\x7f\x00\x49\x2c\x02\x00\x00\x01\x40\x00\x09\x7f\x00\x49\x2d\x02\x00\x00\x01\x40\x00\x0a\x7f\x00\x49\x2e\x02\x00\x00\x01\x40\x00\x0b\x7f\x00\x49\x2f\x02\x00\x00\x01\x40\x00\x0c\x7f\x00\x60\x28\x60\x29\x60\x2a\x60\x2b\x60\x2c\x60\x2d\x60\x2e\x60\x2f\x49\x30\x02\x19\x03\x01\x50\x00\x25\x7f\x00\x49\x31\x02\x19\x03\x01\x50\x00\x26\x7f\x00\x49\x32\x02\x19\x03\x01\x50\x00\x27\x7f\x00\x49\x33\x02\x19\x03\x01\x50\x00\x28\x7f\x00\x49\x34\x02\x19\x03\x01\x50\x00\x29\x7f\x00\x49\x35\x02\x19\x03\x01\x50\x00\x2a\x7f\x00\x49\x36\x02\x19\x03\x01\x50\x00\x2b\x7f\x00\x49\x37\x02\x19\x03\x01\x50\x00\x2c\x7f\x00\x49\x38\x02\x25\x03\x01\x50\x00\x2d\x7f\x00\x49\x39\x02\x25\x03\x01\x50\x00\x2e\x7f\x00\x49\x3a\x02\x25\x03\x01\x50\x00\x2f\x7f\x00\x49\x3b\x02\x25\x03\x01\x50\x00\x30\x7f\x00\x49\x3c\x02\x25\x03\x01\x50\x00\x31\x7f\x00\x49\x3d\x02\x25\x03\x01\x50\x00\x32\x7f\x00\x49\x3e\x02\x25\x03\x01\x50\x00\x33\x7f\x00\x49\x3f\x02\x25\x03\x01\x50\x00\x34\x7f\x00\x60\x30\x60\x31\x60\x32\x60\x33\x60\x34\x60\x35\x60\x36\x60\x37\x60\x38\x60\x39\x60\x3a\x60\x3b\x60\x3c\x60\x3d\x60\x3e\x60\x3f\xf7"
]

# Control map tuples: (msg_index, cc_pos, ch_pos, color_pos, flag_pos [-1 if none])
CONTROLS: List[Tuple[int, int, int, int, int]] = [
    (0,37,34,32,35), (0,48,45,43,46), (0,59,56,54,57), (0,70,67,65,68), (0,81,78,76,79),
    (0,92,89,87,90), (0,103,100,98,101), (0,114,111,109,112), (0,125,122,120,123),
    (0,136,133,131,134), (0,147,144,142,145), (0,158,155,153,156), (0,169,166,164,167),
    (0,180,177,175,178), (0,191,188,186,189), (0,202,199,197,200), (0,213,210,208,211),
    (0,224,221,219,222), (0,235,232,230,233), (0,246,243,241,244), (0,257,254,252,255),
    (0,268,265,263,266), (0,279,276,274,277), (0,290,287,285,288),
    (1,37,34,32,35), (1,48,45,43,46), (1,59,56,54,57), (1,70,67,65,68), (1,81,78,76,79),
    (1,92,89,87,90), (1,103,100,98,101), (1,114,111,109,112), (1,141,138,136,139),
    (1,152,149,147,150), (1,163,160,158,161), (1,174,171,169,172), (1,185,182,180,183),
    (1,196,193,191,194), (1,207,204,202,205), (1,218,215,213,216), (1,229,226,224,227),
    (1,240,237,235,238), (1,251,248,246,249), (1,262,259,257,260), (1,273,270,268,271),
    (1,284,281,279,282), (1,295,292,290,293), (1,306,303,301,304)
]

# Named colors for future use
COLOR_MAP = {
    'red': 0x05, 'orange': 0x09, 'yellow': 0x0d, 'lime': 0x11, 'green': 0x19,
    'turquoise': 0x1d, 'cyan': 0x21, 'light_blue': 0x25, 'blue': 0x29,
    'dark_blue': 0x2d, 'purple': 0x31, 'fuchsia': 0x35, 'pink': 0x39,
    'off': 0x03, 'disabled': 0x00
}


class SysExTemplateGenerator:
    def __init__(self):
        self.base_messages = [bytearray(msg) for msg in EMBEDDED_MSGS]
    
    def _validate_channel(self, channel_1_16: int) -> int:
        """
        Validate and convert 1-16 channel to 0-15 internal representation.
        
        Args:
            channel_1_16: MIDI channel (1-16)
            
        Returns:
            Zero-based channel (0-15)
            
        Raises:
            ValueError: If channel is out of valid range
        """
        if not isinstance(channel_1_16, int) or not (MIN_MIDI_CHANNEL <= channel_1_16 <= MAX_MIDI_CHANNEL):
            raise ValueError(f"Channel must be integer between {MIN_MIDI_CHANNEL} and {MAX_MIDI_CHANNEL}")
        return channel_1_16 - 1
    
    def _validate_template_count(self, count: int) -> int:
        """
        Validate template count.
        
        Args:
            count: Number of templates to generate
            
        Returns:
            Validated template count
            
        Raises:
            ValueError: If count is invalid
        """
        if not isinstance(count, int) or count < 1:
            raise ValueError(f"Template count must be positive integer, got: {count}")
        return count
    
    def _clone_messages(self) -> List[bytearray]:
        """Create a deep copy of base messages for modification."""
        return [bytearray(msg) for msg in self.base_messages]
    
    def _assign_continuous_controllers(
        self, 
        messages: List[bytearray], 
        template_index: int = 0,
        cc_mode: CCMode = CCMode.RESTART_PER_TEMPLATE
    ) -> None:
        """
        Assign CC values based on the specified mode.
        
        Args:
            messages: List of message bytearrays to modify
            template_index: Zero-based template index (for continuous mode)
            cc_mode: CC numbering strategy
        """
        for control_index, (msg_index, cc_pos, _ch_pos, _col_pos, _flag_pos) in enumerate(CONTROLS):
            if cc_mode == CCMode.RESTART_PER_TEMPLATE:
                # Each template starts at CC 1
                cc_value = (control_index % MAX_CC_VALUE) + MIN_CC_VALUE
            else:  # CCMode.CONTINUOUS
                # Continuous CC numbering across templates
                global_control_index = (template_index * len(CONTROLS)) + control_index
                cc_value = (global_control_index % MAX_CC_VALUE) + MIN_CC_VALUE
            
            messages[msg_index][cc_pos] = cc_value
    
    def _set_midi_channel(self, messages: List[bytearray], channel_1_16: int) -> None:
        """
        Set MIDI channel for all controls in the template.
        
        Args:
            messages: List of message bytearrays to modify
            channel_1_16: MIDI channel (1-16)
        """
        zero_based_channel = self._validate_channel(channel_1_16)
        
        for (msg_index, _cc_pos, ch_pos, _col_pos, flag_pos) in CONTROLS:
            messages[msg_index][ch_pos] = zero_based_channel
            if flag_pos >= 0:  # Set local channel mode if flag position exists
                messages[msg_index][flag_pos] = 0x00
    
    def _write_sysex_file(self, file_path: Path, messages: List[bytearray]) -> None:
        """
        Write SysEx messages to file with error handling.
        
        Args:
            file_path: Output file path
            messages: List of message bytearrays to write
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            combined_data = b"".join(bytes(msg) for msg in messages)
            file_path.write_bytes(combined_data)
            logger.debug(f"Successfully wrote {len(combined_data)} bytes to {file_path}")
        except (OSError, IOError) as e:
            raise IOError(f"Failed to write file {file_path}: {e}")
    
    def _get_channel_for_template(
        self, 
        template_num: int, 
        channel_mode: ChannelMode, 
        global_channel: Optional[int] = None
    ) -> int:
        """
        Determine the MIDI channel for a template based on channel mode.
        
        Args:
            template_num: Template number (1-based)
            channel_mode: Channel assignment mode
            global_channel: Global channel (required for GLOBAL mode)
            
        Returns:
            MIDI channel (1-16)
        """
        if channel_mode == ChannelMode.GLOBAL:
            if global_channel is None:
                raise ValueError("Global channel must be specified for GLOBAL channel mode")
            return global_channel
        else:  # ChannelMode.PER_TEMPLATE
            # Cap at channel 16 if template number exceeds 16
            return min(template_num, MAX_MIDI_CHANNEL)
    
    def generate_template(
        self, 
        template_num: int,
        channel_mode: ChannelMode = ChannelMode.PER_TEMPLATE,
        cc_mode: CCMode = CCMode.RESTART_PER_TEMPLATE,
        global_channel: Optional[int] = None
    ) -> List[bytearray]:
        """
        Generate a single template with configurable modes.
        
        Args:
            template_num: Template number (1-based)
            channel_mode: Channel assignment mode
            cc_mode: CC numbering strategy
            global_channel: Global channel for GLOBAL mode
            
        Returns:
            List of configured message bytearrays
        """
        messages = self._clone_messages()
        
        # Determine channel
        channel = self._get_channel_for_template(template_num, channel_mode, global_channel)
        self._set_midi_channel(messages, channel)
        
        # Assign CCs
        template_index = template_num - 1  # Convert to 0-based for CC calculation
        self._assign_continuous_controllers(messages, template_index, cc_mode)
        
        return messages
    
    def generate_all_templates(
        self,
        template_count: int = DEFAULT_TEMPLATE_COUNT,
        channel_mode: ChannelMode = ChannelMode.PER_TEMPLATE,
        cc_mode: CCMode = CCMode.RESTART_PER_TEMPLATE,
        global_channel: Optional[int] = None,
        output_prefix: str = "Serum",
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        Generate templates with configurable settings.
        
        Args:
            template_count: Number of templates to generate
            channel_mode: Channel assignment mode
            cc_mode: CC numbering strategy
            global_channel: Global channel for GLOBAL mode
            output_prefix: Filename prefix for generated files
            output_dir: Output directory (defaults to ./outputs)
            
        Returns:
            List of generated file paths
            
        Raises:
            IOError: If output directory cannot be created or files cannot be written
        """
        template_count = self._validate_template_count(template_count)
        
        if output_dir is None:
            output_dir = Path("./outputs")
        
        # Create output directory with error handling
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, IOError) as e:
            raise IOError(f"Failed to create output directory {output_dir}: {e}")
        
        generated_files = []
        
        logger.info(f"Generating {template_count} templates:")
        logger.info(f"  Channel Mode: {channel_mode.value}")
        logger.info(f"  CC Mode: {cc_mode.value}")
        if channel_mode == ChannelMode.GLOBAL and global_channel:
            logger.info(f"  Global Channel: {global_channel}")
        
        for template_num in range(1, template_count + 1):
            try:
                messages = self.generate_template(
                    template_num=template_num,
                    channel_mode=channel_mode,
                    cc_mode=cc_mode,
                    global_channel=global_channel
                )
                
                output_file = output_dir / f"{output_prefix}_T{template_num:02d}.syx"
                
                # Check if file exists and warn user
                if output_file.exists():
                    logger.warning(f"Overwriting existing file: {output_file}")
                
                self._write_sysex_file(output_file, messages)
                generated_files.append(output_file)
                
                # Log channel and CC info for first few templates
                if template_num <= 3 or logger.level <= logging.DEBUG:
                    channel = self._get_channel_for_template(template_num, channel_mode, global_channel)
                    first_cc = ((template_num - 1) * len(CONTROLS) if cc_mode == CCMode.CONTINUOUS else 0) + 1
                    logger.debug(f"  T{template_num:02d}: Channel {channel}, CCs start at {first_cc}")
                
            except Exception as e:
                logger.error(f"Failed to generate template {template_num}: {e}")
                raise
        
        return generated_files


def generate_templates(output_prefix: str = "Serum") -> List[Path]:
    """
    Legacy function for backward compatibility.
    
    Args:
        output_prefix: Filename prefix for generated files
        
    Returns:
        List of generated file paths
    """
    generator = SysExTemplateGenerator()
    return generator.generate_all_templates(output_prefix=output_prefix)


def main():
    """Main entry point with enhanced argument parsing and feature flags."""
    parser = argparse.ArgumentParser(
        description="Novation LC XL 3 SysEx Template Generator v7",
        epilog="Generates configurable MIDI templates with flexible channel and CC assignment.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Output options
    parser.add_argument(
        "--output-prefix", 
        default="Serum",
        help="Output filename prefix (default: %(default)s)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./outputs"),
        help="Output directory (default: %(default)s)"
    )
    
    # Feature flags
    parser.add_argument(
        "--template-count",
        type=int,
        default=DEFAULT_TEMPLATE_COUNT,
        help=f"Number of templates to generate (default: {DEFAULT_TEMPLATE_COUNT})"
    )
    
    # Channel mode options (mutually exclusive group)
    channel_group = parser.add_mutually_exclusive_group()
    channel_group.add_argument(
        "--global-channel",
        type=int,
        choices=range(1, 17),
        metavar="1-16",
        help="Use same MIDI channel for all templates (1-16)"
    )
    
    # CC numbering mode
    parser.add_argument(
        "--cc-continuous",
        action="store_true",
        help="Use continuous CC numbering 1-127 across templates (default: restart at 1 per template)"
    )
    
    # Logging
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine modes
    channel_mode = ChannelMode.GLOBAL if args.global_channel else ChannelMode.PER_TEMPLATE
    cc_mode = CCMode.CONTINUOUS if args.cc_continuous else CCMode.RESTART_PER_TEMPLATE
    
    try:
        generator = SysExTemplateGenerator()
        generated_files = generator.generate_all_templates(
            template_count=args.template_count,
            channel_mode=channel_mode,
            cc_mode=cc_mode,
            global_channel=args.global_channel,
            output_prefix=args.output_prefix,
            output_dir=args.output_dir
        )
        
        print(f"Successfully generated {len(generated_files)} templates in {args.output_dir}:")
        for file_path in generated_files:
            print(f"  - {file_path.name}")
            
    except Exception as e:
        logger.error(f"Template generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

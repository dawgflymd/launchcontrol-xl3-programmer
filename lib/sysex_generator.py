"""SysEx template generator for Launch Control XL 3."""

import logging
from pathlib import Path
from typing import List, Optional
from enum import Enum

from .constants import (
    EMBEDDED_MSGS, CONTROLS, MAX_CC_VALUE, MIN_CC_VALUE, 
    MAX_MIDI_CHANNEL, MIN_MIDI_CHANNEL, DEFAULT_TEMPLATE_COUNT, DEFAULT_MIN_CC_VALUE,
    SAFE_CC_MIN, SAFE_CC_MAX
)

logger = logging.getLogger(__name__)


class ChannelMode(Enum):
    """Channel assignment modes."""
    PER_TEMPLATE = "per-template"  # T01=Ch1, T02=Ch2, etc. (default)
    GLOBAL = "global"              # All templates use same channel


class CCMode(Enum):
    """CC numbering strategies."""
    RESTART_PER_TEMPLATE = "restart"    # Each template starts at CC 1 (default)
    CONTINUOUS = "continuous"           # CCs 1-127 continuous across templates


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
        if not isinstance(count, int) or count < 1 or count > 15:
            raise ValueError(f"Template count must be integer between 1-15, got: {count}")
        return count
    
    def _clone_messages(self) -> List[bytearray]:
        """Create a deep copy of base messages for modification."""
        return [bytearray(msg) for msg in self.base_messages]
    
    def _assign_continuous_controllers(
        self, 
        messages: List[bytearray], 
        template_index: int = 0,
        cc_mode: CCMode = CCMode.RESTART_PER_TEMPLATE,
        min_cc_value: int = DEFAULT_MIN_CC_VALUE,
        cc_reverse: bool = False
    ) -> None:
        """
        Assign CC values based on the specified mode.
        
        Args:
            messages: List of message bytearrays to modify
            template_index: Zero-based template index (for continuous mode)
            cc_mode: CC numbering strategy
            min_cc_value: Starting CC number
            cc_reverse: Start at 127 and assign backwards
        """
        # Ensure min_cc_value is within safe range
        safe_min_cc = max(min_cc_value, SAFE_CC_MIN)
        available_ccs = SAFE_CC_MAX - safe_min_cc + 1  # Total available CC range within safe limits
        
        for control_index, (msg_index, cc_pos, _ch_pos, _col_pos, _flag_pos) in enumerate(CONTROLS):
            # Calculate which CC number this control should get
            if cc_mode == CCMode.RESTART_PER_TEMPLATE:
                cc_offset = control_index
            else:  # CCMode.CONTINUOUS
                cc_offset = (template_index * len(CONTROLS)) + control_index
            
            # Check if we've exhausted available CC numbers within safe range
            if cc_offset >= available_ccs:
                # Disable this control - set CC to 0 (typically means disabled/unused)
                cc_value = 0
            else:
                if cc_reverse:
                    # Start at SAFE_CC_MAX and go backwards
                    cc_value = SAFE_CC_MAX - cc_offset
                    # Ensure we don't go below safe minimum
                    if cc_value < SAFE_CC_MIN:
                        cc_value = 0  # Disable if outside safe range
                else:
                    # Normal forward assignment within safe range
                    cc_value = safe_min_cc + cc_offset
                    # Ensure we don't exceed safe maximum
                    if cc_value > SAFE_CC_MAX:
                        cc_value = 0  # Disable if outside safe range
            
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
    
    def _set_button_modes(self, messages: List[bytearray]) -> None:
        """
        Set button modes - defaults bottom two button rows (32-47) to toggle mode.
        The button controls already have 0x50 in the embedded messages, so we don't need to modify them.
        This method is kept for future enhancements if needed.
        
        Args:
            messages: List of message bytearrays to modify
        """
        # The embedded SysEx messages already have the correct button mode (0x50) 
        # for the button controls (32-47) in message 1.
        # No modification needed - the buttons are already configured correctly.
        pass
    
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
        global_channel: Optional[int] = None,
        min_cc_value: int = DEFAULT_MIN_CC_VALUE,
        cc_reverse: bool = False
    ) -> List[bytearray]:
        """
        Generate a single template with configurable modes.
        
        Args:
            template_num: Template number (1-based)
            channel_mode: Channel assignment mode
            cc_mode: CC numbering strategy
            global_channel: Global channel for GLOBAL mode
            min_cc_value: Starting CC number
            cc_reverse: Start at 127 and assign backwards
            
        Returns:
            List of configured message bytearrays
        """
        messages = self._clone_messages()
        
        # Determine channel
        channel = self._get_channel_for_template(template_num, channel_mode, global_channel)
        self._set_midi_channel(messages, channel)
        
        # Set button modes (bottom two rows default to toggle)
        self._set_button_modes(messages)
        
        # Assign CCs
        template_index = template_num - 1  # Convert to 0-based for CC calculation
        self._assign_continuous_controllers(messages, template_index, cc_mode, min_cc_value, cc_reverse)
        
        return messages
    
    def generate_all_templates(
        self,
        template_count: int = DEFAULT_TEMPLATE_COUNT,
        channel_mode: ChannelMode = ChannelMode.PER_TEMPLATE,
        cc_mode: CCMode = CCMode.RESTART_PER_TEMPLATE,
        global_channel: Optional[int] = None,
        output_prefix: str = "Serum",
        output_dir: Optional[Path] = None,
        min_cc_value: int = DEFAULT_MIN_CC_VALUE,
        cc_reverse: bool = False
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
            min_cc_value: Starting CC number
            cc_reverse: Start at 127 and assign backwards
            
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
                    global_channel=global_channel,
                    min_cc_value=min_cc_value,
                    cc_reverse=cc_reverse
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
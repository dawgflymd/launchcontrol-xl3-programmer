"""Interactive LED color mapper for Launch Control XL 3."""

import curses
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from .constants import (
    COLOR_MAP, COLOR_NAMES, COLOR_ABBREV, CONTROLS, DEVICE_LAYOUT
)

logger = logging.getLogger(__name__)


class LEDColorMapper:
    """Interactive curses-based LED color mapper for Launch Control XL 3."""
    
    def __init__(self):
        self.colors = {}  # (row, col) -> color_name
        self.cursor_row = 0
        self.cursor_col = 0
        self.current_color_idx = 0
        
        # Initialize all controls to 'off'
        for section in DEVICE_LAYOUT.values():
            for row, col in section:
                self.colors[(row, col)] = 'off'
        
    
    def run_interactive_editor(self):
        """Launch the curses-based color editor."""
        try:
            curses.wrapper(self._curses_main)
        except KeyboardInterrupt:
            print("\nColor editor cancelled.")
            return None
        return self.colors
    
    def edit_template_file(self, template_path: Path):
        """Edit LED colors for a specific template file."""
        try:
            # Read the current template file
            template_data = template_path.read_bytes()
            
            # Parse current colors from the template
            self._extract_colors_from_sysex(template_data)
            
            # Run the interactive editor
            color_map = self.run_interactive_editor()
            
            if color_map:
                # Apply colors to the template and save
                self._apply_colors_to_sysex(template_data, template_path)
                return color_map
            return None
            
        except Exception as e:
            logger.error(f"Failed to edit template file {template_path}: {e}")
            raise
    
    def _extract_colors_from_sysex(self, sysex_data: bytes):
        """Extract current LED colors from SysEx data."""
        # Convert to bytearray for easier manipulation
        messages = self._split_sysex_messages(sysex_data)
        
        # Extract colors from each control
        for control_index, (msg_index, _cc_pos, _ch_pos, color_pos, _flag_pos) in enumerate(CONTROLS):
            if msg_index < len(messages) and color_pos < len(messages[msg_index]):
                color_value = messages[msg_index][color_pos]
                
                # Find color name from value
                color_name = 'off'  # default
                for name, value in COLOR_MAP.items():
                    if value == color_value:
                        color_name = name
                        break
                
                # Map control to device layout position
                row, col = self._control_index_to_position(control_index)
                if row is not None and col is not None:
                    self.colors[(row, col)] = color_name
    
    def _split_sysex_messages(self, sysex_data: bytes) -> List[bytearray]:
        """Split concatenated SysEx data into individual messages."""
        messages = []
        start = 0
        
        while start < len(sysex_data):
            # Find next F0 (SysEx start)
            if sysex_data[start] != 0xF0:
                start += 1
                continue
            
            # Find corresponding F7 (SysEx end)
            end = start + 1
            while end < len(sysex_data) and sysex_data[end] != 0xF7:
                end += 1
            
            if end < len(sysex_data):
                # Include the F7 byte
                messages.append(bytearray(sysex_data[start:end + 1]))
                start = end + 1
            else:
                break
        
        return messages
    
    def _control_index_to_position(self, control_index: int) -> Tuple[Optional[int], Optional[int]]:
        """Convert control index to (row, col) position in device layout."""
        # Create flat list of all positions in order
        all_positions = []
        for section_name in ['knobs_top', 'knobs_mid', 'knobs_bot', 'sliders', 'buttons_top', 'buttons_bot']:
            all_positions.extend(DEVICE_LAYOUT[section_name])
        
        if 0 <= control_index < len(all_positions):
            return all_positions[control_index]
        return None, None
    
    def _apply_colors_to_sysex(self, original_data: bytes, output_path: Path):
        """Apply current color mapping to SysEx data and save to file."""
        messages = self._split_sysex_messages(original_data)
        
        # Apply colors to each control
        for control_index, (msg_index, _cc_pos, _ch_pos, color_pos, _flag_pos) in enumerate(CONTROLS):
            if msg_index < len(messages) and color_pos < len(messages[msg_index]):
                # Get color for this control
                row, col = self._control_index_to_position(control_index)
                if row is not None and col is not None:
                    color_name = self.colors.get((row, col), 'off')
                    color_value = COLOR_MAP.get(color_name, COLOR_MAP['off'])
                    messages[msg_index][color_pos] = color_value
        
        # Write the modified data back to file
        combined_data = b"".join(bytes(msg) for msg in messages)
        output_path.write_bytes(combined_data)
        logger.debug(f"Applied LED colors to {output_path}")

    @staticmethod
    def show_menu(prompt: str, options: List[str]) -> int:
        """Show a simple curses menu and return selected index."""
        def _menu_main(stdscr):
            curses.curs_set(0)  # Hide cursor
            selected = 0
            
            while True:
                stdscr.clear()
                
                # Draw prompt
                stdscr.addstr(0, 0, prompt)
                stdscr.addstr(1, 0, "")  # Empty line
                
                # Draw options
                for i, option in enumerate(options):
                    if i == selected:
                        stdscr.addstr(2 + i, 2, f"> {option}", curses.A_REVERSE)
                    else:
                        stdscr.addstr(2 + i, 2, f"  {option}")
                
                # Draw controls
                stdscr.addstr(4 + len(options), 0, "")  # Empty line
                stdscr.addstr(5 + len(options), 0, "Navigate: ↑↓ or j/k  Select: Enter")
                
                stdscr.refresh()
                
                key = stdscr.getch()
                
                if key == curses.KEY_UP or key == ord('k'):
                    selected = max(0, selected - 1)
                elif key == curses.KEY_DOWN or key == ord('j'):
                    selected = min(len(options) - 1, selected + 1)
                elif key == ord('\n') or key == ord('\r'):
                    return selected
                elif key == ord('q') or key == ord('Q'):
                    return -1  # Cancelled
        
        try:
            return curses.wrapper(_menu_main)
        except KeyboardInterrupt:
            return -1  # Cancelled

    def edit_multiple_templates(self, template_paths: List[Path]) -> bool:
        """Edit LED colors for multiple templates sequentially."""
        for i, template_path in enumerate(template_paths):
            print(f"\nConfiguring LED colors for {template_path.name} ({i+1}/{len(template_paths)})")
            
            try:
                # Read and extract colors from template
                template_data = template_path.read_bytes()
                self._extract_colors_from_sysex(template_data)
                
                # Run editor for this template
                color_map = self.run_interactive_editor()
                
                if color_map:
                    # Apply and save changes
                    self._apply_colors_to_sysex(template_data, template_path)
                    print(f"LED colors saved for {template_path.name}")
                else:
                    print(f"LED color editing cancelled for {template_path.name}")
                    # Ask if user wants to continue with remaining templates
                    if i < len(template_paths) - 1:
                        choice = self.show_menu("Continue with remaining templates?", ["Yes", "No"])
                        if choice != 0:  # Not "Yes"
                            return False
                
            except Exception as e:
                logger.error(f"Failed to edit {template_path.name}: {e}")
                # Ask if user wants to continue
                if i < len(template_paths) - 1:
                    choice = self.show_menu("Error occurred. Continue with remaining templates?", ["Yes", "No"])
                    if choice != 0:  # Not "Yes"
                        return False
        
        return True
    
    def _curses_main(self, stdscr):
        """Main curses interface."""
        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        
        # Setup color pairs - map colors to appropriate terminal colors
        color_pairs = {}
        for i, color_name in enumerate(COLOR_NAMES, 1):
            if color_name == 'red':
                curses.init_pair(i, curses.COLOR_RED, -1)
            elif color_name in ['orange', 'yellow']:
                curses.init_pair(i, curses.COLOR_YELLOW, -1)
            elif color_name in ['lime', 'green']:
                curses.init_pair(i, curses.COLOR_GREEN, -1)
            elif color_name in ['turquoise', 'cyan']:
                curses.init_pair(i, curses.COLOR_CYAN, -1)
            elif color_name == 'light_blue':
                curses.init_pair(i, curses.COLOR_BLUE, -1)  # Light blue -> blue
            elif color_name in ['blue', 'dark_blue']:
                curses.init_pair(i, curses.COLOR_BLUE, -1)
            elif color_name in ['purple', 'fuchsia']:
                curses.init_pair(i, curses.COLOR_MAGENTA, -1)
            elif color_name == 'pink':
                curses.init_pair(i, curses.COLOR_RED, -1)  # Pink -> red (closest match)
            elif color_name == 'off':
                curses.init_pair(i, curses.COLOR_WHITE, -1)
            else:
                curses.init_pair(i, curses.COLOR_WHITE, -1)
            color_pairs[color_name] = i
        
        # Hide cursor
        curses.curs_set(0)
        
        while True:
            stdscr.clear()
            self._draw_interface(stdscr, color_pairs)
            stdscr.refresh()
            
            key = stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key == ord('s') or key == ord('S') or key == ord('\n') or key == ord('\r'):
                return  # Save and exit
            elif key == curses.KEY_UP:
                # Skip slider row (row 3)
                if self.cursor_row == 4:  # Moving up from buttons to knobs
                    self.cursor_row = 2  # Skip slider row, go to bottom knobs
                else:
                    self.cursor_row = max(0, self.cursor_row - 1)
            elif key == curses.KEY_DOWN:
                # Skip slider row (row 3)  
                if self.cursor_row == 2:  # Moving down from knobs to buttons
                    self.cursor_row = 4  # Skip slider row, go to top buttons
                else:
                    self.cursor_row = min(5, self.cursor_row + 1)
            elif key == curses.KEY_LEFT:
                self.cursor_col = max(0, self.cursor_col - 1)
            elif key == curses.KEY_RIGHT:
                self.cursor_col = min(7, self.cursor_col + 1)
            elif key == ord(' ') or key == ord('c') or key == ord('C') or key == ord('\t'):
                # Cycle color forward
                self.current_color_idx = (self.current_color_idx + 1) % len(COLOR_NAMES)
                current_color = COLOR_NAMES[self.current_color_idx]
                self.colors[(self.cursor_row, self.cursor_col)] = current_color
            elif key == 353 or key == 351:  # Shift+Tab or Shift+Space (varies by system)
                # Cycle color backward
                self.current_color_idx = (self.current_color_idx - 1) % len(COLOR_NAMES)
                current_color = COLOR_NAMES[self.current_color_idx]
                self.colors[(self.cursor_row, self.cursor_col)] = current_color
            elif key == ord('r') or key == ord('R'):
                # Paint entire row with current control's color
                current_color = self.colors.get((self.cursor_row, self.cursor_col), 'off')
                for col in range(8):
                    self.colors[(self.cursor_row, col)] = current_color
            elif key == ord('o') or key == ord('O'):
                # Paint entire column with current control's color  
                current_color = self.colors.get((self.cursor_row, self.cursor_col), 'off')
                for row in range(6):
                    self.colors[(row, self.cursor_col)] = current_color
            elif key == ord('x') or key == ord('X'):
                # Turn all controls off
                for row in range(6):
                    for col in range(8):
                        self.colors[(row, col)] = 'off'
    
    def _draw_interface(self, stdscr, color_pairs):
        """Draw the device layout and interface."""
        stdscr.addstr(0, 0, "┌─ Launch Control XL 3 LED Color Mapper ─────┐")
        
        # Draw knob rows
        for i, section_name in enumerate(['knobs_top', 'knobs_mid', 'knobs_bot']):
            y = i + 2
            stdscr.addstr(y, 0, "│ ")
            
            for col in range(8):
                color_name = self.colors.get((i, col), 'off')
                color_pair = color_pairs.get(color_name, 0)
                
                # Highlight cursor position
                abbrev = COLOR_ABBREV.get(color_name, color_name[:2].upper())
                if self.cursor_row == i and self.cursor_col == col:
                    attr = curses.A_REVERSE | curses.color_pair(color_pair)
                    display = f"[{abbrev}]"
                else:
                    attr = curses.color_pair(color_pair)
                    display = f" {abbrev} "
                
                stdscr.addstr(y, 2 + col * 5, display, attr)
            
            stdscr.addstr(y, 44, " │")
        
        # Draw sliders
        y = 5
        stdscr.addstr(y, 0, "│ ")
        for col in range(8):
            color_name = self.colors.get((3, col), 'off')
            color_pair = color_pairs.get(color_name, 0)
            
            if self.cursor_row == 3 and self.cursor_col == col:
                attr = curses.A_REVERSE | curses.color_pair(color_pair)
                display = "[██]"
            else:
                attr = curses.color_pair(color_pair)
                display = " ██ "
            
            stdscr.addstr(y, 2 + col * 5, display, attr)
        stdscr.addstr(y, 44, " │")
        
        # Draw button rows
        for i, section_name in enumerate(['buttons_top', 'buttons_bot']):
            y = i + 6
            stdscr.addstr(y, 0, "│ ")
            
            for col in range(8):
                color_name = self.colors.get((i + 4, col), 'off')
                color_pair = color_pairs.get(color_name, 0)
                
                abbrev = COLOR_ABBREV.get(color_name, color_name[:2].upper())
                if self.cursor_row == i + 4 and self.cursor_col == col:
                    attr = curses.A_REVERSE | curses.color_pair(color_pair)
                    display = f"[{abbrev}]"
                else:
                    attr = curses.color_pair(color_pair)
                    display = f" {abbrev} "
                
                stdscr.addstr(y, 2 + col * 5, display, attr)
            
            stdscr.addstr(y, 44, " │")
        
        # Draw controls
        stdscr.addstr(8, 0, "│                                           │")
        stdscr.addstr(9, 0, "│ Navigate: ↑↓←→  Cycle: SPACE/TAB/C       │")
        stdscr.addstr(10, 0, "│ Row: R  Column: O  All Off: X             │")
        stdscr.addstr(11, 0, "│ Save: S/Enter  Quit: Q                    │")
        
        # Current selection info
        current_color = self.colors.get((self.cursor_row, self.cursor_col), 'off')
        stdscr.addstr(12, 0, f"│ Current: Row {self.cursor_row+1}, Col {self.cursor_col+1} ({current_color})".ljust(43) + " │")
        stdscr.addstr(13, 0, "└───────────────────────────────────────────┘")
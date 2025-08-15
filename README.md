# Novation Launch Control XL 3 SysEx Template Generator

Configurable MIDI template generator for Novation Launch Control XL 3 devices. Written in Python3.11.

## Overview

This tool generates custom MIDI control templates for the Novation Launch Control XL 3, with configurable template count, channel assignment modes, and CC numbering strategies.

This tool was created to generate custom unique templates for mapping Serum 2 parameters without being confined to the GUI interface Novation Components provides. While the official interface is quite good for what it is, greater flexibility was needed for complex parameter mapping scenarios that it could not provide.

**How it works:** The tool is built by reverse-engineering the binary .syx files that Novation Components generates when using Save > Download on a custom mode. The Python script contains hardcoded default template data extracted from these files, then programmatically modifies specific byte positions to customize CC assignments, MIDI channels, and other parameters based on configuration.

## Features

- **Configurable Templates**: Generate 1-15 templates (default: 15)
- **Channel Modes**: Per-template channels (T01=Ch1, T02=Ch2) or global channel for all
- **CC Numbering**: Restart at CC 1 per template, or continuous CC 1-127 across templates  
- **Safe CC Range**: Automatically enforces safe CC range 13-120 (avoids reserved MIDI CCs)
- **Interactive LED Color Mapping**: Visual interface for customizing LED colors
- **Sequential Color Editing**: Configure LED colors for multiple templates in workflow
- **Individual Template Editing**: Edit LED colors for specific template files
- **Default Toggle Mode**: Bottom two button rows automatically set to toggle mode
- **Backward Compatible**: v6 defaults maintained when no flags specified
- **Robust Error Handling**: Input validation and comprehensive error messages
- **Flexible Output**: Customizable filename prefix and output directory

## Quick Start

### Installation
```bash
# No installation required - standalone Python 3 script
python3 main.py --help
```

**Note:** Windows users need to install `windows-curses` for the LED color mapper: `pip install windows-curses`

### Basic Usage
```bash
# Generate default templates (15 templates, per-template channels, CC restart per template)
python3 main.py

# Custom prefix
python3 main.py --output-prefix "MyController"

# Generate 8 templates with continuous CC numbering
python3 main.py --template-count 8 --cc-continuous

# All templates on MIDI channel 5 with verbose logging
python3 main.py --global-channel 5 --verbose

# Generate templates with LED color configuration workflow
python3 main.py --template-count 4
# After generation, you'll be prompted to configure LED colors for each template

# Edit LED colors for specific template file
python3 main.py --leds --template-name Serum_T03.syx
```

### Advanced Usage
```bash
# 15 templates, all on channel 1, continuous CCs 1-127
python3 main.py --template-count 15 --global-channel 1 --cc-continuous

# 4 templates for specific synth setup
python3 main.py --template-count 4 --output-prefix "Moog" --output-dir ./moog_templates
```

## Loading Templates into Your Device

**⚠️ Important:** You cannot load `.syx` files without the **Novation Components** application. The device cannot load SysEx files directly.

### Getting Novation Components

**Web Version (Recommended):**
- Visit: https://components.novationmusic.com/launch-control-xl-3/custom-modes
- Uses Chrome's Web MIDI API (requires Chrome/Edge browser)
- No installation required

**Desktop Version:**
- Go to: https://components.novationmusic.com
- Click menu → "Install" to download the desktop app

**Account Requirements:**
- **No Novation account required** for basic template uploading
- Account only needed if you want to save templates to Novation's cloud

### Using Novation Components

1. **Connect Your Device**
   - Connect your Launch Control XL 3 via USB
   - Open **Novation Components** (web or desktop)

2. **Access Custom Modes**
   - Click on your Launch Control XL 3 device in Components
   - This opens the **Custom Modes** window

3. **Upload Template**
   - Click **"New Custom Mode"**
   - Select **"Upload Custom Mode"**
   - Browse to the `outputs/` folder
   - Select one of the generated `.syx` files (e.g., `Serum_T01.syx`)

4. **Deploy**
   - Click **"Send to Launch Control XL 3"** to deploy to your device
   - Optionally **Save** or **Save As** to store your custom mode for later use

5. **Select on Device**
   - Use your device's mode buttons to switch between loaded custom modes

## Command Line Options

### Core Options
```
  --output-prefix PREFIX    Filename prefix (default: Serum)
  --output-dir PATH        Output directory (default: ./outputs)
  --verbose, -v            Enable detailed logging
  --help                   Show help message
```

### Feature Flags
```
  --template-count N, -c   Number of templates to generate 1-15 (default: 15)
  --global-channel 1-16    Use same MIDI channel for all templates
  --cc-continuous          Use continuous CC 1-127 across templates
                          (default: restart at CC 1 per template)
  --leds, -l               Launch interactive LED color mapper
  --template-name FILE, -t Edit LED colors for specific template file
```

## LED Color Mapping

The tool includes an interactive LED color mapper that allows you to visually configure LED colors for each control on your Launch Control XL 3.

### Interactive Color Editor

The color mapper provides a visual representation of your device layout:

```
┌─ Launch Control XL 3 LED Color Mapper ─────┐
│ [OF]  OF   OF   OF   OF   OF   OF   OF   │  ← Top knobs
│  OF   OF   OF   OF   OF   OF   OF   OF   │  ← Middle knobs  
│  OF   OF   OF   OF   OF   OF   OF   OF   │  ← Bottom knobs
│  ██   ██   ██   ██   ██   ██   ██   ██   │  ← Sliders (not selectable)
│  OF   OF   OF   OF   OF   OF   OF   OF   │  ← Top buttons
│  OF   OF   OF   OF   OF   OF   OF   OF   │  ← Bottom buttons
│                                           │
│ Navigate: ↑↓←→  Change: SPACE/C           │
│ Row: R  Column: O  All Off: X             │
│ Save: S/Enter  Quit: Q                    │
│ Current: Row 1, Col 1 (off)               │
└───────────────────────────────────────────┘
```

### Navigation & Controls

- **Arrow Keys (↑↓←→)**: Navigate between controls (automatically skips slider row)
- **Space/C**: Cycle through available colors for current control
- **R**: Paint entire row with current control's color
- **O**: Paint entire column with current control's color  
- **X**: Turn all controls off (set to 'off' color)
- **S/Enter**: Save changes and exit
- **Q**: Quit without saving

### Available Colors

- **Red** (RD), **Orange** (OR), **Yellow** (YL), **Lime** (LM)
- **Green** (GR), **Turquoise** (TQ), **Cyan** (CY), **Light Blue** (LB)
- **Blue** (BL), **Dark Blue** (DB), **Purple** (PU), **Fuchsia** (FU)
- **Pink** (PK), **Off** (OF)

### Bulk Color Editing

The color mapper includes efficient bulk editing features:

1. **Row Programming**: Navigate to any control with your desired color, then press **R** to paint the entire row
2. **Column Programming**: Navigate to any control with your desired color, then press **O** to paint the entire column  
3. **Reset All**: Press **X** to turn all controls off instantly
4. **Copy Colors**: Navigate to a control with the color you want, then use **R** or **O** to spread it

**Example Workflow:**
- Set first knob to green, press **R** → entire top knob row becomes green
- Set first button to red, press **O** → entire first column becomes red
- Press **X** → everything turns off, start fresh

### LED Workflows

**Integrated Workflow (Recommended):**
```bash
# Generate templates, then configure LED colors
python3 main.py --template-count 4

# After templates are generated, you'll see:
# Configure LED colors?
#   > Yes
#     No
# 
# Select "Yes" to configure colors for each template sequentially
```

**Individual Template Editing:**
```bash
# Edit colors for a specific template file
python3 main.py --leds --template-name Serum_T03.syx

# Works with files in ./outputs/ directory
python3 main.py -l -t MyController_T01.syx
```

**Standalone Color Mapper:**
```bash
# Launch color mapper without template generation
python3 main.py --leds
```

### Usage Examples by Scenario

**Default Behavior (backward compatible):**
```bash
python3 main.py
# Creates: Serum_T01.syx (Ch1, CC1+), Serum_T02.syx (Ch2, CC1+), etc.
```

**Channel Modes:**
```bash
# Per-template channels (default): T01=Ch1, T02=Ch2, etc.
python3 main.py

# Global channel: All templates use Ch5
python3 main.py --global-channel 5
```

**CC Numbering Modes:**
```bash
# Restart per template (default): Each template starts at CC1
python3 main.py

# Continuous: CC1-127 spread across all templates
python3 main.py --cc-continuous
```

## File Structure

```
./
├── main.py                             # Main entry point
├── lib/                                # Library modules
│   ├── __init__.py                     # Package exports
│   ├── cli.py                          # CLI interface
│   ├── constants.py                    # Configuration data
│   ├── led_mapper.py                   # LED color mapper
│   └── sysex_generator.py              # SysEx template generator
├── outputs/                            # Generated templates
│   ├── Serum_T01.syx                  # Channel 1 template
│   ├── Serum_T02.syx                  # Channel 2 template
│   └── ...                            # T03-T15+
└── README.md                          # This file
```

## Recent Improvements

### Safe CC Range Enforcement
The tool now automatically enforces MIDI CC safety by constraining values to the range 13-120:

- **Avoids Reserved CCs**: CCs 1-12 are often reserved for mod wheel, breath control, etc.
- **Avoids Channel Mode Messages**: CCs 121-127 are MIDI channel mode messages that can interfere with device operation
- **Automatic Clamping**: Input values outside the safe range are automatically adjusted or disabled
- **Better Compatibility**: Ensures generated templates work reliably across different MIDI hosts and devices

### Default Toggle Mode for Buttons
Bottom two button rows (below sliders) now default to toggle mode:

- **Controls 32-47**: Top and bottom button rows automatically configured for toggle behavior
- **Improved Workflow**: Toggle mode is more commonly used for button controls in production scenarios
- **Based on Reverse Engineering**: Uses SysEx patterns observed in Novation Components output
- **Maintains Compatibility**: Knobs and sliders remain in continuous mode as expected

## Technical Details

- **SysEx Format**: Uses Novation's SysEx specification (downloaded from Components)
- **CC Range**: 13-120 (safe MIDI CC range, avoids reserved CCs 1-12 and channel mode CCs 121-127)
- **Channel Range**: 1-16 MIDI channels with 0-15 internal representation
- **Button Modes**: Bottom two button rows (below sliders) default to toggle mode for improved workflow
- **Template Count**: Configurable 1-15 templates (default: 15 templates)
- **LED Colors**: 15 available colors mapped to device-specific color values
- **Color Storage**: LED colors stored directly in SysEx template files
- **Interactive Interface**: Curses-based TUI for cross-platform compatibility
- **Error Handling**: Input validation and detailed error messages


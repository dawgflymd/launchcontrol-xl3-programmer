# Novation Launch Control XL 3 SysEx Template Generator

Configurable MIDI template generator for Novation Launch Control XL 3 devices. Written in Python3.11.

## Overview

This tool generates custom MIDI control templates for the Novation Launch Control XL 3, with configurable template count, channel assignment modes, and CC numbering strategies.

This tool was created to generate custom unique templates for mapping Serum 2 parameters without being confined to the GUI interface Novation Components provides. While the official interface is quite good for what it is, greater flexibility was needed for complex parameter mapping scenarios that it could not provide.

**How it works:** The tool is built by reverse-engineering the binary .syx files that Novation Components generates when using Save > Download on a custom mode. The Python script contains hardcoded default template data extracted from these files, then programmatically modifies specific byte positions to customize CC assignments, MIDI channels, and other parameters based on configuration.

## Features

- **Configurable Templates**: Generate any number of templates (default: 16)
- **Channel Modes**: Per-template channels (T01=Ch1, T02=Ch2) or global channel for all
- **CC Numbering**: Restart at CC 1 per template, or continuous CC 1-127 across templates  
- **Full CC Range**: Uses complete CC range 1-127
- **Backward Compatible**: v6 defaults maintained when no flags specified
- **Robust Error Handling**: Input validation and comprehensive error messages
- **Flexible Output**: Customizable filename prefix and output directory

## Quick Start

### Installation
```bash
# No installation required - standalone Python 3 script
python3 launchcontrol_xl3_programmer.py --help
```

### Basic Usage
```bash
# Generate default templates (16 templates, per-template channels, CC restart per template)
python3 launchcontrol_xl3_programmer.py

# Custom prefix
python3 launchcontrol_xl3_programmer.py --output-prefix "MyController"

# Generate 8 templates with continuous CC numbering
python3 launchcontrol_xl3_programmer.py --template-count 8 --cc-continuous

# All templates on MIDI channel 5 with verbose logging
python3 launchcontrol_xl3_programmer.py --global-channel 5 --verbose
```

### Advanced Usage
```bash
# 32 templates, all on channel 1, continuous CCs 1-127
python3 launchcontrol_xl3_programmer.py --template-count 32 --global-channel 1 --cc-continuous

# 4 templates for specific synth setup
python3 launchcontrol_xl3_programmer.py --template-count 4 --output-prefix "Moog" --output-dir ./moog_templates
```

## Loading Templates into Your Device

### Using Novation Components

1. **Connect Your Device**
   - Connect your Launch Control XL 3 via USB
   - Launch **Novation Components** application

2. **Access Custom Modes**
   - Click on your Launch Control XL 3 device in Components
   - This opens the **Custom Modes** window

3. **Upload Template**
   - Click **"New Custom Mode"**
   - Select **"Upload Custom Mode"**
   - Browse to the `outputs/` folder
   - Select one of the generated `.syx` files (e.g., `Serum_T01.syx`)

4. **Save and Deploy**
   - **Save** or **Save As** to store your custom mode
   - Click **"Send to Launch Control XL 3"** to deploy to your device

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
  --template-count N       Number of templates to generate (default: 16)
  --global-channel 1-16    Use same MIDI channel for all templates
  --cc-continuous          Use continuous CC 1-127 across templates
                          (default: restart at CC 1 per template)
```

### Usage Examples by Scenario

**Default Behavior (backward compatible):**
```bash
python3 launchcontrol_xl3_programmer.py
# Creates: Serum_T01.syx (Ch1, CC1+), Serum_T02.syx (Ch2, CC1+), etc.
```

**Channel Modes:**
```bash
# Per-template channels (default): T01=Ch1, T02=Ch2, etc.
python3 launchcontrol_xl3_programmer.py

# Global channel: All templates use Ch5
python3 launchcontrol_xl3_programmer.py --global-channel 5
```

**CC Numbering Modes:**
```bash
# Restart per template (default): Each template starts at CC1
python3 launchcontrol_xl3_programmer.py

# Continuous: CC1-127 spread across all templates
python3 launchcontrol_xl3_programmer.py --cc-continuous
```

## File Structure

```
./
├── launchcontrol_xl3_programmer.py      # Main script
├── outputs/                             # Generated templates
│   ├── Serum_T01.syx                   # Channel 1 template
│   ├── Serum_T02.syx                   # Channel 2 template
│   └── ...                             # T03-T16+
└── README.md                           # This file
```

## Technical Details

- **SysEx Format**: Uses Novation's SysEx specification (downloaded from Components)
- **CC Range**: 1-127 (full MIDI CC range)
- **Channel Range**: 1-16 MIDI channels with 0-15 internal representation
- **Template Count**: Configurable (default: 16 templates)
- **Error Handling**: Input validation and detailed error messages


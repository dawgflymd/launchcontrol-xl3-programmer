"""Command line interface for Launch Control XL 3 SysEx Template Generator."""

import argparse
import logging
import sys
from pathlib import Path

from .sysex_generator import SysExTemplateGenerator, ChannelMode, CCMode
from .led_mapper import LEDColorMapper
from .constants import DEFAULT_TEMPLATE_COUNT, DEFAULT_MIN_CC_VALUE, MIN_CC_VALUE, MAX_CC_VALUE

logger = logging.getLogger(__name__)


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
        "--template-count", "-c",
        type=int,
        default=DEFAULT_TEMPLATE_COUNT,
        help=f"Number of templates to generate 1-15 (default: {DEFAULT_TEMPLATE_COUNT})"
    )
    
    # Channel mode options (mutually exclusive group)
    channel_group = parser.add_mutually_exclusive_group()
    channel_group.add_argument(
        "--global-channel", "-g",
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
    
    parser.add_argument(
        "--min-cc-value",
        type=int,
        choices=range(MIN_CC_VALUE, MAX_CC_VALUE + 1),
        metavar=f"{MIN_CC_VALUE}-{MAX_CC_VALUE}",
        default=DEFAULT_MIN_CC_VALUE,
        help=f"Starting CC number (default: {DEFAULT_MIN_CC_VALUE})"
    )
    
    parser.add_argument(
        "--cc-reverse",
        action="store_true", 
        help="Start at CC 127 and assign backwards (overrides --min-cc-value)"
    )
    
    # LED color mapper
    parser.add_argument(
        "--leds", "-l",
        action="store_true",
        help="Launch interactive LED color mapper"
    )
    
    # Template file editing
    parser.add_argument(
        "--template-name", "-t",
        type=str,
        help="Edit LED colors for specific template file (e.g., Serum_T03.syx)"
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
    
    # Handle LED color mapper
    if args.leds:
        if args.template_name:
            # Edit specific template file
            try:
                template_path = Path(args.template_name)
                if not template_path.is_absolute():
                    # Always search in outputs directory for relative paths
                    template_path = Path("./outputs") / template_path
                
                if not template_path.exists():
                    logger.error(f"Template file not found: {template_path}")
                    sys.exit(1)
                
                mapper = LEDColorMapper()
                color_map = mapper.edit_template_file(template_path)
                if color_map:
                    print(f"LED colors updated for {template_path.name}")
                else:
                    print("LED color editing cancelled.")
            except Exception as e:
                logger.error(f"Template editing failed: {e}")
                sys.exit(1)
        else:
            # Run standalone color mapper
            try:
                mapper = LEDColorMapper()
                color_map = mapper.run_interactive_editor()
                if color_map:
                    print("LED color mapping saved. Integration with SysEx generation coming soon...")
                else:
                    print("LED color mapping cancelled.")
            except Exception as e:
                logger.error(f"LED color mapper failed: {e}")
                sys.exit(1)
        return
    
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
            output_dir=args.output_dir,
            min_cc_value=args.min_cc_value,
            cc_reverse=args.cc_reverse
        )
        
        print(f"Successfully generated {len(generated_files)} templates in {args.output_dir}:")
        for file_path in generated_files:
            print(f"  - {file_path.name}")
        
        # Prompt for LED color configuration
        if generated_files:
            print("\n")  # Add some space
            try:
                mapper = LEDColorMapper()
                choice = mapper.show_menu("Configure LED colors?", ["Yes", "No"])
                
                if choice == 0:  # Yes
                    print("\nStarting LED color configuration...")
                    success = mapper.edit_multiple_templates(generated_files)
                    if success:
                        print("\nLED color configuration completed for all templates!")
                    else:
                        print("\nLED color configuration stopped.")
                else:
                    print("Skipping LED color configuration.")
            except Exception as e:
                logger.error(f"LED color configuration failed: {e}")
            
    except Exception as e:
        logger.error(f"Template generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
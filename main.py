#!/usr/bin/env python3

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Import and run CLI
from lib.cli import main

if __name__ == "__main__":
    main()
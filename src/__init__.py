"""
Dev Crew SDLC WebUI package initialization.

Configures application-wide logging for development and debugging.
"""

import logging
import sys

# Configure root logger for the entire application
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)
logger.debug("Dev Crew SDLC WebUI package initialized - logging configured")

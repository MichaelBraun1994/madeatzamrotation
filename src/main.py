"""
Main of Made@ZAM Rotation
"""

import logging
import sys
from posts_cache import create_post_cache


def setup_logger():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    return logging.getLogger(__name__)


def main():
    logger = setup_logger()
    create_post_cache(logger)


if __name__ == "__main__":
    main()

"""
Flask app
"""

import argparse

from server import start_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Webservice that rotates posts of the Made@ZAM mattermost channel to display projects as polaroids."
    )
    parser.add_argument("settings_path", help="Path to the settings file")
    args = parser.parse_args()

    start_server(args.settings_path)

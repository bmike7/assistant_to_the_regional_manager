"""Authentication utilities for ATTRM."""

import os
from contextlib import suppress
from getpass import getpass
from textwrap import dedent

import click
import keyring

from .cli import abort, cli

SERVICE_NAME = "attrm"
KEY_NAME = "anthropic_api_key"


def get_api_key() -> str | None:
    """
    Get the Anthropic API key from keyring or environment variable.

    Priority:
    1. ANTHROPIC_API_KEY environment variable (for compatibility)
    2. Stored key in keyring
    """
    if env_key := os.environ.get("ANTHROPIC_API_KEY"):
        return env_key
    if keyring_key := keyring.get_password(SERVICE_NAME, KEY_NAME):
        return keyring_key
    abort("No API key found. Please run: `attrm login`")


def set_api_key(api_key: str) -> None:
    """Store the Anthropic API key in keyring."""
    keyring.set_password(SERVICE_NAME, KEY_NAME, api_key)


def delete_api_key() -> None:
    """Delete the Anthropic API key from keyring."""
    with suppress(keyring.errors.PasswordDeleteError):
        keyring.delete_password(SERVICE_NAME, KEY_NAME)


@cli.command(help="Set up authentication with Anthropic API")
def login() -> None:
    """
    Interactive setup for Anthropic API authentication.
    Stores the API key securely using keyring.
    """
    msg = dedent("""
    Anthropic API Key Setup

    To get your API key:
      1. Go to https://console.anthropic.com/
      2. Sign in or create an account
      3. Navigate to API Keys section
      4. Create a new API key or copy an existing one

    """).lstrip()
    click.echo(msg)
    if not (api_key := getpass("Enter your Anthropic API key: ").strip()):
        abort("No API key provided. Authentication cancelled.")

    set_api_key(api_key)
    msg = dedent("""
    API key stored securely!

    You can now use attrm commands that require API access.
    """).strip()
    click.echo(msg)


@cli.command(help="Remove stored authentication credentials")
def logout() -> None:
    """Remove the stored Anthropic API key."""
    stored_key = keyring.get_password(SERVICE_NAME, KEY_NAME)

    if not stored_key:
        abort("No stored credentials found.")

    if click.confirm("Are you sure you want to remove your stored API key?"):
        delete_api_key()
        click.echo("API key removed successfully.")
    else:
        click.echo("Logout cancelled.")

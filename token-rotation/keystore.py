#!/usr/bin/env python3

"""
This module provides functions for securely storing and retrieving passwords using the keyring package.
"""

import keyring
import os

#This function stores the password for the given service and username using the keyring library. The password is read from a local file named auth.txt.
def store_password(service: str, username: str) -> None:
    """
    Store a password for a given service and username in the keyring.

    Args:
        service (str): The name of the service for which the password is being stored.
        username (str): The username associated with the password being stored.

    Returns:
        None
    """

    password = os.environ.get("AUTH_PASSWORD")
    
    keyring.set_password(service, username, password)

#This function retrieves the password for the given service and username using the keyring library.
def get_password(service: str, username: str) -> str:
    """
    Retrieve a password for a given service and username from the keyring.

    Args:
        service (str): The name of the service for which the password is being retrieved.
        username (str): The username associated with the password being retrieved.

    Returns:
        str: The password associated with the given service and username.
    """

    password = keyring.get_password(service, username)
    return password

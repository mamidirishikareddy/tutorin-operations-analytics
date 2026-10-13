# ui/auth_helper.py

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

def initialize_authenticator():
    config_path = os.path.join(os.path.dirname(__file__), "../.streamlit_auth_config.yaml")
    with open(config_path, "r") as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        preauthorized=config.get("preauthorized", {})
    )

    return authenticator

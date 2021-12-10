import os

import pandas as pd
import streamlit as st
from streamlit.legacy_caching import clear_cache


def get_password(df: pd.DataFrame) -> pd.DataFrame:
    """Return true if password is correct"""
    with st.expander("Filter"):
        password = st.text_input("Enter a password", type="password")
        # TODO: check if this flag works
        if os.environ.get("DEBUG"):
            caching_button()
            return df
        if password == os.environ.get("PSW"):
            caching_button()
            return df
    df = df[df.Calendar != "Work"]
    return df


def caching_button():
    btn = st.button("Clear cache")
    if btn:
        clear_cache()
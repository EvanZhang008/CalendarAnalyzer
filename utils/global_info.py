import pandas as pd
import streamlit as st


def global_info(df: pd.DataFrame) -> None:
    days = len(df["DAY"].unique())
    n_act = len(df)
    st.markdown(
        # Trailing spaces removed by pre-commit
        f"""
        🟢 Beginning date: Dec 2019 - Dec 2022 (3 years, 1 month)

        ⌛ Elapsed days: {days}

        🧮 Total activities: {n_act} (~{n_act/days:.0f} per day)
        """
    )

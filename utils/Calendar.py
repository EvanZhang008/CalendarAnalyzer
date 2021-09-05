import json
import requests
import jicson
import streamlit as st
import pandas as pd
import tempfile
import copy
import warnings
import datetime
import os
from utils.sort_df import sort_by_name


class Calendar:
    """Google calendar class"""

    def __init__(self):
        # Dictionary containing calendars
        cached_calendars = self._download_cals()
        self.calendars = copy.deepcopy(cached_calendars)
        self._edit_datetime()

    @st.cache
    def _download_cals(self):
        """Download calendars"""
        cals = []
        links = os.getenv("CALENDAR_LINKS")
        assert links, "Environment variable CALENDAR_LINKS not found"
        links = json.loads(links)
        for link in links:
            cal = self._download_cal(link)
            cal = cal["VCALENDAR"][0]
            cal_name = cal["X-WR-CALNAME"]
            cal_content = pd.DataFrame(
                data=cal["VEVENT"], columns=["SUMMARY", "DTSTART", "DTEND"]
            )
            cal_content["Calendar"] = cal_name
            cals.append(cal_content)
        return pd.concat(cals)

    def _download_cal(self, link):
        """Download ics from Google Calendar, return json"""
        ics = requests.get(link).text
        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write(str(ics))
            json = jicson.fromFile(f.name)
        return json

    def _edit_datetime(self):
        # Transforms dates in date format
        df = self.calendars
        df["DTSTART"] = pd.to_datetime(df["DTSTART"])
        df["DTEND"] = pd.to_datetime(df["DTEND"])

        # Discard before date
        df = df[df["DTSTART"] > "2019-12"]  # Real is 2019-11-16
        # Discard this month
        month = datetime.datetime.today().strftime("%Y-%m")
        df = df[df["DTSTART"] < month]

        # Calculates duration from start to end like:
        #     Groceries	0 days 01:00:00
        # Transform to minutes:
        #     Groceries	1
        df["Duration"] = df["DTEND"] - df["DTSTART"]
        df["Duration"] = df["Duration"].dt.total_seconds() / 60 / 60

        # Remove daily/mulitple days activities and NaN
        self.calendars = df[df.Duration > 0]

    def by_activity(self, cal_sel=None):
        df = self.calendars
        if cal_sel is not None:
            df = df.loc[df["Calendar"] == cal_sel]
        df = df.sort_values(by=["Duration"], ascending=False)
        df = df.groupby(["Calendar", "SUMMARY"]).sum()
        return df.sort_values(by=["Duration"], ascending=False)

    def by_month(self, filter, cal_sel=None):
        df = self.calendars
        df = self._filter_by_cal(df, cal_sel)
        return self._by_period(df, "M", filter)

    def by_week(self, filter, cal_sel=None):
        df = self.calendars
        df = self._filter_by_cal(df, cal_sel)
        return self._by_period(df, "W", filter)

    def _filter_by_cal(self, df: pd.DataFrame, cal_sel: str) -> pd.DataFrame:
        """Filter by selected calendar in the dropdown (Eat, Sport)

        Args:
            cal_sel (str): Selected calendar

        Returns:
            pd.DataFrame: Dataframe smandruppato
        """
        if cal_sel:
            df = df.loc[df["Calendar"] == cal_sel]
            df = df.rename(columns={"SUMMARY": "Activity"})
        else:
            df = df.rename(columns={"Calendar": "Activity"})
        return df

    def _by_period(self, df: pd.DataFrame, period: str, flt: bool):
        """Smandruppa the dataframe

        Args:
            df (pd.DataFrame): Input dataframe
            period (str): Period like week (w) or month (m)
            flt (bool): Filter

        Returns:
            pd.DataFrame: Dataframe smandruppato
        """
        # Hide warning: Converting to PeriodArray/Index representation
        # will drop timezone information.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df["Period"] = df["DTSTART"].dt.to_period(period).astype("str")

        # 2020-11 Breakfast     31.00
        #         Dinner        33.00
        #         Lunch         26.50
        df = df.groupby(["Period", "Activity"]).sum()
        df = df.reset_index()

        # Normalization by number of days is done only in month
        if period == "M":
            df = self._get_normalized_duration(df)
        df = sort_by_name(df, period, flt)
        return df

    def _get_normalized_duration(self, df):
        """
        Normalize activity duration by number of days in the month
        e.g. 10h activity in February -> 10h * 30 / 28 = 10.71h
        """
        df_date = pd.DataFrame(df["Period"])
        df_date["Period"] = pd.to_datetime(df_date["Period"])
        df_date["DaysInMonth"] = df_date["Period"].dt.daysinmonth
        df["Duration"] = df["Duration"] * 30 / df_date["DaysInMonth"]
        return df

"""Streamlit entry point.

TODO(Day 6): auth (access code) + chat UI + trace sidebar + session rate limit.
"""

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Xiehaoyu-Agent", layout="wide")
    st.title("Xiehaoyu-Agent")
    st.info("Scaffold initialized. Implementation coming per Day 1~8 plan.")


if __name__ == "__main__":
    main()

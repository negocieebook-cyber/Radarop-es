"""Navegação programática entre páginas."""

from __future__ import annotations

import streamlit as st


def go_to(page_name: str) -> None:
    st.session_state["page"] = page_name
    st.rerun()


# utils/navigation.py
import streamlit as st
import os

def create_navigation():
    st.sidebar.title("Navigation")
    
    # Main categories
    categories = ["Claims", "Drawings"]
    selected_category = st.sidebar.selectbox("Select Category", categories)
    
    return selected_category

def get_page_by_name(name):
    pages = {
        "Tool": "pages.Tool"
    }
    return pages.get(name)
import streamlit as st
import hw1
import hw2


# Title for the main page
st.title('HOMEWORK MANAGER')

# Sidebar selection
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", ["Home", "Lab 1", "Lab 2", "Lab 3"])

# Home Page
if selection == "Home":
    st.write("""
    ## Welcome to the Dhruv's Streamlit Labs App
    Use the sidebar to navigate to different labs.
    """)

# Lab 1 Page
elif selection == "Lab 1":
    hw1.run()

# Lab 2 Page
elif selection == "Lab 2":
    hw2.run()

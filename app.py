import streamlit as st
import hw1
import hw2
import hw3
import hw5


# Title for the main page
st.title('HOMEWORK MANAGER')

# Sidebar selection
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", ["Home", "Homework 1", "Homework 2", "Homework 3", "Homework 5"])

# Home Page
if selection == "Home":
    st.write("""
    ## Welcome to the Dhruv's Streamlit Homework App
    Use the sidebar to navigate to different Homework.
    """)

# HW 1 Page
elif selection == "Homework 1":
    hw1.run()

# HW 2 Page
elif selection == "Homework 2":
    hw2.run()

elif selection == "Homework 3":
    hw3.run()


elif selection == "Homework 5":
    hw5.run()
import streamlit as st

st.set_page_config(
    page_title="OS Professor Test",
    page_icon="🎓"
)

st.title("🎓 OS Professor")
st.success("Streamlit is working correctly!")

question = st.chat_input("Ask something")

if question:
    st.write("You asked:", question)
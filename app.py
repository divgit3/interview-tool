# Import OpenAI and Streamlit
from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Streamlit Chat", page_icon="💬", layout="wide")
st.title("Chatbot")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False


def complete_setup():
    """
    Mark the setup as complete
    """
    st.session_state.setup_complete = True

def show_feedback():
    """
    Show feedback form
    """
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:
    st.subheader('Personal Information', divider='rainbow')

    if "txtname" not in st.session_state:
        st.session_state.txtname = ""
    if "txtexperience" not in st.session_state:
        st.session_state.txtexperience = ""
    if "txtskills" not in st.session_state:
        st.session_state.txtskills = ""

    txtname = st.text_input(label = 'Name', max_chars=40, value = st.session_state["txtname"], placeholder='Enter your name..')    
    txtexperience = st.text_area(label = 'Experience', max_chars=200, value=st.session_state["txtexperience"], height=None, placeholder='Describe your experience..')
    txtskills = st.text_area(label = 'Skills', max_chars=200, value=st.session_state["txtskills"], height=None, placeholder='Enter your skills..')

    # st.write(f"Your Name: {txtname}")
    # st.write(f"Your Experience: {txtexperience}")
    # st.write(f"Your Skills: {txtskills}")

    st.subheader('Company and Position', divider='rainbow')

    if "level" not in st.session_state:
        st.session_state.level = ""
    if "position" not in st.session_state:
        st.session_state.position = ""
    if "company" not in st.session_state:
        st.session_state.company = ""


    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio("Choose level", key="visibility", options=["Junior", "Mid-level", "Senior"])
    with col2:
        st.session_state["position"] = st.selectbox("Select a Position", options=["Data Scientist", "Data Analyst", "Data Engineer", "Machine Learning Engineer", "BI Analyst", "Financial Analyst"])
    st.session_state["company"] = st.selectbox("Choose a Company", options=["Udemy", "Amazon", "Meta", "Nestle", "LinkedIn", "Spotify", "Netflix", "Google", "Apple"])

    st.write(f"Your Information:  {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}")

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Set up complete. Starting interview...")


if st.session_state.setup_complete and not st.session_state.chat_complete and not st.session_state.feedback_shown:
    st.info(
        """ 
        Start by introducing yourself.
        """,
        icon="🤝"
    )
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o"

    # Entire chat history is stored in messages 
    if not st.session_state.messages:
        st.session_state.messages = [{"role": "system", 
        "content": (f"You are an HR executive that interviews an interviewee called {st.session_state['txtname']} \
        with experience {st.session_state['txtexperience']} and skills {st.session_state['txtskills']}.\
        You should interview the candidate for the position {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}."
        )}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer: ", max_chars = 1000):
            st.session_state.messages.append({"role":"user", "content":prompt})
            with st.chat_message("user"):
                st.markdown(prompt)   
            
            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                        ],
                        stream=True
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role":"assistant", "content":response})
            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching Feedback...")

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for feedback
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Generate feedback using the stored messages and write a system prompt for the feedback
    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overal Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questins.
              """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

import streamlit as st
import os
from openai import OpenAI
import time

st.title("Interactive Content Tutor")
st.subheader("Powered by OpenAI Assistants")

os.environ['OPENAI_API_KEY'] = st.secrets['openai']["open_ai_key"]
client = OpenAI(api_key=st.secrets['openai']["open_ai_key"])

@st.cache_resource
def get_assistant():
    my_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )
    return my_assistants.data[0].id # may need to change if he adds more assistants
a_id = get_assistant()

@st.cache_resource
def start_thread(_file):
    thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": "Here is the file mentioned in your instructions.",
                    "file_ids": [_file.id]
                }
            ]
        )
    return thread

def call_check_oai(thread):
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=a_id
    )

    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
    with st.spinner("Awaiting OpenAI response..."):
        while run.status != 'completed':
                time.sleep(3)
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

    return run

def upload_doc(bytes_data):
    file = client.files.create(
        file=bytes_data,
        purpose='assistants'
    )

    files = client.files.list().data
    with st.spinner('Uploading document...'):
        time.sleep(5)
        while file not in files:
                time.sleep(3)
                files = client.files.list().data
    return file

if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()

    file = upload_doc(bytes_data)
    thread = start_thread(file)
    run = call_check_oai(thread)
    first = client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value
    st.session_state.messages.append({"role":"assistant", "content":first})

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )

            run = call_check_oai(thread)
            res = client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.markdown(res)


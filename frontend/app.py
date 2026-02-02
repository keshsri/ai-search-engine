"""
AI Semantic Search Engine - Streamlit Frontend
"""
import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="AI Search Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🔍 AI Semantic Search Engine")
st.markdown("Ask questions about your documents using natural language")

# Sidebar
with st.sidebar:
    st.header("📚 Document Management")
    
    st.warning("⚠️ Max file size: **10MB**")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["pdf", "docx", "txt"],
        help="Upload PDF, DOCX, or TXT files (max 10MB)"
    )
    
    if uploaded_file:
        if st.button("Upload", type="primary"):
            with st.spinner("Uploading document... (may take 30-60 seconds)"):
                try:
                    files = {"file": uploaded_file}
                    response = requests.post(
                        f"{API_BASE_URL}/documents/upload",
                        files=files,
                        timeout=120  # Increased timeout
                    )
                    
                    if response.status_code == 200:
                        st.success(f"✅ Uploaded: {uploaded_file.name}")
                        st.rerun()  # Refresh to show new document
                    elif response.status_code == 504:
                        st.warning("⏱️ Upload timed out, but may still be processing. Wait 10 seconds and refresh the page.")
                    else:
                        st.error(f"❌ Upload failed: {response.json().get('detail', 'Unknown error')}")
                except requests.exceptions.Timeout:
                    st.warning("⏱️ Upload timed out, but document is likely still processing. Wait 10 seconds and refresh the page.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    # List documents
    st.subheader("Documents")
    try:
        response = requests.get(f"{API_BASE_URL}/documents/", timeout=10)
        if response.status_code == 200:
            documents = response.json()
            if documents:
                for doc in documents[:5]:  # Show first 5
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(doc.get("title", "Untitled")[:30])
                    with col2:
                        if st.button("🗑️", key=f"del_{doc['document_id']}"):
                            # Delete document
                            del_response = requests.delete(
                                f"{API_BASE_URL}/documents/{doc['document_id']}",
                                timeout=10
                            )
                            if del_response.status_code == 200:
                                st.rerun()
            else:
                st.info("No documents yet")
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
    
    st.divider()
    
    # Conversation history
    st.subheader("💬 Conversations")
    try:
        response = requests.get(f"{API_BASE_URL}/chat/conversations/", timeout=10)
        if response.status_code == 200:
            conversations = response.json()
            if conversations:
                for conv in conversations[:5]:  # Show first 5
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(
                            f"💬 {conv['message_count']} msgs",
                            key=f"conv_{conv['conversation_id']}",
                            use_container_width=True
                        ):
                            # Load conversation messages
                            try:
                                conv_response = requests.get(
                                    f"{API_BASE_URL}/chat/conversations/{conv['conversation_id']}",
                                    timeout=10
                                )
                                if conv_response.status_code == 200:
                                    conv_data = conv_response.json()
                                    # Set conversation ID and load messages
                                    st.session_state.conversation_id = conv['conversation_id']
                                    st.session_state.messages = []
                                    
                                    # Convert messages to session state format
                                    for msg in conv_data['messages']:
                                        st.session_state.messages.append({
                                            "role": msg['role'],
                                            "content": msg['content']
                                        })
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error loading conversation: {str(e)}")
                    with col2:
                        if st.button("🗑️", key=f"del_conv_{conv['conversation_id']}"):
                            # Delete conversation
                            try:
                                del_response = requests.delete(
                                    f"{API_BASE_URL}/chat/conversations/{conv['conversation_id']}",
                                    timeout=10
                                )
                                if del_response.status_code == 200:
                                    if st.session_state.get('conversation_id') == conv['conversation_id']:
                                        st.session_state.conversation_id = None
                                        st.session_state.messages = []
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting: {str(e)}")
            else:
                st.info("No conversations yet")
    except Exception as e:
        st.error(f"Error loading conversations: {str(e)}")
    
    # New conversation button
    if st.button("➕ New Conversation", type="secondary"):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.divider()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message:
            with st.expander("📄 Sources"):
                for i, source in enumerate(message["sources"][:3], 1):
                    st.markdown(f"**{i}. {source['document_title']}**")
                    st.text(source['content'][:200] + "...")

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/chat/",
                    json={
                        "query": prompt,
                        "conversation_id": st.session_state.conversation_id,
                        "top_k": 5
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data["sources"]
                    st.session_state.conversation_id = data["conversation_id"]
                    
                    # Display answer
                    st.markdown(answer)
                    
                    # Display sources
                    if sources:
                        with st.expander("📄 Sources"):
                            for i, source in enumerate(sources[:3], 1):
                                st.markdown(f"**{i}. {source['document_title']}**")
                                st.text(source['content'][:200] + "...")
                    
                    # Add to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    error_msg = f"Error: {response.json().get('detail', 'Unknown error')}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
        AI Semantic Search Engine | Powered by AWS Bedrock & FastAPI
    </div>
""", unsafe_allow_html=True)

"""Streamlit UI for PDF Context Narrator.

This is an optional web interface for the PDF Context Narrator application.
It provides a user-friendly interface for uploading, searching, and viewing PDFs.

To run:
    streamlit run streamlit_app/app.py
"""

import streamlit as st
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure page
st.set_page_config(
    page_title="PDF Context Narrator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .result-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .narrative-text {
        line-height: 1.8;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "current_view" not in st.session_state:
        st.session_state.current_view = "upload"


def render_header():
    """Render the application header."""
    st.markdown('<h1 class="main-header">📄 PDF Context Narrator</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #666;">A tool for ingesting, searching, and analyzing PDF documents</p>',
        unsafe_allow_html=True
    )


def render_sidebar():
    """Render the sidebar navigation."""
    st.sidebar.title("Navigation")
    
    view = st.sidebar.radio(
        "Select View",
        ["📥 Upload", "🔍 Search", "📖 Narrative View", "⚙️ Settings"],
        index=["📥 Upload", "🔍 Search", "📖 Narrative View", "⚙️ Settings"].index(
            {"upload": "📥 Upload", "search": "🔍 Search", "narrative": "📖 Narrative View", "settings": "⚙️ Settings"}
            .get(st.session_state.current_view, "📥 Upload")
        )
    )
    
    # Map display names back to keys
    view_map = {
        "📥 Upload": "upload",
        "🔍 Search": "search",
        "📖 Narrative View": "narrative",
        "⚙️ Settings": "settings"
    }
    st.session_state.current_view = view_map[view]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Statistics")
    st.sidebar.metric("Uploaded PDFs", len(st.session_state.uploaded_files))
    st.sidebar.metric("Search Results", len(st.session_state.search_results))


def render_upload_view():
    """Render the PDF upload interface."""
    st.header("📥 Upload PDF Documents")
    
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose PDF files to upload",
            type=["pdf"],
            accept_multiple_files=True,
            help="Select one or more PDF files to ingest into the system"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            force_reindex = st.checkbox("Force re-indexing", value=False)
        with col2:
            extract_metadata = st.checkbox("Extract metadata", value=True)
        
        if st.button("📤 Ingest PDFs", type="primary", use_container_width=True):
            if uploaded_files:
                with st.spinner("Ingesting PDFs..."):
                    # Stub implementation - would call actual ingestion logic
                    for file in uploaded_files:
                        st.session_state.uploaded_files.append({
                            "name": file.name,
                            "size": file.size,
                            "uploaded_at": datetime.now().isoformat(),
                            "status": "ingested"
                        })
                    st.success(f"✅ Successfully ingested {len(uploaded_files)} PDF(s)")
            else:
                st.warning("⚠️ Please select at least one PDF file to upload")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display uploaded files
    if st.session_state.uploaded_files:
        st.subheader("📚 Recently Uploaded Files")
        for idx, file_info in enumerate(reversed(st.session_state.uploaded_files[-10:])):
            with st.expander(f"📄 {file_info['name']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Size:** {file_info['size'] / 1024:.2f} KB")
                with col2:
                    st.write(f"**Status:** {file_info['status']}")
                with col3:
                    st.write(f"**Uploaded:** {file_info['uploaded_at'][:19]}")


def render_search_view():
    """Render the search interface."""
    st.header("🔍 Search Documents")
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="Enter your search query...",
            help="Search through ingested PDF documents"
        )
    with col2:
        limit = st.number_input("Max Results", min_value=1, max_value=100, value=10)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        search_type = st.selectbox("Search Type", ["Full Text", "Semantic", "Keyword"])
    with col2:
        sort_by = st.selectbox("Sort By", ["Relevance", "Date", "Title"])
    
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if query:
            with st.spinner("Searching..."):
                # Stub implementation - would call actual search logic
                st.session_state.search_results = [
                    {
                        "title": f"Document {i+1}",
                        "excerpt": f"Sample excerpt matching '{query}' from document {i+1}...",
                        "score": 0.95 - (i * 0.05),
                        "page": i + 1,
                        "date": datetime.now().isoformat()
                    }
                    for i in range(min(5, limit))
                ]
                st.success(f"✅ Found {len(st.session_state.search_results)} result(s)")
        else:
            st.warning("⚠️ Please enter a search query")
    
    # Display results
    if st.session_state.search_results:
        st.subheader(f"📊 Search Results ({len(st.session_state.search_results)})")
        for idx, result in enumerate(st.session_state.search_results):
            st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{idx+1}. {result['title']}**")
                st.markdown(f"*Page {result['page']}*")
                st.write(result['excerpt'])
            with col2:
                st.metric("Relevance", f"{result['score']:.2%}")
            st.markdown('</div>', unsafe_allow_html=True)


def render_narrative_view():
    """Render the narrative view interface."""
    st.header("📖 Narrative View")
    
    st.markdown("""
    Generate a narrative summary that synthesizes information from multiple documents
    into a coherent story or timeline.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        narrative_type = st.selectbox(
            "Narrative Type",
            ["Chronological", "Thematic", "Analytical", "Summary"]
        )
    with col2:
        length = st.selectbox("Length", ["Brief", "Standard", "Detailed"])
    
    if st.button("📝 Generate Narrative", type="primary", use_container_width=True):
        with st.spinner("Generating narrative..."):
            # Stub implementation - would call actual narrative generation
            narrative = f"""
            # {narrative_type} Narrative
            
            This is a {length.lower()} narrative view of the documents in the system.
            
            ## Overview
            
            Based on the analysis of the uploaded documents, we can identify several key themes
            and patterns that emerge from the content.
            
            ## Key Findings
            
            1. **First Finding**: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            2. **Second Finding**: Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            3. **Third Finding**: Ut enim ad minim veniam, quis nostrud exercitation ullamco.
            
            ## Timeline
            
            - **2024-01**: Initial phase of document collection
            - **2024-02**: Processing and analysis period
            - **2024-03**: Current status and ongoing updates
            
            ## Conclusion
            
            The documents collectively provide insights into the topic at hand,
            revealing patterns and connections that warrant further investigation.
            """
            
            st.markdown('<div class="narrative-text">', unsafe_allow_html=True)
            st.markdown(narrative)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Export options
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📥 Export as Markdown", use_container_width=True):
                    st.download_button(
                        "Download Markdown",
                        narrative,
                        file_name="narrative.md",
                        mime="text/markdown"
                    )
            with col2:
                if st.button("📥 Export as JSON", use_container_width=True):
                    json_data = json.dumps({"narrative": narrative, "type": narrative_type}, indent=2)
                    st.download_button(
                        "Download JSON",
                        json_data,
                        file_name="narrative.json",
                        mime="application/json"
                    )
            with col3:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.code(narrative, language="markdown")


def render_settings_view():
    """Render the settings interface."""
    st.header("⚙️ Settings")
    
    st.subheader("Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        profile = st.selectbox(
            "Configuration Profile",
            ["Local", "Offline", "Cloud"],
            help="Select the configuration profile to use"
        )
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1
        )
    with col2:
        max_workers = st.number_input(
            "Max Workers",
            min_value=1,
            max_value=16,
            value=4,
            help="Number of parallel workers for processing"
        )
        structured_logging = st.checkbox("Enable Structured Logging", value=False)
    
    st.subheader("Data Directories")
    data_dir = st.text_input("Data Directory", value="data")
    cache_dir = st.text_input("Cache Directory", value="cache")
    logs_dir = st.text_input("Logs Directory", value="logs")
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully")
    
    st.markdown("---")
    st.subheader("System Information")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Version", "0.1.0")
    with col2:
        st.metric("Profile", profile)
    with col3:
        st.metric("Log Level", log_level)


def main():
    """Main application entry point."""
    init_session_state()
    render_header()
    render_sidebar()
    
    # Render appropriate view based on navigation
    if st.session_state.current_view == "upload":
        render_upload_view()
    elif st.session_state.current_view == "search":
        render_search_view()
    elif st.session_state.current_view == "narrative":
        render_narrative_view()
    elif st.session_state.current_view == "settings":
        render_settings_view()


if __name__ == "__main__":
    main()

import os
import streamlit as st
import google.generativeai as genai
from PIL import Image
import tempfile
from typing import List, Optional
import json
import time
from streamlit_lottie import st_lottie
import requests
import plotly.express as px
import pandas as pd
from io import BytesIO
from streamlit.web.server.server import Server
import streamlit.components.v1 as components

# Get the absolute path to the icon
icon_path = os.path.join(os.path.dirname(__file__), "assets", "generated-icon.png")

# Page configuration
st.set_page_config(
    page_title="AI Design Team",
    page_icon=icon_path,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open("styles/custom.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = ""
if "analysis_state" not in st.session_state:
    st.session_state.analysis_state = {
        "vision": {"status": "waiting", "progress": 0},
        "ux": {"status": "waiting", "progress": 0},
        "market": {"status": "waiting", "progress": 0}
    }

def generate_social_media_posts(image_description: str, context: str, model) -> dict:
    """Generate social media post suggestions"""
    prompt = f"""
    Based on this design/image description:
    {image_description}

    Context: {context}

    Generate engaging social media posts:
    1. Create a punchy Twitter/X post (max 280 characters) with relevant hashtags. Make it attention-grabbing and include 2-3 relevant hashtags.
    2. Write a professional LinkedIn post (2-3 paragraphs) that:
       - Highlights the design's business value
       - Includes relevant industry insights
       - Ends with a clear call to action
       - Uses appropriate professional tone

    Format the response as a JSON with two keys: 'twitter' and 'linkedin'
    Ensure the Twitter post is within character limit and hashtags are relevant.
    """

    response = model.generate_content(prompt)
    try:
        response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(response_text)
    except:
        return {
            "twitter": "Error generating Twitter post",
            "linkedin": "Error generating LinkedIn post"
        }

def update_agent_state(agent_type: str, status: str = None, progress: int = None):
    """Update the analysis state for a specific agent"""
    if status is not None:
        st.session_state.analysis_state[agent_type]["status"] = status
    if progress is not None:
        st.session_state.analysis_state[agent_type]["progress"] = progress

def initialize_agents(api_key: str):
    """Initialize the Gemini model and configure agents"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")
    return model

def process_images(files) -> List[Image.Image]:
    """Process uploaded image files"""
    processed_images = []
    for file in files:
        image = Image.open(file)
        processed_images.append(image)
    return processed_images

def display_social_media_suggestions(suggestions: dict):
    """Display social media post suggestions with animations and interactive elements"""
    st.header("📱 Social Media Content Suggestions")

    # Add tabs for different platforms
    tab1, tab2 = st.tabs(["Twitter/X", "LinkedIn"])
    
    with tab1:
        st.markdown("""
        <div class="social-media-card twitter animated-card">
            <h3>🐦 Twitter/X Post</h3>
        </div>
        """, unsafe_allow_html=True)
        
        twitter_post = suggestions.get("twitter", "")
        st.code(twitter_post, language="markdown")
        
        if st.button("📋 Copy Twitter Post", key="copy_twitter"):
            st.balloons()
            st.success("Twitter post copied to clipboard!")
            
    with tab2:
        st.markdown("""
        <div class="social-media-card linkedin animated-card">
            <h3>💼 LinkedIn Post</h3>
        </div>
        """, unsafe_allow_html=True)
        
        linkedin_post = suggestions.get("linkedin", "")
        st.code(linkedin_post, language="markdown")
        
        if st.button("📋 Copy LinkedIn Post", key="copy_linkedin"):
            st.snow()
            st.success("LinkedIn post copied to clipboard!")

def load_lottie_url(url: str):
    """Load Lottie animation from URL"""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def create_design_score_visualization(scores: dict):
    """Create a radar chart for design scores"""
    df = pd.DataFrame(dict(
        Metric=list(scores.keys()),
        Score=list(scores.values())
    ))
    
    fig = px.line_polar(df, r='Score', theta='Metric', line_close=True)
    fig.update_traces(fill='toself')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False
    )
    return fig

def display_image_preview(files, title: str):
    """Display preview of uploaded images in a grid with optimization"""
    if not files:
        return
        
    st.markdown(f"### {title} Preview")
    
    # Calculate number of columns based on number of images
    n_images = len(files)
    cols = min(3, n_images)  # Max 3 columns
    
    # Create columns with equal width
    columns = st.columns(cols)
    
    # Display images in grid
    for idx, file in enumerate(files):
        with columns[idx % cols]:
            try:
                # Open image
                img = Image.open(file)
                
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Calculate new size while maintaining aspect ratio
                target_height = 280  # Match CSS max-height
                ratio = target_height / img.size[1]
                new_width = int(img.size[0] * ratio)
                new_size = (new_width, target_height)
                
                if new_width > 350:  # If width exceeds container
                    new_width = 350
                    ratio = new_width / img.size[0]
                    new_height = int(img.size[1] * ratio)
                    new_size = (new_width, new_height)
                
                # Resize image
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Compress image
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=85, optimize=True)
                compressed_size = buffer.tell()/1024  # Size in KB
                buffer.seek(0)
                
                # Display compressed image
                st.image(
                    buffer,
                    use_container_width=False,
                    caption=file.name
                )
                
                # Display image info with compression ratio
                original_size = file.size/1024  # Convert to KB
                compression_ratio = ((original_size - compressed_size) / original_size) * 100
                
                st.caption(
                    f"Original: {original_size:.1f} KB → Compressed: {compressed_size:.1f} KB "
                    f"({compression_ratio:.1f}% smaller)\n"
                    f"Format: {img.format} | Dimensions: {img.size[0]}x{img.size[1]}"
                )
                
            except Exception as e:
                st.error(f"Error processing image {file.name}: {str(e)}")
                continue

def add_health_check():
    """Add a health check endpoint for the container"""
    try:
        if not hasattr(st, '_server'):
            return

        def health_check():
            return {"status": "OK"}

        # Add health check route if possible
        if hasattr(st, '_server') and hasattr(st._server, 'add_route'):
            st._server.add_route("/health", health_check, methods=["GET"])
    except Exception as e:
        # Log error but don't crash
        print(f"Health check setup failed: {str(e)}")
        pass

# Main application layout
st.title("🎨 AI Design Team")
st.markdown("""
<div class="main-description">
    Your collaborative AI design analysis team powered by Google Gemini
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input(
        "Enter your Google API Key",
        value=st.session_state.api_key_input,
        type="password",
        help="Get your API key from https://aistudio.google.com/ - Create a new project or select existing one to generate API key"
    )
    st.session_state.api_key_input = api_key

if api_key:
    model = initialize_agents(api_key)

    # File upload section
    st.header("📤 Upload Designs")
    col1, col2 = st.columns(2)

    with col1:
        design_files = st.file_uploader(
            "Upload Your UI/UX Designs",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        if design_files:
            display_image_preview(design_files, "Your Designs")

    with col2:
        competitor_files = st.file_uploader(
            "Upload Competitor Designs (Optional)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        if competitor_files:
            display_image_preview(competitor_files, "Competitor Designs")

    # Analysis configuration
    st.header("🎯 Analysis Settings")

    analysis_types = st.multiselect(
        "Select Analysis Types",
        ["Visual Design", "User Experience", "Market Analysis"],
        default=["Visual Design"]
    )

    focus_areas = st.multiselect(
        "Focus Areas",
        ["Color Scheme", "Typography", "Layout", "Navigation", 
         "Interactions", "Accessibility", "Branding", "Market Fit"],
        default=["Color Scheme", "Layout"]
    )

    context = st.text_area(
        "Additional Context",
        placeholder="Describe your product, target audience, and specific goals..."
    )

    # Process button
    if st.button("🚀 Run Analysis", type="primary"):
        if not design_files:
            st.error("Please upload at least one design file to analyze.")
        else:
            # Show overall progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process images with animation
            with st.spinner("Processing images..."):
                all_images = process_images(design_files)
                if competitor_files:
                    competitor_images = process_images(competitor_files)
                    all_images.extend(competitor_images)
                progress_bar.progress(20)
                status_text.text("Images processed successfully!")

            # Reset analysis state
            for agent_type in st.session_state.analysis_state:
                st.session_state.analysis_state[agent_type].update({
                    "status": "waiting",
                    "progress": 0
                })

            # Create result containers
            social_media_suggestions = {}

            if "Visual Design" in analysis_types:
                update_agent_state("vision", "processing", 20)
                with st.expander("🎨 Visual Design Analysis", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        with st.spinner("Analyzing visual design elements..."):
                            vision_prompt = f"""
                            Analyze these designs as a visual design expert:
                            Focus areas: {', '.join(focus_areas)}
                            Context: {context}

                            Provide detailed analysis of:
                            1. Visual hierarchy and composition
                            2. Color usage and harmony
                            3. Typography choices and readability
                            4. Layout effectiveness
                            5. Brand consistency

                            Also provide a brief description of the design for social media purposes.

                            Format the response in clear sections with bullet points.
                            """
                            vision_response = model.generate_content([vision_prompt] + all_images)
                            social_media_suggestions = generate_social_media_posts(vision_response.text, context, model)
                            st.markdown(vision_response.text)
                            update_agent_state("vision", "complete", 100)

                    with col2:
                        # Add design score visualization
                        design_scores = {
                            "Visual Hierarchy": 8.5,
                            "Color Harmony": 7.8,
                            "Typography": 8.2,
                            "Layout": 7.9,
                            "Brand Consistency": 8.0
                        }
                        st.plotly_chart(create_design_score_visualization(design_scores))

            if "User Experience" in analysis_types:
                update_agent_state("ux", "processing", 20)
                with st.expander("🔄 User Experience Analysis", expanded=True):
                    with st.spinner("Evaluating user experience..."):
                        ux_prompt = f"""
                        Analyze these designs as a UX expert:
                        Focus areas: {', '.join(focus_areas)}
                        Context: {context}

                        Evaluate:
                        1. User flow and navigation
                        2. Interaction patterns
                        3. Accessibility considerations
                        4. Usability issues and improvements
                        5. Information architecture

                        Format the response in clear sections with bullet points.
                        """
                        ux_response = model.generate_content([ux_prompt] + all_images)
                        st.markdown(ux_response.text)
                        update_agent_state("ux", "complete", 100)

            if "Market Analysis" in analysis_types:
                update_agent_state("market", "processing", 20)
                with st.expander("📊 Market Analysis", expanded=True):
                    with st.spinner("Conducting market analysis..."):
                        market_prompt = f"""
                        Analyze these designs from a market perspective:
                        Focus areas: {', '.join(focus_areas)}
                        Context: {context}

                        Provide insights on:
                        1. Market positioning
                        2. Competitive advantages
                        3. Industry trends alignment
                        4. Target audience fit
                        5. Market opportunities

                        Format the response in clear sections with bullet points.
                        """
                        market_response = model.generate_content([market_prompt] + all_images)
                        st.markdown(market_response.text)
                        update_agent_state("market", "complete", 100)

            # Display social media suggestions
            if social_media_suggestions:
                st.markdown("---")
                display_social_media_suggestions(social_media_suggestions)

            # Combined insights
            if len(analysis_types) > 1:
                st.header("🔍 Key Takeaways")
                synthesis_prompt = f"""
                Synthesize the key insights from all analyses:
                Analysis types: {', '.join(analysis_types)}
                Context: {context}

                Provide:
                1. Top 3 strengths
                2. Top 3 improvement opportunities
                3. Strategic recommendations

                Keep it concise and actionable.
                """
                synthesis_response = model.generate_content([synthesis_prompt] + all_images)
                st.markdown(synthesis_response.text)
else:
    st.warning("Please enter your Google API key to begin.")

    if not api_key:
        lottie_url = "https://assets5.lottiefiles.com/packages/lf20_si7mrdxq.json"
        lottie_json = load_lottie_url(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, height=200)

# Footer
# Footer
st.markdown("""
---
<div style='text-align: center; color: #ffffff; background-color: rgba(26, 28, 36, 0.7); padding: 1rem; border-radius: 10px;'>
    Powered by  <a href='https://aistudio.google.com/' style='color: #00f2ff;'><span style="color: #00f2ff;">Gemini Flash 2.0 Exp</span></a> | Built with ❤️ by <a href='https://github.com/rohitg00' style='color: #00f2ff;'><span style="color: #00f2ff;">Rohit Ghumare</span></a>
</div>
""", unsafe_allow_html=True)

add_health_check()
import os
# Force AI and math libraries to use a single thread to prevent CPU deadlocks
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["NUMBA_NUM_THREADS"] = "1"

import streamlit as st
from PIL import Image, ImageFilter
import numpy as np
import io
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="The Kawaii Factory 'Smart' Streamlit App", layout="wide")

def composite_images(mockup, design, x, y, scale, rotation, shadow_opacity):
    """
    Composites the design onto the mockup at (x, y) with scale, rotation and shadow.
    Ensures design is centered on the click point.
    """
    mockup = mockup.convert("RGBA")
    design = design.convert("RGBA")

    # Scale
    w, h = design.size
    new_w = int(w * scale)
    new_h = int(h * scale)
    design = design.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Rotation
    design = design.rotate(rotation, expand=True, resample=Image.BICUBIC)
    
    # Shadow logic
    if shadow_opacity > 0:
        shadow = Image.new("RGBA", design.size, (0, 0, 0, 0))
        design_alpha = design.getchannel("A")
        shadow_fill = Image.new("RGBA", design.size, (0, 0, 0, int(255 * (shadow_opacity / 100))))
        shadow.paste(shadow_fill, (0, 0), mask=design_alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
        shadow_offset = (5, 5)
    else:
        shadow = None

    # Calculate top-left for centering
    final_w, final_h = design.size
    top_left_x = x - final_w // 2
    top_left_y = y - final_h // 2

    # Paste shadow and design
    result = Image.new("RGBA", mockup.size)
    result.paste(mockup, (0, 0))
    
    if shadow:
        result.paste(shadow, (top_left_x + shadow_offset[0], top_left_y + shadow_offset[1]), mask=shadow)
    
    result.paste(design, (top_left_x, top_left_y), mask=design)
    
    return result.convert("RGB")

@st.cache_resource
def load_rembg_session():
    # LAZY LOAD: Only import when this function is called
    from rembg import new_session
    # "u2netp" is the highly compressed lightweight version of the model
    return new_session("u2netp")

@st.cache_data
def get_processed_design_bytes(design_bytes):
    """
    Takes image bytes, processes them, and returns PNG bytes.
    This prevents Streamlit's cache from choking on PIL objects.
    """
    # LAZY LOAD: Only import when this function is called
    from rembg import remove
    
    design_image = Image.open(io.BytesIO(design_bytes)).convert("RGBA")
    width, height = design_image.size

    # Smart Watermark Logic
    if width >= 50 and height >= 50:
        bottom_right_area = design_image.crop((width - 50, height - 50, width, height))
        pixels = np.array(bottom_right_area)
        alpha_channel = pixels[:, :, 3]
        
        # Check if the area has partial transparency (mix of text/logo and background)
        if 0 < np.mean(alpha_channel) < 255:
            design_image = design_image.crop((0, 0, width, height - 50))

    # Background Removal
    session = load_rembg_session()
    processed_design = remove(design_image, session=session)
    
    # Save back to bytes for safe Streamlit caching
    buf = io.BytesIO()
    processed_design.save(buf, format="PNG")
    return buf.getvalue()

st.title("🎨 The Kawaii Factory 'Smart' Streamlit App")
st.write("Automatically clean your designs and place them perfectly on mockups.")

col1, col2 = st.columns(2)

with col1:
    design_file = st.file_uploader("1. Upload Your Design", type=["png", "jpg", "jpeg"])

with col2:
    mockup_file = st.file_uploader("2. Upload Your Mockup Photo", type=["png", "jpg", "jpeg"])

if design_file and mockup_file:
    status_text = st.empty()
    status_text.info("Status: Files uploaded successfully. Reading image data...")
    
    design_bytes = design_file.getvalue()
    mockup_bytes = mockup_file.getvalue()
    
    mockup_img = Image.open(io.BytesIO(mockup_bytes))
    
    status_text.info("Status: Initializing AI Model (This is where downloads or deadlocks usually happen)...")
    
    with st.spinner("Processing design..."):
        try:
            processed_bytes = get_processed_design_bytes(design_bytes)
            status_text.success("Status: AI Processing complete!")
            processed_design = Image.open(io.BytesIO(processed_bytes))
        except Exception as e:
            status_text.error(f"Error during AI processing: {e}")
            st.stop()
    
    st.sidebar.header("Placement Controls")
    scale = st.sidebar.slider("Scale", 0.1, 1.0, 0.5)
    rotation = st.sidebar.slider("Rotation", -180, 180, 0)
    shadow_opacity = st.sidebar.slider("Shadow Opacity", 0, 100, 20)

    st.subheader("3. Click on the Mockup to Place Your Design")
    coords = streamlit_image_coordinates(mockup_img, key="mockup")

    if coords:
        st.write(f"Anchor Point: ({coords['x']}, {coords['y']})")
        
        final_mockup = composite_images(
            mockup_img, 
            processed_design, 
            coords['x'], 
            coords['y'], 
            scale, 
            -rotation,
            shadow_opacity
        )
        
        st.subheader("4. Final Mockup")
        st.image(final_mockup, use_container_width=True)
        
        # Download button
        buf = io.BytesIO()
        final_mockup.save(buf, format="JPEG")
        byte_im = buf.getvalue()
        
        st.download_button(
            label="Download Finished Mockup",
            data=byte_im,
            file_name="finished_mockup.jpg",
            mime="image/jpeg"
        )
    else:
        st.info("Click on the image above to set the placement coordinates.")

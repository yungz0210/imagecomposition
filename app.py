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
import urllib.request  # Added for safe manual downloading
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="The Kawaii Factory 'Smart' Streamlit App", layout="wide")

def composite_images(mockup, design, x, y, scale, rotation, shadow_opacity):
    mockup = mockup.convert("RGBA")
    design = design.convert("RGBA")

    w, h = design.size
    new_w = int(w * scale)
    new_h = int(h * scale)
    design = design.resize((new_w, new_h), Image.Resampling.LANCZOS)

    design = design.rotate(rotation, expand=True, resample=Image.BICUBIC)
    
    if shadow_opacity > 0:
        shadow = Image.new("RGBA", design.size, (0, 0, 0, 0))
        design_alpha = design.getchannel("A")
        shadow_fill = Image.new("RGBA", design.size, (0, 0, 0, int(255 * (shadow_opacity / 100))))
        shadow.paste(shadow_fill, (0, 0), mask=design_alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
        shadow_offset = (5, 5)
    else:
        shadow = None

    final_w, final_h = design.size
    top_left_x = x - final_w // 2
    top_left_y = y - final_h // 2

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
    return new_session("u2netp")

@st.cache_data
def get_processed_design_bytes(design_bytes):
    # LAZY LOAD: Only import when this function is called
    from rembg import remove
    
    design_image = Image.open(io.BytesIO(design_bytes)).convert("RGBA")
    width, height = design_image.size

    # Smart Watermark Logic
    if width >= 50 and height >= 50:
        bottom_right_area = design_image.crop((width - 50, height - 50, width, height))
        pixels = np.array(bottom_right_area)
        alpha_channel = pixels[:, :, 3]
        
        if 0 < np.mean(alpha_channel) < 255:
            design_image = design_image.crop((0, 0, width, height - 50))

    session = load_rembg_session()
    processed_design = remove(design_image, session=session)
    
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
    
    # --- NEW: MANUAL MODEL DOWNLOAD BYPASS ---
    # We download the model manually to prevent the headless Streamlit server from hanging
    u2net_home = os.path.expanduser("~/.u2net")
    os.makedirs(u2net_home, exist_ok=True)
    model_path = os.path.join(u2net_home, "u2netp.onnx")
    
    if not os.path.exists(model_path):
        status_text.warning("Status: Downloading lightweight AI model (4MB)... Please wait...")
        url = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
        try:
            urllib.request.urlretrieve(url, model_path)
            status_text.success("Status: Model downloaded successfully!")
        except Exception as e:
            status_text.error(f"Failed to download model: {e}")
            st.stop()
            
    status_text.info("Status: Initializing AI Model (Using local cached model)...")
    
    with st.spinner("Processing design..."):
        try:
            processed_bytes = get_processed_design_bytes(design_bytes)
            status_text.success("Status: AI Processing complete! Click on the mockup to place.")
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

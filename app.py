import streamlit as st
from PIL import Image
import numpy as np
import io
from rembg import remove
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import ImageFilter

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
        # Create shadow from alpha channel
        shadow = Image.new("RGBA", design.size, (0, 0, 0, 0))
        design_alpha = design.getchannel("A")
        # Darken the shadow based on opacity (0-100)
        # 100 opacity = black shadow, 0 = no shadow
        shadow_fill = Image.new("RGBA", design.size, (0, 0, 0, int(255 * (shadow_opacity / 100))))
        shadow.paste(shadow_fill, (0, 0), mask=design_alpha)

        # Blur the shadow slightly for realism
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))

        # Offset for shadow
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
    # Pre-loading the session can sometimes help with performance/loading
    from rembg import new_session
    return new_session()

@st.cache_data
def get_processed_design(design_bytes):
    img = Image.open(io.BytesIO(design_bytes))
    return process_design(img)

def process_design(design_image):
    """
    Cleans the design: Smart Watermark Detection + Background Removal.
    """
    # Convert to RGBA if not already
    design_image = design_image.convert("RGBA")
    width, height = design_image.size

    # Smart Watermark Logic: scan bottom-right 50x50 pixel area
    if width >= 50 and height >= 50:
        bottom_right_area = design_image.crop((width - 50, height - 50, width, height))
        # Convert to numpy array to check alpha channel
        pixels = np.array(bottom_right_area)
        alpha_channel = pixels[:, :, 3]

        # If the average pixel color isn't transparent (indicating a logo/text)
        # We assume if any significant part is not transparent, it might be a watermark.
        # The prompt says "If the average pixel color isn't transparent"
        if np.mean(alpha_channel) > 0:
            # Crop that area out automatically
            # Usually this means cropping the whole image to exclude that bottom-right strip?
            # Or just removing that 50x50 block?
            # "crop that area out automatically" likely means removing it from the image.
            # To be safe and follow standard "watermark removal" in this context,
            # let's crop the image to exclude the bottom 50 pixels.
            design_image = design_image.crop((0, 0, width, height - 50))
            st.info("Smart Watermark Detection: Bottom-right watermark area cropped.")

    # Background Removal
    session = load_rembg_session()
    processed_design = remove(design_image, session=session)
    return processed_design

st.title("🎨 The Kawaii Factory 'Smart' Streamlit App")
st.write("Automatically clean your designs and place them perfectly on mockups.")

col1, col2 = st.columns(2)

with col1:
    design_file = st.file_uploader("1. Upload Your Design", type=["png", "jpg", "jpeg"])

with col2:
    mockup_file = st.file_uploader("2. Upload Your Mockup Photo", type=["png", "jpg", "jpeg"])

if design_file and mockup_file:
    design_img = Image.open(design_file)
    mockup_img = Image.open(mockup_file)

    with st.spinner("Processing design..."):
        design_bytes = design_file.getvalue()
        processed_design = get_processed_design(design_bytes)

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
            -rotation, # Negative because PIL rotates CCW, but users often expect CW
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

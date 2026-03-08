# 🎨 The Kawaii Factory 'Smart' Streamlit App

This Streamlit application allows you to take raw designs, automatically clean them (removing watermarks and backgrounds), and precisely place them onto mockup photos with realistic effects.

## ✨ Features

- **Dual File Upload**: Easily upload your design and your mockup photo.
- **Smart Watermark Detection**: Automatically detects and crops out content in the bottom-right 50x50 area (common for logos/watermarks).
- **Background Removal**: Uses `rembg` to transform your design into a transparent PNG.
- **Precision Placement**: Click anywhere on the mockup photo to set the center point for your design.
- **Realistic Controls**:
    - **Scale**: Resize your design (0.1x to 1.0x).
    - **Rotation**: Tilt your design for the perfect angle.
    - **Shadow Opacity**: Add a subtle, blurred drop shadow for increased realism.
- **Instant Download**: Download your finished mockup as a high-quality JPEG.

## 🚀 Installation

1. **Clone the repository** (if applicable).
2. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On the first run, the app will download the background removal model (u2net), which may take a few moments depending on your connection.*

## 🛠️ Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
2. **Upload Your Design**: Choose a PNG or JPG file of your design.
3. **Upload Your Mockup Photo**: Choose the photo you want to place your design on.
4. **Clean the Design**: The app will automatically remove the watermark (if detected) and the background.
5. **Set Placement**: Click on the displayed mockup photo where you want the design to appear.
6. **Adjust Controls**: Use the sliders in the sidebar to scale, rotate, and add a shadow.
7. **Download**: Click "Download Finished Mockup" to save your work.

## 📦 Dependencies

- `streamlit`: Web application framework.
- `Pillow`: Image processing library.
- `rembg`: Background removal tool.
- `streamlit-image-coordinates`: Component for capturing click coordinates.
- `numpy`: Numerical processing for image analysis.
- `onnxruntime`: Backend for `rembg`.

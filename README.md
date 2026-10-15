# PreviewGen

**The Automated Batch Preview Studio for Marketplace Contributors & Digital Artists.**  
Transform folders of transparent **2D assets (PNG, WebP, SVG, TIFF, PSD)** and **3D models (GLB, GLTF, OBJ, STL, PLY, BLEND)** into marketplace-compliant, split-diagonal JPG previews in seconds.

---

## 🎯 The Purpose: Why We Built PreviewGen

Selling digital assets on top marketplaces like **Freepik, Adobe Stock, Shutterstock, Creative Market, Envato, and Etsy** is a high-volume business. However, digital asset platforms have a strict requirement:

> **Every transparent asset (PNG or PSD) must be accompanied by a high-resolution JPG preview that clearly proves transparency to potential buyers before they purchase.**

### The Pain Points We Solve

| The Pain Point | How Designers Handled It Before | How PreviewGen Solves It |
|---|---|---|
| ⏳ **Extreme Time Waste** | Manually opening Photoshop, drawing diagonal masks, generating checkerboards, pasting text badges, and saving one file at a time. | **1-Click Batch Processing**: Process 500+ images in under 60 seconds completely hands-free. |
| ❌ **Marketplace Rejections** | Rejections from reviewers because the preview didn't clearly communicate transparency or lacked a standard split. | **Strict Marketplace Compliance**: Standard diagonal split (checkerboard transparency vs. solid background) approved by reviewers. |
| 🔒 **Privacy & Cloud Leaks** | Uploading unreleased, proprietary art to sketchy "free online converter" websites that steal or scrape artwork. | **100% Local & Offline**: Your files never leave your computer. Complete privacy and zero data leakage. |
| 🔍 **Distortion & Cropping** | Batch scripts that accidentally stretch, crop, trim padding, or resize transparent canvases. | **Zero Distortion Guarantee**: Original alpha channel and dimensions are preserved with pixel-perfect composite. |
| 🎨 **Ugly / Generic Watermarks** | Bland or unreadable watermarks that obscure artwork or blend into transparent areas. | **Full Customization Studio**: Configurable text, fill colors, outer outline/stroke, opacity, scale, and 5 anchor positions. |

---

## 👥 Who Is This For?

- **Stock Marketplace Contributors** (Freepik, Adobe Stock, Shutterstock, 123RF, Dreamstime)
- **Freelance Illustrators & Vector Artists** preparing asset packs for commercial clients
- **Icon & UI/UX Designers** exporting hundreds of transparent components for showcase
- **3D Artists & Game Asset Creators** packaging transparent character renders, props, and textures
- **Creative Studios & Agencies** looking to automate repetitive post-production export workflows

---

## 💡 Why You Should Use PreviewGen

1. **Reclaim Hours of Your Week**: Stop doing repetitive monkey-work in Photoshop. Load your folder, click one button, and let the background worker handle thousands of assets while you focus on creating art.
2. **Increase Submission Approval Rates**: Reviewers on platforms like Freepik accept submissions faster when previews follow the industry-standard diagonal split convention.
3. **Studio-Grade Control**: Whether your brand uses pure white, off-white, light gray, or dark solid backgrounds, customize colors with the interactive palette and instant live preview.
4. **Native Desktop Speed**: Powered by Python, PySide6, and Pillow with multithreaded background workers—no lag, no memory leaks, and no browser slowdowns.

---

## ⚡ 1-Line Universal Installers (No Certificate Warnings)

Because PreviewGen is an independent software project, web browsers may display false "Unknown Publisher" warnings when downloading raw files.

**Running the single command below in your terminal is the fastest, official way to install PreviewGen.** It downloads the latest build, clears browser quarantine tags, installs the app permanently, and **pins an official Desktop Shortcut with icon**.

> **Run this command once.** Afterwards, double-click the **PreviewGen** icon on your Desktop or Start Menu like any regular desktop app!

### 🪟 Windows (PowerShell)
Open **PowerShell** and run:
```powershell
irm https://raw.githubusercontent.com/Mustaqeem66/Freepik-Preview-Generator/main/install.ps1 | iex
```
- Installs to `%LOCALAPPDATA%\Programs\PreviewGen`
- Automatically unblocks files (`Unblock-File`) to bypass Windows SmartScreen
- Creates **Desktop Shortcut** with high-res icon and **Start Menu Shortcut**
- Generates an `uninstall.bat` script
- Launches PreviewGen automatically

---

### 🍎 macOS (Terminal)
Open **Terminal** and run:
```bash
curl -fsSL https://raw.githubusercontent.com/Mustaqeem66/Freepik-Preview-Generator/main/install.sh | bash
```
- Installs directly to `/Applications/PreviewGen.app`
- Strips Apple Gatekeeper quarantine (`xattr -cr`) to bypass the "Unidentified Developer" block
- Creates a **Desktop Shortcut** (`~/Desktop/PreviewGen`)
- Launches PreviewGen automatically

---

### 🐧 Linux (Terminal)
Open your terminal and run:
```bash
curl -fsSL https://raw.githubusercontent.com/Mustaqeem66/Freepik-Preview-Generator/main/install.sh | bash
```
- Installs standalone AppImage to `~/.local/bin/previewgen`
- Configures permissions (`chmod +x`) and installs system icon
- Registers desktop entry (`previewgen.desktop`) and creates **Desktop Shortcut**
- Launches PreviewGen automatically

---

## 📦 Alternative: Manual Download (GitHub Releases)

Prefer downloading manually?
1. Visit the [**Latest Releases**](https://github.com/Mustaqeem66/Freepik-Preview-Generator/releases/latest).
2. Download your platform package:
   - **Windows**: `PreviewGen-Windows.zip` — Extract and double-click `Install-Desktop-Icon.bat`.
   - **macOS**: `PreviewGen-macOS.dmg` — Open DMG, drag to Applications, run `xattr -cr /Applications/PreviewGen.app` if prompted.
   - **Linux**: `PreviewGen-Linux.AppImage` — Run `chmod +x PreviewGen-Linux.AppImage` and double-click.

---

## 📖 How to Use PreviewGen (Step-by-Step Guide)

PreviewGen makes bulk preview creation effortless in 6 simple steps:

```
 1. Select Folder ──► 2. Browse Files ──► 3. Adjust 3D Angle ──► 4. Add Brand Logo ──► 5. Pick Colors ──► 6. Batch Export!
    (or ZIP file)       (◀ Prev / Next ▶)   (Orbit 360° View)      (Freeform Sliders)     (Diagonal Split)     (1-Click JPGs)
```

1. **Select Input Folder (or ZIP Archive)**:
   - Click **Browse…** in panel `1 · Folders` and pick a folder containing your transparent assets.
   - You can drop folders with **PNG, WebP, SVG, TIFF, PSD, 3D models (GLB, OBJ, STL, BLEND)**, or even **`.zip` files**!
2. **Flip Through Files with Live Viewport Navigation**:
   - Use the **`◀ Prev`** and **`Next ▶`** buttons in the toolbar (or press **Left/Right Arrow keys** on your keyboard) to preview any asset in your folder instantly.
3. **Rotate 3D Models in Full 360° (When viewing 3D files)**:
   - Click and drag your mouse directly on the preview image to orbit the model in 360°.
   - Or click an angle preset like **Isometric (3/4)**, **Front**, **Side**, **Top**, or **Back**.
4. **Add Brand Watermarks (Logo, Text, or Both)**:
   - Upload your logo image (`.png`, `.svg`, `.ico`) and adjust **Scale** and **Opacity**.
   - Use the **X** and **Y** position sliders to place your logo and watermark text at any exact percentage coordinate on the canvas.
5. **Choose Split Direction & Background Color**:
   - Choose whether the solid color sits on the Left or Right half.
   - Click the color swatch or choose a preset (White, Off-White, Light Gray, Dark).
6. **Click "Generate All JPG Previews"**:
   - The asynchronous worker processes hundreds of files in the background without freezing the UI.
   - Once finished, click **Open Output Folder** to inspect your ready-to-upload marketplace JPG previews!

---

## 📦 GitHub Releases vs. GitHub Packages (FAQ)

> **What are "GitHub Packages" shown on the repository, and do we need them?**

* **GitHub Releases (What PreviewGen Uses)**:
  * **Purpose**: Distributes ready-to-run desktop applications (`.exe` for Windows, `.dmg` for macOS, `.AppImage` for Linux).
  * **For Users**: End-users download and install the complete app directly without compiling code.
* **GitHub Packages**:
  * **Purpose**: A code library repository for developers (similar to `npm`, `pip`/PyPI, Docker Container Registry, or NuGet).
  * **For Developers**: Used when publishing reusable Python modules (e.g. `pip install previewgen-core`) so other developers can import them into their code.
  * **Verdict**: For standalone desktop software like PreviewGen, **GitHub Releases is the official and correct distribution hub**. You do not need to publish to GitHub Packages unless we split the rendering engine into an open-source library for other developers.

---
## 🚀 Key Features

### 1. Multi-Format 2D Ingestion (PNG, WebP, SVG, TIFF, PSD)
- **PNG**: Pixel-perfect alpha compositing with zero canvas crop or distortion.
- **WebP**: Full support for modern web & mobile transparent assets, with animated WebP keyframe fallback.
- **SVG Vector**: Smooth vector rasterization at crisp high-res 4K target DPI using native QtSvg.
- **TIFF / TIF**: High-bit depth print cutouts with automatic CMYK $\to$ sRGB color profile transform.
- **PSD (Photoshop)**: Headless composite layer extraction directly from Photoshop binaries via `psd-tools` — no Adobe software required!

### 2. Full 360° 3D Model Studio (GLB, GLTF, OBJ, STL, PLY, BLEND)
- **360° Interactive Orbit**: Click and drag your mouse directly on the preview image to rotate 3D models from any angle in real-time.
- **Studio Angle Presets**: 1-click presets for **Isometric 3/4**, **Front**, **Side**, **Top**, and **Back** views.
- **Fine-Grained Controls**: Sliders for horizontal **Yaw (0°–360°)** and vertical **Pitch (-85° to +85°)**.
- **Headless Studio Lighting**: Directional key light + ambient fill with smooth shading and back-face culling onto a transparent canvas.
- **Blender Integration**: Native headless rendering of `.blend` scene files via local Blender CLI.

### 3. File-by-File Viewport Navigation
- **Previous & Next Buttons**: Easily cycle through any asset in your chosen folder using `◀ Prev` and `Next ▶` buttons.
- **Live File Counter**: Visual badge showing current position (e.g. `File 3 / 24`).
- **Keyboard Shortcuts**: Use **Left Arrow** (`◀`) and **Right Arrow** (`▶`) on your keyboard to flip through files effortlessly.
- **Auto-Adapting Controls**: The 3D orbit panel automatically appears when browsing 3D models, and collapses when viewing 2D images.
### 4. Custom Brand Logo & Icon Overlay
- **Upload Any Logo**: Upload brand watermarks (`.png`, `.webp`, `.svg`, `.ico`).
- **Independent Sizing & Opacity**: Scale logos from 20% to 250% and adjust opacity from 10% to 100%.
- **Freeform Position Sliders**: Position logos and text anywhere with continuous horizontal (X: 0–100%) and vertical (Y: 0–100%) offset sliders.
- **Dual Branding**: Run logo only, text watermark only, or display both concurrently.

### 5. Automated ZIP Archive Ingestion & Auto-Cleanup
- **Drop ZIP Files Directly**: Points to folders containing `.zip` archives.
- **Background Decompression**: Automatically extracts archives in memory/temp isolation, discovers all enclosed 2D and 3D assets, and renders previews.
- **Safe Auto-Cleanup**: Automatically deletes all temporary unzipped artifacts immediately upon completion across Windows, macOS, and Linux.

### 6. Diagonal Split Backgrounds
- **Two Equal-Area Triangles**: Cuts the canvas from corner to corner.
- **Directional Flip**: Choose between *Left Solid / Right Transparent* or *Left Transparent / Right Solid*.
- **Interactive Color Palette**: Pick any custom hex color or select from one-click presets (White, Off-White, Light Gray, Dark).

### 7. Typography & Outline Engine
- **Customizable Label**: Defaults to `100% TRANSPARENT`, or enter your own custom text (or leave blank).
- **Outer Outline / Stroke**: Toggleable stroke with custom color and thickness (Thin, Normal, Medium, Thick, Extra Bold) so text remains readable over any image.
- **Live Sliders**: Real-time Font Scale (50% to 180%) and Text Opacity (10% to 100%).

### 8. Premium Design System (Ice Blue & Slate Palette)
- **Light Mode**: Crisp icy-white background (`#F7FBFD`), soft mist blue borders and chips (`#D6E6EF`), and slate steel blue accents (`#7FA6B8`).
- **Dark Mode**: Deep nocturnal slate background (`#0E171E`), elevated dark surfaces (`#15222B`), luminous icy typography (`#F7FBFD`), and complementary slate blue highlights.
- **Animated Sun/Moon Switch**: Smooth pill-style macOS theme toggle with session persistence.

### 9. Live Debounced Viewport & Navigation
- **Instant Feedback**: Any slider movement, color selection, or text edit reflects in the live preview within 120ms.
- **View Modes**: Switch between responsive "Fit to View" and "Original 100%" pixel inspection.
- **Image Metadata & Badge**: Displays active filename, format badge (e.g. `[GLB]`, `[PSD]`, `[SVG]`, `[WEBP]`), and resolution underneath the viewport.

### 10. High-Throughput Batch Engine
- **Non-Blocking Multithreading**: Batch rendering runs in a separate thread pool so the user interface never freezes.
- **Live Metrics**: Real-time progress bar, success counters, error counts, and pending image badges.
- **Single-Click Cancel**: Abort long-running batches safely at any time.
---

## 📸 App Preview & Visual Showcase

### Clean Light Mode
<p align="center">
  <img src="preview-light.png" alt="PreviewGen Light Mode Interface" width="850">
</p>

### Pure Dark Mode
<p align="center">
  <img src="preview-dark.png" alt="PreviewGen Dark Mode Interface" width="850">
</p>

---

## 💻 Developer Quickstart (Run from Source)

```bash
# Clone the repository
git clone https://github.com/Mustaqeem66/Freepik-Preview-Generator.git
cd Freepik-Preview-Generator

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run PreviewGen
python main.py
```

---

## 📜 Licensing Terms

PreviewGen operates under a **Dual-Licensing Model**:

### 🟢 Free for Personal & Non-Commercial Use
PreviewGen is **100% free** for personal evaluation, educational purposes, hobby projects, and non-profit use. You can download, run, and experiment with the application at zero cost.

### 💼 Paid License Required for Commercial Use
If you use PreviewGen to produce previews for:
- Assets sold or monetized on stock platforms (Freepik, Adobe Stock, Shutterstock, Creative Market, Etsy, Envato, etc.)
- Client deliverables, freelance design projects, or agency production
- Commercial products, studios, or enterprise workflows

👉 **A commercial license is required.**

To acquire a commercial license, request volume seats, or discuss enterprise terms, please contact:
- **Email**: [zenartisan66@gmail.com](mailto:zenartisan66@gmail.com)
- **Subject**: `PreviewGen Commercial License Inquiry`

---

## 🤝 Sponsorships & Partnerships

Are you a design agency, marketplace vendor, or tool developer interested in supporting PreviewGen, requesting custom integrations, or featuring your brand?

We welcome sponsors and partners! Get in touch directly:
- **Email**: [zenartisan66@gmail.com](mailto:zenartisan66@gmail.com)
- **Subject**: `PreviewGen Sponsorship / Partnership`

---

## 👤 Author

Created with care by **[Mustaqeem66](https://github.com/Mustaqeem66)** (ZenArtisan).  
If PreviewGen saves you time, please give the repository a **⭐ Star** on GitHub!

# UI Transformation Profile: "Soft-SaaS Aesthetic"

## 1. Global Aesthetic Rules (CSS)
* **Background Palette:** Use a soft, neutral off-white: `#FDFCF8`. 
* **Container Styling:** * `border-radius: 24px;` (High rounding for that "App" feel).
    * `border: 1px solid #F1F5F9;` (Very subtle border).
    * `box-shadow: 0 8px 24px rgba(149, 157, 165, 0.1);` (Soft, lifted elevation).
* **Typography:** Use a clean, rounded sans-serif font stack (e.g., `'Inter', 'Plus Jakarta Sans', sans-serif`).

## 2. Component Blueprint
* **The "Hero" Upload Box:**
    * Remove the default file uploader borders.
    * Replace with a dashed-line zone (`2px dashed #E2E8F0`) centered in a soft-white container.
    * Add a "ghost" icon (e.g., a simple SVG document icon).
* **The Metric Cards:**
    * Replace all tables with a "Flex Row" of cards.
    * Each card should contain:
        * Top: A small, muted label (e.g., "ATS Score").
        * Middle: Large, soft-colored text (e.g., `#6366F1`).
        * Bottom: A very subtle progress bar (use `st.progress` wrapped in a div).
* **The Interaction Bar:**
    * Instead of a sidebar, place all "Analyze" buttons in a fixed, rounded container at the bottom or top-center of the dashboard.

## 3. Implementation Logic (Python/Streamlit)
* **CSS Injection:**
    ```css
    .stApp { background-color: #FDFCF8; }
    
    /* Card Component */
    .app-card {
        background: #FFFFFF;
        padding: 24px;
        border-radius: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    
    /* Header/Text Styling */
    h2 { font-family: 'Plus Jakarta Sans', sans-serif; color: #1E293B; }
    ```
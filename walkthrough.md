# Axiom Core Frontend Walkthrough

I've completed the premium frontend for your dual-strategy quantitative platform. Taking creative freedom, I've named the platform **Axiom Core** and designed a sleek, high-end UI to match.

## What Was Implemented

1. **Aesthetics & Theme**:
   - Implemented a "Deep Obsidian" aesthetic using `#050507` background colors.
   - Designed large, ethereal "orbs" that drift softly in the background for a modern, high-tech glow without overpowering the content.
   - Created a custom cursor effect that expands into a glowing aura over clickable elements.

2. **Typography & Layout**:
   - Used Google Fonts **Outfit** for structural headings (sharp, geometric) and **Inter** for clean, legible body text.
   - Engineered a responsive split-card layout utilizing premium glassmorphism styles (`backdrop-filter: blur`, translucent backgrounds).

3. **Interactivity**:
   - The landing page uses intersection observers (`script.js`) to elegantly fade-in the strategy cards as they enter the viewport.
   - High-quality SVG icons from Phosphor Icons emphasize the precision aspect of the tools.

## The Strategy Cards

The two primary tools are now presented elegantly side-by-side:

### Institutional Credit Intelligence
Connects to your Bond Screener. Features bullet points for "Volumetric Macro Yield Curves" and "Live YTM Modeling". The "Launch Terminal" button links towards your `website_with_screener_&_dashboard_corporate.py` environment.

### Algorithmic Alpha Engine
Connects to your VectorBT Equity Backtester. Highlights "High-Fidelity Historical Backtesting" and "Vectorized Performance Execution". The "Initialize Engine" button directs users to `strategies_for_trading.py`.

## Next Steps

To view the landing page in action:
1. Open the [index.html](file:///c:/Users/Admin/Downloads/Strategies%20for%20trading/index.html) file directly in your web browser.
2. Experience the custom cursor and subtle gradient animations!
3. Later, when you deploy the Python scripts to actual servers (like a Streamlit server), you can replace the placeholder `href` links in the HTML buttons with your live server URLs.

import os
import uuid
from io import BytesIO
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from cursed.pixelator import pixelate_image
from cursed.ai import generate_entity_metadata
from cursed.cards import render_card
from cursed.collection import init_db, save_card, get_collection
from cursed.models import generate_rarity, generate_stats

load_dotenv()
init_db()

st.set_page_config(page_title="CURSED.EXE", page_icon="👾", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,200..800&display=swap');

:root {
    --cream: #fff8ef;
    --pink: #ffb3c6;
    --lime: #c8ffb0;
    --lavender: #d9c2ff;
    --ink: #111111;
}

.stApp {
    background-color: var(--cream);
    background-image:
        linear-gradient(#eadfd5 1px, transparent 1px),
        linear-gradient(90deg, #eadfd5 1px, transparent 1px);
    background-size: 24px 24px;
}

.stApp, .stApp * {
    font-family: 'Bricolage Grotesque', sans-serif;
}

.block-container {
    max-width: 1400px;
    padding: 2.5rem clamp(1rem, 4vw, 4rem) 4rem;
}

h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] {
    color: var(--ink) !important;
}

h1 {
    font-size: clamp(2.5rem, 7vw, 5rem) !important;
    letter-spacing: -0.06em;
    line-height: 0.95;
}

.stButton > button, .stDownloadButton > button {
    min-height: 3rem;
    background-color: var(--lime);
    color: var(--ink) !important;
    border: 3px solid #000000;
    box-shadow: 4px 4px 0px #000000;
    border-radius: 0px;
    font-weight: 800;
    transition: transform 100ms ease, box-shadow 100ms ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translate(2px, 2px);
    box-shadow: 2px 2px 0px #000000;
}

.stButton > button:active, .stDownloadButton > button:active {
    transform: translate(4px, 4px);
    box-shadow: 0 0 0 #000000;
}

div[data-testid="stFileUploader"] {
    background-color: var(--lavender);
    border: 3px solid var(--ink);
    padding: 1.25rem;
    box-shadow: 6px 6px 0 var(--ink);
}

div[data-testid="stImage"] {
    border: 3px solid var(--ink);
    box-shadow: 5px 5px 0 var(--ink);
    background-color: var(--pink);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 1rem;
    border-bottom: 0;
}

.stTabs [data-baseweb="tab"] {
    background-color: var(--pink);
    border: 3px solid var(--ink);
    box-shadow: 4px 4px 0 var(--ink);
    border-radius: 0;
    padding: 0.75rem 1.25rem;
    color: var(--ink) !important;
    font-weight: 800;
}

.stTabs [aria-selected="true"] {
    background-color: var(--lime);
}

.vault-summary {
    display: inline-block;
    margin: 0 0 1.5rem;
    padding: 0.75rem 1rem;
    background: var(--pink);
    border: 3px solid var(--ink);
    box-shadow: 4px 4px 0 var(--ink);
    color: var(--ink);
    font-weight: 700;
}

@media (max-width: 700px) {
    .block-container {
        padding: 1.25rem 0.75rem 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1 1 45%;
        padding: 0.6rem 0.5rem;
        text-align: center;
    }
    div[data-testid="stFileUploader"] {
        padding: 0.75rem;
        box-shadow: 4px 4px 0 var(--ink);
    }
}
</style>
""", unsafe_allow_html=True)

st.title("👾 CURSED.EXE")
st.write("Reality is full of creatures. You just never noticed how weird they were.")

tab_lab, tab_vault = st.tabs(["🧪 The Laboratory", "🗃️ The Vault"])

with tab_lab:
    uploaded_file = st.file_uploader("Upload a photograph of an ordinary object", type=['jpg', 'jpeg', 'png', 'webp'])

    if uploaded_file is not None:
        if uploaded_file.size > 5 * 1024 * 1024:
            st.error("Anomaly too massive. Please upload an image smaller than 5MB.")
        else:
            try:
                image = Image.open(uploaded_file)
                col1, col2 = st.columns(2)

                with col1:
                    st.image(image, caption="Target Acquired", use_container_width=True)

                if st.button("Digitize and Corrupt", use_container_width=True):
                    with st.spinner("Processing visual data and extracting lore..."):
                        pixel_art = pixelate_image(image)
                        metadata = generate_entity_metadata(image)

                        with col2:
                            st.image(pixel_art, caption=f"Subject: {metadata.get('subject', 'Unknown')}", use_container_width=True)

                    st.success("Visuals corrupted successfully.")

                    rarity = generate_rarity()
                    stats = generate_stats()

                    final_card = render_card(pixel_art, metadata, rarity, stats)

                    st.divider()
                    st.subheader("Your Collectible")
                    st.image(final_card, use_container_width=True)

                    card_id = str(uuid.uuid4())[:8]
                    file_path = f"data/cards/{card_id}.png"
                    final_card.save(file_path, format="PNG")
                    save_card(card_id, metadata, rarity, stats, file_path)

                    st.info("Card saved to The Vault.")

                    buf = BytesIO()
                    final_card.save(buf, format="PNG")
                    st.download_button(
                        label="Download Card (PNG)",
                        data=buf.getvalue(),
                        file_name=f"{metadata.get('name', 'cursed_entity').lower().replace(' ', '_')}.png",
                        mime="image/png"
                    )

            except Exception as e:
                st.error(f"Error processing the file: {e}")

with tab_vault:
    st.header("Your Collection")
    cards = get_collection()

    if not cards:
        st.write("Your vault is empty. Go scan some anomalies.")
    else:
        st.markdown(
            f"<div class='vault-summary'>TOTAL ANOMALIES CAPTURED: <strong>{len(cards)}</strong></div>",
            unsafe_allow_html=True,
        )

        cols = st.columns(3)
        for index, card in enumerate(cards):
            with cols[index % 3]:
                try:
                    card_img = Image.open(card["image_path"])
                    st.image(card_img, use_container_width=True)

                    st.markdown(
                        f"**{card.get('name', 'Null Anomaly')}**  \n"
                        f"`{card.get('class', 'GLITCH')}` · **{card.get('rarity', 'COMMON')}**",
                    )
                    stats = card.get("stats", {})
                    stat_text = " · ".join(
                        f"{key}: {max(0, min(100, int(value)))}"
                        for key, value in stats.items()
                        if key in {"Chaotic-ness", "Grass Meter"}
                    )
                    if stat_text:
                        st.caption(stat_text)
                    with st.expander("Read anomaly file"):
                        st.write(card.get("subject", "Unknown subject"))
                        st.write(f'"{card.get("quirky_text", "No signal.")}"')
                        st.write(card.get("lore", "No lore recorded."))

                    buf = BytesIO()
                    card_img.save(buf, format="PNG")
                    st.download_button(
                        label=f"Download #{card['id']}",
                        data=buf.getvalue(),
                        file_name=f"{card.get('name', 'cursed').lower().replace(' ', '_')}_{card['id']}.png",
                        mime="image/png",
                        key=f"dl_{card['id']}"
                    )
                except FileNotFoundError:
                    st.error("Image file missing.")

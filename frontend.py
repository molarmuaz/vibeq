import pandas as pd
import gradio as gr
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Load your songs dataset
songs = pd.read_csv("dataset/final_track_list.csv")  # Adjust path as needed

# Setup embeddings and vector database
raw_doc = TextLoader("dataset/tagged_description.txt").load()
splitter = CharacterTextSplitter(chunk_size=0, chunk_overlap=0, separator="\n")
doc = splitter.split_documents(raw_doc)
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db_songs = Chroma.from_documents(doc, embedding=embedder)


def fetch_songs(query: str, size: int = 10) -> pd.DataFrame:
    response = db_songs.similarity_search(query, k=size)
    result = []
    for i in range(0, len(response)):
        result += [response[i].page_content.split()[0].strip('"')]
    return songs[songs["id"].isin(result)]


def recommend_songs(query: str, count: int):
    recommendations = fetch_songs(query, count)

    # Create HTML with Spotify embeds
    html_content = ""
    for _, row in recommendations.iterrows():
        spotify_id = row["id"]
        title = row["name"]
        artist = row["artist"]

        iframe_html = f'''
        <div style="margin-bottom: 25px; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 15px; border: 1px solid #2a2a5a; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
            <h3 style="color: #ffffff; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; font-weight: 600; margin-bottom: 12px; font-size: 18px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">{title}</h3>
            <p style="color: #b0b0d0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; font-weight: 400; margin-bottom: 15px; font-size: 14px;">by {artist}</p>
            <iframe style="border-radius: 12px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));" 
                    src="https://open.spotify.com/embed/track/{spotify_id}?utm_source=generator&theme=0" 
                    width="100%" 
                    height="152" 
                    frameBorder="0" 
                    allowfullscreen="" 
                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                    loading="lazy">
            </iframe>
        </div>
        '''
        html_content += iframe_html

    return html_content


# Count options
count_options = [5, 10, 20, 50, 100, 500]

custom_css = """
.gradio-container {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.gr-textbox, .gr-dropdown {
    background: rgba(26, 26, 46, 0.8) !important;
    border: 1px solid #2a2a5a !important;
    border-radius: 12px !important;
    color: #ffffff !important;
}

.gr-textbox input, .gr-dropdown select {
    background: transparent !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
}

.gr-textbox input::placeholder {
    color: #8a8ab0 !important;
}

.gr-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    transition: all 0.3s ease !important;
}

.gr-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
}

.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
}

.gr-markdown h1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem !important;
    margin-bottom: 1.5rem !important;
}

.gr-markdown h2 {
    color: #b0b0d0 !important;
    font-size: 1.5rem !important;
    margin-top: 2rem !important;
}

label {
    color: #b0b0d0 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}

.gr-html {
    background: transparent !important;
}
"""

with gr.Blocks(theme=gr.themes.Glass(), css=custom_css) as dashboard:
    gr.Markdown("# 🎵 VibeQ - Muaz Ahmed")
    gr.Markdown("*Discover your next favorite songs with AI-powered recommendations*")

    with gr.Row():
        user_query = gr.Textbox(
            label="🎼 Describe the music you're looking for",
            placeholder="e.g., upbeat dance music, melancholic indie rock, energetic workout songs...",
            lines=2
        )
        count_dropdown = gr.Dropdown(
            choices=count_options,
            label="📊 Number of songs to display",
            value=10
        )
        submit_button = gr.Button("🚀 Find My Music", size="lg")

    gr.Markdown("## 🎧 Your Personalized Recommendations")
    output = gr.HTML(label="Recommended songs")

    submit_button.click(
        fn=recommend_songs,
        inputs=[user_query, count_dropdown],
        outputs=output
    )

if __name__ == "__main__":
    dashboard.launch()
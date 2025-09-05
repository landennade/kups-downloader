import yt_dlp
from rapidfuzz import process
from googleapiclient.discovery import build
import os
import shutil
import streamlit as st

# --- YouTube API setup ---
API_KEY = "AIzaSyB4ZhXpkb1OLnuAGVsNbvwr32Xp6lTzuVU"  # Hardcoded
youtube = build("youtube", "v3", developerKey=API_KEY)

# --- Helper functions ---
def search_youtube(song):
    """Search YouTube for a song and return a dict of {video_id: title}"""
    request = youtube.search().list(q=song, part="snippet", maxResults=5, type="video")
    response = request.execute()
    videos = {item["id"]["videoId"]: item["snippet"]["title"] for item in response["items"]}
    return videos

def find_downloadable_video(song):
    """Try each of the top search results until one is downloadable"""
    videos = search_youtube(song)
    if not videos:
        raise Exception("No search results found")

    # Sort video titles by best fuzzy match
    sorted_videos = sorted(videos.items(), key=lambda kv: process.extractOne(song, [kv[1]])[1], reverse=True)

    ydl_opts = {"format": "bestaudio[ext=m4a]/bestaudio/best", "quiet": True}

    for video_id, title in sorted_videos:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=False)
            return video_url, title
        except Exception:
            continue

    raise Exception("No downloadable video found for this song")

def download_audio(video_url, output_folder):
    """Download audio from YouTube"""
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": f"{output_folder}/%(title)s.%(ext)s",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def process_songs(folder_name, song_input):
    folder_name = folder_name.strip()
    download_folder = os.path.join("downloads", folder_name)
    os.makedirs(download_folder, exist_ok=True)

    song_list = [song.strip() for song in song_input.split(",")]
    results = []

    for song in song_list:
        try:
            video_url, video_title = find_downloadable_video(song)
            results.append(f"🎵 Best match for *{song}*: {video_url}")
            download_audio(video_url, download_folder)
            results.append(f"✅ Downloaded: {video_title}")
        except Exception as e:
            results.append(f"❌ Error with '{song}': {str(e)}")

    # Zip all files
    zip_path = f"{download_folder}.zip"
    shutil.make_archive(download_folder, "zip", download_folder)

    return "\n".join(results), zip_path

# --- Streamlit UI ---
st.title("🎶 YouTube Song Downloader")

st.markdown("""
Enter a folder name and one or more song titles (comma-separated).

💡 **Tip:** If you want family-friendly versions, just add the word **"clean"** to your song title.
For example:  
- `Like a Stone clean`  
- `Sugar on my tongue clean`

⚠️ **Note:** The app will automatically try multiple search results and skip blocked videos.
If no downloadable version is found, you will see a warning.
""")

folder_name = st.text_input("Folder Name", "my_music")
song_input = st.text_area("Song Titles (comma-separated)", "Song 1, Song 2")

if st.button("Download Songs"):
    if not song_input.strip():
        st.error("Please enter at least one song title.")
    else:
        with st.spinner("Processing songs..."):
            results, zip_path = process_songs(folder_name, song_input)
            st.success("All downloads finished!")
            st.text(results)

            with open(zip_path, "rb") as f:
                st.download_button("⬇️ Download ZIP", f, file_name=os.path.basename(zip_path))

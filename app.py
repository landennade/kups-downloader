import yt_dlp
import os
import shutil
import streamlit as st

# --- Helper functions ---
def find_working_video(song):
    """Search YouTube and return the first video URL that can actually be downloaded"""
    ydl_opts = {"quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch5:{song}", download=False)["entries"]
        for result in search_results:
            video_url = f"https://www.youtube.com/watch?v={result['id']}"
            try:
                # Try extracting info to confirm it's downloadable
                ydl.extract_info(video_url, download=False)
                return video_url
            except Exception:
                continue
    raise Exception("No downloadable video found for this song.")

def download_audio(video_url, output_folder):
    """Download audio from YouTube (prefer m4a streams for reliability)"""
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
            video_url = find_working_video(song)
            results.append(f"🎵 Best match for *{song}*: {video_url}")
            download_audio(video_url, download_folder)
            results.append(f"✅ Downloaded: {song}")
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
- `Creep Radiohead Clean`  

⚠️ **Note:** Some videos (VEVO, premium, age-restricted) may still be blocked.  
The app will automatically try the next search result if one fails.
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

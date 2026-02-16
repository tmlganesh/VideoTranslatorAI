from youtube_transcript_api import YouTubeTranscriptApi

video_id = "NHopJHSlVo4"

print(f"Checking {video_id}...")

try:
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)
    
    # iterate over TranscriptList object
    print("Transcripts available:")
    for t in transcript_list:
        print(f" - [{t.language_code}] {t.language} (Generated: {t.is_generated})")
        
    # Check specifically for English
    try:
        en = transcript_list.find_transcript(['en'])
        print(f"Found English transcript: {en.language_code}")
    except:
        print("No English transcript found via find_transcript(['en'])")

except Exception as e:
    print(f"Error: {e}")

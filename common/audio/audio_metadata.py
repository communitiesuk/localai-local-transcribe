import mutagen

def get_recording_time(file_path):
    """
    Extracts the recording timestamp or creation date from various audio formats 
    using Mutagen. Returns a string timestamp/date or None if not found.
    """
    try:
        audio = mutagen.File(file_path)
        
        if audio is None or audio.tags is None:
            return None
            
        tags = audio.tags

        # 1. MP4 / M4A (iPhone Voice Memos, AAC, QuickTime)
        # MP4 tags use '©day' for creation/recording date
        if '©day' in tags:
            val = tags['©day']
            return str(val[0] if isinstance(val, list) else val)

        # 2. ID3 Tags (MP3 files & WAV files with ID3 chunks)
        # TDRC = Recording Time, TYER = Year, TDAT = Date
        id3_keys = ['TDRC', 'TYER', 'TDAT', 'ICRD']
        for key in id3_keys:
            if key in tags:
                return str(tags[key])

        # 3. Vorbis Comments (OGG / FLAC) or General Tag Dictionaries
        vorbis_keys = ['date', 'DATE', 'year', 'YEAR', 'creation_time']
        for key in vorbis_keys:
            if key in tags:
                val = tags[key]
                return str(val[0] if isinstance(val, list) else val)

    except Exception as e:
        print(f"Error reading metadata with Mutagen for {file_path}: {e}")
        
    return None
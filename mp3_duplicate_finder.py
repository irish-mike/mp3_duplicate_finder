from configparser import ConfigParser
from pathlib import Path
from mutagen import File
import os
import shutil

CONFIG = None
STATS = {"duplicates_found": 0}

ERROR_LOG_NAME = "errors.txt"
DUPLICATE_LOG_NAME = "duplicates.txt"


def load_config():
    """Read config.ini and return a settings dictionary."""
    parser = ConfigParser()
    parser.read("config.ini")

    meta_data_key = [v.strip() for v in parser["matching"]["meta_data_key"].split(",")]
    supported_extensions = [v.strip().lower() for v in parser["matching"]["supported_extensions"].split(",")]

    return {
        "MUSIC_DIRECTORY": Path(parser["paths"]["music_directory"]),
        "DUPLICATE_DIRECTORY": Path(parser["paths"]["duplicate_directory"]),
        "LOG_DIRECTORY": Path(parser["paths"]["log_directory"]),
        "META_DATA_KEY": meta_data_key,
        "SUPPORTED_EXTENSIONS": supported_extensions,
    }


def normalize(value):
    """Lowercase and trim whitespace for stable comparisons."""
    return str(value).strip().lower()


def log_error(message):
    """Append an error message to the error log."""
    log_file = CONFIG["LOG_DIRECTORY"] / ERROR_LOG_NAME
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def log_duplicate(original_path, duplicate_path):
    """Record an original/duplicate pair to the duplicates log."""
    log_file = CONFIG["LOG_DIRECTORY"] / DUPLICATE_LOG_NAME
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"Original: {original_path} | Duplicate: {duplicate_path}\n")


def build_song_key(file_path):
    """
    Build a key from configured metadata fields.
    Returns "" on any read error and logs the issue.
    """
    key_params = CONFIG["META_DATA_KEY"]

    try:
        track = File(file_path, easy=True)
    except Exception as e:
        log_error(f"Error opening {file_path}: {e.__class__.__name__}: {e}")
        return ""

    if track is None or getattr(track, "info", None) is None:
        log_error(f"Unreadable or unsupported file: {file_path}")
        return ""

    tags = track.tags or {}
    values = []

    for field in key_params:
        if field == "length":
            try:
                values.append(str(int(track.info.length)))
            except Exception as e:
                log_error(f"Error reading length for {file_path}: {e.__class__.__name__}: {e}")
                return ""
            continue

        tag_value = tags.get(field, "")
        if isinstance(tag_value, list):
            tag_value = tag_value[0] if tag_value else ""
        values.append(normalize(tag_value))

    return "_".join(values)


def search():
    """Walk the music directory, build keys, and detect duplicates."""
    music_directory = CONFIG["MUSIC_DIRECTORY"]
    supported_extensions = tuple(CONFIG["SUPPORTED_EXTENSIONS"])
    track_index = {}  # song_key -> original Path

    for subdir, dirs, files in os.walk(music_directory):
        print(f"Analyzing files in {subdir}...")
        for file_name in files:
            if not file_name.lower().endswith(supported_extensions):
                continue

            file_path = Path(subdir) / file_name
            song_key = build_song_key(file_path)
            if not song_key:  # skip unreadable or unsupported files
                continue

            try:
                handle_track(song_key, file_path, track_index)
            except Exception as e:
                log_error(f"Error handling {file_path}: {e.__class__.__name__}: {e}")
                continue


def handle_track(song_key, file_path, track_index):
    """Update index or move duplicate when a key collision is found."""
    if song_key in track_index:
        print(f"Duplicate found: {file_path}")
        original_path = track_index[song_key]
        move_duplicate(file_path, original_path)
        STATS["duplicates_found"] += 1
        log_duplicate(original_path, file_path)
        return

    track_index[song_key] = file_path


def move_duplicate(duplicate_path: Path, original_path: Path):
    """
    Move a duplicate to the duplicate directory, preserving relative structure.
    Logs and continues on any filesystem error.
    """
    music_directory = CONFIG["MUSIC_DIRECTORY"]
    duplicate_directory = CONFIG["DUPLICATE_DIRECTORY"]

    # Prefer preserving tree; fall back to filename-only if outside source root
    try:
        relative_path = duplicate_path.relative_to(music_directory)
    except Exception:
        relative_path = duplicate_path.name

    destination_path = duplicate_directory / relative_path

    try:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log_error(f"Error creating directory {destination_path.parent}: {e.__class__.__name__}: {e}")
        return

    try:
        shutil.move(str(duplicate_path), str(destination_path))
        print(f"Moved duplicate to: {destination_path}")
    except Exception as e:
        log_error(f"Error moving {duplicate_path} -> {destination_path}: {e.__class__.__name__}: {e}")


def run():
    """Load configuration, run the scan, and print summary stats."""
    global CONFIG
    CONFIG = load_config()

    print("Configured Settings:")
    print(f"  Music Directory: {CONFIG['MUSIC_DIRECTORY']}")
    print(f"  Duplicate Directory: {CONFIG['DUPLICATE_DIRECTORY']}")
    print(f"  Log Directory: {CONFIG['LOG_DIRECTORY']}")
    print(f"  Metadata Key Fields: {CONFIG['META_DATA_KEY']}")
    print(f"  Supported Extensions: {CONFIG['SUPPORTED_EXTENSIONS']}")

    search()

    print("Stats:")
    print(f"  Duplicates Found: {STATS['duplicates_found']}")


if __name__ == "__main__":
    run()

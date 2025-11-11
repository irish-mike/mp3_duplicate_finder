from configparser import ConfigParser
from pathlib import Path
from mutagen import File


def load_config():
    config = ConfigParser()
    config.read("config.ini")

    return {
        "music_directory": Path(config["paths"]["music_directory"]),
        "duplicate_directory": Path(config["paths"]["duplicate_directory"]),
        "log_directory": Path(config["paths"]["log_directory"]),
        "meta_data_key": config["matching"]["meta_data_key"].split(",")
    }


def run():
    settings = load_config()

    print("Configured Settings:")
    print(f"  Music Directory: {settings['music_directory']}")
    print(f"  Duplicate Directory: {settings['duplicate_directory']}")
    print(f"  Log Directory: {settings['log_directory']}")
    print(f"  Metadata Key Fields: {settings['meta_data_key']}")

    sample_track = r"D:\Music\Electronic Music\House\House Banger\Shadow Child - Higher (Extended Mix).mp3"
    key = build_song_key(sample_track, settings["meta_data_key"])

    print(f"  Sample Track Key: {key}")

    return settings

def build_song_key(file_path, key_params):
    audio = File(file_path, easy=True)
    values = []

    for field in key_params:
        if field == "length":
            values.append(str(int(audio.info.length)))
            continue

        tag_value = audio.tags.get(field)
        if isinstance(tag_value, list):
            tag_value = tag_value[0]
        values.append(str(tag_value))

    return "_".join(values)


if __name__ == "__main__":
    run()

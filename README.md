# mp3_duplicate_finder

A Python script for identifying and relocating duplicate MP3 files.

The program scans a specified music directory for MP3 files and builds a lookup table using selected metadata fields. The metadata fields used to determine duplicates are specified in `config.ini`.

When duplicates are detected, the first encountered file remains in its original location. Any subsequent duplicates are moved to the configured duplicate output directory, preserving the relative folder structure. For example, if a duplicate is found at:
```

/music/abba/dancing_queen.mp3

```
it will be moved to:
```

duplicates/abba/dancing_queen.mp3

```

A text file (`originals.txt`) will list the original paths for all duplicate entries. Any errors will be recorded in `errors.txt`.

Author: Irish Mike  
This code may be reused freely. Credit is appreciated.

## Usage

Run the script using the configuration values defined in `config.txt`:

```

python run_find_dupes.py

```

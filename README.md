python script for batch processing many H.264 encoded video files into H.265 using ffmpeg
# Usage
`./condec-convert.py -i `

only valid output files are generated, during generation the file is written as FILE.tmp.EXTENSION, if the conversion is successful it will rename this file to FILE.EXTENSION, if it fails it will delete the tmp file

# Flags
- `-i` `--input`:
> input directory containing video files to convert
- `-o` `--output`:
> output directory where new video files will be written
- `-s` `--skip-existing`:
> skip files which already have a processed output file in the output directory
- `-j` `--jobs`:
> number of instances of ffmpeg to run coccurrently. 
- `-v` `--verbose`:
> enable verbose logging
# Running
warning it is very slow and cpu intensive but that is not a fault of the program, running it with gpu hardware acceleration is possible but results in larger file sizes.
</br>
requires python libraries: `ffmpeg-python`, `colored` (handled by requirements.txt and or uv)
requires system binaries: `ffmpeg` (install using system package manager)

## UV 
<!--the script contains a uv script header, and so assuming `ffmpeg` and `ffprobe` are on path `uv run --script codec_convert.py` or -->
```bash
chmod +x ./codec_convert.py
./codec_convert.py --input ./my-videos --output ./output --jobs 4
```

## pip
```bash
python -m venv venv
source venv/bin/activate
pip install -r ./requirements.txt
python ./codec_convert.py --input ./my-videos --output ./output --jobs 4
```

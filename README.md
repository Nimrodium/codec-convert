python script for batch processing many H.264 encoded video files into H.265 using ffmpeg


simple single file python script to mass reencode many video files </br>

useful if you have a large collection of videos encoded in an outdated codec and can be reencoded with a more efficient codec, for example, a large collection of medal clips 60 FPS encoded in H.264, ammassing 160Gb total, after converting these files to 30fps H.265 the total space is 25gb! thats over a 4x size reduction! (this is actually why i made this)
# Usage


only valid output files are generated, during generation the file is written as FILE.tmp.EXTENSION, if the conversion is successful it will rename this file to FILE.EXTENSION, if it fails it will delete the tmp file

# Flags
- `-i` `--input`:
> input directory containing video files to convert
- `-o` `--output`:
> output directory where new video files will be written
- `-s` `--source`:
> source codec to convert from, accepts any 
- `-f` `--fps`:
> reencode with this FPS
- `-t` `--target`:
> target codec to convert to, eg. libx265 (h265) or libsvtav1 (av1)
- `-j` `--jobs`:
> number of instances of ffmpeg to run coccurrently. 
- `-g` `--use_gpu`:
> use GPU acceleration, required for target codecs which use the GPU, such as hevc_vaapi
- `-s` `--skip-existing`:
> skip files which already have a processed output file in the output directory
- `-v` `--verbose`:
> enable verbose logging
- `-h` `--help`:
> print help information on these flags
# Running
warning it is very slow and cpu intensive but that is not a fault of the program, running it with gpu hardware acceleration is possible but results in larger file sizes.
</br>
requires python libraries: `ffmpeg-python`, `colored` (handled by requirements.txt and or [uv](https://docs.astral.sh/uv/)) </br>
requires system binaries: `ffmpeg` ([Download FFmpeg](https://ffmpeg.org/download.html)) </br>

## UV 
```bash
git clone https://github.com/nimrodium/codec-convert.git && cd codec-convert
chmod +x ./codec_convert.py
./codec_convert.py --input ./my-videos --output ./output --source h264 --target libx265 --jobs 4
```

## pip
```bash
git clone https://github.com/nimrodium/codec-convert.git && cd codec-convert
python -m venv venv
source venv/bin/activate
pip install -r ./requirements.txt
python ./codec_convert.py --input ./my-videos --output ./output --source h264 --target libx265 --jobs 4
```

## Windows
in powershell:
```powershell
cd ~/Downloads 
winget install python ffmpeg git
git clone https://github.com/nimrodium/codec-convert.git
cd codec-convert
python -m venv venv
./venv/scripts/activate.ps1
pip install -r ./requirements.txt
python ./codec_convert.py --input ./my-videos --output ./output --source h264 --target libx265 --jobs 4
```
to uninstall
```powershell
rm ~/Downloads/codec-convert/ -rf
winget uninstall python ffmpeg git # only run if you want to uninstall these
```

# Using hardware acceleration
using the GPU for encoding is supported with the script, however it results in less efficient compression and thus greater file sizes than CPU encoding. with the benefit that the actual encoding process is much quicker. to use hardware acceleration use a hardware accelerated encoder such as `hevc_vaapi` and pass the `--use-gpu` flag to enable some specific flags required for utilizing the gpu.

> tested on an AMD Radeon 5700XT on Linux, if specific flags for other GPUs or Windows/MacOS are required please alert me with a PR or issue.

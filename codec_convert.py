#!/usr/bin/env -S uv run --script
# /// script
#  dependencies = ["ffmpeg-python", "colored"]
# ///
# needs ffmpeg, ffprobe available in env
import argparse
import itertools
import mimetypes
import os
import pathlib
import time
from itertools import chain
from math import ceil
from os import listdir, makedirs, path
from subprocess import Popen
from typing import Callable, Iterator

import colored
import ffmpeg

h265_cpu = "libx265"
h265_gpu = "hevc_vaapi"
av1_cpu = "libsvtav1"
av1_gpu = "av1_vaapi"
HWACCEL = False
SOURCE_ENCODING = "h264"
FPS = 30
TARGET_ENCODING_CPU = h265_cpu  # cpu config
TARGET_ENCODING_GPU = "av1_vaapi"  # gpu config
TARGET_ENCODING = TARGET_ENCODING_GPU if HWACCEL else TARGET_ENCODING_CPU
HWACCEL_CONFIG = ["-vaapi_device", "/dev/dri/renderD128"] if HWACCEL else []
SOURCE_ENCODING_HUMAN_NAME = "H.264"
TARGET_ENCODING_HUMAN_NAME = "H.265"


class Static:
    VERBOSE: bool = False


def error(msg: str):
    print(colored.stylize(msg, colored.fore("red")))


def verbose(msg: str):
    if Static.VERBOSE:
        print(colored.stylize(msg, colored.attr("bold")))


def success(msg: str):
    print(colored.stylize(msg, colored.fore("green")))


def info(msg: str):
    print(colored.stylize(msg, colored.attr("dim")))


def get_files(directory: str) -> Iterator[str]:
    return chain.from_iterable(
        map(
            lambda x: iter([x]) if isinstance(x, str) else x,
            map(
                lambda x: get_files(x) if path.isdir(x) else x,
                map(lambda f: path.join(directory, f), listdir(directory)),
            ),
        )
    )


def filter_video_files(files: Iterator[str]) -> Iterator[str]:
    def is_video_file(file: str) -> bool:
        if not path.exists(file):
            error(f"skipping {file}: does not exist")
            return False
        mimetype, _ = mimetypes.guess_type(file)
        return bool(mimetype) and mimetype.startswith("video/")

    return filter(is_video_file, files)


def filter_existing(files: Iterator[tuple[str, str]]) -> Iterator[tuple[str, str]]:
    def f(io: tuple[str, str]) -> bool:
        exists = path.exists(io[1])
        if exists:
            verbose(f"output path {io[1]} already exists. skipping")
        return not exists

    return filter(f, files)


def filter_h264(files: Iterator[tuple[str, str]]) -> Iterator[tuple[str, str]]:
    def is_h264(file: str) -> bool:
        info(f"reading encoding on {file}")
        try:
            is_h264 = any(
                s.get("codec_type") == "video"
                and s.get("codec_name") == SOURCE_ENCODING
                for s in ffmpeg.probe(file)["streams"]
            )
            if not is_h264:
                verbose(f"skipping {file}: not {SOURCE_ENCODING_HUMAN_NAME} encoded.")
            return is_h264

        except ffmpeg.Error as e:
            error(f"error on reading codec on file {file}: {e}")
            return False

    return filter(lambda f: is_h264(f[0]), files)


def generate_output_path(
    input_root: str, output_dir: str, files: Iterator[str]
) -> Iterator[tuple[str, str]]:
    def output_path(file: str) -> str:
        no_root = pathlib.Path(file).relative_to(input_root)
        output = pathlib.Path(output_dir) / no_root
        return str(output)

    return map(lambda f: (f, output_path(f)), files)


# consumer
def transcode(
    total_files: int,
    # skip_existing: bool,
    batch_size: int,
    files: Iterator[tuple[str, str]],
) -> bool:
    total_start = time.time()
    batch_times: list[float] = []
    succeeded: int = 0
    failed: int = 0
    batches = itertools.batched(files, batch_size)
    batch_count = ceil(total_files / batch_size)
    # batch_n = 0
    info(f"processing {total_files} files")
    for batch_n, batch in enumerate(batches):
        print(f"batch ({batch_n}/{batch_count})")
        start = time.time()
        jobs: list[tuple[str, str, str, Popen]] = []
        for input_file, output_file in batch:
            output_file_path = pathlib.Path(output_file)
            output_file_tmp = str(
                output_file_path.with_suffix(".tmp" + output_file_path.suffix)
            )
            if path.exists(output_file):
                verbose(f"{output_file} already exists... overriding file")
                if skip_existing:
                    continue

            info(f"[batch {batch_n}]: processing {input_file}")
            makedirs(path.dirname(output_file), exist_ok=True)
            subproc: Popen = (
                ffmpeg.input(input_file)
                .output(
                    output_file_tmp,
                    vcodec=TARGET_ENCODING,
                    acodec="copy",
                    quality="speed",
                    vf=f"fps={str(FPS)}" + (",format=nv12,hwupload" if HWACCEL else ""),
                    # **{"vf": "format=nv12,hwupload"} if HWACCEL else {},
                )
                .global_args("-hide_banner", *HWACCEL_CONFIG)
                #         "-vaapi_device", "/dev/dri/renderD128",
                # "-vf", "format=nv12,hwupload"
                .run_async(
                    quiet=True,
                    pipe_stdout=True,
                    pipe_stderr=True,
                    overwrite_output=True,
                )
            )
            jobs.append((input_file, output_file, output_file_tmp, subproc))

        for input_file, output_file, output_file_tmp, subproc in jobs:
            out, err = subproc.communicate()
            if subproc.returncode != 0:
                failed += 1
                error(
                    # theres no proper typing for this in the impl so idk if its always present
                    f"Error processing {input_file}: stderr: {err.decode() if err else out.decode() if out else 'no output to display'}"
                )
                if path.exists(output_file_tmp):
                    os.remove(output_file_tmp)
            else:
                succeeded += 1
                success(f"{input_file} has finished")
                os.rename(output_file_tmp, output_file)
            # success(f"{input_file}")

        # for input_file, subproc, (out, err) in [
        #     (input_file, subproc, subproc.communicate()) for input_file, subproc in jobs
        # ]:
        #     if subproc.returncode != 0:
        #         failed += 1
        #         error(
        #             # theres no proper typing for this in the impl so idk if its always present
        #             f"Error processing {input_file}: stderr: {err.decode() if err else out.decode() if out else 'no output to display'}"
        #         )
        #     else:
        #         succeeded += 1
        end = time.time()
        current_batch_time = end - start
        batch_times.append(current_batch_time)

        avg_batch_time_sec = sum(batch_times) / len(batch_times)
        batches_left = batch_count - batch_n
        time_left_sec = avg_batch_time_sec * batches_left
        # avg_file_time_sec = avg_batch_time_sec / batch_size
        # files_left = total_files - (succeeded + failed)
        # time_left_sec = avg_file_time_sec * files_left

        print(
            f"completed {batch_size} files in {current_batch_time / 60} minutes\naverage rate per batch: {avg_batch_time_sec / 60} minutes\ntime left: {time_left_sec / 60} minutes"
        )
    total_end = time.time()
    total_time = total_end - total_start
    info(f"{succeeded + failed} files processed in {total_time / 60} minutes")
    if failed > 0:
        error(f"{failed} of {succeeded + failed} files failed. ({succeeded} succeeded)")
        return False
    else:
        success(f"All {succeeded} files processed successfully.")
        return True


def parse_command_line() -> tuple[bool, bool, str, str, int]:
    parser = argparse.ArgumentParser(
        prog="codec-convert",
        description=f"mass converter from {SOURCE_ENCODING_HUMAN_NAME} to more efficient {TARGET_ENCODING_HUMAN_NAME} MP4 Codec",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-i", "--input", help="input directory", required=True)
    parser.add_argument(
        "-j", "--jobs", help="max ffmpeg instances to run", default=4, type=int
    )
    parser.add_argument(
        "-s",
        "--skip-existing",
        help="skip processing files if output file is already present",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--output",
        help='output directory (will produce "{output}/{input}")',
        default="./output/",
    )
    parsed = parser.parse_args()

    return (
        parsed.verbose,
        parsed.skip_existing,
        parsed.input,
        parsed.output,
        parsed.jobs,
    )


def inspect_iter(fn: Callable[[str], None], s: str) -> str:
    fn(s)
    return s


if __name__ == "__main__":
    Static.VERBOSE, skip_existing, input, output, jobs = parse_command_line()
    info(f"input := {input}\noutput := {output}")
    makedirs(
        output,
        exist_ok=True,
    )
    info("fetching video files ...")

    valid_files_iter = generate_output_path(
        input,
        output,
        map(
            lambda f: inspect_iter(lambda f: verbose(f"found file: {f}"), f),
            filter_video_files(get_files(input)),
        ),
    )

    valid_files: list[tuple[str, str]]
    if skip_existing:
        valid_files = list(filter_existing(valid_files_iter))
    else:
        valid_files = list(valid_files_iter)

    valid_files_n = len(valid_files)
    print(f"found {valid_files_n} video files")
    try:
        transcode(
            valid_files_n,
            jobs,
            filter_h264(iter(valid_files)),
        )
    except KeyboardInterrupt:
        info("interrupted by user ... exiting")
        exit(1)

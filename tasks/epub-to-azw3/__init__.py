#region generated meta
import typing
class Inputs(typing.TypedDict):
    input_epub: str
    output_path: str
    quality: typing.Literal["low", "medium", "high", "best"]
    preserve_metadata: bool
    kindle_device: typing.Literal["kindle", "kindle_dx", "kindle_fire", "kindle_paperwhite", "kindle_oasis"]
class Outputs(typing.TypedDict):
    output_file: typing.NotRequired[str]
    conversion_log: typing.NotRequired[str]
#endregion

from oocana import Context
import subprocess
import os
from pathlib import Path

def main(params: Inputs, context: Context) -> Outputs:
    """
    Convert EPUB file to AZW3 format optimized for Kindle devices using Calibre

    Args:
        params: Input parameters containing file paths and settings
        context: OOMOL context object

    Returns:
        Output dictionary with converted file path and conversion log
    """

    input_file = params["input_epub"]
    output_file = params["output_path"]
    quality = params["quality"]
    preserve_metadata = params["preserve_metadata"]
    kindle_device = params["kindle_device"]

    # Validate input file exists
    if not os.path.exists(input_file):
        raise ValueError(f"Input EPUB file does not exist: {input_file}")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Build calibre conversion command
    cmd = ["ebook-convert", input_file, output_file]

    # Device-specific settings
    device_profiles = {
        "kindle": "kindle",
        "kindle_dx": "kindle_dx",
        "kindle_fire": "kindle_fire",
        "kindle_paperwhite": "kindle_paperwhite",
        "kindle_oasis": "kindle_oasis"
    }
    cmd.extend(["--output-profile", device_profiles.get(kindle_device, "kindle_paperwhite")])

    # Quality settings specific to AZW3
    quality_settings = {
        "low": ["--mobi-file-type", "new"],
        "medium": ["--mobi-file-type", "new", "--mobi-toc"],
        "high": ["--mobi-file-type", "new", "--mobi-toc", "--prefer-metadata-cover"],
        "best": [
            "--mobi-file-type", "new",
            "--mobi-toc",
            "--prefer-metadata-cover",
            "--share-not-sync",
            "--personal-doc"
        ]
    }
    cmd.extend(quality_settings.get(quality, quality_settings["high"]))

    # Preserve metadata option
    if preserve_metadata:
        cmd.extend(["--preserve-cover-aspect-ratio"])

    # AZW3 specific optimizations
    cmd.extend([
        "--enable-heuristics",
        "--mobi-keep-original-images"
    ])

    log_messages = []
    log_messages.append(f"Converting {input_file} to {output_file}")
    log_messages.append(f"Quality setting: {quality}")
    log_messages.append(f"Target device: {kindle_device}")
    log_messages.append(f"Preserve metadata: {preserve_metadata}")

    try:
        # Execute conversion
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        log_messages.append("Conversion completed successfully")
        if result.stdout:
            log_messages.append(f"Calibre output: {result.stdout}")

        # Verify output file was created
        if not os.path.exists(output_file):
            raise ValueError("Conversion failed: Output file was not created")

        file_size = os.path.getsize(output_file)
        log_messages.append(f"Output file size: {file_size} bytes")

        return {
            "output_file": output_file,
            "conversion_log": "\n".join(log_messages)
        }

    except subprocess.CalledProcessError as e:
        error_msg = f"Conversion failed: {e.stderr}" if e.stderr else str(e)
        log_messages.append(f"Error: {error_msg}")
        raise ValueError("\n".join(log_messages))

    except Exception as e:
        log_messages.append(f"Unexpected error: {str(e)}")
        raise ValueError("\n".join(log_messages))
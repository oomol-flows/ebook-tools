#region generated meta
import typing
class Inputs(typing.TypedDict):
    input_epub: str
    output_path: str | None
    quality: typing.Literal["low", "medium", "high", "best"] | None
    preserve_metadata: bool | None
    kindle_device: typing.Literal["kindle", "kindle_dx", "kindle_fire", "kindle_paperwhite", "kindle_oasis"] | None
class Outputs(typing.TypedDict):
    output_file: typing.NotRequired[str]
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
        Output dictionary with converted file path
    """

    input_file = params["input_epub"]
    quality = params.get("quality") or "high"  # Recommended default
    preserve_metadata = params.get("preserve_metadata")
    if preserve_metadata is None:
        preserve_metadata = True  # Recommended default
    kindle_device = params.get("kindle_device") or "kindle_paperwhite"  # Recommended default

    # Validate input file exists
    if not os.path.exists(input_file):
        raise ValueError(f"Input EPUB file does not exist: {input_file}")

    # Handle output path - use session_dir with source filename if null
    output_file = params.get("output_path")
    if output_file is None:
        input_path = Path(input_file)
        output_filename = input_path.stem + ".azw3"
        output_file = os.path.join(context.session_dir, output_filename)

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

    try:
        # Execute conversion
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # Verify output file was created
        if not os.path.exists(output_file):
            raise ValueError("Conversion failed: Output file was not created")

        return {"output_file": output_file}

    except subprocess.CalledProcessError as e:
        error_msg = f"Conversion failed: {e.stderr}" if e.stderr else str(e)
        raise ValueError(error_msg)

    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")
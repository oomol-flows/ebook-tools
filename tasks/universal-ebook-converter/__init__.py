#region generated meta
import typing
class Inputs(typing.TypedDict):
    input_file: str
    output_format: typing.Literal["epub", "mobi", "azw3", "pdf", "txt", "html"] | None
    output_path: str | None
    quality: typing.Literal["low", "medium", "high", "best"] | None
    preserve_metadata: bool | None
    target_device: typing.Literal["generic", "kindle", "kindle_paperwhite", "ipad", "kobo", "nook"] | None
    custom_options: str | None
class Outputs(typing.TypedDict):
    output_file: typing.NotRequired[str]
#endregion

from oocana import Context
import subprocess
import os
from pathlib import Path

def main(params: Inputs, context: Context) -> Outputs:
    """
    Universal ebook format converter supporting multiple formats

    Args:
        params: Input parameters containing file paths and settings
        context: OOMOL context object

    Returns:
        Output dictionary with converted file path
    """

    input_file = params["input_file"]
    output_format = params.get("output_format") or "epub"  # Recommended default
    quality = params.get("quality") or "high"  # Recommended default
    preserve_metadata = params.get("preserve_metadata")
    if preserve_metadata is None:
        preserve_metadata = True  # Recommended default
    target_device = params.get("target_device") or "generic"  # Recommended default
    custom_options = params.get("custom_options") or ""

    # Validate input file exists
    if not os.path.exists(input_file):
        raise ValueError(f"Input file does not exist: {input_file}")

    # Get input format
    input_format = Path(input_file).suffix.lower().replace(".", "")

    # Handle output path - use session_dir with source filename if null
    output_path = params.get("output_path")
    if output_path is None:
        input_path = Path(input_file)
        output_filename = input_path.stem + f".{output_format}"
        output_path = os.path.join(context.session_dir, output_filename)
    else:
        # Ensure output path has correct extension if user provided path
        if not output_path.lower().endswith(f".{output_format}"):
            output_path = f"{output_path}.{output_format}" if not Path(output_path).suffix else output_path

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Build calibre conversion command
    cmd = ["ebook-convert", input_file, output_path]

    # Device-specific settings
    device_profiles = {
        "generic": "generic_eink",
        "kindle": "kindle",
        "kindle_paperwhite": "kindle_pw",
        "ipad": "ipad",
        "kobo": "kobo",
        "nook": "nook"
    }
    cmd.extend(["--output-profile", device_profiles.get(target_device, "generic_eink")])

    # Quality settings based on input and output formats
    quality_settings = {
        "low": [],
        "medium": ["--pretty-print"],
        "high": ["--pretty-print", "--linearize-tables"],
        "best": [
            "--pretty-print",
            "--linearize-tables",
            "--enable-heuristics",
            "--smarten-punctuation"
        ]
    }
    cmd.extend(quality_settings.get(quality, quality_settings["high"]))

    # Format-specific optimizations
    if output_format in ["mobi", "azw3"]:
        cmd.extend(["--mobi-file-type", "new", "--mobi-toc"])
        if output_format == "azw3":
            cmd.extend(["--mobi-keep-original-images"])

    elif output_format == "epub":
        cmd.extend([
            "--remove-paragraph-spacing",
            "--insert-blank-line"
        ])

    elif output_format == "pdf":
        # PDF specific options - using simpler approach
        cmd.extend(["--paper-size", "a4"])

    # Preserve metadata option
    if preserve_metadata:
        cmd.extend(["--prefer-metadata-cover"])

    # Add custom options if provided
    if custom_options and custom_options.strip():
        custom_args = custom_options.strip().split()
        cmd.extend(custom_args)

    try:
        # Execute conversion
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # Verify output file was created
        if not os.path.exists(output_path):
            raise ValueError("Conversion failed: Output file was not created")

        return {"output_file": output_path}

    except subprocess.CalledProcessError as e:
        error_msg = f"Conversion failed: {e.stderr}" if e.stderr else str(e)

        # Check for common errors and provide helpful messages
        if "DRM" in error_msg.upper() or "ENCRYPTION" in error_msg.upper():
            error_msg += "\nNote: This file may be DRM-protected. DRM-protected files cannot be converted."
        elif "not found" in error_msg.lower():
            error_msg += "\nNote: Make sure Calibre is properly installed."
        elif input_format == output_format:
            error_msg += f"\nNote: Input and output formats are the same ({input_format}). No conversion needed."

        raise ValueError(error_msg)

    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")
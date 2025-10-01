#region generated meta
import typing
class Inputs(typing.TypedDict):
    input_file: str
    output_format: typing.Literal["epub", "mobi", "azw3", "pdf", "txt", "html"]
    output_path: str
    quality: typing.Literal["low", "medium", "high", "best"]
    preserve_metadata: bool
    target_device: typing.Literal["generic", "kindle", "kindle_paperwhite", "ipad", "kobo", "nook"]
    custom_options: str | None
class Outputs(typing.TypedDict):
    output_file: typing.NotRequired[str]
    conversion_log: typing.NotRequired[str]
    file_info: typing.NotRequired[dict]
#endregion

from oocana import Context
import subprocess
import os
import mimetypes
from pathlib import Path

def get_file_info(file_path: str) -> dict:
    """Get basic information about a file"""
    if not os.path.exists(file_path):
        return {}

    stat = os.stat(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)

    return {
        "filename": os.path.basename(file_path),
        "size": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "extension": Path(file_path).suffix.lower(),
        "mime_type": mime_type
    }

def main(params: Inputs, context: Context) -> Outputs:
    """
    Universal ebook format converter supporting multiple formats

    Args:
        params: Input parameters containing file paths and settings
        context: OOMOL context object

    Returns:
        Output dictionary with converted file path, log, and file information
    """

    input_file = params["input_file"]
    output_format = params["output_format"]
    output_path = params["output_path"]
    quality = params["quality"]
    preserve_metadata = params["preserve_metadata"]
    target_device = params["target_device"]
    custom_options = params.get("custom_options", "")

    # Validate input file exists
    if not os.path.exists(input_file):
        raise ValueError(f"Input file does not exist: {input_file}")

    # Get input file info
    input_info = get_file_info(input_file)
    input_format = Path(input_file).suffix.lower().replace(".", "")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Ensure output path has correct extension
    if not output_path.lower().endswith(f".{output_format}"):
        output_path = f"{output_path}.{output_format}" if not Path(output_path).suffix else output_path

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

    log_messages = []
    log_messages.append(f"Converting {input_file} ({input_format.upper()}) to {output_path} ({output_format.upper()})")
    log_messages.append(f"Input file size: {input_info.get('size_mb', 0)} MB")
    log_messages.append(f"Quality setting: {quality}")
    log_messages.append(f"Target device: {target_device}")
    log_messages.append(f"Preserve metadata: {preserve_metadata}")
    if custom_options:
        log_messages.append(f"Custom options: {custom_options}")

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
        if not os.path.exists(output_path):
            raise ValueError("Conversion failed: Output file was not created")

        # Get output file info
        output_info = get_file_info(output_path)
        log_messages.append(f"Output file size: {output_info.get('size_mb', 0)} MB")

        file_info = {
            "input": input_info,
            "output": output_info,
            "conversion": {
                "from_format": input_format,
                "to_format": output_format,
                "quality": quality,
                "device": target_device,
                "size_change_mb": round(output_info.get('size_mb', 0) - input_info.get('size_mb', 0), 2)
            }
        }

        return {
            "output_file": output_path,
            "conversion_log": "\n".join(log_messages),
            "file_info": file_info
        }

    except subprocess.CalledProcessError as e:
        error_msg = f"Conversion failed: {e.stderr}" if e.stderr else str(e)

        # Check for common errors and provide helpful messages
        if "DRM" in error_msg.upper() or "ENCRYPTION" in error_msg.upper():
            error_msg += "\nNote: This file may be DRM-protected. DRM-protected files cannot be converted."
        elif "not found" in error_msg.lower():
            error_msg += "\nNote: Make sure Calibre is properly installed."
        elif input_format == output_format:
            error_msg += f"\nNote: Input and output formats are the same ({input_format}). No conversion needed."

        log_messages.append(f"Error: {error_msg}")
        raise ValueError("\n".join(log_messages))

    except Exception as e:
        log_messages.append(f"Unexpected error: {str(e)}")
        raise ValueError("\n".join(log_messages))
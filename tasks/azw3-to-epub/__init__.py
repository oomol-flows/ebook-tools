#region generated meta
import typing
class Inputs(typing.TypedDict):
    input_azw3: str
    output_path: str | None
    quality: typing.Literal["low", "medium", "high", "best"] | None
    preserve_metadata: bool | None
    fix_drm_protected: bool | None
    clean_formatting: bool | None
class Outputs(typing.TypedDict):
    output_file: typing.NotRequired[str]
#endregion

from oocana import Context
import subprocess
import os
from pathlib import Path

def main(params: Inputs, context: Context) -> Outputs:
    """
    Convert AZW3/AZW file to EPUB format using Calibre

    Args:
        params: Input parameters containing file paths and settings
        context: OOMOL context object

    Returns:
        Output dictionary with converted file path
    """

    input_file = params["input_azw3"]
    quality = params.get("quality") or "high"  # Recommended default
    preserve_metadata = params.get("preserve_metadata")
    if preserve_metadata is None:
        preserve_metadata = True  # Recommended default
    fix_drm_protected = params.get("fix_drm_protected")
    if fix_drm_protected is None:
        fix_drm_protected = False  # Recommended default
    clean_formatting = params.get("clean_formatting")
    if clean_formatting is None:
        clean_formatting = True  # Recommended default

    # Validate input file exists
    if not os.path.exists(input_file):
        raise ValueError(f"Input AZW3 file does not exist: {input_file}")

    # Handle output path - use session_dir with source filename if null
    output_file = params.get("output_path")
    if output_file is None:
        input_path = Path(input_file)
        output_filename = input_path.stem + ".epub"
        output_file = os.path.join(context.session_dir, output_filename)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Build calibre conversion command
    cmd = ["ebook-convert", input_file, output_file]

    # Quality settings for AZW3 to EPUB conversion
    quality_settings = {
        "low": ["--output-profile", "generic_eink"],
        "medium": ["--output-profile", "generic_eink", "--pretty-print"],
        "high": ["--output-profile", "generic_eink", "--pretty-print", "--linearize-tables"],
        "best": [
            "--output-profile", "generic_eink",
            "--pretty-print",
            "--linearize-tables",
            "--unsmarten-punctuation",
            "--asciiize"
        ]
    }
    cmd.extend(quality_settings.get(quality, quality_settings["high"]))

    # Preserve metadata option
    if preserve_metadata:
        cmd.extend(["--preserve-cover-aspect-ratio"])

    # DRM handling (note: this only works for non-protected files)
    if fix_drm_protected:
        cmd.extend(["--ignore-drm-errors"])

    # Clean formatting for better EPUB compatibility
    if clean_formatting:
        cmd.extend([
            "--fix-indents",
            "--remove-paragraph-spacing",
            "--remove-paragraph-spacing-indent-size", "1.5",
            "--insert-blank-line",
            "--html-unwrap-factor", "0.4"
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

        # Check for common DRM-related errors
        if "DRM" in error_msg.upper() or "ENCRYPTION" in error_msg.upper():
            error_msg += "\nNote: This file may be DRM-protected. DRM-protected files cannot be converted."

        raise ValueError(error_msg)

    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")
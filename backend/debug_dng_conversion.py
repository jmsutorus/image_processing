#!/usr/bin/env python3
"""
Debug script for DNG conversion issues.
Tests the conversion process step-by-step with detailed logging.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from converter import _convert_dng, ConversionError
from PIL import Image, ImageOps
import subprocess

def check_image_info(image_path, label):
    """Check and display image information."""
    print(f"\n{'='*60}")
    print(f"{label}: {image_path}")
    print(f"{'='*60}")

    if not os.path.exists(image_path):
        print("  ❌ File does not exist")
        return

    # File size
    size_mb = os.path.getsize(image_path) / (1024 * 1024)
    print(f"  File size: {size_mb:.2f} MB")

    # PIL info
    try:
        with Image.open(image_path) as img:
            print(f"  Dimensions: {img.size} (width x height)")
            print(f"  Mode: {img.mode}")
            print(f"  Format: {img.format}")

            # Check EXIF
            exif = img.getexif()
            if exif:
                orientation = exif.get(274, None)  # 274 is Orientation tag
                orientation_names = {
                    1: "Normal (0°)",
                    3: "180°",
                    6: "90° CW (Rotate 270° to view)",
                    8: "90° CCW (Rotate 90° to view)"
                }
                if orientation:
                    print(f"  EXIF Orientation: {orientation} = {orientation_names.get(orientation, 'Unknown')}")
                else:
                    print(f"  EXIF Orientation: Not set")

                # Other useful tags
                make = exif.get(271, "Unknown")  # Make
                model = exif.get(272, "Unknown")  # Model
                datetime = exif.get(306, "Unknown")  # DateTime
                print(f"  Camera: {make} {model}")
                print(f"  DateTime: {datetime}")
            else:
                print(f"  EXIF: No EXIF data found")
    except Exception as e:
        print(f"  ❌ Error reading with PIL: {e}")

    # Exiftool info
    try:
        result = subprocess.run(
            ['exiftool', '-Orientation', '-ImageWidth', '-ImageHeight', image_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"\n  Exiftool output:")
            for line in result.stdout.strip().split('\n'):
                print(f"    {line}")
        else:
            print(f"  ⚠️ exiftool error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"  ⚠️ exiftool timed out")
    except FileNotFoundError:
        print(f"  ⚠️ exiftool not found in PATH")

def test_exif_transpose():
    """Test ImageOps.exif_transpose behavior."""
    print(f"\n{'='*60}")
    print(f"Testing ImageOps.exif_transpose() Behavior")
    print(f"{'='*60}")

    test_path = "test_images/test_result_v2.jpg"
    if not os.path.exists(test_path):
        print(f"  ⚠️ Test file not found: {test_path}")
        return

    print(f"\n1. Opening image...")
    img = Image.open(test_path)
    print(f"   Size before: {img.size}")
    exif_before = img.getexif()
    orientation_before = exif_before.get(274, 1) if exif_before else 1
    print(f"   Orientation before: {orientation_before}")

    print(f"\n2. Calling ImageOps.exif_transpose()...")
    result = ImageOps.exif_transpose(img)

    print(f"   Returned value type: {type(result)}")
    print(f"   Result is None: {result is None}")
    print(f"   Result is img (same object): {result is img}")

    if result:
        print(f"   Size after: {result.size}")
        exif_after = result.getexif()
        orientation_after = exif_after.get(274, 1) if exif_after else 1
        print(f"   Orientation after: {orientation_after}")

        # Check if dimensions changed
        if img.size != result.size:
            print(f"   ✅ Dimensions changed (rotation applied)")
        else:
            print(f"   ⚠️ Dimensions unchanged")

        # Check if orientation was reset
        if orientation_after == 1 and orientation_before != 1:
            print(f"   ✅ Orientation reset to 1 (normal)")
        elif orientation_after != 1:
            print(f"   ⚠️ Orientation not reset (still {orientation_after})")

    img.close()

def test_full_conversion():
    """Test the full conversion process."""
    print(f"\n{'='*60}")
    print(f"Testing Full DNG Conversion")
    print(f"{'='*60}")

    input_file = "test_images/sample.DNG"
    output_file = "test_images/debug_output.jpg"

    if not os.path.exists(input_file):
        print(f"  ❌ Input file not found: {input_file}")
        return

    print(f"\n1. Checking input DNG file...")
    check_image_info(input_file, "INPUT DNG")

    print(f"\n2. Running conversion...")
    try:
        _convert_dng(input_file, output_file)
        print(f"   ✅ Conversion succeeded")
    except ConversionError as e:
        print(f"   ❌ Conversion failed: {e}")
        return

    print(f"\n3. Checking output JPEG file...")
    check_image_info(output_file, "OUTPUT JPEG")

    print(f"\n4. Cleaning up...")
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"   Removed {output_file}")

def main():
    """Main test runner."""
    print(f"\n{'#'*60}")
    print(f"# DNG Conversion Debug Tool")
    print(f"{'#'*60}")

    # Test 1: Check existing conversion output
    print(f"\n\nTEST 1: Analyze existing conversion")
    check_image_info("test_images/test_result_v2.jpg", "Existing Conversion Output")

    # Test 2: Test exif_transpose behavior
    print(f"\n\nTEST 2: Test exif_transpose behavior")
    test_exif_transpose()

    # Test 3: Full conversion with logging
    print(f"\n\nTEST 3: Full conversion test")
    test_full_conversion()

    print(f"\n{'#'*60}")
    print(f"# Debug Complete")
    print(f"{'#'*60}\n")

if __name__ == "__main__":
    main()

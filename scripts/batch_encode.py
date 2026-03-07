#!/usr/bin/env python3
"""Batch encode all images in a selected folder using arithmetic and Huffman coding.

This script automatically processes all image files in a selected folder,
applying the same encoding options to each image.
"""

import os
import sys
from pathlib import Path
from tkinter import Tk, filedialog, simpledialog

# Ensure local modules are importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(ROOT, "arithmetic_coding"))
sys.path.insert(0, os.path.join(ROOT, "huffman"))

import arithmetic_coding as _ac_mod
from arithmetic_coding import ArithmeticEncoder
import huffman_coding as _hf_mod
from huffman_coding import HuffmanEncoder

# Import functions from encode_image.py
from encode_image import extract_channel_pixels, encode_arithmetic, encode_huffman, save_json

# Supported image extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}


def choose_folder_and_options():
    """Choose input folder and encoding options."""
    root = Tk()
    root.withdraw()
    
    # Select input folder
    input_folder = filedialog.askdirectory(title="Select folder containing images to encode")
    if not input_folder:
        raise SystemExit("No folder selected")
    
    # Choose encoding options (applied to all images)
    channel = simpledialog.askstring("Channel", "Choose channel for all images: R, G, B or L (luminance). Default R:", initialvalue="R")
    if channel is None:
        raise SystemExit("No channel chosen")
    channel = channel.strip().upper()
    if channel not in ("R", "G", "B", "L"):
        raise SystemExit("Invalid channel")
    
    offset = simpledialog.askinteger("Brightness offset", "Brightness offset for all images (integer, can be negative). Default 0:", initialvalue=0)
    if offset is None:
        offset = 0
    
    return input_folder, channel, offset


def find_image_files(folder_path):
    """Find all image files in the folder."""
    folder = Path(folder_path)
    image_files = []
    
    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            image_files.append(str(file_path))
    
    return sorted(image_files)


def process_image(image_path, channel, offset):
    """Process a single image: extract channel and encode."""
    print(f"Processing: {os.path.basename(image_path)}")
    
    try:
        # Extract pixels
        pixels, shape = extract_channel_pixels(image_path, channel, offset)
        
        # Prepare output prefix
        dir_name, base = os.path.split(image_path)
        name, _ = os.path.splitext(base)
        safe_channel = channel
        out_prefix = os.path.join(dir_name, f"{name}__{safe_channel}")
        
        # Save metadata
        meta = {"image": image_path, "channel": channel, "shape": shape}
        save_json(out_prefix + "__meta.json", meta)
        
        # Encode with both methods
        print("  Encoding arithmetic...")
        encode_arithmetic(pixels, out_prefix)
        
        print("  Encoding Huffman...")
        encode_huffman(pixels, out_prefix)
        
        print(f"  Saved encoded files with prefix: {out_prefix}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error processing {os.path.basename(image_path)}: {e}")
        return False


def main():
    # Get folder and options
    input_folder, channel, offset = choose_folder_and_options()
    
    # Find all images
    image_files = find_image_files(input_folder)
    
    if not image_files:
        print("No image files found in the selected folder.")
        return
    
    print(f"Found {len(image_files)} image files to process.")
    print(f"Using channel: {channel}, offset: {offset}")
    print("-" * 50)
    
    # Process each image
    success_count = 0
    for image_path in image_files:
        if process_image(image_path, channel, offset):
            success_count += 1
        print()
    
    print(f"Batch encoding complete! Successfully processed {success_count}/{len(image_files)} images.")


if __name__ == "__main__":
    main()
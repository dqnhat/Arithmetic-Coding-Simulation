#!/usr/bin/env python3
"""Select an image, extract a channel, optionally change brightness, then
compute frequencies and encode with Arithmetic and Huffman encoders.

Outputs four files in the same directory as the selected image:
 - <image>__<channel>__arithmetic_freq.json
 - <image>__<channel>__arithmetic_encoded.json
 - <image>__<channel>__huffman_freq.json
 - <image>__<channel>__huffman_encoded.json

This script depends on Pillow and the local modules in the repo.
"""

import json
import math
import os
import sys
from collections import Counter
from tkinter import Tk, filedialog, simpledialog

from PIL import Image

# Ensure local modules are importable regardless of package layout
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(ROOT, "arithmetic_coding"))
sys.path.insert(0, os.path.join(ROOT, "huffman"))

import arithmetic_coding as _ac_mod
from arithmetic_coding import ArithmeticEncoder
import huffman_coding as _hf_mod
from huffman_coding import HuffmanEncoder


EOM = "<EOM>"  # legacy name; scripts will use numeric EOM_SYMBOL per file


def choose_image_and_options():
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select an image file",
                                      filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff"), ("All files", "*")])
    if not path:
        raise SystemExit("No file selected")

    channel = simpledialog.askstring("Channel", "Choose channel: R, G, B or L (luminance). Default R:", initialvalue="R")
    if channel is None:
        raise SystemExit("No channel chosen")
    channel = channel.strip().upper()
    if channel not in ("R", "G", "B", "L"):
        raise SystemExit("Invalid channel")

    offset = simpledialog.askinteger("Brightness offset", "Brightness offset (integer, can be negative). Default 0:", initialvalue=0)
    if offset is None:
        offset = 0

    return path, channel, int(offset)


def extract_channel_pixels(path, channel, offset=0):
    im = Image.open(path).convert("RGB")
    if channel == "L":
        im = im.convert("L")
        pixels = list(im.getdata())
        w, h = im.size
    else:
        r, g, b = im.split()
        mapping = {"R": r, "G": g, "B": b}
        ch = mapping[channel]
        pixels = list(ch.getdata())
        w, h = ch.size

    if offset != 0:
        # apply brightness offset and clip
        pixels = [min(255, max(0, p + offset)) for p in pixels]

    return pixels, (h, w)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def encode_arithmetic(pixels, out_prefix):
    freqs = dict(Counter(pixels))
    
    # Compute source entropy (before adding EOM)
    total = sum(freqs.values())
    entropy = 0
    for count in freqs.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    # Choose a numeric EOM symbol not present in pixels
    max_val = max(freqs.keys()) if freqs else -1
    EOM_SYMBOL = int(max_val) + 1
    freqs[EOM_SYMBOL] = 1

    # Estimate needed bits so that the arithmetic encoder has enough range
    total_unique = len(freqs)
    N = len(pixels) + 1  # include EOM
    bits = max(8, math.ceil(math.log2(total_unique + N + 1)) + 2)

    encoder = ArithmeticEncoder(frequencies=freqs, bits=bits, EOM=EOM_SYMBOL)

    # message: pixel values followed by EOM_SYMBOL
    message = list(pixels) + [EOM_SYMBOL]

    bits_out = list(encoder.encode(message))

    freq_meta = {
        "method": "arithmetic",
        "frequencies": freqs,
        "bits": bits,
        "EOM": EOM_SYMBOL,
    }
    encoded_meta = {
        "method": "arithmetic",
        "channel_size_bits": len(pixels) * 8,
        "channel_size_bytes": len(pixels),
        "encoded_bits": len(bits_out),
        "encoded_bytes": (len(bits_out) + 7) // 8,
        "compression_ratio": len(pixels) / ((len(bits_out) + 7) // 8) if (len(bits_out) + 7) // 8 > 0 else float('inf'),
        "source_entropy": entropy,
        "ideal_compression_ratio": 8 / entropy if entropy > 0 else float('inf'),
        "bits": bits_out
    }
    save_json(out_prefix + "__arithmetic_freq.json", freq_meta)
    save_json(out_prefix + "__arithmetic_encoded.json", encoded_meta)

    return freq_meta, encoded_meta


def encode_huffman(pixels, out_prefix):
    freqs = dict(Counter(pixels))
    
    # Compute source entropy (before adding EOM)
    total = sum(freqs.values())
    entropy = 0
    for count in freqs.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    # Use the same numeric EOM symbol as in the arithmetic encoder convention.
    # Choose an EOM that is not one of the pixel values
    max_val = max(freqs.keys()) if freqs else -1
    EOM_SYMBOL = int(max_val) + 1
    freqs[int(EOM_SYMBOL)] = 1
    encoder = HuffmanEncoder(freqs, EOM=EOM_SYMBOL)
    message = list(pixels) + [EOM_SYMBOL]
    bits_str = encoder.encode(message)

    freq_meta = {"method": "huffman", "frequencies": freqs, "EOM": EOM_SYMBOL}
    encoded_meta = {
        "method": "huffman",
        "channel_size_bits": len(pixels) * 8,
        "channel_size_bytes": len(pixels),
        "encoded_bits": len(bits_str),
        "encoded_bytes": (len(bits_str) + 7) // 8,
        "compression_ratio": len(pixels) / ((len(bits_str) + 7) // 8) if (len(bits_str) + 7) // 8 > 0 else float('inf'),
        "source_entropy": entropy,
        "ideal_compression_ratio": 8 / entropy if entropy > 0 else float('inf'),
        "bits": bits_str
    }
    save_json(out_prefix + "__huffman_freq.json", freq_meta)
    save_json(out_prefix + "__huffman_encoded.json", encoded_meta)

    return freq_meta, encoded_meta


def main():
    path, channel, offset = choose_image_and_options()
    pixels, shape = extract_channel_pixels(path, channel, offset)

    dir_name, base = os.path.split(path)
    name, _ = os.path.splitext(base)
    safe_channel = channel
    out_prefix = os.path.join(dir_name, f"{name}__{safe_channel}")

    # Save some metadata about the image/channel
    meta = {"image": path, "channel": channel, "shape": shape}
    save_json(out_prefix + "__meta.json", meta)

    print("Encoding arithmetic... (this may take a while for large images)")
    encode_arithmetic(pixels, out_prefix)

    print("Encoding huffman...")
    encode_huffman(pixels, out_prefix)

    print("Saved encoded files with prefix:", out_prefix)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Decode encoded JSON files produced by `encode_image.py`.

The script will ask the user to pick one of the encoded JSON files and
attempt to decode both arithmetic and huffman encodings if present, then
reconstruct the channel as a raw byte array and save as a PNG next to the
original files.
"""

import json
import os
import sys
from tkinter import Tk, filedialog
from PIL import Image

# Make local modules importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(ROOT, "arithmetic_coding"))
sys.path.insert(0, os.path.join(ROOT, "huffman"))

import arithmetic_coding as _ac_mod
from arithmetic_coding import ArithmeticEncoder
import huffman_coding as _hf_mod
from huffman_coding import HuffmanEncoder


def choose_file():
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select encoded JSON file",
                                      filetypes=[("JSON files", "*.json"), ("All files", "*")])
    if not path:
        raise SystemExit("No file selected")
    return path


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def attempt_arithmetic(freq_meta, encoded_meta):
    # freq_meta must contain initial_symbols and bits
    initial_symbols = freq_meta.get("initial_symbols")
    bits = freq_meta.get("bits")
    EOM_SYMBOL = freq_meta.get("EOM")
    if initial_symbols is None or bits is None:
        raise ValueError("Invalid arithmetic metadata")
    encoder = ArithmeticEncoder(frequencies=initial_symbols, bits=bits, EOM=EOM_SYMBOL)
    bits_list = encoded_meta.get("bits")
    if bits_list is None:
        raise ValueError("No bits in encoded metadata")

    decoded = list(encoder.decode(bits_list))
    return decoded


def attempt_huffman(freq_meta, encoded_meta):
    freqs = freq_meta.get("frequencies")
    EOM_SYMBOL = freq_meta.get("EOM")
    if freqs is None:
        raise ValueError("Invalid huffman metadata")
    encoder = HuffmanEncoder(freqs, EOM=EOM_SYMBOL)
    bits_str = encoded_meta.get("bits")
    if bits_str is None:
        raise ValueError("No bits in encoded metadata")
    decoded = encoder.decode(bits_str)
    return decoded


def save_channel_as_image(pixels, out_path, mode="L", size=None):
    if size is None:
        # attempt to infer size as square
        n = len(pixels)
        side = int(n ** 0.5)
        if side * side == n:
            size = (side, side)
        else:
            size = (n, 1)

    im = Image.new(mode, size)
    # ignore EOM tokens when building pixel data
    cleaned = []
    for p in pixels:
        if p == EOM_SYMBOL if isinstance(p, type(p)) and False else False:
            # defensive no-op; keep standard conversion below
            pass
        cleaned.append(int(p) if not (isinstance(p, str) and p == "<EOM>") else 0)

    im.putdata(cleaned[: size[0] * size[1]])
    im.save(out_path)


def main():
    path = choose_file()
    data = load_json(path)
    base = os.path.splitext(path)[0]

    # Try to locate companion freq and encoded files with arithmetic/huffman
    dir_name = os.path.dirname(path)
    name_base = os.path.basename(base).rsplit("__", 1)[0]

    # Attempt to load meta file saved by the encoder to get the original shape
    meta_path = name_base + "__meta.json"
    meta = None
    try:
        meta = load_json(os.path.join(dir_name, meta_path))
        shape = tuple(meta.get("shape")) if meta and "shape" in meta else None
    except Exception:
        shape = None
    # Try arithmetic
    ar_freq_path = base.replace("__arithmetic_encoded", "__arithmetic_freq") + ".json"
    hf_freq_path = base.replace("__huffman_encoded", "__huffman_freq") + ".json"

    # Provide useful outputs
    outputs = []

    try:
        if data.get("method") == "arithmetic":
            freq_meta = load_json(ar_freq_path)
            decoded = attempt_arithmetic(freq_meta, data)
            out_img = base + "__arithmetic_decoded.png"
            save_channel_as_image(decoded, out_img, size=shape)
            outputs.append(out_img)
    except Exception as exc:
        print("Arithmetic decode failed:", exc)

    try:
        if data.get("method") == "huffman":
            freq_meta = load_json(hf_freq_path)
            decoded = attempt_huffman(freq_meta, data)
            out_img = base + "__huffman_decoded.png"
            save_channel_as_image(decoded, out_img, size=shape)
            outputs.append(out_img)
    except Exception as exc:
        print("Huffman decode failed:", exc)

    if outputs:
        print("Saved decoded images:")
        for o in outputs:
            print(" ", o)
    else:
        print("No decoded outputs produced.")


if __name__ == "__main__":
    main()

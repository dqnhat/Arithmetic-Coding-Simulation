# File selection
import tkinter as tk
from tkinter import filedialog
import sys

import os
import json
import pandas as pd
from pathlib import Path


def export_encoding_comparison(input_folder, output_excel):
    """Export compression results comparing arithmetic and huffman encodings."""
    records = []
    input_folder = Path(input_folder)
    output_excel = Path(output_excel)

    # Find all encoded JSON files
    encoded_files = list(input_folder.glob("*_encoded.json"))
    
    # Group by base name (image__channel)
    grouped = {}
    for file in encoded_files:
        # Extract base name by removing __arithmetic_encoded, __huffman_encoded
        base_name = file.name.replace("__arithmetic_encoded.json", "").replace("__huffman_encoded.json", "")
        if base_name not in grouped:
            grouped[base_name] = {}
        
        method = "arithmetic" if "arithmetic" in file.name else "huffman"
        grouped[base_name][method] = file

    # Process each group
    for base_name, files in grouped.items():
        record = {"image_channel": base_name}
        
        # Load arithmetic data
        if "arithmetic" in files:
            try:
                with open(files["arithmetic"], "r", encoding="utf-8") as f:
                    arith_data = json.load(f)
                record["arithmetic_channel_size_bytes"] = arith_data.get("channel_size_bytes")
                record["arithmetic_encoded_bits"] = arith_data.get("encoded_bits")
                record["arithmetic_encoded_bytes"] = arith_data.get("encoded_bytes")
                record["arithmetic_compression_ratio"] = arith_data.get("compression_ratio")
                record["arithmetic_source_entropy"] = arith_data.get("source_entropy")
                record["arithmetic_ideal_ratio"] = arith_data.get("ideal_compression_ratio")
            except Exception as e:
                print(f"❌ Error reading arithmetic data for {base_name}: {e}")
        
        # Load huffman data
        if "huffman" in files:
            try:
                with open(files["huffman"], "r", encoding="utf-8") as f:
                    huffman_data = json.load(f)
                record["huffman_channel_size_bytes"] = huffman_data.get("channel_size_bytes")
                record["huffman_encoded_bits"] = huffman_data.get("encoded_bits")
                record["huffman_encoded_bytes"] = huffman_data.get("encoded_bytes")
                record["huffman_compression_ratio"] = huffman_data.get("compression_ratio")
                record["huffman_source_entropy"] = huffman_data.get("source_entropy")
                record["huffman_ideal_ratio"] = huffman_data.get("ideal_compression_ratio")
            except Exception as e:
                print(f"❌ Error reading huffman data for {base_name}: {e}")
        
        # Calculate comparison metrics
        if "arithmetic" in files and "huffman" in files:
            arith_ratio = record.get("arithmetic_compression_ratio", 0)
            huffman_ratio = record.get("huffman_compression_ratio", 0)
            if arith_ratio and huffman_ratio:
                record["better_method"] = "arithmetic" if arith_ratio > huffman_ratio else "huffman"
                record["ratio_difference"] = abs(arith_ratio - huffman_ratio)
        
        records.append(record)

    # Create DataFrame
    df = pd.DataFrame(records)
    
    # Save to Excel
    df.to_excel(output_excel, index=False)
    print(f"✅ Saved {len(df)} records to {output_excel}")


if __name__ == "__main__":
    root = tk.Tk()
    
    # Select input folder with encoded JSON files
    input_folder = filedialog.askdirectory(
        title="Select folder with encoded JSON files"
    )
    
    if not input_folder:
        sys.exit()
    
    # Select output Excel file
    output_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        title="Save comparison results as",
    )
    
    if not output_path:
        sys.exit()
    
    export_encoding_comparison(input_folder, output_path)


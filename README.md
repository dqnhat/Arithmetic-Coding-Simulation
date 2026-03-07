# Arithmetic-Coding-Simulation
This project simulate the process of encode a image in JPEG 2000 format using Arithmetic Coding and compare its performent with huffman coding.


## Source

Arithmetic Coding: https://github.com/tommyod/arithmetic-coding.git

Sample Image Data Set: [Random Image Sample Dataset](https://www.kaggle.com/datasets/pankajkumar2002/random-image-sample-dataset)

## How to use

1. Install package

> pip install -r requirements.txt

2. Encode

> python scripts\encode_image.py

  - Select image and channel (Red, green, blue, lumin)
  - Program auto encode to 4 file json
    - Encode arithmetic
    - Arithmetic frequencies
    - Encode huffman
    - Huffman frequencies

3. Decode

> python scripts\decode_image.py

  - Select encode json
  - Program auto decode to image
    - Find frequencies file
    - Find meta file

Since encode process only use one color channel, decode only have one channel.
# -*- coding: utf-8 -*-
"""
This module implements a HuffmanEncoder class for encoding and decoding.


Minimal example
===============

Create a message consisting of symbols.

>>> message = ['A', 'B', 'B', 'B', '<EOM>']

Create frequency counts.

>>> frequencies = {'A': 1, 'B': 3, '<EOM>': 1}

Create the encoder and encode the message.

>>> encoder = HuffmanEncoder(frequencies)
>>> bits = encoder.encode(message)
>>> bits
'10111100'

Verify decoding returns the original message.

>>> encoder.decode(bits)
['A', 'B', 'B', 'B', '<EOM>']


Compression example
===================

>>> import random
>>> rng = random.Random(42)
>>> message = rng.choices(['e', 'q'], weights=[136, 1], k=1000) + ['<EOM>']
>>> frequencies = {'e': 13600, 'q': 100, '<EOM>': 1}

>>> encoder = HuffmanEncoder(frequencies)
>>> encoded = encoder.encode(message)
>>> decoded = encoder.decode(encoded)
>>> decoded == message
True
"""

import heapq
from collections import defaultdict


class Node:
    """A node in the Huffman tree."""

    def __init__(self, freq, symbol=None, left=None, right=None):
        self.freq = freq
        self.symbol = symbol
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq


class HuffmanEncoder:
    """Huffman encoder/decoder."""

    def __init__(self, frequencies, EOM="<EOM>"):
        """
        Initialize the Huffman encoder.

        Parameters
        ----------
        frequencies : dict
            Dictionary mapping symbols to frequencies.
        EOM : str
            End of message symbol.
        """

        self.EOM = EOM
        self.frequencies = frequencies.copy()

        if self.EOM not in self.frequencies:
            raise ValueError("Frequencies must include the EOM symbol.")

        self.root = self._build_tree()
        self.codes = {}
        self._generate_codes(self.root, "")

        # reverse lookup for decoding
        self.reverse_codes = {v: k for k, v in self.codes.items()}

    def _build_tree(self):
        """Build Huffman tree using a priority queue."""
        heap = [Node(freq, sym) for sym, freq in self.frequencies.items()]
        heapq.heapify(heap)

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)

            merged = Node(left.freq + right.freq, None, left, right)
            heapq.heappush(heap, merged)


        return heap[0]

    def _generate_codes(self, node, current_code):
        """Generate Huffman codes recursively."""
        if node is None:
            return

        if node.symbol is not None:
            self.codes[node.symbol] = current_code or "0"
            return

        self._generate_codes(node.left, current_code + "0")
        self._generate_codes(node.right, current_code + "1")

    def encode(self, iterable):
        """
        Encode an iterable of symbols into a bit string.

        Examples
        --------
        >>> frequencies = {'A':2, 'B':1, '<EOM>':1}
        >>> encoder = HuffmanEncoder(frequencies)
        >>> encoder.encode(['A','B','<EOM>'])
        '01011'
        """
        bits = []

        for symbol in iterable:
            if symbol not in self.codes:
                raise ValueError(f"Unknown symbol: {symbol}")
            bits.append(self.codes[symbol])

        return "".join(bits)

    def decode(self, bits):
        """
        Decode a bit string into symbols.

        Examples
        --------
        >>> frequencies = {'A':2, 'B':1, '<EOM>':1}
        >>> encoder = HuffmanEncoder(frequencies)
        >>> encoded = encoder.encode(['A','B','<EOM>'])
        >>> encoder.decode(encoded)
        ['A', 'B', '<EOM>']
        """
        result = []
        buffer = ""

        for bit in bits:
            buffer += bit
            if buffer in self.reverse_codes:
                symbol = self.reverse_codes[buffer]
                result.append(symbol)
                buffer = ""
                if symbol == self.EOM:
                    break

        return result


if __name__ == "__main__":
    # Example
    message = ["B", "A", "A", "A", "<EOM>"]
    frequencies = {"A": 3, "B": 1, "<EOM>": 1}

    encoder = HuffmanEncoder(frequencies)

    bits = encoder.encode(message)
    decoded = encoder.decode(bits)

    print("Codes:", encoder.codes)
    print("Encoded:", bits)
    print("Decoded:", decoded)

    assert decoded == message


if __name__ == "__main__":
    import doctest
    doctest.testmod()
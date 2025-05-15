# Rotate svg by 90 degree, for yEd generated diagrams
from bs4 import BeautifulSoup
import sys

bs = BeautifulSoup(sys.stdin, "xml")
height = bs.svg.attrs["height"]
width = bs.svg.attrs["width"]

bs = BeautifulSoup(f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" height="{width}" width="{height}">
<g transform="rotate(90 0 0) translate(0 -{height})">
{bs.svg}
</g>
</svg>
""", "xml")
print(bs)
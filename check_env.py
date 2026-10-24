"""Check that the packages iso2cii.py needs are installed.

Run it in the same environment as the tool:

    conda activate neutral_convertor
    python check_env.py
"""

import importlib.util
import sys

# import name -> pip install name
REQUIRED = {
    "fitz": "pymupdf",
    "rapidocr_onnxruntime": "rapidocr-onnxruntime",
    "PIL": "pillow",
    "numpy": "numpy",
    "openpyxl": "openpyxl",
}


def missing_packages(required=None):
    """Return the pip names of packages that cannot be imported."""
    required = REQUIRED if required is None else required
    return [pip for mod, pip in required.items() if importlib.util.find_spec(mod) is None]


def main():
    missing = missing_packages()
    if not missing:
        print("All packages found.")
        return 0
    print("Missing packages: " + ", ".join(missing))
    print("Install them with:  pip install " + " ".join(missing))
    return 1


if __name__ == "__main__":
    sys.exit(main())

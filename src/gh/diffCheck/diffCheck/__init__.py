import os
import sys

__version__ = "0.0.17"

PATH_TO_DLL = "dlls"
extra_dll_dir = os.path.join(os.path.dirname(__file__), PATH_TO_DLL)
os.add_dll_directory(extra_dll_dir)
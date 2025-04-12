import os
from pathlib import Path
import csv
import sys

try:
    from module.nlp.process_csv import read_csv
except ModuleNotFoundError:
    print("ModuleNotFoundError: Could not find module process_csv from module.nlp")
    print("Please check the path to the module.nlp")
    print("Current working directory: (os)", os.getcwd())
    print("Current working directory: (pathlib)", Path.cwd())
    path__from_modules = Path('modules/nlp/process_csv.py').resolve()
    path__from_nlp = Path('nlp/process_csv.py').resolve()
    path__from_and_modules = Path('/modules/nlp/process_csv.py').resolve()
    print("path finds using filepath: \n")
    print("resolve path using 'modules/nlp/[filename]':\t\t", path__from_modules)
    print("resolve path using 'nlp/[filename]':\t\t\t",  path__from_nlp)
    print("resolve path using '/modules/nlp/[filename]':\t\t", path__from_and_modules)

    current_file = Path(__file__).resolve()
    current_dir = os.path.dirname(__file__)
    wd = Path('..').resolve()
    print("\ncurrent file is: ", current_file)
    print("current directory is: ", current_dir)
    print("working directory is: ", wd)

    print("\nos relpath commands:")
    module_path = os.path.abspath("nlp/process_csv.py")  
    relpath_wd = os.path.relpath(module_path, '..')
    relpath_curr = os.path.relpath(module_path, current_file)
    print("relative path of module to working directory: ", relpath_wd)
    print("relative path of module to current file: ", relpath_curr)
    print("Module search path: ", sys.path)

def run_nlp(filepath):
    # read csv file
    fields, rows = read_csv(filepath)
    print(fields)
    print(rows)


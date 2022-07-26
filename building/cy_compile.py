from sys import argv

def print_usage():
    print("Usage :")
    print("py cy_compile.py <source>   -> Compiles the file(s) at source (may be a file or folder)")
    exit()

if len(argv) != 2:
    print_usage()

import os.path as pth
import os

target = argv[1]

if pth.isfile(target) and target.endswith((".py", ".pyx")):
    files = [target]
elif pth.isdir(target):
    from fs.iterators import type_iter
    py_it = type_iter("py", target)
    pyx_it = type_iter("pyx", target)
    files = list(pi for pi in py_it if pth.basename(pi) != "__init__.py") + list(pi for pi in pyx_it if pth.basename(pi) != "__init__.py")
else:
    print("Could not compile " + repr(target))
    exit()

argv[1:] = ["build_ext", "--inplace"]

if target[0] in "\\/":
    target = target[1:]
target = pth.abspath(target)
current = os.getcwd()
base = current
rel = ""
while pth.commonpath((current, target)) not in (current, target) or "__init__.py" in os.listdir():
    os.chdir("..")
    rel = pth.basename(current) + "/" + rel
    current = os.getcwd()

for i, pi in enumerate(files):
    files[i] = rel + pi

# print("target :", target)
# print("current :", current)
# print("base :", base)
# print("rel :", rel)
# print("files :", files)
# print("name :", pth.splitext(pth.basename(target))[0])

from setuptools import setup
from Cython.Build import cythonize

setup(
    name=pth.splitext(pth.basename(target))[0],
    ext_modules=cythonize(files, language="c++", annotate = True),
    zip_safe=False,
    extra_compile_args = ["-O3"]
)
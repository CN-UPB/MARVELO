import setuptools
import sys

if sys.version_info < (3,6):
    sys.exit('Python < 3.6 is not supported for MARVELO.')

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name='marvelo',
    version='2.0-beta',
    license='MIT',
    scripts=["fission/templates/fission_admin.py",
             "fission/templates/fission_interactive.py",
             "fission/templates/fission_debug.py"],
    description="A framework for distributed wirless computing.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.cs.upb.de/js99/afdwc",
    packages=["marvelo"] +
        setuptools.find_packages(include=["fission.*"]),
    install_requires=[
        'dispy>=4.12',
        'lxml==4.6.3',
        'pycos>=4.8.13',
        'graphviz==0.13.2',
    ]
)

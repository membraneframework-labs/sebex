from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent.absolute()

about = {}
with open(here / "sebex" / "__about__.py", encoding="utf-8") as f:
    exec(f.read(), about)

with open(here / "README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__summary__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=about["__uri__"],
    author=about["__author__"],
    author_email=about["__email__"],
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages(include=["sebex", "sebex.*"]),
    python_requires=">=3.7, <4",
    package_data={"sebex.language.elixir": ["elixir_analyzer"],},
    entry_points={"console_scripts": ["sebex=sebex.__main__:main"]},
    install_requires=[
        "python-dotenv~=0.10.5",
        "pygithub~=1.47",
        "gitpython~=3.0",
        "colorama",
        "semver~=2.9",
        "click~=7.0",
        "pyyaml~=5.3",
        "graphviz~=0.13",
        "petname~=2.6",
    ],
    project_urls={
        "Membrane Framework Homepage": "https://membraneframework.org",
        "Source": about["__uri__"],
    },
)

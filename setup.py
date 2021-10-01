# type: ignore
import json
from pathlib import Path
from setuptools import find_namespace_packages, setup

# Get the long description from the README file
ROOT_DIR = Path(__file__).parent.resolve()
long_description = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
VERSION_FILE = ROOT_DIR / "dataclass_argparse" / "VERSION"
VERSION = json.loads(VERSION_FILE.read_text(encoding="utf-8"))["version"]


setup(
    name="dataclass-argparse",
    version=VERSION,
    description="argparse with a type annotated namespace dataclass",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fynnbe/dataclass-argparse",
    author="Fynn Beuttenmüller",
    classifiers=[  # Optional
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_namespace_packages(exclude=["tests"]),  # Required
    install_requires=[],
    extras_require={"test": ["mypy"], "dev": ["pre-commit"]},
    include_package_data=True,
    project_urls={  # Optional
        "Bug Reports": "https://github.com/fynnbe/dataclass-argparse/issues",
        "Source": "https://github.com/fynnbe/dataclass-argparse",
    },
)

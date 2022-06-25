from pathlib import Path
from setuptools import find_packages, setup
from src.expense_bot import __version__

PROJECT_FOLDER = Path(__file__).parent


def read_content(rel_path: str):
    with open(PROJECT_FOLDER / rel_path, "r", encoding="utf-8") as fin:
        return fin.read()


setup(
    name="expense-bot",
    version=__version__,
    description=read_content("README.md"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=read_content("reqs/requirements.txt"),
    zip_safe=False,
)

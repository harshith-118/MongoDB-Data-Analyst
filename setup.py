"""
Setup script for MongoDB Data Analyst package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mongodb-data-analyst",
    version="2.0.0",
    author="MongoDB Data Analyst Team",
    description="A LangGraph-powered natural language interface for querying MongoDB databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harshith-118/MongoDB-Data-Analyst",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mongodb-analyst=main:main",
        ],
    },
)


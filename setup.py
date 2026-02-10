from setuptools import setup, find_packages
import sys

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="comms-shield",
    version="1.0.0",
    description="Defensive Communication Security Toolkit",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "comms-shield=main:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
    ],
)
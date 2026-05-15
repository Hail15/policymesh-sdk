from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="policymesh",
    version="0.1.0",
    author="PolicyMesh",
    author_email="ian@policymesh.net",
    description="Python SDK for the PolicyMesh AI Agent Control Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Hail15/policymesh",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0"
    ]
)
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="moviecp",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A daemon for monitoring, approving, and copying movies to network shares",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/moviecp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "moviecp=moviecp.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "moviecp.web": ["templates/**/*", "static/**/*"],
    },
)

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="email-agent",
    version="1.0.0",
    author="AI Email Agent Team",
    author_email="support@emailagent.ai",
    description="An intelligent email drafting assistant with AI integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/email-agent",
    package_dir={"": "."},
    packages=find_packages(where="."),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "email-agent=src.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.j2", "config/*.yaml", "profiles/*.json"],
    },
)
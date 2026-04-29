from setuptools import setup, find_packages

setup(
    name="aidoc",
    version="0.1.0",
    description="AIDOC — AI-Native Document Format Toolkit",
    long_description=open("../README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="旗鱼",
    python_requires=">=3.8",
    py_modules=["aidoc"],
    package_dir={"": "."},
    entry_points={
        "console_scripts": [
            "aidoc=aidoc:main",
        ],
    },
)

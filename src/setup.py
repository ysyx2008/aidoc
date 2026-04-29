from setuptools import setup, find_packages

setup(
    name="aidoc-tool",
    version="0.1.0",
    description="AIDOC — AI-Native Document Format Toolkit",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="旗鱼",
    author_email="nuoyan_cfan@163.com",
    url="https://github.com/ysyx2008/aidoc",
    project_urls={
        "Documentation": "https://github.com/ysyx2008/aidoc#readme",
        "Source": "https://github.com/ysyx2008/aidoc",
        "Issues": "https://github.com/ysyx2008/aidoc/issues",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.8",
    py_modules=["aidoc"],
    package_dir={"": "."},
    entry_points={
        "console_scripts": [
            "aidoc=aidoc:main",
        ],
    },
)

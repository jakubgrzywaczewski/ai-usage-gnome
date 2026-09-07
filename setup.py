from setuptools import find_packages, setup

setup(
    name="ai-usage",
    version="0.5.0",
    description="GNOME tray app for tracking Claude, Codex, and GitHub Copilot usage limits",
    author="jakubgrzywaczewski",
    url="https://github.com/jakubgrzywaczewski/ai-usage-gnome",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"ai_usage": ["resources/*.svg"]},
    install_requires=[
        "PyGObject>=3.42.0",
        "pycairo>=1.20.0",
        "secretstorage>=3.3.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": ["pytest>=7", "ruff>=0.5"],
    },
    entry_points={
        "console_scripts": [
            "ai-usage=ai_usage.main:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: GTK",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)

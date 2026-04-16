from setuptools import setup, find_packages

setup(
    name="ai-usage",
    version="0.2.0",
    description="GNOME tray app for tracking Claude, Codex, and GitHub Copilot usage limits",
    author="jakubgrzywaczewski",
    url="https://github.com/jakubgrzywaczewski/ai-usage",
    packages=find_packages(),
    package_data={"ai_usage": ["resources/*.svg"]},
    install_requires=[
        "PyGObject>=3.42.0",
        "pycairo>=1.20.0",
        "secretstorage>=3.3.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "ai-usage=ai_usage.main:main",
        ],
    },
    python_requires=">=3.10",
)

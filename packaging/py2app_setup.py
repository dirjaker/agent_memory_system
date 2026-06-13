"""
py2app 打包脚本 - Agent Memory System
======================================
使用方法:
    python packaging/py2app_setup.py py2app
"""

from setuptools import setup

APP = ["src/macos/app.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "packages": ["src"],
    "includes": ["tkinter"],
    "excludes": ["matplotlib", "numpy", "scipy", "pandas", "sentence_transformers"],
    "iconfile": None,
    "plist": {
        "CFBundleName": "Agent Memory System",
        "CFBundleDisplayName": "Agent Memory System",
        "CFBundleIdentifier": "com.dirjaker.agent-memory-system",
        "CFBundleVersion": "2.0.0",
        "CFBundleShortVersionString": "2.0.0",
        "NSHumanReadableCopyright": "MIT License",
    },
}

setup(
    name="Agent Memory System",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)

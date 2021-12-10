from setuptools import setup, find_packages


def readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()


requires = [
    'pytest',
    'pytest-xdist',
    'pytest-parallel',
    'altwalker',
    'selenium<4.0.0',
    'Appium-Python-Client',
    'numpy',
    'langdetect',
    'lxml',
    'bs4',
    'pyautogui',
    'pyperclip',
    'pypeln',
    'mitmproxy'
]


setup(
    name="ui-automation-tools-mbt",
    version="1.2.0",
    author="Ashton Szabo",
    author_email="ashton.szabo@rakuten.com",
    description="Tools for UI automation using model based testing",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/rakutentech/ui-automation-tools-mbt",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requires
)

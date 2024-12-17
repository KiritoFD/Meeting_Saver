from setuptools import setup, find_packages

setup(
    name="meeting-saver",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "flask-cors>=3.0.0",
        "opencv-python>=4.5.0",
        "numpy>=1.19.0",
        "pyyaml>=5.4.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A professional video meeting solution with real-time object removal",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/meeting-saver",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.7",
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.0.0',
            'flake8>=3.9.0',
            'black>=21.0',
            'mypy>=0.900',
        ],
    },
    entry_points={
        'console_scripts': [
            'meeting-saver=src.cli:main',
        ],
    },
) 
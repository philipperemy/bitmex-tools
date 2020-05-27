from setuptools import setup, find_packages

setup(
    name='bitmex-tools',
    version='1.6',
    description='Bitmex Tools',
    author='Philippe Remy',
    license='MIT',
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'sortedcontainers',
        'websocket-client==0.47.0'
    ]
)

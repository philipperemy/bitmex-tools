from setuptools import setup

setup(
    name='bitmex-tools',
    version='1.2',
    description='Bitmex Tools',
    author='Philippe Remy',
    license='MIT',
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    packages=['bitmex_tools'],
    install_requires=[
        'numpy',
        'pandas',
        'websocket-client==0.47.0'
    ]
)

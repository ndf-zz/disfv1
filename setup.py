import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    python_requires='>2.6',
    name="disfv1",
    version="1.0.6",
    author="Nathan Fraser",
    author_email="ndf@metarace.com.au",
    description="FV-1 Disassembler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ndf-zz/disfv1",
    entry_points={
        'console_scripts': [
            'disfv1=disfv1:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
	'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Assemblers',
    ],
    py_modules=['disfv1',],
)


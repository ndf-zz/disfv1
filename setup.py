import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    python_requires='>=3',
    name="disfv1",
    version="1.0.0",
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
        'Development Status :: 3 - Alpha',
	'Environment :: Console',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Assemblers',
    ],
    py_modules=['disfv1',],
)


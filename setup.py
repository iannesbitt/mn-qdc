import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    author='Ian Nesbitt',
    author_email='nesbitt@nceas.ucsb.edu',
    name='mn_qdc',
    version='0.0.1',
    description='DataONE Figshare Qualified Dublin Core staging workflow',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/iannesbitt/mn-qdc',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'dataone.common',
        'dataone.libclient',
        'metapype',
    ],
    extras_require={
        'dev': [
            'sphinx',
        ]
    },
    entry_points = {
        'console_scripts': [
            'mnqdc=mn_qdc.run:main',
            'testmnqdc=mn_qdc.test:main'
        ],
    },
    python_requires='>=3.9, <4.0',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
    license='Apache Software License 2.0',
)
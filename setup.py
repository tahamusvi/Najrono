from setuptools import setup, find_packages

setup(
    name='najrono',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[],
    author='Taha Musvi',
    author_email='TahaM8000@gmail.com',
    description='Django library for managing **Jalali (Persian) dates** in your models',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/tahamusvi/najrono',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

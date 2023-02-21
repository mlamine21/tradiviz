# Tradiviz

## Description

The TraDiViz tool is a python tool based on the networkx library that allows the display of transition diagrams. 
It must connecct to a server running a mongoDB database that follows the structure requirement of the [NOVA software](https://github.com/hcmlab/nova) (see [Documentation](https://rawgit.com/hcmlab/nova/master/docs/index.html#general-structure) for details about the database structure)

## Installation

```
conda create -n travidiz python=3.9.13 

conda activate travidiz

conda install numpy pandas mongodb matplotlib==3.7.0 networkx pillow==9.0.0

cd path/to/TRAVIDIZ_folder/

python transitionGUI.py

```

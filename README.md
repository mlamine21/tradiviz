# Tradiviz

## Description

The TraDiViz tool is a python tool based on the networkx library that allows the display of transition diagrams. 
It must connecct to a server running a mongoDB database that follows the structure requirement of the [NOVA software](https://github.com/hcmlab/nova) (see [Documentation](https://rawgit.com/hcmlab/nova/master/docs/index.html#general-structure) for details about the database structure)

## Installation 

### Windows 

1. Download and install Anaconda if you don't already have it : [Download Anaconda](https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Windows-x86_64.exe)

2. Run an anaconda prompt : Type <kbd>⊞ Win</kbd>, search for 'Anaconda Prompt', then <kbd>Enter ⏎</kbd>.
  
You should now see a terminal looking like this : 
  
```console
  (base) C:\Users\yourusername>
```
3. In the terminal, type the following command then <kbd>Enter ⏎</kbd>:
```
conda create -n tradiviz python=3.9.13 
```
This command is used to create a conda virtual environment with 'tradiviz' as name and configure it to use python v.3.9.13.  
4. After that we have to activate the evironment we just created :   
```
conda activate travidiz
```
The terminal should now look like this : 
  
```console
  (tradiviz) C:\Users\yourusername>
```
5. We then install, in this new environment, all the libraries required by tradiviz to run :
```
conda install numpy pandas pymongo matplotlib==3.7.0 networkx pillow==9.0.0
```
We are now ready to run Tradiviz, go to the [**How to run** section](#how-to-run) to run it, and go directly to step 3.

## How to run
### First run

**Note** : you should first followe the [Installation instructions](#installation) at least one time on the computer you are using.

1. Run an anaconda prompt : Type <kbd>⊞ Win</kbd>, search for 'Anaconda Prompt', then <kbd>Enter ⏎</kbd>.

2. Activate the tradiviz evironment created during the installation :   
```
conda activate travidiz
```
The terminal should now look like this : 
  
```console
  (tradiviz) C:\Users\yourusername>
```
3. Download the github repo : [Download tradiviz](https://github.com/mlamine21/tradiviz/archive/refs/heads/main.zip), , and unzip it in the location of your choice. For example in the 'Documents' folder on your computer. 

4. Go back to the anaconda prompt and move to the location where you extracted the zip file of the github repo with the following command : 
```
cd location/tradiviz-main
```
And replace location with the correct location. For example, if you extracted it in the 'Documents' folder, you should type : 
```
cd Documents/tradiviz-main
```
You can also type the full path to the folder, for example : 
```
cd C:/Users/yourusername/Documents/tradiviz-main
```
5. Now execute the Tradiviz tool with the following command : 
```
python transitionGUI.py
```

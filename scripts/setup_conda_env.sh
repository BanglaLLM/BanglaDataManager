#!/bin/bash

# Check if conda is installed
if ! command -v conda &> /dev/null
then
    echo "conda could not be found. Please install Anaconda or Miniconda."
    exit 1
fi

# Check if the environment already exists
if conda info --envs | grep -q drishtikon
then
    echo "Conda environment 'drishtikon' already exists."
    echo "Activating existing environment..."
else
    echo "Creating new conda environment 'drishtikon'..."
    conda create -n drishtikon python=3.9 -y
fi

# Get the path to the conda base directory
CONDA_BASE=$(conda info --base)

# Activate the environment
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate drishtikon

# Check if activation was successful
if [ $? -ne 0 ]; then
    echo "Failed to activate conda environment. Exiting."
    exit 1
fi

# Install pip in the conda environment
echo "Installing pip in the conda environment..."
conda install pip -y

# Check if pip installation was successful
if [ $? -ne 0 ]; then
    echo "Failed to install pip. Exiting."
    exit 1
fi

# Get the full path to the conda environment's pip
CONDA_PIP="$CONDA_BASE/envs/drishtikon/bin/pip"

# Verify that the pip executable exists
if [ ! -f "$CONDA_PIP" ]; then
    echo "Could not find pip at $CONDA_PIP. Exiting."
    exit 1
fi

# Print Python and pip versions for debugging
echo "Python version:"
"$CONDA_BASE/envs/drishtikon/bin/python" --version
echo "Pip version:"
"$CONDA_PIP" --version

# Check if requirements.txt exists in the parent directory
REQUIREMENTS_FILE="../requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Could not find requirements.txt in the parent directory. Exiting."
    exit 1
fi

# Install the required packages using the conda environment's pip
echo "Installing required packages from $REQUIREMENTS_FILE..."
"$CONDA_PIP" install -r "$REQUIREMENTS_FILE"

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo "Failed to install required packages. Please check your requirements.txt file and try again."
    exit 1
fi

# Print success message
echo "Conda environment 'drishtikon' has been set up and activated."
echo "Required packages have been installed."
echo "To activate this environment in the future, run:"
echo "conda activate drishtikon"
#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Docker on Linux
install_docker_linux() {
    echo "Installing Docker on Linux..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt-get update
    sudo apt-get install -y docker-ce
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
}

# Function to install Docker on macOS
install_docker_macos() {
    echo "Installing Docker on macOS..."
    if command_exists brew; then
        brew install --cask docker
    else
        echo "Homebrew is not installed. Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
}

# Function to install Docker on Windows
install_docker_windows() {
    echo "Installing Docker on Windows..."
    echo "Please download and install Docker Desktop for Windows from: https://www.docker.com/products/docker-desktop"
    echo "After installation, please restart your computer and run this script again to verify the installation."
    exit 0
}

# Function to install Docker Compose
install_docker_compose() {
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
}

# Main script
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if ! command_exists docker; then
        install_docker_linux
    else
        echo "Docker is already installed."
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! command_exists docker; then
        install_docker_macos
    else
        echo "Docker is already installed."
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    if ! command_exists docker; then
        install_docker_windows
    else
        echo "Docker is already installed."
    fi
else
    echo "Unsupported operating system"
    exit 1
fi

# Install Docker Compose if not already installed
if ! command_exists docker-compose; then
    install_docker_compose
else
    echo "Docker Compose is already installed."
fi

echo "Installation complete. Please restart your terminal or log out and back in to apply changes."
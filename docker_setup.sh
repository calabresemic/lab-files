#!/bin/bash

#Check for root
if (( $EUID != 0 )); then
    echo "Please run as root"
    exit 1
fi

#Declare variables
SWAP_CREATE="true"
SWAP_SIZE="6144"

#Swap file management
if [ "${SWAP_CREATE}" == "true" ];
then
    if [[ $(swapon --show) ]]; then
      echo 'Swap Exists'
    else
        echo "Swap file not present creating a new swap file"
        dd if=/dev/zero bs=1M count=${SWAP_SIZE} of=/mnt/docker.swap
        chmod 600 /mnt/docker.swap
        mkswap /mnt/docker.swap
        swapon /mnt/docker.swap
        echo '/mnt/docker.swap swap swap defaults 0 0' | tee -a /etc/fstab
    fi
fi

#Set up repository for docker
echo 'Installing pre-reqs'

apt-get update
apt-get install ca-certificates curl gnupg lsb-release -y

echo "Adding Docker's official GPG key"

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --yes --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

#Install docker
echo "Installing Docker"

apt-get update
apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
#!/bin/bash

nwd="/opt/bwackwat/hell"

mkdir -p $nwd

cd $nwd

set -x

cd $(dirname $BASH_SOURCE)

wget=$(wget "https://raw.githubusercontent.com/bwackwat/hell/master/init.sh")

if [ $? -ne 0 ]; then
  echo "Could not update this init script!"
  exit
fi
  
if [[ -z "$1" ]] ; then
  echo "First argument must be the name of a folder (also internal daemon name) from https://github.com/bwackwat/hell."
  exit
fi

wget=$(wget "https://raw.githubusercontent.com/bwackwat/hell/master/$1/init.sh")

if [ $? -ne 0 ]; then
  echo "Could not pull init.sh script for daemon $1

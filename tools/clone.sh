#!/bin/sh

REPOSRC=$2
LOCALREPO=$3
BRANCH=$1

# We do it this way so that we can abstract if from just git later on
LOCALREPO_VC_DIR=$LOCALREPO/.git

if [ ! -d $LOCALREPO_VC_DIR ]
then
    git clone --branch $BRANCH $REPOSRC $LOCALREPO || echo "Error: failed to clone $REPOSRC"
else
    cd $LOCALREPO
    git pull origin $BRANCH || echo "Error: failed to pull $REPOSRC"
fi

# End
#!/bin/bash

set -o nounset
set -o errexit
set -o pipefail

INPUT=${1:?Add an input directory as the first argument}

rm $INPUT/*_predict.png

for i in $INPUT/*; do
    o=${i%.*}_predict.png

    echo "Recognizing image $i"
    python3 recognize.py --detector face_detection_model --embedding_model openface_nn4.small2.v1.t7 --recognizer output/recognizer.pickle --le output/le.pickle \
        -i $i -o $o
    echo
done

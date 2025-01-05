#!/bin/bash

set -o nounset
set -o errexit
set -o pipefail


rm -rf output
mkdir -p output

# python3 extract_embeddings.py --dataset dataset --embeddings output/embeddings.pickle --detector face_detection_model --embedding_model openface_nn4.small2.v1.t7
# python3 train_model.py --embeddings output/embeddings.pickle --recognizer output/recognizer.pickle --le output/le.pickle

python extract_embeddings.py --dataset dataset --embeddings output/embeddings.pickle --detector face_detection_model --embedding_model openface_nn4.small2.v1.t7
python train_model.py --embeddings output/embeddings.pickle --recognizer output/recognizer.pickle --le output/le.pickle


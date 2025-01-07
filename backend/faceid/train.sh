#!/bin/bash

set -o nounset
set -o errexit
set -o pipefail


rm -rf output
mkdir -p output

# python3 extract_embeddings.py --dataset dataset --embeddings output/embeddings.pickle --detector face_detection_model --embedding_model openface_nn4.small2.v1.t7
# python3 train_model.py --embeddings output/embeddings.pickle --recognizer output/recognizer.pickle --le output/le.pickle
if [ -z "$1" ]; 
then echo "Please provide the path to the backend/faceid directory" exit 1
fi # Change to the specified directory 
cd "$1" || exit
# Change to the backend/faceid directory

# Run the extract_embeddings.py script
python extract_embeddings.py --dataset dataset --embeddings output/embeddings.pickle --detector face_detection_model --embedding_model openface_nn4.small2.v1.t7

# Run the train_model.py script
python train_model.py --embeddings output/embeddings.pickle --recognizer output/recognizer.pickle --le output/le.pickle

# python backend/faceid/extract_embeddings.py --dataset dataset --embeddings output/embeddings.pickle --detector face_detection_model --embedding_model openface_nn4.small2.v1.t7
# python backend/faceid/train_model.py --embeddings output/embeddings.pickle --recognizer output/recognizer.pickle --le output/le.pickle


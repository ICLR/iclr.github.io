import sys
import torch
import json
import pickle
import gzip
from suggest_utils import calc_reviewer_db_mapping, print_text_report, print_progress
from suggest_reviewers import create_embeddings, calc_similarity_matrix
from models import load_model
import torch

accepted_submissions = pickle.load(open("../data/pkl/cached_or.pkl", "br"))

# Load the model
abstracts = []
abstract_keys = list(accepted_submissions.keys())
for k, v in accepted_submissions.items():
    abstracts.append(v.content["abstract"])
conf_abs = abstracts
    
print('Loading model', file=sys.stderr)
model, epoch = load_model(None, "scratch/similarity-model.pt")
model.eval()
assert not model.training

# Get recommendations within the conference
paper_embs = create_embeddings(model, conf_abs)

pickle.dump(paper_embs, open("paper_embeddings.pkl", "bw"))

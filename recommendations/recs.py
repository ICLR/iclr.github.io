import sys
import torch
import json
import pickle
import gzip
from suggest_utils import calc_reviewer_db_mapping, print_text_report, print_progress
from suggest_reviewers import create_embeddings, calc_similarity_matrix
from models import load_model
import torch

accepted_submissions = pickle.load(open("../cached_or.pkl", "br"))

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
intra_recs = calc_similarity_matrix(model, conf_abs, conf_abs)
recs = {}
_, papers =  torch.topk(torch.tensor(intra_recs), 5, -1)
for i in range(papers.shape[0]):
    # print(accepted_submissions[i].content["title"])
    recs[abstract_keys[i]] = []
    for j in range(5):
        # print("\t", accepted_submissions[papers[i, j]].content["title"])
        recs[abstract_keys[i]].append(abstract_keys[j])
        
# Get author recs. 
with gzip.open("scratch/papers.json.gz", "r") as f:
        db = [json.loads(x) for x in f][:100]  # for debug
        db_abs = [x['paperAbstract'] for x in db][:100]
mat = calc_similarity_matrix(model, db_abs, conf_abs)


def get_papers(names):
    inp = [{"ids":[""], "names":[n]} for n in names]
    out = calc_reviewer_db_mapping(inp,
                                   db, author_col="name", author_field='authors')
    print(out.shape)
    data = {}
    for j, n in enumerate(names):
        ind,  = out[:, j].nonzero()
        _, papers = torch.topk(torch.tensor(mat[:, ind].sum(-1)), 25)
        # print("Author:", n)
        # for i in papers:
        #     print("\t", accepted_submissions[i].content["title"])
        #     print()
        #     print()
        data[n] = papers.tolist()
    return data
recs2 = get_papers(pickle.load(open("authors", "br")))

pickle.dump((recs, recs2), open("rec.pkl", "bw"))

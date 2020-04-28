import sys
import torch
import json
import pickle
import gzip
from suggest_utils import calc_reviewer_db_mapping, print_text_report, print_progress
from suggest_reviewers import create_embeddings, calc_similarity_matrix
from models import load_model
import numpy as np
import torch
import hrecs
from autoassigner import auto_assigner, tpms_assignment

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

#from sklearn.metrics import pairwise_distances
#lda_matrix = np.load(open('iclr_paper_topics.np', 'rb'))
#intra_recs = pairwise_distances(lda_matrix, metric="cosine")

# Get recommendations within the conference
intra_recs = calc_similarity_matrix(model, conf_abs, conf_abs)

intra_recs += (-intra_recs.min()) + 1e-5 # make all >0
for i in range(intra_recs.shape[0]):
    intra_recs[i,i] = -1 # declare "COI" with self to avoid rec'ing
recs = {}
recs_n = {}
_, papers =  torch.topk(torch.tensor(intra_recs), 4, -1)
for i in range(papers.shape[0]):
    # print(accepted_submissions[i].content["title"])
    recs[abstract_keys[i]] = []
    recs_n[i] = []
    for j in papers[i]:
        # print("\t", accepted_submissions[papers[i, j]].content["title"])
        recs[abstract_keys[i]].append(abstract_keys[j])
        recs_n[i].append(j.item())

print("DEFAULT ASSIGNMENT")
hrecs.print_rec_stats(intra_recs, recs_n)

if True:
    print("RANDOM ASSIGNMENT")
    n = intra_recs.shape[0]
    def mk_random(i):
        j = np.random.randint(n-1)
        if j >= i: j += 1
        return j
    rnd = { i : [mk_random(i) for _ in range(4)] for i in range(n) }
    hrecs.print_rec_stats(intra_recs, rnd)

if True:
    pr4a = auto_assigner(intra_recs,  # similarity matrix, (#rev*#pap)
                         demand = 4,  # 4 "reviewers" (rec'd papers) per rec'ing paper
                         ability = 4, # maximum number of times any paper is rec'd
                         iter_limit = 4,
                         time_limit = np.inf,
    )
    pr4a.fair_assignment()
    print("PR4A ASSIGNMENT (demand=4, ability=4, iter_limit=4")
    hrecs.print_rec_stats(intra_recs, pr4a.fa)

if True:
    mmatch = tpms_assignment(papload=4, revload=4, similarity=intra_recs)
    print("MAXMATCH ASSIGNMENT")
    hrecs.print_rec_stats(intra_recs, mmatch)

    def print_delta_item(ii, delta, item_id, sc1, sc2, r1, r2):
        print(f"""
        {ii} {item_id} ({delta} : {sc1} -> {sc2})
             {accepted_submissions[abstract_keys[item_id]].content['title']}
             {accepted_submissions[abstract_keys[item_id]].content.get('TL;DR','')}""")
        for j in (r1):
            print(f"""
                 -- {j} [{intra_recs[item_id][j]}] {accepted_submissions[abstract_keys[j]].content['title']}
                 -- {accepted_submissions[abstract_keys[j]].content.get('TL;DR','')}""")
        for j in (r2):
            print(f"""
                 ++ {j} [{intra_recs[item_id][j]}] {accepted_submissions[abstract_keys[j]].content['title']}
                 ++ {accepted_submissions[abstract_keys[j]].content.get('TL;DR','')}""")

    hrecs.print_biggest_deltas(intra_recs, recs_n, mmatch, print_delta_item, k=4)


# Get author recs. 
with gzip.open("scratch/papers.json.gz", "r") as f:
        db = [json.loads(x) for x in f]  # for debug
        db_abs = [x['paperAbstract'] for x in db]
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
        data[n] = [abstract_keys[p] for p in papers.tolist()]
    return data
recs2 = get_papers(pickle.load(open("authors", "br")))

pickle.dump((recs, recs2), open("rec.pkl", "bw"))
import ipdb; ipdb.set_trace() # enter debugger

import pickle
from tqdm import tqdm
import yaml, json

# Converts pkl/cached_or.pkl file to json/cached_or.json
def convert_cached_or():
    notes = pickle.load(open("pkl/cached_or2.pkl", "rb"))

    cached_or_dict = {}
    keys = list(notes.keys())

    for k in tqdm(keys):
        cached_or_dict[k] = {}
        for k2 in notes[k].__dict__:
            if k2 in ["content", "forum", "id"]:
                cached_or_dict[k][k2] = notes[k].__dict__[k2]

    return cached_or_dict

# Converts pkl/rec.pkl file to json/author_records.json and json/paper_records.json
def convert_rec():
    paper_records, author_records = pickle.load(open("pkl/rec.pkl", "rb"))

    paper_records_dict = dict(paper_records)
    author_records_dict = dict(author_records)

    return paper_records_dict, author_records_dict


if __name__ == '__main__':
    site_data = {}

    cached_or = convert_cached_or()
    paper_records, author_records = convert_rec()

    site_data["cached_or"] = cached_or
    site_data["paper_records"] = paper_records
    site_data["author_records"] = author_records
    site_data["sponsors"] = {}
    site_data["workshops"] = {}
    site_data["socials"] = {}
    site_data["calendar"] = {}

    with open("../sitedata/papers.json", "w") as f:
        f.write(json.dumps(site_data["cached_or"]))

    with open("../sitedata/paper_recs.json", "w") as f:
        f.write(json.dumps(site_data["paper_records"]))

    with open("../sitedata/author_recs.json", "w") as f:
        f.write(json.dumps(site_data["author_records"]))

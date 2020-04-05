import pickle, json
from tqdm import tqdm

# Converts pkl/cached_or.pkl file to json/cached_or.json
def convert_cached_or():
    notes = pickle.load(open("pkl/cached_or.pkl", "rb"))

    cached_or_dict = {}
    keys = list(notes.keys())

    for k in tqdm(keys):
        cached_or_dict[k] = notes[k].__dict__

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

    with open("json/site_data.json", "w") as f:
        f.write(json.dumps(site_data, indent=2))
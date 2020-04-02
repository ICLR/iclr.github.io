import pickle, json
from tqdm import tqdm


def convert_cached_or():
    notes = pickle.load(open("pkl/cached_or.pkl", "rb"))

    cached_or_dict = {}
    keys = list(notes.keys())

    for k in tqdm(keys):
        cached_or_dict[k] = notes[k].__dict__

    cached_or_json = json.dumps(cached_or_dict, indent=2)

    with open('json/cached_or.json', 'w') as f:
        f.write(cached_or_json)

def convert_rec():
    paper_records, author_records = pickle.load(open("pkl/rec.pkl", "rb"))

    paper_records_json = json.dumps(dict(paper_records), indent=2)
    author_records_json = json.dumps(dict(author_records), indent=2)

    with open('json/paper_records.json', 'w') as f:
        f.write(paper_records_json)
    
    with open('json/author_records.json', 'w') as f:
        f.write(author_records_json)

convert_rec()

import openreview
import pickle
from suggest_utils import calc_reviewer_db_mapping
import gzip
import json
import pickle
client = openreview.Client(baseurl='https://openreview.net')

authors = set()
for y in ["2017", "2018", "2019", "2020"]:
    blind_notes = {note.id: note
                   for note in openreview.tools.iterget_notes(client,
                                                              invitation = 'ICLR.cc/2020/Conference/-/Blind_Submission', details='original')}
    for k, v in blind_notes.items():
        for author in v.content["authors"]:
            authors.add(author)
pickle.dump(list(authors), open("authors", "wb"))
        

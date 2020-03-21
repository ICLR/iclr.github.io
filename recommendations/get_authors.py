
import openreview
import pickle
from suggest_utils import calc_reviewer_db_mapping
import gzip
import json
import pickle
client = openreview.Client(baseurl='https://openreview.net')
blind_notes = {note.id: note for note in openreview.tools.iterget_notes(client,
                invitation = 'ICLR.cc/2020/Conference/-/Blind_Submission', details='original')}
authors = []
for k, v in blind_notes.items():
    for author in v.content["authors"]:
        authors.append(author)
pickle.dump(authors, open("authors", "wb"))
        

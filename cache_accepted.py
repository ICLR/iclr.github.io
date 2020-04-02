import openreview
import pickle

client = openreview.Client(baseurl='https://openreview.net')
blind_notes = {note.id: note for note in openreview.tools.iterget_notes(client,
                invitation = 'ICLR.cc/2020/Conference/-/Blind_Submission', details='original')}
meta_reviews = openreview.tools.iterget_notes(client, invitation='ICLR.cc/2020/Conference/Paper.*/-/Decision')
accepted_submissions = {decision_note.forum : blind_notes[decision_note.forum]
                        for decision_note in meta_reviews
                        if 'Accept' in decision_note.content['decision']}

# Write out accepted submissions
pickle.dump(accepted_submissions, open("openreview_data/pkl/cached_or.pkl", "bw"))

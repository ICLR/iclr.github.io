from flask import Flask

app = Flask(__name__)
app.config.from_object(__name__)


from flask import Flask, render_template, render_template_string
from flask_frozen import Freezer
import pickle
import os.path
from os import path
import sys

# Load all for openreview one time. 
if path.exists("cached_or"):
    notes = pickle.load(open("cached_or", "br"))

else:
    import openreview
    c = openreview.Client(baseurl='https://openreview.net')
    notes = c.get_notes(invitation='ICLR.cc/2020/Conference/-/Blind_Submission') + \
            c.get_notes(invitation='ICLR.cc/2020/Conference/-/Blind_Submission',
                        offset=1000, limit=1000) + \
            c.get_notes(invitation='ICLR.cc/2020/Conference/-/Blind_Submission',
                        offset=2000, limit=1000)

    pickle.dump(notes, open("cached_or", "bw"))

keywords = {}
for i, n in enumerate(notes):
    n.content["iclr_id"] = i

    if "TL;DR" in n.content:
        n.content["TLDR"] = n.content["TL;DR"]
    else:
        n.content["TLDR"] = n.content["abstract"][:250] + "..."
    for k in n.content["keywords"]:
        keywords.setdefault(k, [])
        keywords[k].append(n)

            

# Pull the OpenReview info for a poster. 
@app.route('/poster_<poster>.html')
def poster(poster):

    node_id = int(poster)
    print(poster, notes[node_id])
    data = {"openreview": notes[node_id], "id": node_id,
            "next": node_id +1 , "prev": node_id-1}
    print(data)
    return render_template('pages/page.html', **data)


# Show by Keyword
@app.route('/keyword_<keyword>.html')
def keyword(keyword):
    data = {"keyword": keyword,
            "openreviews": keywords[keyword]}
    return render_template('pages/keyword.html', **data)



# Code to turn it all static
freezer = Freezer(app, with_no_argument_rules=False, log_url_for=False)
@freezer.register_generator
def your_generator_here():
    for i in range(1, 10):
        yield "poster", {"poster": str(i)}

    for k in keywords:
        if "/" not in k:
            yield "keyword", {"keyword": k}


# Start the app
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(port=5000)

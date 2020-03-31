from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)
app.config.from_object(__name__)


from flask import Flask, render_template, render_template_string
from flask_frozen import Freezer
import pickle
import os.path
from os import path
import sys

# Load all for openreview one time.
notes = pickle.load(open("cached_or.pkl", "br"))
notes_keys = list(notes.keys())
# author_recs = pickle.load(open("rec_cached", "br"))
paper_recs, author_recs = pickle.load(open("rec.pkl", "br"))
# print(author_recs["Yuntian Deng"])
titles = {}
keywords = {}
for i, (k,n) in enumerate(notes.items()):
    n.content["iclr_id"] = k
    # n.content["key_id"] =
    titles[n.content["title"]] = k
    if "TL;DR" in n.content:
        n.content["TLDR"] = n.content["TL;DR"]
    else:
        n.content["TLDR"] = n.content["abstract"][:250] + "..."
    for k in n.content["keywords"]:
        keywords.setdefault(k.lower(), [])
        keywords[k.lower()].append(n)


@app.route('/livestream.html')
def livestream():
    return render_template('pages/main.html', **{})

@app.route('/index.html')
def home():
    return render_template('pages/home.html', **{})

@app.route('/papers_old.html')
def papers():
    data = {"keyword": "all",
            "openreviews": notes.values()}
    return render_template('pages/keyword.html', **data)

@app.route('/papers.html')
def papers_v2():
    data = {"keyword": "all",
            "openreviews": notes.values()}
    return render_template('pages/papers.html', **data)

@app.route('/papers.json')
def papers_raw():
    paper_list = [value.__dict__ for value in notes.values()]
    return jsonify(paper_list)

@app.route('/recs.html')
def recommendations():
    data = {"choices": author_recs.keys(),
            "keywords": keywords.keys(),
            "titles": titles.keys()

    }
    return render_template('pages/recs.html', **data)


@app.route('/title_<title>.html')
def title(title):
    return poster(titles[title])

# Pull the OpenReview info for a poster.
@app.route('/poster_<poster>.html')
def poster(poster):
    note_id = poster
    data = {"openreview": notes[note_id], "id": note_id,
            "paper_recs" : [notes[n] for n in paper_recs[note_id]][1:]}
    # print(data)
    return render_template('pages/page.html', **data)


# Show by Keyword
@app.route('/keyword_<keyword>.html')
def keyword(keyword):
    data = {"keyword": keyword.lower(),
            "openreviews": keywords[keyword.lower()]}
    return render_template('pages/keyword.html', **data)

# Show by Keyword
@app.route('/recs_<author>.html')
def recs(author):
    data = {"keyword": author,
            "openreviews": [notes[n] for n in author_recs[author]]}
    return render_template('pages/keyword.html', **data)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/embeddings_<emb>.json')
def embeddings(emb):
    return send_from_directory('static', 'embeddings_'+emb+'.json')

@app.route('/paper_vis.html')
def paperVis():
    return render_template('pages/papers_vis.html')



# Code to turn it all static
freezer = Freezer(app, with_no_argument_rules=False, log_url_for=False)
@freezer.register_generator
def your_generator_here():
    yield "livestream", {}
    yield "home", {}
    yield "papers", {}
    yield "recommendations", {}


    for i in notes.keys():
        yield "poster", {"poster": str(i)}

    # for t in titles:
    #     yield "title", {"title": t}

    for k in keywords:
        if "/" not in k:
            yield "keyword", {"keyword": k}

    for a in author_recs:
        if "/" not in k:
            yield "recs", {"author": a}

# Start the app
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(port=5000)

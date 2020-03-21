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
notes = pickle.load(open("cached_or.pkl", "br"))
notes_keys = list(notes.keys())
# author_recs = pickle.load(open("rec_cached", "br"))
paper_recs, author_recs = pickle.load(open("rec.pkl", "br"))
# print(author_recs["Yuntian Deng"])
titles = {}
keywords = {}
for i, n in enumerate(notes.values()):
    n.content["iclr_id"] = i

    if "TL;DR" in n.content:
        n.content["TLDR"] = n.content["TL;DR"]
    else:
        n.content["TLDR"] = n.content["abstract"][:250] + "..."
    for k in n.content["keywords"]:
        keywords.setdefault(k.lower(), [])
        keywords[k.lower()].append(n)
    titles[n.content["title"]] = i
         
@app.route('/livestream.html')
def livestream():
    return render_template('pages/main.html', **{})

@app.route('/index.html')
def home():
    return render_template('pages/home.html', **{})

@app.route('/papers.html')
def papers():
    data = {"keyword": "all",
            "openreviews": notes.values()}
    return render_template('pages/keyword.html', **data)


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
    note_id = int(poster)
    data = {"openreview": notes[notes_keys[note_id]], "id": note_id,
            "paper_recs" : [notes[n] for n in paper_recs[notes_keys[note_id]]][1:],
            "next": note_id +1 , "prev": note_id-1}
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



# Code to turn it all static
freezer = Freezer(app, with_no_argument_rules=False, log_url_for=False)
@freezer.register_generator
def your_generator_here():
    yield "livestream", {}
    yield "home", {}
    yield "papers", {}
    yield "recommendations", {}


    for i in range(len(notes_keys)):
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

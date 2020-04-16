from flask import Flask, render_template, render_template_string
from flask import jsonify, send_from_directory, redirect
from flask_frozen import Freezer
import pickle, json, yaml
import os, sys, argparse
import glob


site_data = {}

titles = {}
keywords = {}


# Loads up the necessary data
def main(site_data_path):
    global site_data
    global titles
    global keywords

    # Load all for notesj data one time.
    for f in glob.glob(site_data_path +"/*"):
        name, typ = f.split("/")[-1].split(".")
        if typ == "json":
            site_data[name] = json.load(open(f))
        elif typ == "yml":
            site_data[name] = yaml.load(open(f).read(),
                                        Loader=yaml.BaseLoader)


    paper_session = {}
    for v in site_data["poster_schedule"]:
        for poster in v["posters"]:
            paper_session.setdefault(poster, [])
            paper_session[poster].append( v["name"])

    for i, (k,n) in enumerate(site_data["papers"].items()):
        n["content"]["iclr_id"] = k
        n["content"]["session"] = paper_session[k]
        titles[n["content"]["title"]] = k

        if "TL;DR" in n["content"]:
            n["content"]["TLDR"] = n["content"]["TL;DR"]
        else:
            n["content"]["TLDR"] = n["content"]["abstract"][:250] + "..."
        for k in n["content"]["keywords"]:
            keywords.setdefault(k.lower(), [])
            keywords[k.lower()].append(n)
    print("Data Successfully Loaded")



def parse_arguments():
    parser = argparse.ArgumentParser(description="ICLR Portal Command Line")

    parser.add_argument('--build', action='store_true', default=False,
                        help="Convert the site to static assets")

    parser.add_argument('-b', action='store_true', default=False, dest="build",
                        help="Convert the site to static assets")

    parser.add_argument('path',
                        help="Pass the JSON data path and run the server")

    args = parser.parse_args()
    return args



# ------------- SERVER CODE -------------------->

app = Flask(__name__)
app.config.from_object(__name__)


# MAIN PAGES

@app.route('/')
def index():
    return redirect('/index.html')

@app.route('/index.html')
def home():
    return render_template('pages/index.html', **{})


@app.route('/livestream.html')
def livestream():
    return render_template('pages/livestream.html', **{})

@app.route('/daily_<day>.html')
def daily(day):
    out = [s for s in site_data["oral_schedule"] if s["day"] == day][0]

    out = { "day": out["day"],
            "section":
            [{"theme": o["theme"],
              "papers": [site_data["papers"][id]
                         for id in o["ids"]]}
             for o in out["section"]] }
    return render_template('pages/daily.html', **out)


@app.route('/papers.html')
def papers():
    data = {"keyword": "all",
            "page": "papers",
            "openreviews": site_data["papers"].values()}
    return render_template('pages/papers.html', **data)


@app.route('/paper_vis.html')
def paperVis():
    return render_template('pages/papers_vis.html')


@app.route('/recs.html')
def recommendations():
    data = {"choices": site_data["author_recs"].keys(),
            "keywords": keywords.keys(),
            "titles": titles.keys()}
    return render_template('pages/recs.html', **data)


@app.route('/faq.html')
def faq():
    return render_template('pages/faq.html', **site_data["faq"])

@app.route('/calendar.html')
def schedule():
    return render_template('pages/schedule.html')

@app.route('/socials.html')
def socials():
    return render_template('pages/socials.html', **site_data["socials"])


@app.route('/sponsors.html')
def sponsors():
    return render_template('pages/sponsors.html', **site_data["sponsors"])

@app.route('/workshops.html')
def workshops():
    return render_template('pages/workshops.html', **site_data["workshops"])


@app.route('/speakers.html')
def speakers():
    return render_template('pages/speakers.html', **site_data["speakers"])


# DYNAMIC PAGES

@app.route('/workshops_<workshop>.html')
def workshop(workshop):
    return render_template('pages/workshop.html',
                           **{"info":site_data["workshops"]["workshops"][int(workshop) -1 ] })


@app.route('/poster_<poster>.html')
def poster(poster):
    note_id = poster
    data = {"openreview": site_data["papers"][note_id], "id": note_id,
            "paper_recs": [site_data["papers"][n] for n in site_data["paper_recs"][note_id]][1:]}

    return render_template('pages/page.html', **data)

# DATA FILES

@app.route('/papers.json')
def paper_json():
    paper_list = [value for value in site_data["papers"].values()]
    return jsonify(paper_list)


@app.route('/embeddings_<emb>.json')
def embeddings(emb):
    try:
        return send_from_directory('static', 'embeddings_' + emb + '.json')
    except FileNotFoundError:
        return ""


@app.route('/schedule.json')
def schedule_json():
    return jsonify(site_data["schedule"])


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Code to turn it all static
freezer = Freezer(app, with_no_argument_rules=False, log_url_for=False)


@freezer.register_generator
def your_generator_here():
    yield "livestream", {}
    yield "home", {}
    yield "papers", {}
    yield "schedule", {}
    yield "socials", {}
    yield "sponsors", {}
    yield "workshops", {}
    yield "paperVis", {}
    yield "papers", {}
    yield "paper_json", {}
    yield "index", {}
    yield "faq", {}
    yield "speakers", {}
    yield "schedule", {}
    yield "schedule_json", {}
    yield "embeddings", {"emb":"tsne"}
    for day in ["Monday", "Tuesday",
                "Wednesday","Thursday"]:
        yield "daily", {"day": day}

    for i in site_data["papers"].keys():
        yield "poster", {"poster": str(i)}
    for i in range(len(site_data["workshops"])):
        yield "workshop", {"workshop": str(i)}


# --------------- DRIVER CODE -------------------------->

if __name__ == "__main__":
    args = parse_arguments()

    site_data_path = args.path
    main(site_data_path)

    if args.build:
        freezer.freeze()
    else:
        debug_val = False
        if(os.getenv("FLASK_DEBUG") == "True"):
            debug_val = True

        app.run(port=5000, debug=debug_val)

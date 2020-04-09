from flask import Flask, render_template, render_template_string
from flask import jsonify, send_from_directory, redirect
from flask_frozen import Freezer
import pickle, json
import os, sys, argparse
import yaml

# has keys => ['cached_or', 'paper_records', 'author_records', 'sponsors', 'workshops', 'socials', 'calendar']
site_data = {}

titles = {}
keywords = {}


# Loads up the necessary data
def main(site_data_path):
    global site_data

    global titles
    global keywords

    # Load all for notes data one time.
    site_data_file = open(site_data_path, "r")
    site_data = json.loads(site_data_file.read())
    site_data_file.close()
    
    for i, (k,n) in enumerate(site_data["cached_or"].items()):
        n["content"]["iclr_id"] = k
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

    parser.add_argument('path', action='append', type=argparse.FileType("r"),
                        help="Pass the JSON data path and run the server")
    
    args = parser.parse_args()
    return args



# ------------- SERVER CODE -------------------->

app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def index():
    return redirect('/index.html')


@app.route('/index.html')
def home():
    return render_template('pages/home.html', **{})


@app.route('/livestream.html')
def livestream():
    return render_template('pages/main.html', **{})


@app.route('/papers.html')
def papers():
    data = {"keyword": "all",
            "page": "papers",
            "openreviews": site_data["cached_or"].values()}
    return render_template('pages/papers.html', **data)


@app.route('/paper_vis.html')
def paperVis():
    return render_template('pages/papers_vis.html')


@app.route('/papers_old.html')
def papers_old():
    data = {"keyword": "all",
            "openreviews": site_data["cached_or"].values()}
    return render_template('pages/keyword.html', **data)


@app.route('/papers.json')
def paper_json():
    paper_list = [value for value in site_data["cached_or"].values()]
    return jsonify(paper_list)


@app.route('/recs.html')
def recommendations():
    data = {"choices": site_data["author_records"].keys(),
            "keywords": keywords.keys(),
            "titles": titles.keys()}
    return render_template('pages/recs.html', **data)


@app.route('/faq.html')
def faq():
    try:
        s = yaml.load(open('static/faq.yml', 'r'))
        return render_template('pages/faq.html', **s)
    except FileNotFoundError:
        return ""


@app.route('/calendar.html')
def schedule():
    return render_template('pages/calendar.html')


@app.route('/socials.html')
def socials():
    try:
        s = yaml.load(open('static/socials.yml', 'r'))
        return render_template('pages/socials.html', **s)
    except FileNotFoundError:
        return ""




@app.route('/sponsors.html')
def sponsors():
    try:
        s = yaml.load(open('static/sponsors.yml', 'r'))
        return render_template('pages/sponsors.html', **s)
    except FileNotFoundError:
        return ""




@app.route('/workshops.html')
def workshops():
    try:
        s = yaml.load(open('static/workshops.yml', 'r'))
        return render_template('pages/workshops.html', **s)
    except FileNotFoundError:
        return ""

@app.route('/workshops_<workshop>.html')
def workshop(workshop):
    try:
        s = yaml.load(open('static/workshops.yml', 'r'))
        return render_template('pages/workshop.html', **{"info": s["workshops"][int(workshop)]})
    except FileNotFoundError:
        return ""


@app.route('/speakers.html')
def speakers():
    try:
        s = yaml.load(open('static/speakers.yml', 'r'))
        return render_template('pages/speakers.html', **s)
    except FileNotFoundError:
        return ""



# Pull the OpenReview info for a poster.
@app.route('/poster_<poster>.html')
def poster(poster):
    note_id = poster
    data = {"openreview": site_data["cached_or"][note_id], "id": note_id,
            "paper_recs": [site_data["cached_or"][n] for n in site_data["paper_records"][note_id]][1:]}

    return render_template('pages/page.html', **data)


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/embeddings_<emb>.json')
def embeddings(emb):
    try:
        return send_from_directory('static', 'embeddings_' + emb + '.json')
    except FileNotFoundError:
        return ""


@app.route('/schedule.json')
def schedule_json():
    try:
        s = yaml.load(open('static/schedule.yml', 'r'))
        return jsonify(s)
    except FileNotFoundError:
        return ""


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
    yield "recommendations", {}
    yield "embeddings", {"emb":"tsne"}

    for i in site_data["cached_or"].keys():
        yield "poster", {"poster": str(i)}


# --------------- DRIVER CODE -------------------------->

if __name__ == "__main__":
    args = parse_arguments()
    
    site_data_path = args.path[0].name    
    main(site_data_path)

    if args.build:
        freezer.freeze()
    else:
        debug_val = False        
        if(os.getenv("FLASK_DEBUG") == "True"):
            debug_val = True

        app.run(port=5000, debug=debug_val)

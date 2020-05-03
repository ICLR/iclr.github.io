from flask import Flask, render_template, render_template_string, make_response
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
    session_times = {}
    session_links = {}

    slide_link = {}
    for p in site_data["poster_slides"]["slides"]:
        slide_link[p["uid"]] = p["slides_id"]


    for s in site_data["oral_schedule"]:
        day = s["day"]
        for section in s["section"]:
            key = day + ": " +section["theme"]
            for poster in section["ids"]:
                paper_session.setdefault(poster, [])
                paper_session[poster].append(key)
                session_times.setdefault(poster, [])
                session_links.setdefault(poster, [])
                session_times[poster].append(None)
                session_links[poster].append(None)

    nk = list(site_data["papers"].keys())
    nk.sort()
    for i, k in enumerate(nk, 1):
        site_data["papers"][k]["content"]["chat"] = "poster_" + str(i)

    extra_kw = {d["paper"] : d["keywords"] for d in site_data["keywords"]}
    for i, (k,n) in enumerate(site_data["papers"].items()):
        n["content"]["iclr_id"] = k
        n["content"]["slides"] = slide_link[k]
        n["content"]["authors"] = [a.replace("*", "") for a in n["content"]["authors"]]
        if k in paper_session:
            n["content"]["session"] = paper_session[k]
            n["content"]["session_times"] = session_times[k]
            n["content"]["session_links"] = session_links[k]
        titles[n["content"]["title"]] = k

        if "TL;DR" in n["content"]:
            n["content"]["TLDR"] = n["content"]["TL;DR"]
        else:
            n["content"]["TLDR"] = n["content"]["abstract"][:250] + "..."

        if k in extra_kw:
            n["content"]["keywords"] += extra_kw[k]
    
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

adays = {"Monday":"Mon",
         "Tuesday":"Tues",
         "Wednesday":"Wed",
         "Thursday":"Thurs"}

@app.route('/index.html')
def home():
    site_data["about"]["sponsors"] = site_data["sponsors"]["sponsors"]
    site_data["about"]["volunteers"] = site_data["volunteers"]
    return render_template('pages/index.html', **site_data["about"])


@app.route('/papers.html')
def papers():
    data = {"keyword": "all",
            "page": "papers",
            "openreviews": site_data["papers"].values()}
    return render_template('pages/papers.html', **data)


@app.route('/paper_vis.html')
def paperVis():
    return render_template('pages/papers_vis.html')

@app.route('/about.html')
def about():
    site_data["about"]["FAQ"] = site_data["faq"]["FAQ"]
    return render_template('pages/about.html', **site_data["about"])


@app.route('/calendar.html')
def schedule():
    all_days = {"days": []}
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday"]:
        speakers = [s for s in site_data["speakers"]["speakers"]
                    if s["day"] == day]

        out = [s for s in site_data["oral_schedule"] if s["day"] == day][0]
        out = { "day": out["day"],
                "short": adays[day],
                "speakers": speakers,
                "section":
                [{"theme": o["theme"],
                  "papers": [site_data["papers"][id]
                             for id in o["ids"]]}
                for o in out["section"]] }

        all_days["days"].append(out)
    all_days["expos"] = site_data["expos"]["expos"]
    return render_template('pages/schedule.html', **all_days)


@app.route('/workshops.html')
def workshops():
    return render_template('pages/workshops.html', **site_data["workshops"])


# DYNAMIC PAGES

@app.route('/workshops_<workshop>.html')
def workshop(workshop):
    return render_template('pages/workshop.html',
                           **{"info":site_data["workshops"]["workshops"][int(workshop) -1 ] })

@app.route('/speaker_<speaker>.html')
def speaker(speaker):
    return render_template('pages/speaker.html',
                           **{"info":site_data["speakers"]["speakers"][int(speaker) -1 ],
                              "id": int(speaker)
                           })

@app.route('/expo_<expo>.html')
def expo(expo):
    return render_template('pages/expo.html',
                           **{"info":site_data["expos"]["expos"][int(expo) -1 ],
                              "id": int(expo)
                           })


@app.route('/poster_<poster>.html')
def poster(poster):
    note_id = poster
    data = {"openreview": site_data["papers"][note_id], "id": note_id,
            "paper_recs": [site_data["papers"][n] for n in site_data["paper_recs"][note_id]][1:]}

    return render_template('pages/page.html', **data)

@app.route('/papers.json')
def paper_json():
    paper_list = [value for value in site_data["papers"].values()]

    json = []
    for k, v in site_data["papers"].items():
        json.append( {
            "id": v["id"],
            "forum": v["forum"],
            "content": {"title": v["content"]["title"],
                        "authors": v["content"]["authors"],
                        "iclr_id": v["content"]["iclr_id"],
                        "keywords": v["content"]["keywords"],
                        "abstract": " ",
                        "TLDR": v["content"]["TLDR"],
                        "recs": [],
                        "session": v["content"].get("session", []),
                        "session_times": v["content"].get("session_times", []),
                        "session_links": v["content"].get("session_links", [])
            }})
    return jsonify(json)


@app.route('/embeddings_<emb>.json')
def embeddings(emb):
    try:
        return send_from_directory('static', 'embeddings_' + emb + '_2.json')
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
    yield "home", {}
    yield "papers", {}
    yield "schedule", {}
    yield "workshops", {}
    yield "paperVis", {}
    yield "papers", {}
    yield "paper_json", {}
    yield "index", {}
    yield "schedule", {}
    yield "schedule_json", {}
    yield "about", {}
    yield "embeddings", {"emb":"tsne"}

    for i in site_data["papers"].keys():
        yield "poster", {"poster": str(i)}
    for i in range(1, len(site_data["workshops"]["workshops"])+1):
        yield "workshop", {"workshop": str(i)}
    for i in range(1, len(site_data["speakers"]["speakers"])+1):
        yield "speaker", {"speaker": str(i)}
    for i in range(1, 5):
        yield "expo", {"expo": str(i)}


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

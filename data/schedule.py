import csv, yaml


days = {
    "Monday" : "Mon",
    "Tuesday" : "Tues",
    "Wednesday" : "Wed",
    "Thursday" : "Thurs",
    }

session = {
    "5:00 to 7:00 GMT": 1,
    "8:00 to 10:00 GMT": 2,
    "12:00 to 14:00 GMT" : 3,
    "17:00 to 19:00 GMT": 4,
    "20:00 to 22:00 GMT": 5
    }

# ps = open("oral_schedule.yml", "w")
# sessions = {}

# with open('raw/final_oral.tsv', newline='') as csvfile:
#      posters = csv.DictReader(csvfile, delimiter='\t')
#      for p in posters:
#          if "Day" not in p:
#              continue
#          p["forum"] = p["forum link"].split("=")[-1]
#          # print(p)
#          theme = p["Session Theme"].strip()
#          sessions.setdefault(p["Day"], {})
#          sessions[p["Day"]].setdefault(theme, [])
#          sessions[p["Day"]][theme].append(p["forum"])

# out = [{"day": k, "section": [ {"theme" :k2, "ids": v2} for k2, v2 in v.items()]}
#        for k, v in sessions.items()]
# ps.write(yaml.dump(out))


ps = open("poster_schedule.yml", "w")
sessions = {}

with open('raw/final_assignments_unbal.csv', newline='') as csvfile:
     posters = csv.DictReader(csvfile, delimiter=',')
     for p in posters:
         p["forum"] = p["uniqueid"]
         p["sessid"] = "%s Session %s" % (days[p["day"]], session[p["session"]])
         sessions.setdefault(p["sessid"], [])
         sessions[p["sessid"]].append(p["uniqueid"])

out = [{"name": k, "posters":v}  for k, v in sessions.items()]
ps.write(yaml.dump(out))

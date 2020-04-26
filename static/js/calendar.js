function make_cal(name) {
    $.get(name).then(function (data) {
    // parse the ics data
    var jcalData = ICAL.parse(data.trim());
              var comp = new ICAL.Component(jcalData);
    var eventComps = comp.getAllSubcomponents("vevent");
    // map them to FullCalendar events
    var events = $.map(eventComps, function (item) {

        if (item.getFirstPropertyValue("class") == "PRIVATE") {
            return null;
        }
        else  {
            var toreturn = {
                "title": item.getFirstPropertyValue("summary"),
                "location": "",
            };
            if (toreturn["title"].indexOf("Live Q&A") > -1 ) {
                return null;
            }
            if (toreturn["title"].indexOf("Poster Day") > -1 ) {
                return null;
            }
            var rrule=item.getFirstPropertyValue("rrule");
            if(rrule!= null){ //event recurs
                toreturn.rrule={};
              if(rrule.freq) toreturn.rrule.freq=rrule.freq;
                if(rrule.parts.BYDAY) toreturn.rrule.byweekday=rrule.parts.BYDAY;
                if(rrule.until) toreturn.rrule.until=rrule.until.toString();
                if(rrule.until) toreturn.rrule.until=rrule.until.toString();
                if(rrule.interval) toreturn.rrule.interval=rrule.interval;
                var dtstart=item.getFirstPropertyValue("dtstart").toString();
                var dtend=item.getFirstPropertyValue("dtend").toString();
                toreturn.rrule.dtstart=dtstart;
                //count duration ms
                var startdate=new Date(dtstart);
                var enddate=new Date(dtend);
                toreturn.duration = enddate - startdate;
            }else{
                if (item.getFirstPropertyValue("dtstart") == null)
                    return null;
                if (item.getFirstPropertyValue("dtend") == null)
                    return null;

                toreturn.start=item.getFirstPropertyValue("dtstart").toString();
                toreturn.end=item.getFirstPropertyValue("dtend").toString();
            }
            return toreturn;
        }});

        var calEl = document.getElementById('calendar');
        var cal = new FullCalendar.Calendar(calEl,
                                            {
                                                plugins: [ 'list', 'googleCalendar' ],
                                                defaultView: 'listWeek',
                                                views: {
                                                    listDay: { buttonText: 'list day' }
                                                },
                                                header :{left:'', center:'', right: ''},
                                                eventTimeFormat: { // like '14:30:00'
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                    meridiem: false,
                                                    hour12: false,
                                                    timeZoneName: "long"
                                                },
                                                height: 350,
                                                events: events,
                                                eventClick: function(info) {
                                                    $(window).scrollTop($("#" +info.event.title.split(" ").join("_").replace('?','')).position().top - 100);
                                                },
                                                eventRender: function (info) {
                                                    // console.log(info.event);
                                                    // append location
                                                    if (info.event.extendedProps.location != null && info.event.extendedProps.location != "") {
                                                        info.el.append(info.event.extendedProps.location );
                                                    }},
                                            });

        cal.gotoDate("2020-04-26");
        cal.render();
    });

}

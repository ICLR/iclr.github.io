const table_height = 8o00;

let sc = null;
let min_max_time = [];
let currentTimeZone = moment.tz.guess(true);
let tzNames = moment.tz.names();

function updateTable() {
    const scale = d3.scaleTime().domain(min_max_time).range([25, table_height])

    const day_format = d3.utcFormat('%a %m/%e');
    const day_name = d3.utcFormat('%A');
    const day_parse = d3.utcParse('%Y-%m-%e');

    //TODO: replace
    const today = day_parse('2020-04-28');

    const days = d3.select('.main-table')
      .selectAll('.day').data(sc.conference)
      .join(enter => {
          const res = enter.append('div')
          res.append('a')
              .attr('class', 'day_header')
              .attr("href", d => "#" + day_name(day_parse(d.day)))             
            .text(d => day_format(day_parse(d.day)))
              .attr('data-name', d => day_parse(d.day));

          
          return res;
      })
      .attr('class', d => 'day')
      .classed('today', d => {
          return day_format(today) === day_format(day_parse(d.day))
      })
      .style('margin-top', "30px")
      .style('height', `${table_height}px`)

    const slots = sc.time_slots;
    const parse_full_time = d3.utcParse('%Y-%m-%e %I:%M %p');
    const utc_time_format = d3.utcFormat('%I:%M %p');

    // const tf = d3.timeFormat('%I:%M %p')

    const tf = date => moment(date).tz(currentTimeZone).format('hh:mm A')
    // const tf_moment_GMT = date => moment(date).tz('GMT').format('hh:mm A')
    const day_diff = date => {
        const m = moment(date)
        return m.tz(currentTimeZone).date() - m.utc().date();
    }

    days.selectAll('.event').data(d => d.events.map(event => {
        event.time_slot = slots[event.slot];
        event.real_times = slots[event.slot]
          .map(sl => parse_full_time(d.day + ' ' + utc_time_format(sl)));
        return event;
    }))
      .join('div')
      .attr('class', d => 'event ' + d.type)
      .style('top', d => scale(d.time_slot[0]) + "px")
      .style('height',
        d => Math.max(20,
          (scale(d.time_slot[1]) - scale(d.time_slot[0]) - 2)) + 'px')
      .html(d => {
          let res = '';
          if (d.type === 'poster') {
              const matches = d.short.match(/P([0-9]+)S([0-9]+)/);
              const dd = day_diff(d.real_times[1]);
              day = ""
              if (matches[1] == 1) {
                  day = "Mon";
              } else if (matches[1] == 2) {
                  day = "Tues";
              } else if (matches[1] == 3) {
                  day = "Wed";
              } else if (matches[1] == 4) {
                  day = "Thurs";
              }

              res += `<div  class="time_slot"> ${tf(d.real_times[0])} - ${tf(
                d.real_times[1])} ${dd!==0 ? '+' + dd + 'd' : ''} </div>`
              res += `<a href="papers.html?filter=session&search=${day}+Session+${matches[2]}"> <span class="session-title">` +
                `Poster Day ${matches[1]} Session ${matches[2]}</span> </a>`

          } else if (d.type === 'qa') {
              res += `<span class="time_slot">${tf(
                d.real_times[0])} </span><span class="session-title">` +
                `${d.name} </span>`
          }

          // res+=`<br/><span  class="time_slot"> ${tf(d.time_slot[0])} - ${tf(
          //   d.time_slot[1])} </span>`

          return res;
      })
}


const start = () => {
    d3.json('schedule.json').then((sch) => {
        sc = sch;
        // date conversions for times
        const parseTime = d3.utcParse('%I:%M %p');
        let all_ts = [];
        Object.keys(sch.time_slots).forEach((k) => {
            const timeSlot = sch.time_slots[k].map(parseTime);
            sch.time_slots[k] = timeSlot;
            all_ts.push(timeSlot)
        });
        all_ts = _.flatten(all_ts);
        min_max_time = d3.extent(all_ts);


        d3.select('.info')
          .text(`Times are displayed for timezone: ${currentTimeZone}`)

        updateTable();
    })
      .catch(e => console.error(e))

    const tzOptons = d3.select('#tzOptions')
    tzOptons.selectAll('option').data(tzNames)
      .join('option')
      .attr('data-tokens', d => d.split("/").join(" "))
      .text(d => d)
    $('.selectpicker')
      .selectpicker('val', currentTimeZone)
      .on('changed.bs.select',
        function (e, clickedIndex, isSelected, previousValue) {
            currentTimeZone = tzNames[clickedIndex]
            updateTable();
        })

}

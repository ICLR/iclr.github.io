const table_height = 600;

let sc = null;
let min_max_time = [];


function updateTable() {
    const scale = d3.scaleTime().domain(min_max_time).range([25, table_height])

    const day_format = d3.utcFormat('%a %m/%e');
    const day_parse = d3.utcParse('%Y-%m-%e');

    //TODO: replace
    const today = day_parse('2020-04-28');

    const days = d3.select('.main-table')
      .selectAll('.day').data(sc.conference)
      .join(enter => {
          const res = enter.append('div')
          res.append('div')
            .attr('class', 'day_header')
            .text(d => day_format(day_parse(d.day)))
            .attr('data-name', d => day_parse(d.day))
          return res;
      })
      .attr('class', d => 'day')
      .classed('today', d => {
          return day_format(today) === day_format(day_parse(d.day))
      })
      .style('height', `${table_height}px`)

    const slots = sc.time_slots;
    const parse_full_time = d3.utcParse('%Y-%m-%e %I:%M %p');
    const utc_time_format = d3.utcFormat('%I:%M %p');

    const tf = d3.timeFormat('%I:%M %p')
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
        d => (scale(d.time_slot[1]) - scale(d.time_slot[0]) - 2) + 'px')
      .html(d => {
          let res = '';
          if (d.type==='poster'){
              const matches = d.short.match(/P([0-9]+)S([0-9]+)/);
              // console.log(matches, d.short,"--- matches, d.short");
              res+=`<div  class="time_slot"> ${tf(d.time_slot[0])} - ${tf(
            d.time_slot[1])} </div>`
              res+= `<span class="session-title">`+
                `Poster Day ${matches[1]} Session ${matches[2]} (${d.short})</span>`

          }else if (d.type === 'qa'){
              res+= `<span class="time_slot">${tf(d.time_slot[0])} </span><span class="session-title">`+
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
          .text(`Times are displayed for timezone: ${Intl.DateTimeFormat().resolvedOptions().timeZone}`)

        updateTable();
    })
      .catch(e => console.error(e))


}


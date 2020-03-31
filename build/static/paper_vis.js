let all_papers = [];
let all_pos = [];
const allKeys = {
    authors: [],
    keywords: [],
    titles: []
}
const filters = {
    authors: null,
    keywords: null,
    title: null
};

let currentTippy = null;

const sizes = {
    margins: {l: 20, b: 20, r: 20, t: 20}
}

const plot_size = () => {
    const cont = document.getElementById('container');
    // console.log(window.innerHeight-100, cont.offsetWidth,"--- window.innerWidth, cont.offsetWidth");
    const wh = Math.max(window.innerHeight - 200, 300)
    const ww = Math.max(cont.offsetWidth, 300)
    return [ww, wh]
}

const xS = d3.scaleLinear().range([0, 500]);
const yS = d3.scaleLinear().range([0, 500]);
const plot = d3.select('.plot');
const l_bg = plot.append('g');
const l_main = plot.append('g');
const l_fg = plot.append('g');

const updateVis = () => {

    const is_filtered = filters.authors || filters.keywords || filters.titles;

    const [pW, pH] = plot_size();

    plot.attr('width', pW).attr('height', pH)

    xS.range([sizes.margins.l, pW - sizes.margins.r]);
    yS.range([sizes.margins.t, pH - sizes.margins.b]);

    all_pos = all_papers.map(d => {
        const r2 = (d.is_selected ? 8 : 4);
        const [x, y] = [xS(d.pos[0]), yS(d.pos[1])];
        return new cola.Rectangle(x - r2, x + r2, y - r2, y + r2);
    })

    cola.removeOverlaps(all_pos);

    l_main.selectAll('.dot').data(all_papers, d => d.id)
      .join('circle')
      .attr('class', 'dot')
      .attr('r', d => d.is_selected ? 8 : 6)
      .attr('cx', (d,i) => all_pos[i].cx())
      .attr('cy', (d,i) => all_pos[i].cy())
      .classed('highlight', d => d.is_selected)
      .classed('non-highlight', d => !d.is_selected && is_filtered)
      .on('click',
        d => window.open(`poster_${d.content.iclr_id}.html`, '_blank'))

    if (!currentTippy) {
        currentTippy = tippy('.dot', {
            content(reference) {
                // const id = reference.getAttribute('data-template');
                // const template = document.getElementById(id);
                // console.log(reference,"--- reference");
                // console.log(d3.select(reference), "--- d3.select(reference)");
                return tooltip_template(d3.select(reference).datum());
            },
            allowHTML: true
        });
    }

}

const render = () => {
    const f_test = [];
    Object.keys(filters)
      .forEach(k => {filters[k] ? f_test.push([k, filters[k]]) : null});

    let test = d => {
        let i = 0, pass_test = true;
        while (i < f_test.length && pass_test) {
            if (f_test[i][0] === 'titles') {
                pass_test &= d.content['title'] === f_test[i][1];
            } else {
                pass_test &= d.content[f_test[i][0]].indexOf(
                  f_test[i][1]) > -1
            }
            i++;
        }
        return pass_test;
    }

    if (f_test.length === 0) test = d => false;

    all_papers.forEach(paper => paper.is_selected = test(paper));

    updateVis();

}


//language=HTML
const tooltip_template = (d) => `
    <div>
        <div class="tt-title">${d.content.title}</div>
        <p>${d.content.authors.join(', ')}</p>
     </div>   
`


const start = () => {
    Promise.all([
        d3.json('papers.json'),
        d3.json('embeddings_tsne.json')
    ]).then(([papers, proj]) => {
        // all_proj = proj;

        proj.forEach((pos, i) => papers[i].pos = pos)
        all_papers = papers;

        calcAllKeys(all_papers, allKeys);
        setTypeAhead('authors', allKeys, filters, render);


        xS.domain(d3.extent(proj.map(p => p[0])));
        yS.domain(d3.extent(proj.map(p => p[1])));

        updateVis();
    })
      .catch(e => console.error(e))


}


/**
 *  EVENTS
 **/

d3.selectAll('.filter_option input').on('click', function () {
    const me = d3.select(this);
    const filter_mode = me.property('value');
    setTypeAhead(filter_mode, allKeys, filters, render);

})

$(window).on('resize', _.debounce(updateVis, 150));

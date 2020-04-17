

let allPapers = [];
const allKeys = {
    authors: [],
    keywords: [],
    session: [],
    titles: [],
    recs: [],
}
const filters = {
    authors: null,
    keywords: null,
    session: null,
    title: null,
    recs: null,
};

let render_mode = 'compact';


const updateCards = (papers) => {
    const all_mounted_cards = d3.select('.cards').selectAll('.myCard')
      .data(papers, d => d.number)
      .join('div')
      .attr('class', 'myCard col-xs-6 col-md-4')
      .html(card_html)
}

/* Randomize array in-place using Durstenfeld shuffle algorithm */
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        const temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
}

const render = () => {
    const f_test = [];
    Object.keys(filters)
      .forEach(k => {filters[k] ? f_test.push([k, filters[k]]) : null})

    console.log(f_test, filters, "--- f_test, filters");
    if (f_test.length === 0) updateCards(allPapers)
    else {
        const fList = allPapers.filter(
          d => {
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
          });
        console.log(fList, "--- fList");
        updateCards(fList)
    }

}

let callstox = 0;

/**
 * START here and load JSON.
 */
const start = () => {
    d3.json('papers.json').then(papers => {
        shuffleArray(papers);

        allPapers = papers;
        calcAllKeys(allPapers, allKeys);
        console.log(getUrlParameter("filter") || 'authors');
        setTypeAhead(getUrlParameter("filter") || 'authors',
                     allKeys, filters, render);
        updateCards(allPapers)
        if (getUrlParameter("search") != null) {
            filters[getUrlParameter("filter")] = getUrlParameter("search");
            $('.typeahead_all').val(getUrlParameter("search"));
            render();
        }

    }).catch(e => console.error(e))
}


/**
 * EVENTS
 * **/

d3.selectAll('.filter_option input').on('click', function () {
    const me = d3.select(this)

    const filter_mode = me.property('value');
    setQueryStringParameter("filter", me.property('value'));

    setTypeAhead(filter_mode, allKeys, filters, render);
})

d3.selectAll('.render_option input').on('click', function () {
    const me = d3.select(this);
    render_mode = me.property('value');
    render();
})

d3.select('.reshuffle').on('click', () => {
    shuffleArray(allPapers);
    render();
})

/**
 * CARDS
 */

const keyword = kw => `<a href="papers.html?filter=keywords&search=${kw}"
                       class="text-secondary text-decoration-none">${kw.toLowerCase()}</a>`
//language=HTML
const card_html = openreview => `
        <div class="pp-card">
            <div class="pp-card-header">
                <a href="poster_${openreview.content.iclr_id}.html"
                   class="text-muted">
                   <h5 class="card-title" align="center"> ${openreview.content.title} </h5></a>
                <h6 class="card-subtitle text-muted" align="center">
                        ${openreview.content.authors.join(', ')}
</h6>
    <center><img class="cards_img" src="https://iclr.github.io/iclr-images/${openreview.content.iclr_id}.png" width="80%"/></center>

            </div>`
  + ((render_mode === 'detail') ? `
            <div class="pp-card-header">
                <p class="card-text"> ${openreview.content.TLDR}</p>
                <p class="card-text"><span class="font-weight-bold">Keywords:</span>
                    ${openreview.content.keywords.map(keyword).join(', ')}
                </p>
            </div>
        </div>` : '</div>')

let allPapers = [];
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
let render_mode = 'compact';


const updateCards = (papers) => {
    const all_mounted_cards = d3.select('.cards').selectAll('.myCard')
      .data(papers, d => d.number)
      .join('div')
      .attr('class', 'myCard col-12 col-sm-6 col-lg-4')
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

const initTypeAhead = (list, css_sel, name, callback) => {
    const bh = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        local: list
    });

    // remove old
    $(css_sel).typeahead('destroy')
      .off('keydown')
      .off('typeahead:selected')
      .val('');

    $(css_sel).typeahead({
          hint: true,
          highlight: true, /* Enable substring highlighting */
          minLength: 1 /* Specify minimum characters required for showing suggestions */
      },
      {name, source: bh})
      .on('keydown', function (e) {
          if (e.which === 13) {
              e.preventDefault();
              callback(e, e.target.value);
          }
      })
      .on('typeahead:selected', function (evt, item) {
          callback(evt, item)
      })

    $(css_sel + '_clear').on('click', function () {
        $(css_sel).val('');
        callback(null, '');
    })
}

const setTypeAhead = (subset) => {

    Object.keys(filters).forEach(k => filters[k] = null);

    initTypeAhead(allKeys[subset], '.typeahead_all', subset,
      (e, it) => {
          console.log(e, it, "--- e,it");
          filters[subset] = it.length > 0 ? it : null;
          render()
      })
}


/**
 * START here and load JSON.
 */
const start = () => {
    d3.json('papers.json').then(papers => {
        shuffleArray(papers);

        allPapers = papers;

        const collectAuthors = new Set();
        const collectKeywords = new Set();

        allPapers.forEach(
          d => {
              d.content.authors.forEach(a => collectAuthors.add(a));
              d.content.keywords.forEach(a => collectKeywords.add(a))
              allKeys.titles.push(d.content.title)
          });
        allKeys.authors = Array.from(collectAuthors);
        allKeys.keywords = Array.from(collectKeywords);

        setTypeAhead('authors');

        updateCards(allPapers)

    }).catch(e => console.error(e))
}


/**
 * EVENTS
 * **/

d3.selectAll('.filter_option input').on('click', function () {
    const me = d3.select(this);
    const filter_mode = me.property('value');
    setTypeAhead(filter_mode);
    render();
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

const keyword = kw => `<a href="keyword_${kw}.html"
                       class="text-secondary text-decoration-none">${kw.toLowerCase()}</a>`
//language=HTML
const card_html = openreview => `
        <div class="card" style="margin-bottom: 10px;">
            <div class="card-header">
                <a href="poster_${openreview.content.iclr_id}.html"
                   class="text-dark">
                   <h4 class="card-title"> ${openreview.content.title} </h4></a>
                <h6 class="card-subtitle mb-2 text-muted">
                        ${openreview.content.authors.join(', ')}
                </h6>
            </div>`
  + ((render_mode === 'detail') ? `
            <div class="card-body">
                <p class="card-text"> ${openreview.content.TLDR}</p>
                <p class="card-text"><span class="font-weight-bold">Keywords:</span>
                    ${openreview.content.keywords.map(keyword).join(', ')}
                </p>
            </div>
        </div>` : '</div>')

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

const setTypeAhead = (subset, allKeys,filters, render) => {

    Object.keys(filters).forEach(k => filters[k] = null);

    initTypeAhead(allKeys[subset], '.typeahead_all', subset,
      (e, it) => {
          filters[subset] = it.length > 0 ? it : null;
          render()
      })
}


let calcAllKeys = function (allPapers, allKeys) {
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
};

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

let order_by = null;
let likelihood_outdated = false;
let $grid = null;
let allProj = [];

// From https://stackoverflow.com/questions/7128675/from-green-to-red-color-depend-on-percentage

//var percentColors = [
//    { pct: 0.0, color: { r: 0xff, g: 0x00, b: 0 } },
//    { pct: 0.5, color: { r: 0xff, g: 0xff, b: 0 } },
//    { pct: 1.0, color: { r: 0x00, g: 0xff, b: 0 } }
//];

var percentColors = [
    { pct: 0.0, color: { r: 205, g: 92, b: 92 } }, // { pct: 0.0, color: { r: 236, g: 0, b: 0 } },
    { pct: 0.5, color: { r: 243, g: 187, b: 0 } },
    { pct: 1.0, color: { r: 0, g: 176, b: 13 } }
];

var getColorForPercentage = function(pct) {
    for (var i = 1; i < percentColors.length - 1; i++) {
        if (pct < percentColors[i].pct) {
            break;
        }
    }
    var lower = percentColors[i - 1];
    var upper = percentColors[i];
    var range = upper.pct - lower.pct;
    var rangePct = (pct - lower.pct) / range;
    var pctLower = 1 - rangePct;
    var pctUpper = rangePct;
    var color = {
        r: Math.floor(lower.color.r * pctLower + upper.color.r * pctUpper),
        g: Math.floor(lower.color.g * pctLower + upper.color.g * pctUpper),
        b: Math.floor(lower.color.b * pctLower + upper.color.b * pctUpper)
    };
    return 'rgb(' + [color.r, color.g, color.b].join(',') + ')';
    // or output as hex if preferred
}

var scoreToPercentage = function(score){
    var scale = 0.9;
    return Math.max(Math.min((score * scale - 1) * -0.5, 1), 0);
}

const updateCards = (papers) => {
  jQuery('.cards').append(jQuery.map(papers, card_html))
  lazyLoader();
}

const setOrderBy = value => {
  if (value != order_by){
    jQuery('.btn-group.order_by input[value="' + value + '"]').click()
  }
}

const likesChanged = () => {
  // Add to url
  const likestr = jQuery('.myCard[data-likes!=0]').map((i, el) => {
       let val = parseInt(jQuery(el).attr('data-likes'));
       return jQuery(el).attr('data-id') + "=" + val; // (val >= 0 ? "+" : "-") + Math.abs(val); 
     }).toArray().join(",");
  setQueryStringParameter("likes", encodeURIComponent(likestr));

  // Note: we minimize, so like gets low value
  // Only update directly if we are currently sorting by likelihood,
  // otherwise we will update when sorting by likelihood
  if (order_by == "likelihood"){
    computeLikelihood();
  } else {
    likelihood_outdated = true;
  }
}

const addLike = (card, delta) => {
  let mycard = card.parent()

  const likes = parseInt(mycard.attr('data-likes') || '0') + delta;
  mycard.attr('data-likes', likes);
  // Remove responsiveness to mouse temporarily, so card is no longer hovered
  card.css('pointerEvents', "none");
  // Undo after timeout (this way it is queued so we give time for unhover to happen)
  setTimeout(() => { card.css('pointerEvents', "auto") }, 0)

  card.find('.preview.like').toggle(likes > 0);
  card.find('.preview.dislike').toggle(likes < 0);

  likesChanged()
  
}

const setLikesFromStr = (likestr) => {

  var patt = /(([A-Za-z0-9]+)=([-]?\d+))/
  var changed = false;
  jQuery.each(likestr.split(","), (i, s) => { 
    const match = s.match(patt);
    if (match){
      changed = true;

      const id = match[2];
      const likes = parseInt(match[3]);

      const card = jQuery('#card-' + id);
      const mycard = card.parent();

      mycard.attr('data-likes', likes);

      card.find('.preview.like').toggle(likes > 0);
      card.find('.preview.dislike').toggle(likes < 0);
    }

  })

  if (changed) {
    likesChanged();
  }
  
}

const doSearch = it => {

    $('.typeahead_all').val(it);
    setQueryStringParameter("search", encodeURIComponent(it));

    const gridItems = $grid.find('.grid-item');

    // TODO improve search functionality

    if (it.length > 0){
      itarr = it.toLowerCase().split(" ");
      itarr = jQuery(itarr).filter((i, el) => { return el.length >= 4 })
      gridItems.each((i, el) => {
        el = jQuery(el)
        const haystack = el.text();
        const compute_match = haystack => {
          haystack = haystack.trim().toLowerCase();
          var score = 0;
          jQuery.each(itarr, (i, w) => {
            if (haystack.indexOf(w) > -1){
              score++
            }
          })
          return score;
        }

        const score = (
          compute_match(el.find('.card-title').text()) * 4 + 
          compute_match(el.find('.card-subtitle').text()) * 2 + 
          compute_match(el.find('.keywords').text()) * 2 + 
          compute_match(el.find('.tldr').text()) * 1
        ) 
        el.attr('data-search-match', score)
      })
    } else {
      gridItems.attr('data-search-match', 1)
    }

    $grid.isotope({ filter: function() {
      return parseFloat(jQuery(this).attr('data-search-match')) > 0;
    } })

    if (it.length > 0){
      // Sort descending by filter score
      if (order_by == 'search'){
        $grid.isotope('updateSortData').isotope();
      } else {
        setOrderBy('search')
      }
    } else {
      if (order_by == 'search'){
        // If the ordering was set to search but we cleared the search, we're effectively
        // ordering random, so set ordering to random explicitly to make this clear
        setOrderBy('random')
      }
      
    }
};

function computeLikelihoodResponse(response)
{  
   //$('.progress-container').css('background', "linear-gradient(to right, " + response.quantiles.map(scoreToPercentage).map(getColorForPercentage).join(",") + ")");
   if (response) {
    likelihood_outdated = false; // We have updated
    $.each( response.predictions, function( key, val ) {
      // Lower is better, get 95% conf to sort on
      $item = jQuery('#card-' + val.id).parent();
      // $item.attr('data-like', val.score);
      $item.attr('data-max-score', val.pred - 2 * val.sig);
      $item.attr('data-score', val.pred);
      $item.attr('data-score-prev', val.prev_pred);
      $item.attr('data-sig', val.sig);
      $item.attr('data-ei', val.acq);
      // $item.attr('data-size', val.size);
      $item.find('.score').text(Math.round(val.pred*-100));
      /*$item.find('.min-score').text(Math.round(((val.pred + 2 * val.sig) - 1) * -50));
      $item.find('.max-score').text(Math.round(((val.pred - 2 * val.sig) - 1) * -50));*/
      $item.find('.avg-score').text(Math.round(((val.pred) - 1) * -50));
      $item.find('.std-score').text(Math.round((2 * val.sig) * 50));

      $matchperc = $item.find('.matchperc');
      var perc = scoreToPercentage(val.pred);
      if (val.score < 0) perc = 1;
      if (val.score > 0) perc = 0;
      $matchperc.width(Math.round(perc * 100) + "%");
      var color = getColorForPercentage(perc);
      $matchperc.css("background-color", color);

      //$item.toggleClass('grid-item--size2', val.islarge)
    });
  } else {
    jQuery('.myCard').each( (i, el) => { 
      jQuery(el).attr('data-score', 0)
    })
  }
  jQuery('#loading').hide();
  // jQuery('#main-grid').removeClass('grid-non-updating');
  if (order_by == 'likelihood'){
    // Update in realtime, otherwise don't since random will reshuffle as well
    $grid.isotope('updateSortData').isotope();
  }
}

function computeLikelihood(){
    // API does minimization, so flip the likes to obtain the score (lower = better)
    let feedback = jQuery('.myCard[data-likes!=0]').map((i, el) => {
       return { 'item_id': jQuery(el).attr('data-id'), 'value': -parseInt(jQuery(el).attr('data-likes'))} 
     }).toArray();
    // jQuery('#loading').show();
    let data = {
      'embeddings': allProj,
      'feedback': feedback
    }
    jQuery('#loading').show();
    if (LIKE_API) {
      jQuery.ajax({
        url: LIKE_API,
        type: "POST",
        data: JSON.stringify(data),
        contentType:"application/json; charset=utf-8",
        dataType: "json",
        crossDomain: true,
        success: computeLikelihoodResponse,
        error: function (xhr, ajaxOptions, thrownError) {
          computeLikelihoodResponse(null)
        }
      });  
    } else {
      computeLikelihoodResponse(null)
    }
    
}


/**
 * START here and load JSON.
 */
const start = () => {
    // jQuery.noConflict(); // Free the dollar sign

    Promise.all([
        jQuery.getJSON('papers.json'),
        jQuery.getJSON('embeddings_tsne.json')
    ]).then(([papers, proj]) => {
        // shuffleArray(papers);

        allPapers = papers;
        allProj = proj;
        calcAllKeys(allPapers, allKeys);
        const allKeysCombined = allKeys['authors'].concat(allKeys['keywords'], allKeys['titles'])
        initTypeAhead(allKeysCombined, '.typeahead_all', 'ilike', (el, it) => { doSearch(it) });
        updateCards(allPapers)



        

        // Copy id's into parent cards for sorting
        jQuery('.myCard').each( (i, el) => { 
          el = jQuery(el)
          el.attr('data-id', el.find('.pp-card').attr('data-id'))
          el.attr('data-likes', 0)
        })



        jQuery('.pp-card .keywords').on('click', 'a', function(){ 
          doSearch(jQuery(this).text());
          return false; 
        });

        $grid = jQuery('.grid');

        $grid.isotope({
          // options
          itemSelector: '.grid-item',
          layoutMode: 'fitRows',
          getSortData: {
            searchMatch: '[data-search-match] parseFloat',
            id: '[data-id]',
            //searchMatch: '.pp-card[data-search-match] parseFloat',
            //id: '.pp-card[data-id]',
            score: '[data-score] parseFloat',
            maxScore: '[data-max-score] parseFloat',
            ei: '[data-ei] parseFloat',
            like: '[data-likes] parseInt',
          }
        });

        $grid.on( 'click', '.grid-item .feedback .like', function() {
          addLike(jQuery(this.closest('.pp-card')), 1)
        });
        
        $grid.on( 'click', '.grid-item .feedback .dislike', function() {
          addLike(jQuery(this.closest('.pp-card')), -1)
        });

        const urlSearch = decodeURIComponent(getUrlParameter("search"));
        const likestr = decodeURIComponent(getUrlParameter("likes"));
        const orderBy = decodeURIComponent(getUrlParameter("order_by")) || "likelihood";
        if (urlSearch !== '') {
          doSearch(urlSearch)
        }

        // Set the likes
        setLikesFromStr(likestr);

        setOrderBy(orderBy);


    }).catch(e => console.error(e))
}


/**
 * EVENTS
 * **/

jQuery('.btn-group.order_by').on( 'click', 'input', function() {
  order_by = jQuery(this).attr('value');
  setQueryStringParameter("order_by", encodeURIComponent(order_by));
  $grid.isotope('updateSortData').isotope();
  if (order_by == 'random'){
    $grid.isotope({ sortBy: 'random', sortAscending: true });
  } else if(order_by == 'search') {
    $grid.isotope({
      sortBy: ['searchMatch', 'random'],
      sortAscending: {
        'searchMatch': false,
        'random': true
      }
    });
  } else if (order_by == 'likelihood'){
    if (likelihood_outdated){
      computeLikelihood();
    }
    $grid.isotope({ sortBy: ['like', 'score', 'random'], sortAscending: {
        'like': false,
        'score': true,
        'random': true
      } });
  }
});

/**
 * CARDS
 */

const keyword = kw => `<a href="papers.html?filter=keywords&search=${kw}"
                       class="text-secondary text-decoration-none">${kw.toLowerCase()}</a>`
//language=HTML
const card_html = openreview => `
      <div class="myCard col-xs-6 col-md-4 grid-item">
        <div class="pp-card pp-mode-ilike" data-id="${openreview.content.iclr_id}" id="card-${openreview.content.iclr_id}">
            <div class="pp-card-header">
                <div class="title-wrapper">
                  <div class="preview dislike">
                    <div class="dislike">
                          <i class="fas fa-thumbs-up fa-stack-1x"></i>
                    </div>
                  </div><!--
               --><div class="feedback dislike">
                    <div class="fa-stack fa-lg dislike">
                      <!--<i class="fa fa-circle-thin fa-stack-2x"></i>-->
                      <i class="far fa-thumbs-up fa-stack-1x"></i>
                      <!--<i class="fas fa-times fa-stack-1x"></i>-->
                    </div>
                  </div><!--
               --><div class="title-inner">
                    <a href="${SITE_ROOT}poster_${openreview.content.iclr_id}.html" target="_blank"
                     class="text-muted">
                      <h5 class="card-title" align="center"> ${openreview.content.title} </h5>
                    </a>
                    <h6 class="card-subtitle text-muted" align="center">
                        ${openreview.content.authors.join(', ')}
                    </h6>
                  </div><!--
               --><div class="feedback like">
                    <div class="fa-stack fa-lg like">
                      <!--<i class="fa fa-circle-thin fa-stack-2x"></i>-->
                      <i class="far fa-thumbs-up fa-stack-1x"></i>
                      <!--<i class="far fa-heart fa-stack-1x"></i>-->
                    </div>
                  </div><!--
               --><div class="preview like">
                    <div class="like">
                        <i class="fas fa-thumbs-up fa-stack-1x"></i>
                    </div>
                  </div>
                </div>
                
                <center>
                  <img class="lazy-load-img cards_img" data-src="https://iclr.github.io/iclr-images/small/${openreview.content.iclr_id}.jpg" width="80%"/>
                </center>
                <div class="pp-card-detail">
                  <p class="card-text tldr"> ${openreview.content.TLDR}</p>
                  <p class="card-text keywords"><span class="font-weight-bold">Keywords:</span>
                      ${openreview.content.keywords.map(keyword).join(', ')}
                  </p>
                </div>
            </div>
        </div>
      </div>`
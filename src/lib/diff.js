function cmp_articles(a, b) {

	if( a === b ) {
		return 0
	} else if( (a[0] === 'equal' || a[0] === 'replace' || a[0] === 'delete') && (b[0] === 'equal' || b[0] === 'replace' || b[0] === 'delete') ) {
		return (a[3] < b[3] ? -1 : 1)
	} else if( (a[0] === 'equal' || a[0] === 'replace' || a[0] === 'insert') && (b[0] === 'equal' || b[0] === 'replace' || b[0] === 'insert') ) {
		return (a[4] < b[4] ? -1 : 1)
	} else {
		return (a[0] === 'delete' && b[0] === 'insert' ? -1 : 1)
	}
}

/**
 * Create a large-scale diff between articles.
 *
 * The two texts must have their articles names formatted in Markdown: on a single line, beginning
 * with one or more hash characters, followed by the string " Article " followed by the article name.
 *
 * TODO compare the summaries
 * TODO classify between renamed and moved articles (renamed is in the same location in the summary)
 * TODO detect moved headers
 *
 * @param str text_a First text to be compared.
 * @param str text_b Second text to be compared.
 * @return [[op, name_a, name_b, index_a, index_b, text_a, text_b]] where op is in ["equal", "replace", "delete", "insert"].
 */
function diff_articles(text_a, text_b) {

	const article_regex = /^(#+ )((?:Article )?)([^\n]+)\n*((?:(?!#)[^\n]*\n*)*)/gm
	let x, articles_a = {}, articles = {}, summary_a = [], summary_b = []
	while( x = article_regex.exec(text_a) ) {
		summary_a.push( x[1] + x[2] + x[3] )
		if( !x[2] ) {
			continue
		}
		articles[x[3]] = ['delete', x[3], '', x.index, null, x[4], '']
		articles_a[x[4]] = x[3]
	}
	while( x = article_regex.exec(text_b) ) {
		summary_b.push( x[1] + x[2] + x[3] )
		if( !x[2] ) {
			continue
		}
		if( x[4] in articles_a && x[3] === articles_a[x[4]] ) {
			articles[x[3]] = ['equal', x[3], x[3], articles[x[3]][3], x.index, x[4], x[4]]
		//} else if( x[4] in articles_a ) {
		//	// This will become move/rename operation, but it will probably handled in a separate data structure
		//	articles[x[3]] = ['move', x[3], x[3], articles[x[3]][3], x.index, articles[x[3]][5], x[4]]
		} else {
			if( x[3] in articles ) {
				articles[x[3]] = ['replace', x[3], x[3], articles[x[3]][3], x.index, articles[x[3]][5], x[4]]
			} else {
				articles[x[3]] = ['insert', '', x[3], null, x.index, '', x[4]]
			}
		}
	}

	articles = Object.values(articles)
	articles.sort(cmp_articles)

	return articles
}

export { diff_articles }

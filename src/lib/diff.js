import { lcs } from './lcs'
import { ratcliff_obershelp } from './ratcliff_obershelp'

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
 * TODO classify between renamed and moved articles (renamed is in the same location in the summary)
 * TODO detect moved headers
 *
 * @param str text_a First text to be compared.
 * @param str text_b Second text to be compared.
 * @return {articles, moved_articles} with:
 *         article := [[op, name_a, name_b, index_a, index_b, text_a, text_b]] where op is in ["equal", "replace", "delete", "insert"].
 *         moved_articles := [set_a, set_b] where set_a are articles names in text_a, set_b are articles in text_b and these
 *                           articles have the same content (but are non-identical articles names), so they are renamed or moved articles
 *                           (note that each set will often have only one element, it can not always be the case for common content).
 */
function diff_articles(text_a, text_b) {

	const article_regex = /^(#+ )((?:Article )?)([^\n]+)\n*((?:(?!#)[^\n]*\n*)*)/gm
	let x, ident, articles_a = {}, articles = {}, summary_a = [], summary_b = [], summary_a_raw = [], summary_b_raw = []
	while( x = article_regex.exec(text_a) ) {
		summary_a.push( [ x.index, x[1].length-1, x[2] + x[3] ] )
		summary_a_raw.push( x[2] + x[3] )
		if( !x[2] ) {
			continue
		}
		x[4] = x[4].trim()
		articles[x[3]] = ['delete', x[3], '', x.index, null, x[4], '']
		if( ! (x[4] in articles_a) ) {
			articles_a[x[4]] = [new Set(), new Set()]
		}
		articles_a[x[4]][0].add(x[3])
	}
	while( x = article_regex.exec(text_b) ) {
		summary_b.push( [ x.index, x[1].length-1, x[2] + x[3] ] )
		summary_b_raw.push( x[2] + x[3] )
		if( !x[2] ) {
			continue
		}
		x[4] = x[4].trim()
		ident = x[4] in articles_a
		if( ident && articles_a[x[4]][0].has(x[3]) !== -1 ) {
			articles[x[3]] = ['equal', x[3], x[3], articles[x[3]][3], x.index, x[4], x[4]]
			articles_a[x[4]][0].delete(x[3])
			if( articles_a[x[4]][0].size === 0 &&  articles_a[x[4]][1].size === 0 ) {
				delete articles_a[x[4]]
			}
		} else {
			if( x[3] in articles ) {
				articles[x[3]] = ['replace', x[3], x[3], articles[x[3]][3], x.index, articles[x[3]][5], x[4]]
			} else {
				articles[x[3]] = ['insert', '', x[3], null, x.index, '', x[4]]
				if( ident ) {
					articles_a[x[4]][1].add(x[3])
				}
			}
		}
	}

	let matching_blocks = ratcliff_obershelp( summary_a_raw, summary_b_raw)
	let opcodes = opcodes_from_matching_blocks( matching_blocks )
	let summary = [], i, j, level = -1
	for( i=0; i<opcodes.length; i++ ) {
		if( opcodes[i][0] === 'equal' ) {
			for( j=opcodes[i][1]; j<opcodes[i][2]; j++ ) {
				summary.push( [ 'equal', summary_a[j][1], summary_a[j][2] ] )
			}
		} else if( opcodes[i][0] === 'delete' ) {
			for( j=opcodes[i][1]; j<opcodes[i][2]; j++ ) {
				summary.push( [ 'delete', summary_a[j][1], summary_a[j][2] ] )
			}
		} else if( opcodes[i][0] === 'insert' ) {
			for( j=opcodes[i][3]; j<opcodes[i][4]; j++ ) {
				summary.push( [ 'insert', summary_b[j][1], summary_b[j][2] ] )
			}
		} else if( opcodes[i][0] === 'replace' ) {
			let minij = opcodes[i][4] - opcodes[i][3] < opcodes[i][2] - opcodes[i][1] ? opcodes[i][4] - opcodes[i][3] : opcodes[i][2] - opcodes[i][1]
			for( j=0; j<minij; j++ ) {
				const titleA = summary_a[opcodes[i][1]+j][2],
				      titleB = summary_b[opcodes[i][3]+j][2]
				if( ( titleA.substring(0, 8) === 'Article ' && titleB.substring(0, 8) !== 'Article ' ) ||
				    ( titleA.substring(0, 8) !== 'Article ' && titleB.substring(0, 8) === 'Article ' ) ) {
					summary.push( [ 'delete', summary_a[j][1], summary_a[j][2] ] )
					summary.push( [ 'insert', summary_b[j][1], summary_b[j][2] ] )
				} else {
					summary.push( [ 'replace', summary_a[opcodes[i][1]+j][1], summary_a[opcodes[i][1]+j][2],
					                           summary_b[opcodes[i][3]+j][1], summary_b[opcodes[i][3]+j][2] ] )
				}
			}
		}
	}

	const moved_articles = Object.values(articles_a).filter(s => s[1].size !== 0)

	articles = Object.values(articles)
	articles.sort(cmp_articles)

	return { articles, moved_articles, summary }
}

function opcodes_from_matching_blocks( matching_blocks ) {

	let opcodes = [], i = 0, j = 0,
	    tag, ai, bj, size, k

	for( k=0; k<matching_blocks.length; k++ ) {
		tag = ''
		//[ ai, bj, size ] = matching_blocks[k]
		ai = matching_blocks[k][0]
		bj = matching_blocks[k][1]
		size = matching_blocks[k][2]
		if( i < ai && j < bj ) {
			tag = 'replace'
		} else if( i < ai ) {
			tag = 'delete'
		} else if( j < bj ) {
			tag = 'insert'
		}
		if( tag ) {
			opcodes.push( [ tag, i, ai, j, bj ] )
		}
		i = ai + size
		j = bj + size
		if( size ) {
			opcodes.push( [ 'equal', ai, i, bj, j ] )
		}
	}

	return opcodes
}

function keep_lcs_words(i, j, k, lcs, text_a, text_b, n, m) {

	// LCS matching this condition are guaranteed to be kept. Possibly they will be shortened, except if it would result in removing them.
	// This veto is in the following cases:
	// - LCS containing a newline
	// - LCS at the beginning or at the end of the text
	let lcs_value = text_a.substring( lcs[0], lcs[0] + k ),
	    veto_keep = ( lcs_value.indexOf('\n') !== -1 || i === 0 || j === 0 || i+k === n || j+k === m )

	// Minimum length of the LCS, except if vetoed by the condition above
	const minimum_length = 5

	// If the LCS is too small, don’t consider it is a valuable LCS, except if vetoed
	if( k <= minimum_length && ! veto_keep ) {
		return { i, j, k, l: false }
	}

	let l0 = 0,
	    k0 = k,
	    lcs0 = lcs_value

	const two_letters = /[a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ0-9'’]{2}/i

	// If the LCS starts in the middle of a word, remove these characters from the LCS
	if( i > 0 && j > 0 ) {
		let strA = text_a.substring( i - 1, i + k0 ),
		    strB = text_b.substring( j - 1, j + k0 )
		while( k0 && ( two_letters.test( strA.substring( l0, l0 + 2 ) ) || two_letters.test( strB.substring( l0, l0 + 2 ) ) ) ) {
			k0--
			l0++
		}
	}

	// If the LCS ends in the middle of a word, remove these characters from the LCS
	if( i + k < n && j + k < m ) {
		let strA = text_a.substring( i, i + l0 + k0 + 1 ),
		    strB = text_b.substring( j, j + l0 + k0 + 1 )
		while( k0 && ( two_letters.test( strA.substring( l0 + k0 - 1, l0 + k0 + 1 ) ) || two_letters.test( strB.substring( l0 + k0 -1, l0 + k0 + 1 ) ) ) ) {
			k0--
		}
	}

	// If the LCS is too small, don’t consider it is a valuable LCS, except if vetoed
	if( k0 <= minimum_length && ! veto_keep ) {
		return { i, j, k, l: false }
	}

	i += l0
	j += l0
	k = k0

	return { i, j, k, l: true }
}

export { diff_articles, opcodes_from_matching_blocks, keep_lcs_words }

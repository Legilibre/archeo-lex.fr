import config from '../../../../../../../config'
import git from '../../../../../../../lib/git'
import { diff_articles, opcodes_from_matching_blocks, keep_lcs_words } from '../../../../../../../lib/diff';
import { lcs } from '../../../../../../../lib/lcs';
import { ratcliff_obershelp } from '../../../../../../../lib/ratcliff_obershelp';

function is404(res) {
	return (res.writeHead(404, { 'Content-Type': 'application/json' }), res.end('null'))
}
function is400(res) {
	return (res.writeHead(400, { 'Content-Type': 'application/json' }), res.end('null'))
}

export async function get(req, res) {

	const { nature, identifiant, date } = req.params

	// If the request is too bad, return 400
	if( !config.natures.has(nature) || !/^\d{8}$/.test(date) ) {
		return is400(res)
	}

	const texts = await git.list_refs(config.repo),
	      texte = texts[identifiant]

	if( !texte ) {
		return is404(res)
	}

	const vigueur = texte.texte,
	      vigueur_future = texte['texte-futur'],
	      natureTexte = texte.nature

	if( natureTexte !== nature ) {
		return is404(res)
	}

	let rev = null
	if( vigueur_future ) {
		rev = await git.get_commit_older_than(config.repo, (vigueur?vigueur+'...':'')+vigueur_future, 'vigueur-future', date)
	}
	if( vigueur && !rev ) {
		rev = await git.get_commit_older_than(config.repo, vigueur, 'vigueur', date)
	}
	if( !rev ) {
		return is404(res)
	}

	const tree = await git.cat_file(config.repo, rev.tree),
	      blob_hash = /^100644 blob ([0-9a-f]+)/m.exec(tree)[1],
	      blob = await git.cat_file(config.repo, blob_hash)

	let rev_prev, tree_prev, blob_hash_prev, blob_prev

	try {
		rev_prev = await git.get_commit(config.repo, rev.hash+'~1')
		tree_prev = await git.cat_file(config.repo, rev_prev.tree)
		blob_hash_prev = /^100644 blob ([0-9a-f]+)/m.exec(tree_prev)[1]
		blob_prev = await git.cat_file(config.repo, blob_hash_prev)
	} catch(error) {
		rev_prev = {}
		blob_prev = ''
	}

	let { articles, moved_articles } = diff_articles(blob_prev, blob)

	let diffs = articles.filter(s => {
		return s[0] !== 'equal'
	}).map(s => {
		let matching_blocks = ratcliff_obershelp( s[5], s[6], keep_lcs_words )
		let opcodes = opcodes_from_matching_blocks( matching_blocks )
		let t = opcodes.map(u => {
			if( u[0] === 'equal' ) {
				return s[5].substring(u[1], u[2])
			} else if( u[0] === 'delete' ) {
				return '<del>' + s[5].substring(u[1], u[2]).replace(/\n/g, '</del>\n<del>').replace(/<del><\/del>/g, '') + '</del>'
			} else if( u[0] === 'insert' ) {
				return '<ins>' + s[6].substring(u[3], u[4]).replace(/\n/g, '</ins>\n<ins>').replace(/<ins><\/ins>/g, '') + '</ins>'
			} else if( u[0] === 'replace' ) {
				return '<del>' + s[5].substring(u[1], u[2]).replace(/\n/g, '</del>\n<del>').replace(/<del><\/del>/g, '') + '</del>' +
				       '<ins>' + s[6].substring(u[3], u[4]).replace(/\n/g, '</ins>\n<ins>').replace(/<ins><\/ins>/g, '') + '</ins>'
			}
		}).join('')
		s.push('# Article ' + ( s[1] || s[2] ) + '\n\n' + t)
		return s
	})

	const result = {
		date_prev: rev_prev.date || null,
		condensat_prev: rev_prev.hash || null,
		etat_prev: rev_prev.etat || null,
		date: rev.date,
		condensat: rev.hash,
		etat: rev.etat,
		diffs,
	}

	// Expires at 20:00:00 CE(S)T
	let d = new Date(), d2, maxage = 300
	d.setHours(20)
	d.setMinutes(0)
	d.setSeconds(0)
	d2 = Math.round((d - new Date())/1000)
	if( d2 > 300 && d2 < 57600 ) {
		maxage = d2
	}

	res.writeHead(200, {
		'Content-Type': 'application/json',
		'Expires': d.toGMTString(),
		'Cache-Control': 'public, max-age=' + maxage,
	})
	res.end(JSON.stringify(result))
}

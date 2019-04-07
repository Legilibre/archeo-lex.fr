import DiffMatchPatch from 'diff-match-patch';
import config from '../../../../../../config'
import git from '../../../../../../lib/git'
import { diff_articles } from '../../../../../../../lib/diff';

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
	      blob = await git.cat_file(config.repo, blob_hash),
	      commit_prev = await git.get_commit(config.repo, rev.hash+'~1'),
	      tree_prev = await git.cat_file(config.repo, commit_prev.tree),
	      blob_hash_prev = /^100644 blob ([0-9a-f]+)/m.exec(tree_prev)[1],
	      blob_prev = await git.cat_file(config.repo, blob_hash_prev)

	let dmp = new DiffMatchPatch()

	let diffs = diff_articles(prev_blob, blob).filter(s => {
		return s[0] !== 'equal'
	}).map(s => {
		let diffs_articles = dmp.diff_main(s[5], s[6])
		dmp.diff_cleanupSemantic(diffs_articles)
		let t = diffs_articles.map(u => {
			if( u[0] === 0 ) {
				return u[1]
			} else if( u[0] === -1 ) {
				return '<del>' + u[1].replace(/\n/g, '</del>\n<del>').replace(/<del><\/del>/g, '') + '</del>'
			} else if( u[0] === 1 ) {
				return '<ins>' + u[1].replace(/\n/g, '</ins>\n<ins>').replace(/<ins><\/ins>/g, '') + '</ins>'
			}
		}).join('')
		s.push('# Article ' + s[1] + '\n\n' + t)
		return s
	})

	const result = {
		date_prev: prev_rev.date,
		condensat_prev: prev_rev.hash,
		etat_prev: prev_rev.etat,
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

import config from '../../../../../../config'
import git from '../../../../../../lib/git'

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
	      result = {
	      	date: rev.date,
	      	condensat: rev.hash,
	      	etat: rev.etat,
	      	texte: blob
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

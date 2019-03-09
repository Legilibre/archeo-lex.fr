import config from '../../../config';
import git from '../../../lib/git';

export async function get(req, res) {

	const { nature, identifiant } = req.params;

	if( config.natures.has(nature) ) {

		const texts = await git.list_refs(config.repo);

		res.writeHead(200, {
			'Content-Type': 'application/json'
		});

		const texte = texts[identifiant],
		      vigueur = texte.texte,
		      vigueur_future = texte['texte-futur'],
		      natureTexte = texte.nature;

		if( natureTexte != nature ) {
			res.writeHead(404, {
				'Content-Type': 'application/json'
			});
			res.end(JSON.stringify({
				message: 'Not found'
			}));
		}

		const default_state = vigueur ? 'vigueur' : 'vigueur-future';
		let revs = [];
		if( vigueur_future ) {
			revs = revs.concat(await git.list_revs(config.repo, (vigueur?vigueur+'...':'')+vigueur_future, 'vigueur-future', default_state));
		}
		if( vigueur ) {
			revs = revs.concat(await git.list_revs(config.repo, vigueur, 'vigueur', default_state));
		}
		res.end(JSON.stringify({etat: default_state, versions: revs}));
	} else {
		res.writeHead(404, {
			'Content-Type': 'application/json'
		});

		res.end(JSON.stringify({
			message: 'Not found'
		}));
	}
}

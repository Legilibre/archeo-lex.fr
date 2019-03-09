import config from '../../../../../config';
import git from '../../../../../lib/git';

export async function get(req, res) {

	const { nature, identifiant, date } = req.params;

	if( config.natures.has(nature) ) {
		const texts = await git.list_refs(config.repo),
		      texte = texts[identifiant],
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

		res.writeHead(200, {
			'Content-Type': 'application/json'
		});

		let revs = [];
		if( vigueur_future ) {
			revs = revs.concat(await git.list_revs(config.repo, (vigueur?vigueur+'...':'')+vigueur_future, 'vigueur-future'));
		}
		if( vigueur ) {
			revs = revs.concat(await git.list_revs(config.repo, vigueur, 'vigueur'));
		}
		let rev = null, item;
		for( item in revs ) {
			if( revs[item].date.replace(/-/g, '') === date ) {
				rev = revs[item];
				break;
			}
		}
		let commit_hash = rev.hash,
		    commit = await git.cat_file(config.repo, commit_hash);
		let tree_hash = /^tree ([0-9a-f]+)$/m.exec(commit)[1],
		    tree = await git.cat_file(config.repo, tree_hash);
		let blob_hash = /^100644 blob ([0-9a-f]+)/m.exec(tree)[1],
		    blob = await git.cat_file(config.repo, blob_hash);

		let result = {
			date: rev.date,
			condensat: rev.hash,
			etat: rev.etat,
			texte: blob
		};

		res.end(JSON.stringify(result));
	} else {
		res.writeHead(404, {
			'Content-Type': 'application/json'
		});

		res.end(JSON.stringify({
			message: 'Not found'
		}));
	}
}

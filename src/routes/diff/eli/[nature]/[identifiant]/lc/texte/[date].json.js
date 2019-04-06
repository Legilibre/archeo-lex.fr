import DiffMatchPatch from 'diff-match-patch';
import config from '../../../../../../../config';
import git from '../../../../../../../lib/git';
import { diff_articles } from '../../../../../../../lib/diff';

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
		let rev = null, item, prev_item = false, prev_rev = null;
		for( item in revs ) {
			if( revs[item].date.replace(/-/g, '') === date ) {
				prev_item = true
				rev = revs[item]
			} else if( prev_item ) {
				prev_rev = revs[item]
				break
			}
		}
		let commit_hash = rev.hash,
		    commit = await git.cat_file(config.repo, commit_hash);
		let tree_hash = /^tree ([0-9a-f]+)$/m.exec(commit)[1],
		    tree = await git.cat_file(config.repo, tree_hash);
		let blob_hash = /^100644 blob ([0-9a-f]+)/m.exec(tree)[1],
		    blob = await git.cat_file(config.repo, blob_hash);

		commit_hash = prev_rev.hash
		commit = await git.cat_file(config.repo, commit_hash)
		tree_hash = /^tree ([0-9a-f]+)$/m.exec(commit)[1]
		tree = await git.cat_file(config.repo, tree_hash)
		blob_hash = /^100644 blob ([0-9a-f]+)/m.exec(tree)[1]
		let prev_blob = await git.cat_file(config.repo, blob_hash)

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

		let result = {
			date_prev: prev_rev.date,
			condensat_prev: prev_rev.hash,
			etat_prev: prev_rev.etat,
			date: rev.date,
			condensat: rev.hash,
			etat: rev.etat,
			diffs,
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

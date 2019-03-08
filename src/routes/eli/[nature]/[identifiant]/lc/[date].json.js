const simpleGit = require('simple-git');
const git = require('simple-git/promise')('/mnt/TEST/legi/codes2/.git');

const repo = simpleGit('/mnt/TEST/legi/codes2/.git');

const natures = new Set(['code']);

const moisFR = { 'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08', 'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12' };

const dateFR2ISO8601 = (date) => {
	const r = /^(?:Version consolidée au )?([0-9]+)(?:er)? ([a-zéû]+) ([0-9]+)$/.exec(date);
	if(r) {
		return r[3] + '-' + moisFR[r[2]] + '-' + (r[1].length == 1 ? '0' : '') + r[1];
	}
	return null;
};

const list_refs = (fn) => {
	repo.raw(['show-ref'], (err, data) => {
		let d = data.trim().split('\n').reduce( (obj, item) => {
			let r = /^([0-9a-f]+) (refs\/.*)$/.exec(item);
			obj[r[2]] = r[1];
			return obj;
		}, {});
		let texts = {};
		for( let item in d) {
			let r = /^refs\/([^\/]+)\/([^\/]+)\/(texte(?:-futur)?)$/.exec(item);
			if( !r ) {
				continue;
			}
			texts[r[2]] = Object.assign(texts[r[2]] || {}, {nature: r[1].replace(/s$/, ''), [r[3]]: d[item]});
		}
		fn(texts);
	});
};

const list_revs = async (hash, state) => {
	const data = await git.log({ [hash]: null, format: { hash: '%H', message: '%s' }});
	return data.all.map(item => { return { hash: item.hash, date: dateFR2ISO8601(item.message), etat: state } });
};

const cat_file = async (hash) => {
	const data = await git.catFile([ '-p', hash]);
	return data;
};

export async function get(req, res) {

	const { nature, identifiant, date } = req.params;

	if( natures.has(nature) ) {
		list_refs(async data => {
			res.writeHead(200, {
				'Content-Type': 'application/json'
			});

			const texte = data[identifiant],
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

			let revs = [];
			if( vigueur_future ) {
				revs = revs.concat(await list_revs((vigueur?vigueur+'...':'')+vigueur_future, 'vigueur-future'));
			}
			if( vigueur ) {
				revs = revs.concat(await list_revs(vigueur, 'vigueur'));
			}
			let rev = null, item;
			for( item in revs ) {
				if( revs[item].date.replace(/-/g, '') === date ) {
					rev = revs[item];
					break;
				}
			}
			let commit_hash = rev.hash,
			    commit = await cat_file(commit_hash);
			let tree_hash = /^tree ([0-9a-f]+)$/m.exec(commit)[1],
			    tree = await cat_file(tree_hash);
			let blob_hash = /^100644 blob ([0-9a-f]+)/m.exec(tree)[1],
			    blob = await cat_file(blob_hash);

			let result = {
				date: rev.date,
				condensat: rev.hash,
				etat: rev.etat,
				texte: blob
			};

			res.end(JSON.stringify(result));
		});
	} else {
		res.writeHead(404, {
			'Content-Type': 'application/json'
		});

		res.end(JSON.stringify({
			message: 'Not found'
		}));
	}
}

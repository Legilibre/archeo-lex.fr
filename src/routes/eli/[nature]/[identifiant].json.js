import * as config from '../../../config';

const git = require('simple-git/promise')(config.repo);

const moisFR = { 'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08', 'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12' };

const dateFR2ISO8601 = (date) => {
	const r = /^(?:Version consolidée au )?([0-9]+)(?:er)? ([a-zéû]+) ([0-9]+)$/.exec(date);
	if(r) {
		return r[3] + '-' + moisFR[r[2]] + '-' + (r[1].length == 1 ? '0' : '') + r[1];
	}
	return null;
};

const list_refs = async () => {
	const showref = await git.raw(['show-ref']);

	const refs = showref.trim().split('\n').reduce( (obj, item) => {
		let r = /^([0-9a-f]+) (refs\/.*)$/.exec(item);
		obj[r[2]] = r[1];
		return obj;
	}, {});

	let texts = {};
	for( let item in refs) {
		let r = /^refs\/([^\/]+)\/([^\/]+)\/(texte(?:-futur)?)$/.exec(item);
		if( r ) {
			texts[r[2]] = Object.assign(texts[r[2]] || {}, {nature: r[1].replace(/s$/, ''), [r[3]]: refs[item]});
		}
	}

	return texts;
};

const list_revs = async (hash, state) => {
	const data = await git.log({ [hash]: null, format: { hash: '%H', message: '%s' }});
	return data.all.map(item => { return { hash: item.hash, date: dateFR2ISO8601(item.message), etat: state } });
};

export async function get(req, res) {

	const { nature, identifiant } = req.params;

	if( config.natures.has(nature) ) {

		const texts = await list_refs();

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

		let revs = [];
		if( vigueur_future ) {
			revs = revs.concat(await list_revs((vigueur?vigueur+'...':'')+vigueur_future, 'vigueur-future'));
		}
		if( vigueur ) {
			revs = revs.concat(await list_revs(vigueur, 'vigueur'));
		}
		res.end(JSON.stringify(revs));
	} else {
		res.writeHead(404, {
			'Content-Type': 'application/json'
		});

		res.end(JSON.stringify({
			message: 'Not found'
		}));
	}
}

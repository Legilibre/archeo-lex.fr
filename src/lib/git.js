const gitp = require('simple-git/promise');

const moisFR = { 'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08', 'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12' };

function dateFR2ISO8601(date) {
	const r = /^(?:Version consolidée au )?([0-9]+)(?:er)? ([a-zéû]+) ([0-9]+)$/.exec(date);
	return r ? r[3] + '-' + moisFR[r[2]] + '-' + (r[1].length == 1 ? '0' : '') + r[1] : null;
}

async function list_refs(repo) {
	const git = gitp(repo),
	      showref = await git.raw(['show-ref']),
	      refs = showref.trim().split('\n').reduce( (obj, item) => {
		let r = /^([0-9a-f]+) (refs\/.*)$/.exec(item);
		obj[r[2]] = r[1];
		return obj;
	}, {});
	let r, item, texts = {};

	for( item in refs) {
		r = /^refs\/([^\/]+)\/([^\/]+)\/(texte(?:-futur)?)$/.exec(item);
		if( r ) {
			texts[r[2]] = Object.assign(texts[r[2]] || {}, {nature: r[1].replace(/s$/, ''), [r[3]]: refs[item]});
		}
	}

	return texts;
}

async function list_revs(repo, hash, state) {
	const data = await gitp(repo).log({ [hash]: null, format: { hash: '%H', message: '%s' }});
	return data.all.map(item => { return { hash: item.hash, date: dateFR2ISO8601(item.message), etat: state } });
}

async function cat_file(repo, hash) {
	const data = await gitp(repo).catFile([ '-p', hash]);
	return data;
}


export default { dateFR2ISO8601, list_refs, list_revs, cat_file };

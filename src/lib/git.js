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
		r = /^refs\/([^\/]+)\/([^\/]+)\/(texte(?:-futur|-abrogé)?)$/.exec(item);
		if( r ) {
			texts[r[2]] = Object.assign(texts[r[2]] || {}, {nature: r[1].replace(/s$/, ''), [r[3]]: refs[item]});
		}
	}

	return texts;
}

async function list_revs(repo, hash, state) {
	const data = await gitp(repo).log({ [hash]: null, format: { hash: '%H', message: '%s', tree: '%T' }});
	return data.all.map(item => { return { hash: item.hash, date: dateFR2ISO8601(item.message), tree: item.tree, etat: state } });
}

async function cat_file(repo, hash) {
	const data = await gitp(repo).catFile([ '-p', hash]);
	return data;
}

async function get_commit(repo, hash) {
	const git = gitp(repo),
	      log = await git.silent(true).raw(['log', '-1', '--pretty=%H %T %ai %s', hash]),
	      r = /^([0-9a-f]+) ([0-9a-f]+) ([0-9]{4}-[0-9]{2}-[0-9]{2}) 00:00:00 \+0[12]00 (.*)$/.exec( log.trim() )
	return {
		hash: r[1],
		date: dateFR2ISO8601(r[4]),
		tree: r[2],
	}
}

async function get_commit_older_than(repo, hash, state, date) {
	const git = gitp(repo)
	date = date.substring(0, 4) + '-' + date.substring(4, 6) + '-' + date.substring(6, 8)
	if( date >= "19700103" ) {
		let log = await git.raw(['log', '--before='+date, '-1', '--pretty=%H %T %ai %s', hash])
		if( log ) {
			let r = /^([0-9a-f]+) ([0-9a-f]+) ([0-9]{4}-[0-9]{2}-[0-9]{2}) 00:00:00 \+0[12]00 (.*)$/.exec( log.trim() )
			if( state === 'vigueur-future' && r[3] !== date ) {
				return null
			}
			return {
				hash: r[1],
				date: r[3],
				tree: r[2],
				etat: state,
			}
		}
		if( state === 'vigueur-future' ) {
			return null
		}
	}
	const data = await git.log({ [hash]: null, format: { hash: '%H', message: '%s', tree: '%T' }});
	const older = data.all.map(item => { return { hash: item.hash, date: dateFR2ISO8601(item.message), tree: item.tree, etat: state } }).filter(s => {
		return s.date <= date
	})
	return older.length >= 1 ? older[0] : null
}


export default { dateFR2ISO8601, list_refs, list_revs, cat_file, get_commit_older_than, get_commit };

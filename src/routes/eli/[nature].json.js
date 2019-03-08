import * as config from '../../config';

const git = require('simple-git/promise')(config.repo);

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

export async function get(req, res) {

	const { nature } = req.params;

	if( config.natures.has(nature) ) {
		res.writeHead(200, {
			'Content-Type': 'application/json'
		});

		const texts = await list_refs();
		for( let item in texts ) {
			if( texts[item].nature != nature ) {
				delete texts[item];
			} else {
				delete texts[item]['nature'];
			}
		}

		res.end(JSON.stringify(texts));
	} else {
		res.writeHead(404, {
			'Content-Type': 'application/json'
		});
		res.end(JSON.stringify({
			message: 'Not found'
		}));
	}
}

const simpleGit = require('simple-git');

const repo = simpleGit('/mnt/TEST/legi/codes2/.git');

const natures = new Set(['code']);

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

export function get(req, res) {

	const { nature } = req.params;

	if( natures.has(nature) ) {
		list_refs(data => {
			res.writeHead(200, {
				'Content-Type': 'application/json'
			});

			for( let item in data ) {
				if( data[item].nature != nature ) {
					delete data[item];
				} else {
					delete data[item]['nature'];
				}
			}

			res.end(JSON.stringify(data));
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

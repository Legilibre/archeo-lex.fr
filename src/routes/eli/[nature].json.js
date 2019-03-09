import config from '../../config';
import git from '../../lib/git';

export async function get(req, res) {

	const { nature } = req.params;

	if( config.natures.has(nature) ) {
		res.writeHead(200, {
			'Content-Type': 'application/json'
		});

		const texts = await git.list_refs(config.repo);
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

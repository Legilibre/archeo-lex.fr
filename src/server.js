import sirv from 'sirv';
import polka from 'polka';
import compression from 'compression';
import csp from 'helmet-csp';
import uuid from 'uuid/v4';
import * as sapper from '../__sapper__/server.js';
import config from './config.js';

const { PORT, NODE_ENV } = process.env;
const dev = NODE_ENV === 'development';

let connectSrc = ["'self'"];
if( dev ) {
	connectSrc.push(config.devServer);
}
const base = '/' + config.base.replace(/\/+/g, '/').replace(/^\//, '').replace(/\/$/, '');

polka()
	.use((req, res, next) => {
		res.locals = {}
		res.locals.nonce = uuid()
		next()
	})
	.use(csp({
		directives: {
			defaultSrc: ["'none'"],
			styleSrc: ["'self'", "'unsafe-inline'"],
			scriptSrc: ["'self'", "'unsafe-eval'", (req, res) => `'nonce-${res.locals.nonce}'`],
			fontSrc: ["'self'"],
			baseUri: ["'self'"],
			connectSrc: connectSrc,
			workerSrc: ["'self'"],
			imgSrc: ["'self'"],
		},
		reportOnly: dev
	}))
	.use(
		base,
		compression({ threshold: 0 }),
		sirv('static', { dev }),
		sapper.middleware()
	)
	.listen(PORT, err => {
		if (err) console.log('error', err);
	});

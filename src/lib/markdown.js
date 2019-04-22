function get_summary(markdown) {


}

function balance_html(text) {

	let ltext = text.split(/(<div(?: [a-zA-Z]+="[^"]*")*>|<\/div>)/), i, ic = 0;

	for( i=0; i<ltext.length; i++ ) {
		if( ltext[i].substring(0, 4) === '<div' ) {
			ic += 1;
		} else if( ltext[i].substring(0, 6) === '</div>' ) {
			ic -= 1;
		}
		if( ic < 0 ) {
			ltext[i] = Array(-ic).fill('<div>').join('') + ltext[i];
			ic = 0;
			console.log([ic,ltext[i]]);
		}
	}

	text = ltext.join('');
	if( ic > 0 ) {
		text += Array(ic).fill('</div>').join('');
	}

	return text;
}

function markdown_article(text) {

	// Paragraphs
	text = ('\n\n'+text+'\n\n').replace(/^\n([^\n]+)(?=\n\n)/gm, (match, p1) => {
		let t = '<p><span>' + p1 + '</span></p>';
		t = t.replace(/<ins>/g, '</span><ins>');
		t = t.replace(/<del>/g, '</span><del>');
		t = t.replace(/<\/ins>/g, '</ins><span>');
		t = t.replace(/<\/del>/g, '</del><span>');
		return t;
	});

	text = text.replace(/<span><\/span>/g, '');
	text = text.replace(/<del><\/del>/g, '');
	text = text.replace(/<ins><\/ins>/g, '');

	return text;
}

function markdown2html(markdown) {

	let html = '\n' + markdown + '\n'

	// Typography
	html = html.replace(/[  _]?;/g, ' ;');
	html = html.replace(/[  _]?:/g, ' :');
	html = html.replace(/'/g, '’');

	// Cleaning
	html = html.replace(/<div[^\/>]*\/>/g, '');

	// Transform articles
	html = html.replace(/^(?:#+) ((?:<ins>|<del>)?)Article ([^\n]+)\n((?:(?!#)[^\n]*\n*)*)/gm, (match, p1, p2, p3) => {
		return '<div id="article_' + p2 + '" class="article"><h3>' + p1 + 'Article ' + p2 + '</h3>\n' + markdown_article(balance_html(p3)) + '</div>\n\n';
	});

	// Transform headers
	html = html.replace(/^(#+) (.*)$/gm, (match, p1, p2) => {
		return '<h2 class="h' + p1.length + ' hmod3r' + ((p1.length-1)%3) + '" id="' + p2.replace(/[  ]/g, '_').replace(/’/g, "'") + '">' + p2 + '</h2>';
	});

	// Lists
	html = html.replace(/^((?:- [^\n]+\n)+)/gm, '<ul>\n$1</ul>\n\n');
	html = html.replace(/^- ([^\n]+)\n/gm, '<li>$1</li>\n');

	// Cleaning
	html = html.replace(/<\/p>\n+<p(?=[> ])/g, '</p>\n<p');
	html = html.replace(/\n{3,}/g, '\n\n');

	return html.trim();
}

const markdown = {
	get_summary,
	markdown2html
};
export default markdown;

function get_summary(markdown) {


}

function markdown2html(markdown) {

	let html = '\n' + markdown + '\n'

	html = html.replace(/^(#+) (.*)$/gm, (match, p1, p2) => { return '<h2 class="h' + p1.length + '">' + p2 + '</h2>' });

	return html;
}

const markdown = {
	get_summary,
	markdown2html
};
export default markdown;

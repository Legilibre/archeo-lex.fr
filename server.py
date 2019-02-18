# coding: utf-8

import http.server
import subprocess
import time
import sys
import os
import re

import metslesliens

basename = '/mnt/TEST/legi/codes'

cache = {}

mois = {
    'janvier':   '01',
    'février':   '02',
    'mars':      '03',
    'avril':     '04',
    'mai':       '05',
    'juin':      '06',
    'juillet':   '07',
    'août':      '08',
    'septembre': '09',
    'octobre':   '10',
    'novembre':  '11',
    'décembre':  '12',
}
mois2 = {
    '01': 'janvier',
    '02': 'février',
    '03': 'mars',
    '04': 'avril',
    '05': 'mai',
    '06': 'juin',
    '07': 'juillet',
    '08': 'août',
    '09': 'septembre',
    '10': 'octobre',
    '11': 'novembre',
    '12': 'décembre',
}

def metsenformelarticle(x, url1=None, url2=None):

    texte = x.group(2)

    #return '<div id="article_' + x.group(1) + '" class="article"><h3>Article ' + x.group(1) + '</h3>\n' + balance_html(texte) + '</div>\n\n'

    translation = 0
    for lien in metslesliens.generateur_donnelescandidats(texte, 'structuré'):
        if 'article' in lien and ('texte' not in lien):
            index = lien['index']
            texte_lie = texte[index[0]+translation:index[1]+translation]
            if not isinstance(lien['article'], list):
                lien['article'] = [lien['article']]
            for noms_article in lien['article']:
                if isinstance(noms_article, str):
                    noms_article = [noms_article]
                for nom_article in noms_article:
                    if nom_article == 'présent':
                        continue
                    m = texte_lie.find(nom_article)
                    span = (m, m+len(nom_article))
                    destination_article = re.sub('^([LDRA])\.? ?', r'\1', re.sub('^L\.?O\.? ', 'LO', nom_article))
                    href = url1.replace('\\1', 'article_' + destination_article) if url1 else '#article_' + destination_article
                    texte_lie = texte_lie[:span[0]] + '<a href="' + href + '">' + texte_lie[span[0]:span[1]] + '</a>' + texte_lie[span[1]:]
            texte = texte[:index[0]+translation] + texte_lie + texte[index[1]+translation:]
            translation += len(texte_lie) - index[1] + index[0]
        elif 'article' in lien and 'texte' in lien and 'nom' in lien['texte'] and (lien['texte']['nom'].startswith('code ') or lien['texte']['nom'] == 'livre des procédures fiscales'):
            index = lien['index']
            texte_lie = texte[index[0]+translation:index[1]+translation]
            if not isinstance(lien['article'], list):
                lien['article'] = [lien['article']]
            for noms_article in lien['article']:
                if isinstance(noms_article, str):
                    noms_article = [noms_article]
                for nom_article in noms_article:
                    m = texte_lie.find(nom_article)
                    span = (m, m+len(nom_article))
                    destination_article = re.sub('^([LDRA])\.? ?', r'\1', re.sub('^L\.?O\.? ', 'LO', nom_article))
                    href = url2.replace('\\1', 'article_' + destination_article).replace('\\2', 'code').replace('\\3', lien['texte']['nom'].replace(' ', '_'))
                    texte_lie = texte_lie[:span[0]] + '<a href="' + href + '">' + texte_lie[span[0]:span[1]] + '</a>' + texte_lie[span[1]:]
            texte = texte[:index[0]+translation] + texte_lie + texte[index[1]+translation:]
            translation += len(texte_lie) - index[1] + index[0]

    return '<div id="article_' + x.group(1) + '" class="article"><h3>Article ' + x.group(1) + '</h3>\n' + balance_html(texte) + '</div>\n\n'

def markdown2html(text, url1=None, url2=None):

    html = '\n' + text + '\n'

    # Typography
    html = re.sub(r'[  _]?;', ' ;', html)
    html = re.sub(r'[  _]?:', ' :', html)
    html = html.replace("'", '’')

    summary = '<div class="summary">'
    for x in re.finditer(r'(?<=\n)(#+) ([^\n]+)', html):
        if re.match(r'Article ', x.group(2)):
            #summary += '<p>' + ('&gt;'*len(x.group(1))) + ' <a href="#' + re.sub(' ', '_', x.group(2)) + '">' + x.group(2) + '</a></p>\n'
            pass
        else:
            summary += '<p>' + '<span style="visibility:hidden">' + ('&gt;'*(len(x.group(1))-1)) + '</span>&gt;' + ' <a href="#' + re.sub('[  ]', '_', x.group(2).replace('’', "'")) + '">' + x.group(2) + '</a></p>\n'
            #summary += '<p>' + ('&gt;'*len(x.group(1))) + ' ' + x.group(2) + '</p>\n'
    summary += '</div>'

    # Cleaning
    html = re.sub(r'<div[^/>]*/>', '', html)

    # Transform headers (titles and articles)
    html = re.sub(r'(?<=\n)(?:#+) Article ([^\n]+)\n((?:(?!#)[^\n]*\n*)*)', lambda x : metsenformelarticle(x, url1, url2), html)
    html = re.sub(r'(?<=\n)(#+) ([^\n]+)', lambda x: '<h2 class="h'+str(len(x.group(1)))+' hmod3r'+str((len(x.group(1))-1)%3)+'" id="'+re.sub('[  ]','_',x.group(2).replace('’', "'"))+'">'+x.group(2)+'</h2>', html)

    html = re.sub(r'(?<=\n)((?:- [^\n]+\n)+)', r'<ul>\n\1</ul>\n\n', html)
    html = re.sub(r'(?<=\n)- ([^\n]+)\n', r'<li>\1</li>\n', html)

    html = re.sub(r'(?<=\n\n)([^\n<][^\n]*)(?=\n\n)', r'<p>\1</p>', html)

    # Cleaning
    html = re.sub(r'</p>\n+<p>', r'</p>\n<p>', html)
    html = re.sub(r'\n{3,}', r'\n\n', html)

    html = html.strip()

    return summary + '\n' + html


def balance_html(html):

    div_in = len([m for m in re.finditer('<div[ >]', html)])
    div_out = len([m for m in re.finditer('</div>', html)])

    if div_in < div_out:
        html = ( '<div>' * (div_out-div_in) ) + html

    if div_in > div_out:
        html = html + ( '</div>' * (div_in-div_out) )

    return html


def html_page(texte, titre, date_consolidation = None, condensat = None):
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<title>""" + titre + """</title>
<link rel="stylesheet" type="text/css" href="https://archeo-lex.local/css/main.css">
</head>
<body>
<div id="texte" class="centre">

<!--<div style="text-align: center; border: 2px dashed #323232; margin-top: 1em;">
Cette page est une maquette d’une partie tronquée du code de commerce, le but est d’obtenir la meilleure lisibilité du texte.<br />Viendront ensuite des développements pour mettre en production sur l’entièreté des textes.
</div>-->

<h1>""" + titre + """</h1>

""" + ( """<div class="soustitre">""" + date_consolidation + """ <span class="version">(version """ + condensat + """)</span></div>

""" if date_consolidation and condensat else '' ) + texte + """

</div>
</body>
</html>
"""


def get_history(ref):

    global basename, cache

    if 'gitrefs' not in cache:
        cache['gitrefs'] = str(subprocess.check_output(['git', 'show-ref'], cwd=basename), 'utf-8').strip()

    if 'history_' + ref + '/texte' not in cache:
        cache['history_' + ref + '/texte'] = []
        if re.search(r'^([0-9a-f]+) ' + re.escape(ref) + '/texte$', cache['gitrefs'], re.M):
            history = str(subprocess.check_output(['git', 'log', '--pretty=%H %s', ref+'/texte'], cwd=basename), 'utf-8')
            for x in re.finditer(r'^([0-9a-f]+) Version consolidée au ([0-9]+)(?:er)? ([a-zéû]+) ([0-9]+)$', history, flags=re.M):
                cache['history_' + ref + '/texte'].append((x.group(4) + mois[x.group(3)] + ('0' if len(x.group(2)) == 1 else '') + x.group(2), x.group(1)))

    if 'history_' + ref + '/texte-futur' not in cache:
        cache['history_' + ref + '/texte-futur'] = []
        if re.search(r'^([0-9a-f]+) ' + re.escape(ref) + '/texte-futur$', cache['gitrefs'], re.M):
            if cache['history_' + ref + '/texte']:
                history = str(subprocess.check_output(['git', 'log', '--pretty=%H %s', ref+'/texte..'+ref+'/texte-futur'], cwd=basename), 'utf-8')
            else:
                history = str(subprocess.check_output(['git', 'log', '--pretty=%H %s', ref+'/texte-futur'], cwd=basename), 'utf-8')
            for x in re.finditer(r'^([0-9a-f]+) Version consolidée au ([0-9]+)(?:er)? ([a-zéû]+) ([0-9]+)$', history, flags=re.M):
                cache['history_' + ref + '/texte-futur'].append((x.group(4) + mois[x.group(3)] + ('0' if len(x.group(2)) == 1 else '') + x.group(2), x.group(1)))

    return (cache['history_' + ref + '/texte'], cache['history_' + ref + '/texte-futur'])


class ArcheoLexHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    server_version = "ArcheoLexHTTP/0.1"

    def do_GET(self):

        global basename, mois, mois2, cache

        uri = str( bytes( [ord(c.group()) if len(c.group()) == 1 else int( c.group(1), 16 ) for c in re.finditer(r'%([0-9a-fA-F]{2})|.', self.path)] ), 'utf-8' )

        status = 200
        error404 = None
        html = ''

        if uri.startswith('/eli/'):
            regex_eli = re.match(r'^/eli/([a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ_-]+)/([^/]+)(/(jo|lc))?(/(texte|article_[a-z0-9._-]+))?(/([0-9]{4}-?[0-9]{2}-?[0-9]{2}|indéterminé))?(?:[?#].*)?$', uri, re.I)

            # Affichage du texte
            if regex_eli and regex_eli.group(1) in ['code'] and regex_eli.group(4) == 'lc':
                eli_type = regex_eli.group(1)
                eli_domain = regex_eli.group(2).replace('’', "'")
                eli_version = regex_eli.group(4)
                eli_level = regex_eli.group(6)
                eli_point_in_time = regex_eli.group(8).replace('-', '') if regex_eli.group(8) else None
                eli_point_in_time = 'indéterminé' if eli_point_in_time == '22220222' else eli_point_in_time

                titre = eli_domain[0].upper() + eli_domain[1:].replace('_', ' ')
                vigueur_future = False

                if 'gitrefs' not in cache:
                    cache['gitrefs'] = str(subprocess.check_output(['git', 'show-ref'], cwd=basename), 'utf-8').strip()
                ref = 'refs/'+eli_type+'s/'+eli_domain
                h = None
                href = re.search(r'^([0-9a-f]+) ' + re.escape(ref) + '/texte$', cache['gitrefs'], re.M)
                hreff = re.search(r'^([0-9a-f]+) ' + re.escape(ref) + '/texte-futur$', cache['gitrefs'], re.M)
                if not href and not hreff:
                    error404 = 'Code inexistant'
                elif eli_point_in_time:
                    history = get_history(ref)
                    if history[0]:
                        for s in history[0]:
                            if eli_point_in_time >= s[0]:
                                h = s[1]
                                break
                    if history[1]:
                        for s in history[1]:
                            if (s[0] != '22220222' and eli_point_in_time >= s[0]) or (s[0] == '22220222' and eli_point_in_time == 'indéterminé'):
                                h = s[1]
                                vigueur_future = True
                                break
                    if not h:
                        error404 = 'Date antérieure à la création du texte'
                else:
                    h = href.group(1) if href else hreff.group(1)
                    vigueur_future = False if href else True
                if h:
                    commit_object = str(subprocess.check_output(['git', 'cat-file', '-p', h], cwd=basename), 'utf-8')
                    tree_sha1 = re.search(r'^tree ([0-9a-f]+)$', commit_object, re.M)
                    message_commit = re.search('\n\n(.*)$', commit_object, re.M)
                    date_consolidation = 'Version consolidée à une date future indéterminée' if eli_point_in_time == 'indéterminé' else message_commit.group().strip()
                    tree_object = str(subprocess.check_output(['git', 'cat-file', '-p', tree_sha1.group(1)], cwd=basename), 'utf-8')
                    nom = eli_domain
                    nom = re.sub( '"', r'\"', ''.join( [ chr(c) if c < 128 else '\\%o' % c for c in bytes(re.sub(r'\\', r'\\\\', nom), 'utf-8') ] ) )
                    nom = '"' + nom + '.md"' if '\\' in nom else nom + '.md'
                    blob_sha1 = re.search('^100644 blob ([0-9a-f]+)\t'+re.escape(nom)+'$', tree_object, re.M)
                    texte = str(subprocess.check_output(['git', 'cat-file', '-p', blob_sha1.group(1)], cwd=basename), 'utf-8')

                    if eli_level and eli_level.startswith('article_'):
                        numero = eli_level[8:]
                        t = re.search(r'^#+ Article '+numero+'\n((?:(?!#)[^\n]*\n*)*)', texte, re.M)
                        if t:
                            texte = t.group()
                        else:
                            error404 = 'Article inexistant'

                    if not error404:
                        url_eli1 = '/eli/'+eli_type+'/'+eli_domain+('/'+eli_version if eli_version else '')+'/\\1'+('/'+eli_point_in_time if eli_point_in_time else '') if eli_version and eli_level and eli_level != 'texte' else None
                        url_eli2 = '/eli/\\2/\\3'+('/'+eli_version if eli_version else '')+'/\\1'+('/'+eli_point_in_time if eli_point_in_time else '')
                        html = html_page(markdown2html(texte, url_eli1, url_eli2), titre, date_consolidation, href.group(1)[:7])

            # Affichage de la liste des versions
            elif regex_eli and regex_eli.group(1) in ['code'] and not regex_eli.group(4) and not regex_eli.group(6) and not regex_eli.group(8):
                eli_type = regex_eli.group(1)
                eli_domain = regex_eli.group(2)

                titre = eli_domain[0].upper() + eli_domain[1:].replace('_', ' ')

                if 'gitrefs' not in cache:
                    cache['gitrefs'] = str(subprocess.check_output(['git', 'show-ref'], cwd=basename), 'utf-8').strip()
                ref = 'refs/'+eli_type+'s/'+eli_domain
                href = re.search(r'^([0-9a-f]+) ' + re.escape(ref) + '/texte$', cache['gitrefs'], re.M)
                hreff = re.search(r'^([0-9a-f]+) ' + re.escape(ref) + '/texte-futur$', cache['gitrefs'], re.M)
                if not href and not hreff:
                    error404 = 'Code inexistant'
                else:
                    history = get_history(ref)
                    if history[0] or history[1]:
                        html += '<ul>\n'
                    if history[1]:
                        for l in history[1]:
                            lien = 'indéterminé' if l[0] == '22220222' else l[0]
                            date = 'date indéterminée' if l[0] == '22220222' else ( l[0][6:8] if l[0][6] != '0' else l[0][7:8] ) + ('er' if l[0][6:8] == '01' else '') + ' ' + mois2[l[0][4:6]] + ' ' + l[0][0:4]
                            html += '<li><a href="/diff' + uri + '/lc/texte/' + lien + '">' + date + '</a> (<a href="' + uri + '/lc/texte/' + lien + '">texte</a>) <i>(version future prévue)</i></li>\n'
                    if history[0]:
                        for l in history[0]:
                            date = ( l[0][6:8] if l[0][6] != '0' else l[0][7:8] ) + ('er' if l[0][6:8] == '01' else '') + ' ' + mois2[l[0][4:6]] + ' ' + l[0][0:4]
                            html += '<li><a href="/diff' + uri + '/lc/texte/' + l[0] + '">' + date + '</a> (<a href="' + uri + '/lc/texte/' + l[0] + '">texte</a>)</li>\n'
                    if history[0] or history[1]:
                        html += '<ul>\n'
                    html = html_page(html, titre)

            else:
                status = 400
                html = 'Erreur de format d’URL'

        elif uri.startswith('/diff/eli/'):
            regex_eli = re.match(r'^/diff/eli/([a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ_-]+)/([^/]+)(/(jo|lc))?(/(texte|article_[a-z0-9._-]+))?(/([0-9]{4}-?[0-9]{2}-?[0-9]{2}|indéterminé))?(?:[?#].*)?$', uri, re.I)
            if regex_eli and regex_eli.group(1) in ['code']:
                eli_type = regex_eli.group(1)
                eli_domain = regex_eli.group(2).replace('’', "'")
                eli_version = regex_eli.group(4)
                eli_level = regex_eli.group(6)
                eli_point_in_time = regex_eli.group(8).replace('-', '') if regex_eli.group(8) else None
                eli_point_in_time = 'indéterminé' if eli_point_in_time == '22220222' else eli_point_in_time

                if 'gitrefs' not in cache:
                    cache['gitrefs'] = str(subprocess.check_output(['git', 'show-ref'], cwd=basename), 'utf-8').strip()
                ref = 'refs/'+eli_type+'s/'+eli_domain
                h = None
                href = re.search(r'^([0-9a-f]+) ' + re.escape(ref) + '/texte$', cache['gitrefs'], re.M)
                hreff = re.search(r'^([0-9a-f]+) ' + re.escape(ref) + '/texte-futur$', cache['gitrefs'], re.M)
                if not href and not hreff:
                    error404 = 'Code inexistant'
                elif eli_point_in_time:
                    history = get_history(ref)
                    if history[0]:
                        for s in history[0]:
                            if eli_point_in_time >= s[0]:
                                h = s[1]
                                break
                    if history[1]:
                        for s in history[1]:
                            if (s[0] != '22220222' and eli_point_in_time >= s[0]) or (s[0] == '22220222' and eli_point_in_time == 'indéterminé'):
                                h = s[1]
                                vigueur_future = True
                                break
                    if not h:
                        error404 = 'Date antérieure à la création du texte'
                else:
                    h = href.group(1) if href else hreff.group(1)
                    vigueur_future = False if href else True
                if h:
                    diff = str(subprocess.check_output(['git', 'show', h], cwd=basename), 'utf-8').strip()
                    diff = re.sub('\n', '<br />', diff)
                    html += diff

        elif re.match('^/($|[?#])', uri):
            if 'gitrefs' not in cache:
                cache['gitrefs'] = str(subprocess.check_output(['git', 'show-ref'], cwd=basename), 'utf-8').strip()
            codes = {}
            for x in re.finditer('^([0-9a-f]+) refs/codes/([^/]+)/texte(-futur)?$', cache['gitrefs'], flags=re.M):
                if x.group(2) not in codes:
                    codes[x.group(2)] = [None, None]
                if x.group(3):
                    codes[x.group(2)][0] = x.group(1)
                else:
                    codes[x.group(2)][1] = x.group(1)
            lcodes = list(codes.keys())
            lcodes.sort()
            html += '<p>' + str(len(codes)) + ' codes</p>'
            html += '<ul>'
            for code in lcodes:
                html += '<li><a href="/eli/code/' + code + '">' + code[0].upper() + code[1:].replace('_', ' ') + '</a></li>\n'
            html += '</ul>'

        elif re.match('^/(css|js)/([^.]+\.(?:css|js|otf))$', uri) and os.path.isfile( uri[1:] ):
            with open(uri[1:], 'rb') as f:
                bcontent = f.read()
            self.send_response(status)
            if uri.endswith('.css'):
                self.send_header('Content-Type', 'text/css')
            elif uri.endswith('.js'):
                self.send_header('Content-Type', 'text/javascript')
            elif uri.endswith('.otf'):
                self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', len(bcontent))
            self.end_headers()
            self.wfile.write(bcontent)
            return

        else:
            status = 400
            html = 'Erreur de format d’URL'

        if error404:
            error404 = '<div class="error">' + error404 + '</div>'
            html = html_page(error404, titre)
            status = 404
        elif status != 200:
            html = html_page(html, html)

        bhtml = bytes(html, 'utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(bhtml))
        self.end_headers()
        self.wfile.write(bhtml)


if __name__ == "__main__":

    httpd = http.server.HTTPServer(('127.0.0.1', 8081), ArcheoLexHTTPRequestHandler)
    sa = httpd.socket.getsockname()
    t = time.time()
    print("***", time.strftime('[%d/%b/%Y %H:%M:%S')+('%.5f]'%(t-int(t)))[1:], "***", "Serving HTTP on", sa[0], "port", sa[1], "...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
        httpd.server_close()
        sys.exit(0)

# vim: set ts=4 sw=4 sts=4 et:

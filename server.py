# coding: utf-8

import http.server
import collections
import subprocess
import argparse
import functools
import time
import sys
import os
import re

import diff_match_patch
import metslesliens

basename = None

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

def get_summary(text):

    """
    Obtain the summary in a Markdown text.

    :param text:
        (str) 
    """

    summary = collections.OrderedDict()
    parents = [summary]
    titles = []
    articles = collections.OrderedDict()
    for x in re.finditer(r'(?<=\n)(#+) ([^\n]+)', '\n' + text):
        level = len(x.group(1))
        title = x.group(2)
        if title.startswith('Article '):
            parents[-1][title] = None
            articles[title[8:]] = titles
        else:
            if level < len(parents):
                parents = parents[:level]
                titles = titles[:level-1]
            parents[-1][title] = collections.OrderedDict()
            parents.append(parents[-1][title])
            titles.append(title)

    return summary, articles

def print_summary(summary, i=0):

    for x in summary:
        print((' '*i) + '>' + x)
        if summary[x] is not None:
            print_summary(summary[x], i+1)


def metsenformelarticle(x, mode='all', url1=None, url2=None):

    if mode == 'all':
        texte = x.group(2)
    elif mode == 'article':
        texte = x

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
                    if nom_article in ['présent', 'précédent', 'suivant']:
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
                    href = url2.replace('\\2', 'code').replace('\\3', lien['texte']['nom'].replace(' ', '_'))
                    href = href.replace('\\1', 'article_' + destination_article) if url1 else href.replace('\\1', 'texte') + '#' + 'article_' + destination_article
                    texte_lie = texte_lie[:span[0]] + '<a href="' + href + '">' + texte_lie[span[0]:span[1]] + '</a>' + texte_lie[span[1]:]
            texte = texte[:index[0]+translation] + texte_lie + texte[index[1]+translation:]
            translation += len(texte_lie) - index[1] + index[0]

    if mode == 'all':
        return '<div id="article_' + x.group(1) + '" class="article"><h3>Article ' + x.group(1) + '</h3>\n' + balance_html(texte) + '</div>\n\n'
    elif mode == 'article':
        return balance_html(texte)

def repl_p(x):

    text = '<p><span>' + x.group(1) + '</span></p>\n'

    text = text.replace('<ins>', '</span><ins>')
    text = text.replace('<del>', '</span><del>')
    text = text.replace('</ins>', '</ins><span>')
    text = text.replace('</del>', '</del><span>')

    return text

def repl_insdel(x, tag):

    return re.sub('</span></p>\n*<p><span>', '</' + tag + '></p>\n<p><' + tag + '>', x.group())


def markdown2html(text, mode='all', url1=None, url2=None):

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

    # Transform articles
    if mode == 'all':
        html = re.sub(r'(?<=\n)(?:#+) Article ([^\n]+)\n((?:(?!#)[^\n]*\n*)*)', lambda x : metsenformelarticle(x, 'all', url1, url2), html)
    elif mode == 'article':
        html = metsenformelarticle(html, 'article', url1, url2)

    # Transform headers
    html = re.sub(r'(?<=\n)(#+) ([^\n]+)', lambda x: '<h2 class="h'+str(len(x.group(1)))+' hmod3r'+str((len(x.group(1))-1)%3)+'" id="'+re.sub('[  ]','_',x.group(2).replace('’', "'"))+'">'+x.group(2)+'</h2>', html)

    html = re.sub(r'(?<=\n)((?:- [^\n]+\n)+)', r'<ul>\n\1</ul>\n\n', html)
    html = re.sub(r'(?<=\n)- ([^\n]+)\n', r'<li>\1</li>\n', html)

    html = re.sub(r'(?<=\n\n)([^\n][^\n]*)(?=\n\n)', repl_p, '\n\n' + html+'\n\n').strip()
    html = '<p><span>' + html + '</span></p>'
    html = html.replace('<span></span>', '')
    html = html.replace('<del></del>', '')
    html = html.replace('<ins></ins>', '')

    html = re.sub(r'<ins>((?!</ins>)<?[^<]*)*', lambda x: repl_insdel(x, 'ins'), html, flags=re.S)
    html = re.sub(r'<del>((?!</del>)<?[^<]*)*', lambda x: repl_insdel(x, 'del'), html, flags=re.S)

    html = re.sub(r'<p><del>((?:(?!/del>)(?!/ins>)[^<]*<)*)/del></p>', r'<p class="delete">\1/p>', html)
    html = re.sub(r'<p><ins>((?:(?!/ins>)(?!/del>)[^<]*<)*)/ins></p>', r'<p class="insert">\1/p>', html)

    # Cleaning
    html = re.sub(r'</p>\n+<p(?=[> ])', r'</p>\n<p', html)
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


def get_commit(h):

    global basename

    commit_object = str(subprocess.check_output(['git', 'cat-file', '-p', h], cwd=basename), 'utf-8')
    tree_sha1 = re.search(r'^tree ([0-9a-f]+)$', commit_object, re.M)
    message_commit = re.search('\n\n(.*)$', commit_object, re.M)
    date_consolidation = message_commit.group().strip()
    if date_consolidation == 'Version consolidée au 22 février 2222':
        date_consolidation = 'Version consolidée à une date future indéterminée'
    tree_object = str(subprocess.check_output(['git', 'cat-file', '-p', tree_sha1.group(1)], cwd=basename), 'utf-8')
    blob_sha1 = re.search('^100644 blob ([0-9a-f]+)\t[^\n]+$', tree_object, re.M)
    texte = str(subprocess.check_output(['git', 'cat-file', '-p', blob_sha1.group(1)], cwd=basename), 'utf-8')

    return texte, date_consolidation


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


def cmp_articles(a, b):

    if a == b:
        return 0
    elif a[0] in ['equal', 'replace', 'delete'] and b[0] in ['equal', 'replace', 'delete']:
        return -1 if a[1] < b[1] else 1
    elif a[0] in ['equal', 'replace', 'insert'] and b[0] in ['equal', 'replace', 'insert']:
        return -1 if a[2] < b[2] else 1
    else:
        return -1 if a[0] == 'delete' and b[0] == 'insert' else 1


def diff_articles(text_a, text_b):

    articles_a = {x.start(): x.group(1) for x in re.finditer(r'^#+ Article ([^\n]+\n(?:(?!#)[^\n]*\n*)*)', text_a, re.M)}
    articles_b = {x.start(): x.group(1) for x in re.finditer(r'^#+ Article ([^\n]+\n(?:(?!#)[^\n]*\n*)*)', text_b, re.M)}

    articles_a_inv = {articles_a[x]: x for x in articles_a}
    articles_b_set = set(articles_b.values())

    articles = {}
    for offset in articles_a:
        if articles_a[offset] in articles_b_set:
            continue
        title = re.match('[^\n]+', articles_a[offset]).group()
        articles[title] = ('delete', offset, None, 'Article ' + articles_a[offset], '')

    for offset in articles_b:
        if articles_b[offset] in articles_a_inv:
            title = re.match('[^\n]+', articles_b[offset]).group()
            articles[title] = ('equal', articles_a_inv[articles_b[offset]], offset, 'Article ' + articles_b[offset], 'Article ' + articles_b[offset])
        else:
            title = re.match('[^\n]+', articles_b[offset]).group()
            if title in articles:
                articles[title] = ('replace', articles[title][1], offset, articles[title][3], 'Article ' + articles_b[offset])
            else:
                articles[title] = ('insert', None, offset, '', 'Article ' + articles_b[offset])

    articles = sorted(articles.values(), key=functools.cmp_to_key(cmp_articles))

    return articles

def html_diff(articles, url1=None, url2=None, articlessummary_a=None, articlessummary_b=None):

    dmp = diff_match_patch.diff_match_patch()
    parents_a = []
    parents_b = []
    html = '<div class="diff">'
    for article in articles:

        title = re.match('Article [^\n]*', article[3]).group() if article[3] else re.match('Article [^\n]*', article[4]).group()
        number = title[8:]

        if article[0] in ['delete', 'insert', 'replace']:
            if number in articlessummary_a or number in articlessummary_b:
                m_a = len(articlessummary_a[number]) if number in articlessummary_a else 0
                m_b = len(articlessummary_b[number]) if number in articlessummary_b else 0
                max_ab = max(m_a, m_b)
                for i in range(0, max_ab):
                    if i < m_a:
                        if articlessummary_a[number][i] not in parents_a:
                            html += '<h3>' + articlessummary_a[number][i] + '</h3>'
                    elif i < m_b:
                        if articlessummary_b[number][i] not in parents_b:
                            html += '<h3>' + articlessummary_b[number][i] + '</h3>'
                if number in articlessummary_a:
                    parents_a = articlessummary_a[number]
                if number in articlessummary_b:
                    parents_b = articlessummary_b[number]

        if article[0] == 'delete':

            html += '<div class="article delete"><h3>' + title + '</h3>' + markdown2html(article[3][len(title):].strip(), 'article', url1, url2) + '</div>'

        elif article[0] == 'insert':

            html += '<div class="article insert"><h3>' + title + '</h3>' + markdown2html(article[4][len(title):].strip(), 'article', url1, url2) + '</div>'

        elif article[0] == 'replace':

            diff = dmp.diff_main(article[3][len(title):].strip(), article[4][len(title):].strip())
            dmp.diff_cleanupSemantic(diff)
            j = 0
            for i in range(0, len(diff)):
                if i+j+1 < len(diff) and diff[i+j][0] == diff[i+j+1][0]:
                    diff[i+j] = (diff[i+j][0], diff[i+j][1] + diff[i+j+1][1])
                    del diff[i+j+1]
                    j -= 1

                if i+j+2 < len(diff) and diff[i+j][0] == 0 and diff[i+j+1][0] == -1 and diff[i+j+2][0] == 1 and len(diff[i+j][1]) and len(diff[i+j+2][1]) and len(diff[i+j+2][1]):
                    if re.match('^[a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ0-9\']{2}$', diff[i+j][1][-1] + diff[i+j+1][1][0], re.I) and re.match('^[a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ0-9\']{2}$', diff[i+j][1][-1] + diff[i+j+2][1][0], re.I):
                        common_word = re.search('[a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ0-9\']+$', diff[i+j][1], re.I)
                        diff[i+j] = (0, diff[i+j][1][:-len(common_word.group())])
                        diff[i+j+1] = (-1, common_word.group() + diff[i+j+1][1])
                        diff[i+j+2] = (1, common_word.group() + diff[i+j+2][1])
                    if not len(diff[i+j][1]):
                        del diff[i+j]
                        j -= 1
                    elif len(diff[i+j][1]) < 3 and '\n' not in diff[i+j][1]:
                        common_word = diff[i+j][1]
                        diff[i+j+1] = (-1, common_word + diff[i+j+1][1])
                        diff[i+j+2] = (1, common_word + diff[i+j+2][1])
                        del diff[i+j]
                        j -= 1

                if i+j+2 < len(diff) and diff[i+j][0] == -1 and diff[i+j+1][0] == 1 and diff[i+j+2][0] == 0 and len(diff[i+j][1]) and len(diff[i+j+2][1]) and len(diff[i+j+2][1]):
                    if re.match('^[a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ0-9\']{2}$', diff[i+j][1][-1] + diff[i+j+2][1][0], re.I) and re.match('^[a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ0-9\']{2}$', diff[i+j+1][1][-1] + diff[i+j+2][1][0], re.I):
                        common_word = re.match('^[a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ0-9\']+', diff[i+j+2][1], re.I)
                        diff[i+j] = (-1, diff[i+j][1] + common_word.group())
                        diff[i+j+1] = (1, diff[i+j+1][1] + common_word.group())
                        diff[i+j+2] = (0, diff[i+j+2][1][len(common_word.group()):])
                    if not len(diff[i+j+2][1]):
                        del diff[i+j+2]
                        j -= 1
                    elif len(diff[i+j+2][1]) < 3 and '\n' not in diff[i+j+2][1]:
                        common_word = diff[i+j+2][1]
                        diff[i+j] = (-1, diff[i+j][1] + common_word)
                        diff[i+j+1] = (1, diff[i+j+1][1] + common_word)
                        del diff[i+j+2]
                        j -= 1
            for i in range(0, len(diff)):
                if i+2 < len(diff) and diff[i][0] != 0 and diff[i+1][0] != 0 and diff[i][0] == diff[i+2][0]:
                    diff[i] = (diff[i][0], diff[i][1] + diff[i+2][1])
                    del diff[i+2]
            htmld = []
            for (op, data) in diff:
                text = (data.replace("&", "&amp;").replace("<", "&lt;")
                           .replace(">", "&gt;"))
                if op == dmp.DIFF_INSERT:
                    htmld.append("<ins>%s</ins>" % text)
                elif op == dmp.DIFF_DELETE:
                    htmld.append("<del>%s</del>" % text)
                elif op == dmp.DIFF_EQUAL:
                    htmld.append(text)
            html += '<div class="article replace"><h3>' + title + '</h3>' + markdown2html(''.join(htmld), 'article', url1, url2) + '</div>'

    html += '</div>'
    return html


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
                    texte, date_consolidation = get_commit(h)
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
                        html = html_page(markdown2html(texte, 'all', url_eli1, url_eli2), titre, date_consolidation, href.group(1)[:7])

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

                titre = eli_domain[0].upper() + eli_domain[1:].replace('_', ' ')

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
                    diff = str(subprocess.check_output(['git', 'show', '--pretty=raw', h], cwd=basename), 'utf-8').strip()
                    date_consolidation = re.search('\n\n *Version consolidée au [^\n]*\n\n', diff)
                    diff = re.search('\n\ndiff --git[^\n]*\n(?:new file[^\n]*\n)?index [^\n]*\n--- [^\n]*\n\+\+\+[^\n]*\n(.*)', diff, re.DOTALL)
                    diff = diff.group(1)
                    #diffstruct = [(x[0], x[1:]) for x in diff.splitlines() if x[0] in '+- ']
                    #diff = '<br />'.join([x[1] for x in diffstruct])
                    diff = diff.replace('\n', '<br />')
                    #html = html_page(diff, titre, date_consolidation.group().strip(), h[:7])
                    try:
                        articles_a, date_a = get_commit(h+'~1')
                    except subprocess.CalledProcessError:
                        articles_a, date_a = '', None
                    articles_b, date_b = get_commit(h)
                    articles_diff = diff_articles(articles_a, articles_b)
                    summary_a, articlessummary_a = get_summary(articles_a)
                    summary_b, articlessummary_b = get_summary(articles_b)
                    url_eli1 = '/eli/'+eli_type+'/'+eli_domain+('/'+eli_version if eli_version else '')+'/\\1'+('/'+eli_point_in_time if eli_point_in_time else '')
                    url_eli2 = '/eli/\\2/\\3'+('/'+eli_version if eli_version else '')+'/\\1'+('/'+eli_point_in_time if eli_point_in_time else '')
                    articles_diff_html = html_diff(articles_diff, url_eli1, url_eli2, articlessummary_a, articlessummary_b)
                    html = html_page(articles_diff_html, titre, date_consolidation.group().strip(), h[:7])

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

        elif re.match('^/(?:(?:css|js)/([^.]+\.(?:css|js|otf))|favicon\.ico)$', uri):
            status = 404
            bcontent = b''
            if os.path.isfile(uri[1:]):
                with open(uri[1:], 'rb') as f:
                    bcontent = f.read()
                    status = 200
            self.send_response(status)
            if uri.endswith('.css'):
                self.send_header('Content-Type', 'text/css')
            elif uri.endswith('.js'):
                self.send_header('Content-Type', 'application/javascript')
            elif uri.endswith('.otf'):
                self.send_header('Content-Type', 'application/octet-stream')
            elif uri.endswith('.ico'):
                self.send_header('Content-Type', 'image/vnd.microsoft.icon')
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

    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', help='Path where is located the meta-repo codes containing all codes', required=True)
    parser.add_argument('--listen', help='Binding IP', default='127.0.0.1')
    parser.add_argument('--port', help='Binding port', type=int, default=8081)
    args = parser.parse_args()
    basename = args.repo
    httpd = http.server.HTTPServer((args.listen, args.port), ArcheoLexHTTPRequestHandler)
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

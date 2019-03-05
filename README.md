Interface du site archeo-lex.fr
===============================

[Archeo-Lex.fr](https://archeo-lex.fr/next) a pour objectif de présenter les codes français (et bientôt également les lois) dans une interface à la fois simple et puissante :

* Simple et épurée pour faciliter le plus possible l’accès aux lois et la navigation dans le corpus juridique français,
* Puissante en permettant la recherche dans l’histoire des lois.

Le site Archeo-Lex.fr s’appuie de façon sous-jacente sur [Archéo Lex](https://github.com/Legilibre/Archeo-Lex) qui crée des dépôts Git des codes français, permettant d’utiliser des outils encore plus puissants pour analyser l’histoire des lois.

Ce dépôt Git est le futur site archeo-lex.fr ayant notamment les fonctionnalités suivantes en plus de l’actuel/l’ancien :

* les adresses sont entièrement basées sur [le standard ELI](http://www.eli.fr/fr/) – un peu augmenté puisqu’il ne prévoit pas de notation pour les codes ;
* meilleur confort de lecture (nous l’espérons) ;
* des liens internes sont disponibles entre les différents codes ;
* une table des matières est disponible lors de l’affichage du code entier ;
* l’affichage d’un seul article est possible, par exemple [/eli/code/code\_civil/lc/article\_1](https://archeo-lex.fr/next/eli/code/code_civil/lc/article_1).

Encore à améliorer :

* la liste des codes ;
* créer une page de recherche qui servira pour les lois ;
* améliorer le rendu des diffs (le site actuel/ancien est probablement meilleur sur les écrans "diff mot-à-mot" que j’avais particulièrement travaillé, il faut réécrire ces algorithmes depuis PHP vers Python ou JavaScript) ;
* probablement affiner le graphisme en fonction d’opinions plus expertes que moi et de retours utilisateurs ;
* ajouter un tutorial/aide.

L’actuel/ancien site était basé sur GitList, son fork est dans le dépôt [Archeo-Lex-web](https://github.com/Legilibre/Archeo-Lex-web). Quoique cette nouvelle maquette est écrite en Python, j’ai pour projet de le réécrire en [Sapper](https://sapper.svelte.technology), en conservant un graphisme et des fonctionnalités similaires.


### Avertissements

Les dépôts Git résultats de ce programme n’ont en aucune manière un caractère officiel et n’ont reçu aucune reconnaissance de quelque sorte que ce soit d’une instance officielle. Il n’ont d’autre portée qu’informative et d’exemple. Pour les versions d’autorité, se référer au Journal officiel de la République française.

### Licence

Ce programme est sous licence [WTFPL 2.0](http://www.wtfpl.net) avec clause de non-garantie. Voir le fichier COPYING pour les détails.

### Contact

Sébastien Beyou ([courriel](https://www.seb35.fr/contact)) ([site](http://blog.seb35.fr))

### Liens

* [Légifrance](http://legifrance.gouv.fr), service officiel de publication de l’information légale française sur l’internet
* [La Fabrique de la Loi](http://www.lafabriquedelaloi.fr), visualisation de l’évolution des projets de lois, comportant également un dépôt Git des projets de lois
* [Direction de l’information légale et administrative (DILA)](http://www.dila.premier-ministre.gouv.fr), direction responsable de la publication du JO et assurant la diffusion de l’information légale
* [Téléchargement des bases de données d’information légale française](http://rip.journal-officiel.gouv.fr/index.php/pages/juridiques)
* [Dépôt Git d’Archéo Lex](https://github.com/Seb35/Archeo-Lex)
* [Dépôt Git d’exemple avec le Code de la propriété intellectuelle](https://github.com/Seb35/CPI)
* [Billet de blog introductif](http://blog.seb35.fr/billet/Archéo-Lex,-Pure-Histoire-de-la-Loi-française,-pour-étudier-son-évolution)

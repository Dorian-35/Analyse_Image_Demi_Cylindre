# Mesure de la période d'oscillation d'un demi-cylindre par analyse vidéo

Ce programme mesure la **période d'oscillation** d'un demi-cylindre qui oscille sur un plan à partir d'une vidéo de l'expérience. La période est obtenue **directement à partir des images** : on repère les instants où l'objet atteint ses positions extrêmes, puis on mesure le temps qui sépare deux extrêmes identiques. Aucun modèle théorique n'est ajusté aux données.

Le programme peut s'utiliser de deux façons :
- avec une **interface graphique** (boutons, curseurs, aperçu en direct) ;
- **en ligne de commande** (terminal ou Jupyter).

---

## Sommaire

1. [Fichiers](#1-fichiers)
2. [Installation](#2-installation)
3. [Utilisation avec l'interface graphique](#3-utilisation-avec-linterface-graphique)
4. [Utilisation sans interface (ligne de commande)](#4-utilisation-sans-interface-ligne-de-commande)
5. [Principe de fonctionnement](#5-principe-de-fonctionnement)
6. [Limites et précautions](#6-limites-et-précautions)
7. [Conseils de tournage](#7-conseils-de-tournage)

---

## 1. Fichiers

| Fichier | Rôle |
|---|---|
| `analyse_image.py` | Le cœur du programme : suivi de l'objet et calcul de la période. Il s'utilise seul en ligne de commande. |
| `interface_oscillation.py` | L'interface graphique. Elle **réutilise** `analyse_image.py`, donc les deux fichiers doivent être dans le **même dossier**. |

---

## 2. Installation

Il faut Python 3.8 ou une version plus récente, ainsi que trois bibliothèques :

```bash
pip install opencv-python numpy scipy
```

L'interface graphique utilise **Tkinter**, qui est fourni avec Python sous Windows et macOS. Sous Linux, il faut parfois l'installer : `sudo apt install python3-tk`.

> L'interface graphique et les fenêtres de sélection ont besoin d'un écran. Elles **ne fonctionnent pas** dans un Jupyter en ligne comme Google Colab. Dans ce cas, utilisez la ligne de commande avec les options `--roi` et `--sans-affichage` (voir § 4).

---

## 3. Utilisation avec l'interface graphique

### Lancement

```bash
python interface_oscillation.py              # depuis un terminal
python interface_oscillation.py video_1.mp4  # ouvre directement une vidéo
```
Dans Jupyter :
```python
%run interface_oscillation.py
```

### Étapes

1. **Ouvrir une vidéo.** Si la vidéo a été filmée **au ralenti**, indiquez la vraie cadence de prise de vue dans « fps réels », par exemple 240 (voir § 6.4).
2. **1. Choisir la zone de travail.** Tracez à la souris un rectangle autour du demi-cylindre **et de tout l'espace où il bouge**. Il apparaît en bleu clair.
3. **2. Sélectionner le cylindre** (conseillé). Tracez un petit rectangle **entièrement à l'intérieur** du demi-cylindre. Il apparaît en jaune. Le programme retient la couleur de l'objet et ignore ensuite le fond et l'ombre.
4. **Vérifier.** Faites glisser le curseur « Image de la vidéo ». Le **contour vert** doit épouser le demi-cylindre et la **ligne rouge** doit rester parallèle à sa face plane, sur toute la vidéo.
5. **Ajuster si nécessaire** avec les curseurs du cadre « Réglages de l'image ». Cochez **« Voir l'image traitée »** pour afficher ce que voit le programme : en blanc, ce qu'il prend pour le demi-cylindre.
6. **Portion analysée** (facultatif). Les boutons « = image affichée » fixent le début ou la fin de l'analyse à l'image en cours. Ça permet par exemple de retirer le lâcher de l'objet.
7. **Démarrer.** La vidéo défile avec le suivi et la période s'affiche à la fin. Le bouton **Arrêter** interrompt l'analyse et calcule la période sur la partie déjà analysée.

La case **« Enregistrer la vidéo annotée »** crée un fichier `…_suivi.mp4` qui montre le temps, le contour et la ligne rouge.

Le menu **« ? »** (ou la touche **F1**) ouvre l'aide.

### Les réglages

| Curseur | Quand l'utiliser | Effet |
|---|---|---|
| Contraste | Image terne, objet peu distinct du fond | 1 = image inchangée, 2 = deux fois plus contrastée |
| Luminosité | Image trop sombre ou trop claire | 0 = inchangée |
| Seuil (0 = auto) | **Sans** sélection du cylindre | Niveau de gris qui sépare l'objet du fond. 0 = choix automatique |
| Tolérance couleur | **Avec** sélection du cylindre | Écart de couleur accepté. S'il manque des morceaux de l'objet, augmentez. Si l'ombre ou le fond sont pris, diminuez. |

---

## 4. Utilisation sans interface (ligne de commande)

### Lancement

```bash
python analyse_image.py video_1.mp4
```
Dans Jupyter :
```python
%run analyse_image.py video_1.mp4
```

> Ne tapez pas `python analyse_image.py ...` directement dans une cellule Jupyter : vous obtiendrez une `SyntaxError`. Utilisez `%run` ou `!python`.

Le programme ouvre la première image et vous demande de tracer la zone de travail (validez avec **Entrée**). La vidéo défile ensuite avec le suivi, puis la période s'affiche :

```
Périodes mesurées (s) :
  entre maxima : [0.853 0.853 0.844 ...]
  entre minima : [0.876 0.827 0.858 ...]

>>> Période T = 0.850 ± 0.003 s   (20 périodes mesurées, 60 images/s)
```

### Options

| Option | Rôle |
|---|---|
| `--reglage_selection` | Sélectionner le demi-cylindre en traçant un petit rectangle dessus. Sa couleur est retenue et l'ombre et le fond sont ignorés. |
| `--reglage` | Ouvre une fenêtre à curseurs (contraste, luminosité, seuil ou tolérance) avec l'image traitée à côté. Les valeurs choisies sont affichées pour être réutilisées. |
| `--contraste 1.5`, `--luminosite 20` | Réglage de l'image sans passer par les curseurs |
| `--seuil 80` | Seuil de gris fixe (0 = automatique) |
| `--tolerance 35` | Tolérance de couleur, avec `--reglage_selection` |
| `--debut 2 --fin 15` | Portion de la vidéo à analyser, en secondes |
| `--fps-reel 240` | Cadence réelle d'une vidéo au ralenti |
| `--enregistrer suivi.mp4` | Enregistre la vidéo annotée |
| `--sans-affichage` | N'affiche pas la vidéo pendant le suivi (plus rapide) |
| `--roi x,y,l,h` | Zone de travail donnée en pixels, sans la souris |
| `--zone_objet x,y,l,h` | Rectangle sur le cylindre donné en pixels, avec `--reglage_selection` |
| `--mode couleur --couleur rouge` | Suit une gommette de couleur plutôt que la forme. Couleurs possibles : rouge, vert, bleu, jaune, orange. |
| `--mode marqueur` | Suit un motif choisi à la souris, comme un trait de feutre |

### Exemples

```bash
# Cas courant : on sélectionne le cylindre, on vérifie les réglages
python analyse_image.py video_1.mp4 --reglage_selection --reglage

# Réutiliser les mêmes réglages sur une autre vidéo
python analyse_image.py video_2.mp4 --reglage_selection --tolerance 35

# Sans écran (Colab...) : tout est donné en pixels
python analyse_image.py video_1.mp4 --roi 150,200,400,215 \
       --reglage_selection --zone_objet 270,320,40,30 --sans-affichage
```

---

## 5. Principe de fonctionnement

Le programme ne « voit » pas le demi-cylindre comme nous. Pour lui, une vidéo est une suite d'images, et chaque image est un tableau de pixels. Il travaille en quatre étapes :

```
1. lire la vidéo            → une image toutes les 1/fps secondes
2. isoler le demi-cylindre  → une tache blanche sur fond noir
3. mesurer son inclinaison  → un angle θ par image
4. analyser θ(t)            → les instants des extrêmes → la période
```

### 5.1 Lire la vidéo et connaître le temps

La vidéo est lue image par image avec la bibliothèque **OpenCV**. Le temps n'est pas chronométré, il est **déduit du numéro de l'image** :

$$t = \frac{\text{numéro de l'image}}{\text{fps}}$$

Par exemple, à 60 images par seconde, l'image n° 30 correspond à t = 0,5 s, et deux images successives sont séparées de 1/60 s ≈ 16,7 ms.

C'est pour ça que la cadence doit être **juste**. Si elle est fausse, tous les temps et la période sont faux dans la même proportion (voir § 6.4 pour les vidéos au ralenti).

### 5.2 Isoler le demi-cylindre

Le programme doit d'abord décider, pour chaque pixel, s'il appartient au demi-cylindre ou non. Il fabrique ainsi une image en **noir et blanc**, appelée *masque* :
- **blanc** = demi-cylindre ;
- **noir** = tout le reste (fond, sol, ombre…).

C'est ce masque qu'on voit à droite dans « Voir l'image traitée ». Il y a deux façons de le construire.

**a) Par la couleur** (quand vous avez sélectionné le cylindre)
Le programme mesure la couleur moyenne du petit rectangle que vous avez tracé sur l'objet. Ensuite, sur chaque image, il garde en blanc tous les pixels dont la couleur est **proche** de celle-ci. Le curseur *Tolérance* fixe à partir de quand un pixel est jugé « trop différent ».
Une ombre grise ou un fond clair ont une couleur différente de l'objet, donc ils restent noirs.

> Les couleurs sont comparées dans un système appelé **Lab**, conçu pour que l'écart entre deux couleurs corresponde à peu près à la différence que perçoit notre œil. C'est plus fiable que de comparer directement le rouge, le vert et le bleu.

**b) Par le niveau de gris** (sans sélection)
L'image est passée en niveaux de gris (de 0 = noir à 255 = blanc). Tous les pixels plus sombres qu'un **seuil** sont gardés, ou plus clairs si l'objet est clair sur fond sombre. Si le seuil vaut 0, le programme le choisit seul avec la **méthode d'Otsu** : il cherche la valeur qui sépare le mieux les pixels « sombres » des pixels « clairs » de l'image.

**Nettoyage.** Le masque contient souvent quelques pixels blancs isolés dus au bruit de la caméra. Une opération de nettoyage les efface. Avec la sélection par couleur, une seconde opération bouche aussi les petits trous dans l'objet.
Enfin, s'il reste plusieurs taches blanches, le programme garde **la plus grande** : c'est le demi-cylindre. Son contour est le **contour vert** affiché sur la vidéo.

### 5.3 Mesurer l'inclinaison de la tache

À ce stade, le programme ne connaît qu'une **liste de pixels blancs**, chacun avec ses coordonnées (x, y). Il ne sait pas où est la face plane. Il doit déduire l'inclinaison de la tache seulement à partir de ces points.

#### Étape 1 : trouver le centre de la tache

On fait la **moyenne des positions** de tous les pixels blancs :

$$x_G = \text{moyenne des } x \qquad y_G = \text{moyenne des } y$$

C'est le **centre de gravité** de la forme, comme si chaque pixel était un petit grain de même masse. C'est le **point rouge** au milieu de la ligne rouge.

> En traitement d'image, on appelle ces sommes des **moments** :
> - m₀₀ = nombre de pixels blancs, c'est-à-dire l'aire de la tache ;
> - m₁₀ = somme des x, et m₀₁ = somme des y.
>
> Le centre vaut donc x_G = m₁₀ / m₀₀ et y_G = m₀₁ / m₀₀.

#### Étape 2 : trouver dans quelle direction la tache s'étale

Imaginez un crayon posé de travers sur une table. Si l'on regarde comment ses points sont répartis autour de son centre :
- **le long du crayon**, ils sont très étalés ;
- **en travers**, ils sont serrés.

La direction dans laquelle les points sont **le plus étalés** s'appelle l'**axe principal**. C'est elle qui indique l'inclinaison.

Pour la trouver, le programme calcule l'écart (dx, dy) de chaque pixel blanc au centre, puis trois nombres :

| Nombre | Calcul | Ce qu'il indique |
|---|---|---|
| μ₂₀ | somme des dx² | l'étalement **horizontal** |
| μ₀₂ | somme des dy² | l'étalement **vertical** |
| μ₁₁ | somme des dx · dy | si la forme **penche**, et de quel côté |

Pour μ₁₁ :
- si les pixels situés à droite du centre sont plutôt en haut, et ceux de gauche plutôt en bas, les produits dx·dy sont surtout d'un même signe et μ₁₁ est nettement positif ou négatif ;
- si la forme penche dans l'autre sens, μ₁₁ change de signe ;
- si la forme est bien droite, les contributions se compensent et μ₁₁ vaut 0.

Une formule classique combine ces trois nombres et donne l'angle de l'axe principal :

$$\theta = \frac{1}{2}\arctan\left(\frac{2\,\mu_{11}}{\mu_{20}-\mu_{02}}\right)$$

Pas besoin de la retenir. C'est la même formule qui donne les **axes d'inertie** d'un solide en mécanique : la direction autour de laquelle il est le plus facile de le faire tourner.

#### Étape 3 : pourquoi cet axe est la face plane

Vu de profil, le demi-cylindre est un **demi-disque** de rayon R :
- il mesure **2R de large**, le long de la face plane ;
- mais seulement **R de haut**.

Il est donc deux fois plus étalé le long de sa face plane, et son axe principal est **parallèle à la face plane**. Quand le demi-cylindre bascule, sa face plane bascule, l'axe principal aussi, et l'angle θ suit exactement l'inclinaison de l'objet.

C'est cet axe qui est dessiné en **ligne rouge** sur la vidéo.

#### En résumé

1. Moyenne des positions des pixels blancs → **centre** (point rouge).
2. Direction dans laquelle les pixels sont le plus étalés autour de ce centre → **axe principal** (ligne rouge).
3. Pour un demi-disque, cet axe est la face plane, et son angle avec l'horizontale est **θ**.

Ce calcul est répété sur chaque image, ce qui donne **θ en fonction du temps**.

#### Pourquoi cette méthode est robuste

- Elle utilise **tous les pixels** de la forme et pas seulement quelques points du bord. Si quelques pixels sont mal détectés, le résultat change à peine.
- Elle ne dépend **pas de la position** de l'objet. Le demi-cylindre se déplace un peu en roulant, et ça ne change pas l'angle mesuré.
- Un axe n'a pas de sens : « incliné de 10° » et « incliné de 190° » désignent la même droite. Le programme compare chaque angle au précédent pour éviter les sauts de 180° d'une image à l'autre.

### 5.4 De la courbe θ(t) à la période

On dispose maintenant d'une courbe θ(t) qui oscille, avec un point par image. La période est le temps qu'il faut pour revenir au **même extrême**.

**1. Combler les trous.** Si l'objet n'a pas été trouvé sur quelques images, la valeur manquante est estimée à partir des images voisines.

**2. Lisser.** Chaque point est remplacé par la moyenne de lui-même et de ses 4 voisins (2 avant, 2 après). Ça efface le petit tremblement de la mesure sans déplacer les sommets de la courbe.

**3. Trouver les sommets.** Le programme repère les **maxima** (l'objet est au plus loin d'un côté) et les **minima** (au plus loin de l'autre côté). Pour ne pas prendre un petit soubresaut pour un vrai sommet, il impose deux règles :
- un sommet doit dépasser ses voisins d'au moins **15 % de l'amplitude** totale ;
- deux sommets doivent être séparés d'au moins **60 % de l'écart habituel** entre sommets.

**4. Placer chaque sommet plus précisément qu'une image.** Le vrai sommet tombe rarement pile sur une image : il est souvent entre deux. Le programme fait passer une **parabole** par le point le plus haut et ses deux voisins, puis prend le sommet de cette parabole. On obtient ainsi l'instant du maximum avec une précision **meilleure que la durée d'une image**.

**5. Calculer la période.** Le programme mesure toutes les durées entre deux maxima successifs, puis entre deux minima successifs. La période **T** est la **moyenne** de toutes ces durées. Pour 10 oscillations filmées, on obtient environ 20 mesures de la période.

**6. Calculer l'incertitude.** Les périodes mesurées ne sont pas toutes identiques : elles sont un peu dispersées autour de la moyenne. Leur **écart-type** σ mesure cette dispersion. L'incertitude sur la moyenne vaut :

$$u(T) = \frac{\sigma}{\sqrt{N}}$$

où N est le nombre de périodes mesurées. C'est une incertitude de **type A** (obtenue par répétition des mesures). Plus on filme d'oscillations, plus N est grand et plus l'incertitude est petite.


---

## 6. Limites et précautions

### 6.1 Les ombres : visibles, mais pas forcément gênantes

Il est fréquent de voir une ombre sous le demi-cylindre, et parfois de la voir **englobée par le contour vert**. Ça ne veut pas dire que la période est fausse.

- **La période est peu sensible à l'ombre.** L'ombre est liée à l'objet et bouge **au même rythme** que lui. Même si elle est comptée dans la forme, la courbe θ(t) garde la même période. Sur une vidéo de test avec une ombre bien marquée, le programme trouve la même période (0,850 s) que l'ombre soit incluse ou exclue.
- **L'angle, lui, peut être faussé.** Si l'ombre est fusionnée avec l'objet, la forme analysée n'est plus un demi-disque. Son axe principal n'est plus parallèle à la face plane, donc l'**amplitude** mesurée et la **valeur** de θ sont faussées. C'est un problème seulement si l'on veut exploiter l'angle lui-même : amplitude, amortissement, comparaison avec une valeur théorique.
- **Une ombre peut être visible sur la vidéo sans entrer dans la mesure.** Avec la sélection par couleur, l'ombre, plus claire et grise, est exclue du masque. Elle apparaît sur l'image mais pas dans la vue « image traitée ». Seule cette vue montre ce qui est réellement mesuré.
- **Quand l'ombre devient vraiment gênante.** C'est le cas lorsqu'elle **change de forme d'une image à l'autre** : elle apparaît, disparaît, ou se sépare puis se recolle à l'objet. Le contour « saute », ce qui peut créer de faux extrêmes et augmenter l'incertitude. La ligne rouge tremble alors visiblement : il faut revoir la sélection ou la tolérance.
- **La zone de contact** entre le demi-cylindre et son ombre est la plus délicate : leurs couleurs y sont proches. Si le bas du contour déborde un peu, l'effet sur l'angle reste en général faible, car l'axe principal est surtout déterminé par la face plane, qui est la plus grande dimension.

### 6.2 Reflets et éclairage

Un reflet brillant sur l'objet peut être exclu du masque et créer un « trou » dans la forme. Un éclairage qui varie pendant la vidéo (néons, nuages) modifie les couleurs, et la tolérance choisie au départ peut ne plus convenir. Vérifiez la détection au début, au milieu et à la fin de la vidéo.

### 6.3 Résolution temporelle

La précision dépend de la cadence. À 30 fps, une image dure 33 ms. L'interpolation parabolique fait mieux que cette durée, mais seulement si chaque oscillation compte assez d'images, idéalement plus de 20 par période. Pour des oscillations rapides, filmez à 60 fps ou au ralenti.

### 6.4 Vidéos au ralenti et cadence variable

- Une vidéo au ralenti, par exemple filmée à 240 fps, est souvent **enregistrée comme une vidéo à 30 fps**. Sans l'option « fps réels » (`--fps-reel`), tous les temps sont faux d'un facteur 8.
- Les smartphones enregistrent parfois à **cadence variable** : l'intervalle entre deux images n'est pas exactement constant. Le programme suppose une cadence constante. L'erreur est en général faible, mais réelle. Si possible, choisissez une cadence fixe dans les réglages de l'appareil.

### 6.5 Géométrie et perspective

Le programme mesure l'angle de la **silhouette dans l'image**, c'est-à-dire en 2D. Si la caméra n'est pas bien perpendiculaire au plan d'oscillation, l'angle apparent diffère de l'angle réel. Les instants des extrêmes, et donc la **période**, ne sont pas affectés.

### 6.6 Petites oscillations et amortissement

Le mouvement est amorti, donc les dernières oscillations sont de plus en plus petites. Celles dont l'amplitude tombe sous 15 % de l'amplitude totale ne sont plus détectées, ce qui est voulu pour éviter de prendre le bruit pour des oscillations. Si la fin de la vidéo n'apporte que du bruit, réduisez la portion analysée.

La période peut aussi dépendre légèrement de l'amplitude (non-isochronisme). Le programme donne la **moyenne** sur les oscillations analysées. Le détail des périodes successives permet de voir si elles évoluent.

### 6.7 Ce que l'incertitude affichée ne contient pas

L'incertitude affichée vient uniquement de la **dispersion** des mesures (type A). Elle ne tient **pas** compte des erreurs systématiques : cadence mal connue, cadence variable, ou défaut de suivi régulier sur toute la vidéo.

---

## 7. Conseils de tournage

- Caméra **fixe** sur un trépied, **face** au demi-cylindre, avec l'axe de visée perpendiculaire au plan d'oscillation.
- **Fond uni**, d'une couleur bien différente de celle du demi-cylindre.
- **Éclairage diffus** ou placé du côté de la caméra, pour limiter les ombres et les reflets.
- Le demi-cylindre doit rester **entièrement dans le champ** pendant tout le mouvement.
- Filmez **au moins 5 à 10 oscillations**.
- Cadence **60 fps ou plus** si possible, en notant la cadence réelle en cas de ralenti.
- Une gommette ou un trait sur la face plane facilite le contrôle visuel. Elle permet aussi d'utiliser `--mode couleur` en ligne de commande.

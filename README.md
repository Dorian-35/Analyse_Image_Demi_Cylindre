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

Le traitement suit quatre étapes :

```
vidéo  →  une mesure d'angle par image  →  courbe θ(t)  →  instants des extrêmes  →  période
```

### 5.1 Lecture de la vidéo et du temps

La vidéo est lue image par image avec **OpenCV**. Le temps n'est pas mesuré : il est **calculé** à partir du numéro de l'image et de la cadence :

$$t = \frac{n^\circ\ \text{image}}{\text{fps}}$$

À 60 images/s, deux images successives sont séparées de 16,7 ms.

### 5.2 Isoler le demi-cylindre

Chaque image est réduite à la zone de travail, puis légèrement floutée pour atténuer le bruit du capteur. Le programme fabrique ensuite un **masque binaire** : en blanc l'objet, en noir le reste. Il y a deux façons de le faire :

- **Par la couleur** (quand le cylindre a été sélectionné). La couleur moyenne du petit rectangle tracé sur l'objet est mémorisée. Un pixel est gardé si sa couleur en est assez proche, à la *tolérance* près. Les couleurs sont comparées dans l'espace **CIE Lab**, où l'écart entre deux couleurs correspond à peu près à la différence perçue par l'œil.
- **Par le niveau de gris** (sans sélection). Les pixels plus sombres (ou plus clairs) qu'un seuil sont gardés. Si le seuil vaut 0, il est choisi automatiquement par la **méthode d'Otsu**, qui cherche le seuil séparant le mieux les deux populations de gris de l'image.

Une opération morphologique, l'*ouverture*, retire les petits points isolés. Avec la sélection par couleur, une *fermeture* bouche aussi les petits trous. Le programme garde ensuite **le plus grand contour**, qui est le demi-cylindre. C'est le **contour vert**.

### 5.3 Mesurer l'angle : les moments d'image

Les **moments** de la forme sont des sommes calculées sur tous ses pixels, comme en mécanique :

- le moment d'ordre 0, $m_{00}$, est l'**aire** ;
- les moments d'ordre 1 donnent le **centre de gravité** de la forme : $x_G = m_{10}/m_{00}$ et $y_G = m_{01}/m_{00}$ ;
- les moments centrés d'ordre 2, $\mu_{20}$, $\mu_{02}$ et $\mu_{11}$, jouent le rôle des moments d'inertie. Ils indiquent dans quelle direction la forme est la plus étalée.

L'angle de l'**axe principal** de la forme s'en déduit :

$$\theta = \frac{1}{2}\arctan\left(\frac{2\,\mu_{11}}{\mu_{20}-\mu_{02}}\right)$$

Vu de profil, un demi-cylindre est un demi-disque. Il est deux fois plus large que haut, donc son axe principal est **parallèle à la face plane**. C'est la **ligne rouge**, tracée à partir du centre de gravité, qui est le point rouge.

Quelques propriétés de cette mesure :
- elle utilise **tous les pixels** de la forme et pas seulement quelques points du bord, donc elle est peu sensible au bruit ;
- elle ne dépend **pas de la position** de l'objet. Le demi-cylindre se déplace un peu en roulant, et ça ne change pas l'angle mesuré ;
- un axe n'a pas de sens, donc l'angle pourrait sauter de 180° d'une image à l'autre. Le programme corrige ces sauts en comparant chaque angle au précédent.

### 5.4 De la courbe θ(t) à la période

1. **Trous.** Les images où l'objet n'a pas été trouvé sont remplacées par une interpolation linéaire entre leurs voisines.
2. **Lissage.** Chaque point est remplacé par une moyenne glissante sur 5 images.
3. **Extrêmes.** Les maxima puis les minima sont détectés (`scipy.signal.find_peaks`). Deux critères écartent les faux pics dus au bruit :
   - la *proéminence* : un pic doit dépasser ses voisins d'au moins 15 % de l'amplitude totale ;
   - la *distance* : deux pics doivent être séparés d'au moins 60 % de l'écart habituel entre pics.
4. **Précision inférieure à une image.** Le vrai sommet tombe rarement pile sur une image. Une **parabole** est ajustée sur le pic et ses deux voisins, et l'instant de son sommet est retenu. On obtient ainsi l'instant de l'extrême avec une précision meilleure que 1/fps.
5. **Période.** Le programme calcule toutes les durées entre deux maxima successifs et entre deux minima successifs. La période est leur **moyenne** :

$$T = \overline{\Delta t}$$

6. **Incertitude.** C'est une incertitude-type de type A, calculée à partir de la dispersion des $N$ périodes mesurées :

$$u(T) = \frac{\sigma}{\sqrt{N}}$$

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Période d'oscillation d'un demi-cylindre mesurée directement sur la vidéo.

On suit l'objet image par image, on repère les instants où il passe par
ses positions extrêmes, et la période est le temps écoulé entre deux
extrêmes identiques successifs. Aucun modèle théorique n'est utilisé.

Utilisation :
    python analyse_image.py video_1.mp4          (terminal)
    %run analyse_image.py video_1.mp4            (Jupyter)

Options :
    --mode angle | marqueur | couleur   (défaut : angle)
    --couleur rouge|vert|bleu|jaune|orange
    --debut 2 --fin 15                  portion de la vidéo à analyser (s)
    --fps-reel 240                      si la vidéo a été filmée au ralenti
    --roi x,y,l,h                       zone en pixels (sinon à la souris)
    --sans-affichage                    ne pas montrer la vidéo pendant le suivi
    --enregistrer suivi.mp4             enregistre la vidéo annotée
    --reglage                           curseurs pour régler contraste / seuil
    --contraste 1.5 --luminosite 20 --seuil 90   (réglages sans curseurs)
    --reglage_selection                 tracer un petit rectangle SUR le demi-cylindre :
                                        le programme garde uniquement sa couleur
                                        (ombre et fond ignorés)
    --tolerance 40                      écart de couleur accepté avec --reglage_selection
"""

import argparse
import sys

import cv2
import numpy as np
from scipy.signal import find_peaks

VIDEO_PAR_DEFAUT = "video_1.mp4"

PLAGES_HSV = {
    "rouge":  [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (180, 255, 255))],
    "vert":   [((40, 70, 50), (85, 255, 255))],
    "bleu":   [((95, 120, 50), (130, 255, 255))],
    "jaune":  [((20, 100, 100), (35, 255, 255))],
    "orange": [((10, 120, 100), (20, 255, 255))],
}


# ---------------------------------------------------------------- sélection
def choisir_roi(image, titre, roi_cli=None):
    if roi_cli:
        return tuple(int(v) for v in roi_cli.split(","))
    print(f">> {titre} : tracez un rectangle puis appuyez sur ENTRÉE.")
    h, w = image.shape[:2]
    e = min(1.0, 1280 / w, 800 / h)
    petit = cv2.resize(image, None, fx=e, fy=e) if e < 1 else image
    x, y, rw, rh = cv2.selectROI(titre, petit, showCrosshair=True)
    cv2.destroyWindow(titre)
    if rw == 0 or rh == 0:
        sys.exit("Aucune zone sélectionnée.")
    return tuple(int(round(v / e)) for v in (x, y, rw, rh))


# ---------------------------------------------------------------- suivis
class SuiviAngle:
    """Inclinaison de l'objet (moments d'image) dans la zone choisie."""

    def __init__(self, image0, roi, contraste=1.0, luminosite=0, seuil=0):
        self.roi = roi
        self.contraste = contraste    # 1 = inchangé, 2 = deux fois plus contrasté
        self.luminosite = luminosite  # ajouté à chaque pixel (-100 à +100)
        self.seuil = seuil            # 0 = automatique (Otsu), sinon 1 à 255
        g = self._gris(image0)
        h, w = g.shape
        self.sombre = g[h // 4:3 * h // 4, w // 4:3 * w // 4].mean() < g.mean()
        self.prec = None
        self.couleur_objet = None     # rempli par selectionner_objet()
        self.tolerance = 30

    def _lab(self, image):
        x, y, w, h = self.roi
        z = cv2.convertScaleAbs(image[y:y + h, x:x + w], alpha=self.contraste,
                                beta=128 * (1 - self.contraste) + self.luminosite)
        z = cv2.GaussianBlur(z, (5, 5), 0)
        return cv2.cvtColor(z, cv2.COLOR_BGR2LAB).astype(np.float32)

    def selectionner_objet(self, image, zone):
        """Apprend la couleur du demi-cylindre à partir d'un rectangle tracé dessus.
        zone = (x, y, l, h) dans l'image entière."""
        x, y, w, h = zone
        x0, y0 = self.roi[:2]
        lab = self._lab(image)[y - y0:y - y0 + h, x - x0:x - x0 + w].reshape(-1, 3)
        if lab.size == 0:
            sys.exit("Le rectangle doit être dans la zone choisie au départ.")
        self.couleur_objet = lab.mean(axis=0)
        # tolérance : assez large pour couvrir les nuances de l'objet
        dispersion = np.linalg.norm(lab - self.couleur_objet, axis=1)
        self.tolerance = int(max(20, np.percentile(dispersion, 98) * 1.5))
        print(f"Couleur du demi-cylindre enregistrée (tolérance {self.tolerance}).")

    def _gris(self, image):
        x, y, w, h = self.roi
        g = cv2.cvtColor(image[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
        # nouveau pixel = contraste * (pixel - 128) + 128 + luminosite
        g = cv2.convertScaleAbs(g, alpha=self.contraste,
                                beta=128 * (1 - self.contraste) + self.luminosite)
        return cv2.GaussianBlur(g, (5, 5), 0)

    def masque(self, image):
        """Image noir et blanc : blanc = ce que le programme prend pour l'objet."""
        if self.couleur_objet is not None:
            # on garde les pixels dont la couleur est proche de celle de l'objet
            d = np.linalg.norm(self._lab(image) - self.couleur_objet, axis=2)
            m = (d < self.tolerance).astype(np.uint8) * 255
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        mode = cv2.THRESH_BINARY_INV if self.sombre else cv2.THRESH_BINARY
        if self.seuil > 0:
            _, m = cv2.threshold(self._gris(image), self.seuil, 255, mode)
        else:
            _, m = cv2.threshold(self._gris(image), 0, 255, mode + cv2.THRESH_OTSU)
        return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    def mesure(self, image):
        m = self.masque(image)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs:
            return np.nan, None
        c = max(cs, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] < 50:
            return np.nan, None
        a = 0.5 * np.degrees(np.arctan2(2 * M["mu11"], M["mu20"] - M["mu02"]))
        if self.prec is not None:
            a -= 180 * round((a - self.prec) / 180)
        self.prec = a
        x0, y0 = self.roi[:2]
        centre = (M["m10"] / M["m00"] + x0, M["m01"] / M["m00"] + y0)
        return a, (c + np.array([x0, y0]), centre, a)

    def dessiner(self, image, info):
        if info is None:
            return
        contour, (cx, cy), a = info
        cv2.drawContours(image, [contour.astype(np.int32)], -1, (0, 255, 0), 3)
        L = 0.45 * max(self.roi[2], self.roi[3])
        dx, dy = L * np.cos(np.radians(a)), L * np.sin(np.radians(a))
        cv2.line(image, (int(cx - dx), int(cy - dy)), (int(cx + dx), int(cy + dy)),
                 (0, 0, 255), 3)
        cv2.circle(image, (int(cx), int(cy)), 5, (0, 0, 255), -1)


class SuiviMarqueur:
    """Motif choisi à la souris, suivi par corrélation."""

    def __init__(self, image0, roi):
        x, y, w, h = roi
        self.w, self.h, self.pos = w, h, (x, y)
        self.modele = cv2.cvtColor(image0[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
        self.marge = 2 * max(w, h)
        self.depart = (x + w / 2, y + h / 2)

    def mesure(self, image):
        g = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        H, W = g.shape
        x, y = self.pos
        x0, y0 = max(0, x - self.marge), max(0, y - self.marge)
        x1, y1 = min(W, x + self.w + self.marge), min(H, y + self.h + self.marge)
        res = cv2.matchTemplate(g[y0:y1, x0:x1], self.modele, cv2.TM_CCOEFF_NORMED)
        _, score, _, (mx, my) = cv2.minMaxLoc(res)
        if score < 0.4:
            return np.nan, None
        self.pos = (x0 + mx, y0 + my)
        cx, cy = self.pos[0] + self.w / 2, self.pos[1] + self.h / 2
        return cx, (cx, cy)

    def dessiner(self, image, info):
        if info is None:
            return
        x, y = self.pos
        cv2.rectangle(image, (x, y), (x + self.w, y + self.h), (0, 255, 0), 3)
        cv2.line(image, tuple(int(v) for v in self.depart), tuple(int(v) for v in info),
                 (0, 0, 255), 3)


class SuiviCouleur:
    """Gommette de couleur vive."""

    def __init__(self, couleur):
        self.plages = PLAGES_HSV[couleur]
        self.depart = None

    def mesure(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        m = np.zeros(hsv.shape[:2], np.uint8)
        for bas, haut in self.plages:
            m |= cv2.inRange(hsv, np.array(bas), np.array(haut))
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cs:
            return np.nan, None
        c = max(cs, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] < 10:
            return np.nan, None
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
        if self.depart is None:
            self.depart = (cx, cy)
        return cx, (c, cx, cy)

    def dessiner(self, image, info):
        if info is None:
            return
        c, cx, cy = info
        (xc, yc), r = cv2.minEnclosingCircle(c)
        cv2.circle(image, (int(xc), int(yc)), int(r) + 6, (0, 255, 0), 3)
        cv2.line(image, tuple(int(v) for v in self.depart), (int(cx), int(cy)),
                 (0, 0, 255), 3)


# ---------------------------------------------------------------- réglage
def regler(suivi, cap, i_debut, i_fin):
    """Curseurs pour ajuster le contraste, la luminosité et le seuil en direct.
    À gauche : la vidéo avec le contour vert. À droite : ce que voit le programme
    (blanc = objet). Le curseur « Image » permet de vérifier sur toute la vidéo."""
    fen = "Reglage (ENTREE pour valider)"
    cv2.namedWindow(fen, cv2.WINDOW_NORMAL)
    rien = lambda v: None
    cv2.createTrackbar("Contraste x10", fen, int(suivi.contraste * 10), 50, rien)
    cv2.createTrackbar("Luminosite", fen, suivi.luminosite + 100, 200, rien)
    selection = suivi.couleur_objet is not None
    if selection:
        cv2.createTrackbar("Tolerance", fen, suivi.tolerance, 150, rien)
    else:
        cv2.createTrackbar("Seuil (0=auto)", fen, suivi.seuil, 255, rien)
    cv2.createTrackbar("Image", fen, 0, max(1, i_fin - i_debut - 1), rien)
    n_aff = -1
    while True:
        n = cv2.getTrackbarPos("Image", fen)
        if n != n_aff:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i_debut + n)
            ok, image = cap.read()
            n_aff = n
        suivi.contraste = max(0.1, cv2.getTrackbarPos("Contraste x10", fen) / 10)
        suivi.luminosite = cv2.getTrackbarPos("Luminosite", fen) - 100
        if selection:
            suivi.tolerance = max(1, cv2.getTrackbarPos("Tolerance", fen))
        else:
            suivi.seuil = cv2.getTrackbarPos("Seuil (0=auto)", fen)
        suivi.prec = None
        _, info = suivi.mesure(image)
        vis = image.copy()
        suivi.dessiner(vis, info)
        x, y, w, h = suivi.roi
        zone = vis[y:y + h, x:x + w]
        m = cv2.cvtColor(suivi.masque(image), cv2.COLOR_GRAY2BGR)
        cv2.imshow(fen, np.hstack([zone, m]))
        if cv2.waitKey(30) & 0xFF in (13, 32, 27):
            break
    cv2.destroyWindow(fen)
    suivi.prec = None
    cap.set(cv2.CAP_PROP_POS_FRAMES, i_debut + 1)
    fin = f"--tolerance {suivi.tolerance}" if selection else f"--seuil {suivi.seuil}"
    print(f"Réglage choisi : --contraste {suivi.contraste:.1f} "
          f"--luminosite {suivi.luminosite} {fin}")


# ---------------------------------------------------------------- période
def instants_extremes(t, s):
    """Instants des maxima et des minima (précision inférieure à une image)."""
    s = np.convolve(np.pad(s, 2, mode="edge"), np.ones(5) / 5, mode="valid")  # léger lissage
    amp = np.ptp(s)
    # écart typique entre maxima, pour rejeter les faux pics trop rapprochés
    brut, _ = find_peaks(s, prominence=0.15 * amp)
    ecart = int(0.6 * np.median(np.diff(brut))) if len(brut) > 2 else 1
    resultats = []
    for signe in (1, -1):
        idx, _ = find_peaks(signe * s, prominence=0.15 * amp, distance=max(1, ecart))
        instants = []
        for p in idx:
            if 0 < p < len(s) - 1:
                y0, y1, y2 = signe * s[p - 1], signe * s[p], signe * s[p + 1]
                den = y0 - 2 * y1 + y2
                d = 0.5 * (y0 - y2) / den if den != 0 else 0.0
                instants.append(t[p] + d * (t[1] - t[0]))
        resultats.append(np.array(instants))
    return resultats  # [maxima, minima]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?", default=VIDEO_PAR_DEFAUT)
    ap.add_argument("--mode", choices=["angle", "marqueur", "couleur"], default="angle")
    ap.add_argument("--couleur", choices=list(PLAGES_HSV), default="rouge")
    ap.add_argument("--roi")
    ap.add_argument("--debut", type=float, default=0.0)
    ap.add_argument("--fin", type=float)
    ap.add_argument("--fps-reel", type=float)
    ap.add_argument("--sans-affichage", action="store_true")
    ap.add_argument("--reglage", action="store_true",
                    help="fenêtre à curseurs pour régler contraste / luminosité / seuil")
    ap.add_argument("--contraste", type=float, default=1.0)
    ap.add_argument("--luminosite", type=int, default=0)
    ap.add_argument("--seuil", type=int, default=0, help="0 = automatique")
    ap.add_argument("--reglage_selection", "--reglage-selection", action="store_true",
                    help="sélectionner directement le demi-cylindre (sa couleur)")
    ap.add_argument("--tolerance", type=int, help="écart de couleur accepté (sélection)")
    ap.add_argument("--zone_objet", help="rectangle x,y,l,h sur l'objet (sinon à la souris)")
    ap.add_argument("--enregistrer", metavar="FICHIER.mp4",
                    help="enregistre la vidéo annotée (temps, contour, ligne)")
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        sys.exit(f"Impossible d'ouvrir la vidéo : {args.video}")
    fps = args.fps_reel or cap.get(cv2.CAP_PROP_FPS) or 30.0
    n_images = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    i = int(round(args.debut * fps))
    i_fin = int(round(args.fin * fps)) if args.fin else n_images
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ok, image = cap.read()
    if not ok:
        sys.exit("Impossible de lire la vidéo.")

    if args.mode == "angle":
        suivi = SuiviAngle(image, choisir_roi(image, "Zone autour du demi-cylindre", args.roi),
                           args.contraste, args.luminosite, args.seuil)
        if args.reglage_selection:
            zone = choisir_roi(image, "Petit rectangle A L'INTERIEUR du demi-cylindre",
                               args.zone_objet)
            suivi.selectionner_objet(image, zone)
            if args.tolerance:
                suivi.tolerance = args.tolerance
        if args.reglage:
            regler(suivi, cap, i, i_fin)
    elif args.mode == "marqueur":
        suivi = SuiviMarqueur(image, choisir_roi(image, "Motif collé sur le demi-cylindre", args.roi))
    else:
        suivi = SuiviCouleur(args.couleur)

    t, s = [], []
    sortie = None
    while ok and i < i_fin:
        valeur, info = suivi.mesure(image)
        t.append(i / fps)
        s.append(valeur)
        if not args.sans_affichage or args.enregistrer:
            vis = image.copy()
            suivi.dessiner(vis, info)
            texte = f"t = {i / fps:.3f} s"
            cv2.rectangle(vis, (0, 0), (vis.shape[1], 55), (0, 0, 0), -1)
            cv2.putText(vis, texte, (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (255, 255, 255), 3)
            if args.enregistrer:
                if sortie is None:
                    h, w = vis.shape[:2]
                    sortie = cv2.VideoWriter(args.enregistrer, cv2.VideoWriter_fourcc(*"mp4v"),
                                             cap.get(cv2.CAP_PROP_FPS) or fps, (w, h))
                sortie.write(vis)
        if not args.sans_affichage:
            h, w = vis.shape[:2]
            e = min(1.0, 1280 / w, 800 / h)
            cv2.imshow("Suivi (q pour arreter)", cv2.resize(vis, None, fx=e, fy=e) if e < 1 else vis)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
        ok, image = cap.read()
        i += 1
    cap.release()
    if sortie is not None:
        sortie.release()
        print(f"Vidéo annotée enregistrée : {args.enregistrer}")
    cv2.destroyAllWindows()

    t, s = np.array(t), np.array(s, dtype=float)
    ok = np.isfinite(s)
    if ok.sum() < 10:
        sys.exit("L'objet n'a pas été suivi correctement (zone ou mode à changer).")
    s = np.interp(t, t[ok], s[ok])

    maxima, minima = instants_extremes(t, s)
    periodes = np.concatenate([np.diff(maxima), np.diff(minima)])
    if len(periodes) == 0:
        sys.exit("Moins de deux oscillations détectées : vidéo trop courte ?")

    T = periodes.mean()
    incertitude = periodes.std(ddof=1) / np.sqrt(len(periodes)) if len(periodes) > 1 else 1 / fps

    print("\nPériodes mesurées (s) :")
    print("  entre maxima :", np.round(np.diff(maxima), 3))
    print("  entre minima :", np.round(np.diff(minima), 3))
    print(f"\n>>> Période T = {T:.3f} ± {incertitude:.3f} s   "
          f"({len(periodes)} périodes mesurées, {fps:.0f} images/s)")
    return T


if __name__ == "__main__":
    main()

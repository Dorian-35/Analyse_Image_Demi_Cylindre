#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface graphique pour mesurer la période d'oscillation d'un demi-cylindre.

Ce fichier doit être placé dans le MÊME dossier que analyse_image.py
(il réutilise ses fonctions de suivi).

Lancement :
    python interface_oscillation.py            (terminal)
    %run interface_oscillation.py              (Jupyter, sur votre ordinateur)
    python interface_oscillation.py video_1.mp4   (ouvre directement la vidéo)
"""

import os
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse_image as ai  # noqa: E402

LARGEUR_MAX, HAUTEUR_MAX = 860, 520

TEXTE_AIDE = """
# À quoi sert ce programme ?
Il mesure la période d'oscillation d'un demi-cylindre filmé en vidéo. Le programme suit l'inclinaison du demi-cylindre image par image, repère les instants où il est au plus loin d'un côté (maxima) et de l'autre (minima), puis mesure le temps entre deux extrêmes identiques successifs. La période affichée est la moyenne de toutes ces durées.

# Étapes
1. Ouvrir une vidéo : choisissez votre fichier (.mp4, .mov, .avi...).
   Si la vidéo a été filmée au RALENTI, indiquez la vraie cadence (par ex. 240) dans « fps réels », sinon tous les temps seront faux.

2. Choisir la zone de travail : tracez à la souris un rectangle autour du demi-cylindre ET de tout l'espace où il bouge (rectangle bleu clair). Le programme n'analyse que cette zone.

3. Sélectionner le cylindre (conseillé) : tracez un petit rectangle entièrement À L'INTÉRIEUR du demi-cylindre (rectangle jaune). Le programme retient sa couleur et ne garde ensuite que les pixels de cette couleur : l'ombre et le fond sont ignorés.

4. Vérifier : déplacez le curseur « Image de la vidéo ». Le contour VERT doit épouser le demi-cylindre et la ligne ROUGE doit rester parallèle à sa face plane, sur toute la vidéo.

5. Démarrer : la vidéo défile avec le suivi. Le bouton « Arrêter » interrompt l'analyse (la période est quand même calculée sur la partie analysée).

# Voir l'image traitée (réglage)
Cette case (dans « Réglages de l'image ») ouvre une fenêtre qui montre ce que « voit » le programme :
 • à gauche, l'image de la zone après réglage du contraste et de la luminosité ;
 • à droite, la détection : en BLANC ce que le programme considère comme le demi-cylindre, en NOIR le reste.
Le réglage est bon quand le demi-cylindre est entièrement blanc et que le fond et l'ombre sont noirs. La fenêtre se met à jour en direct quand vous bougez les curseurs ou changez d'image.

# Les réglages
 • Contraste : 1 = image inchangée. Augmentez-le si l'objet se distingue mal du fond.
 • Luminosité : 0 = inchangée. Négatif = plus sombre, positif = plus clair.
 • Seuil (0 = auto) : utilisé seulement SI vous n'avez PAS sélectionné le cylindre. Niveau de gris qui sépare l'objet du fond. 0 = choix automatique. Si l'ombre est détectée avec l'objet, baissez-le progressivement.
 • Tolérance couleur : utilisée seulement SI vous avez sélectionné le cylindre. Écart de couleur accepté par rapport à la couleur du cylindre. Des morceaux du cylindre manquent → augmentez. L'ombre ou le fond sont pris → diminuez.

# Portion analysée
Début / Fin en secondes. Placez-vous sur une image avec le curseur puis cliquez sur « = image affichée » pour utiliser cet instant. Pratique pour enlever le moment où l'on lâche le cylindre ou la fin où il est presque immobile.

# Le résultat
T = valeur ± incertitude (en secondes).
L'incertitude est calculée à partir de la dispersion des périodes mesurées : écart-type / racine(nombre de périodes). Plus il y a d'oscillations filmées, plus elle est petite.
Le détail des périodes entre maxima et entre minima est affiché en dessous : si une valeur est très différente des autres, le suivi s'est probablement trompé à cet endroit.
« Enregistrer la vidéo annotée » crée un fichier « ..._suivi.mp4 » à côté de votre vidéo, avec le temps, le contour vert et la ligne rouge.

# Conseils de tournage
 • Caméra fixe (trépied), face au demi-cylindre, perpendiculaire au plan d'oscillation.
 • Fond uni, de couleur bien différente de celle du demi-cylindre.
 • Éclairage diffus ou de face pour limiter les ombres et les reflets.
 • Filmer au moins 5 à 10 oscillations.
 • Une cadence élevée (60 fps ou ralenti) améliore la précision.

# Problèmes fréquents
 • « L'objet n'a pas été suivi » : la zone ne contient pas le cylindre, ou les réglages sont mauvais. Ouvrez la vue de réglage.
 • La ligne rouge tremble ou saute : l'ombre ou un reflet perturbe la détection → sélectionnez le cylindre et ajustez la tolérance.
 • Période deux fois trop grande ou trop petite : vérifiez la case « fps réels ».
"""


def annoter_temps(image, t):
    cv2.rectangle(image, (0, 0), (image.shape[1], 55), (0, 0, 0), -1)
    cv2.putText(image, f"t = {t:.3f} s", (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                (255, 255, 255), 3)


class Application:
    def __init__(self, racine, video=None):
        self.r = racine
        self.r.title("Oscillations du demi-cylindre")
        self.cap = None
        self.zone = None          # (x, y, l, h) zone de travail
        self.objet = None         # (x, y, l, h) rectangle sur le cylindre / le motif
        self.img_objet = None     # image sur laquelle l'objet a été sélectionné
        self.selection = None     # "zone" ou "objet" pendant le tracé à la souris
        self.en_cours = False
        self.image = None
        self.fen_reglage = None
        self.fen_aide = None
        self._construire()
        if video:
            self.charger(video)

    # ------------------------------------------------------------ interface
    def _construire(self):
        menu = tk.Menu(self.r)
        menu_aide = tk.Menu(menu, tearoff=0)
        menu_aide.add_command(label="Aide (F1)", command=self.ouvrir_aide)
        menu.add_cascade(label="Aide", menu=menu_aide)
        self.r.config(menu=menu)
        self.r.bind("<F1>", lambda e: self.ouvrir_aide())

        gauche = tk.Frame(self.r)
        gauche.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        droite = tk.Frame(self.r)
        droite.pack(side="right", fill="y", padx=6, pady=6)

        self.canvas = tk.Canvas(gauche, width=LARGEUR_MAX, height=HAUTEUR_MAX, bg="#222")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self._souris_appui)
        self.canvas.bind("<B1-Motion>", self._souris_glisse)
        self.canvas.bind("<ButtonRelease-1>", self._souris_relache)
        self.item_image = self.canvas.create_image(0, 0, anchor="nw")

        self.var_pos = tk.IntVar(value=0)
        self.curseur_pos = tk.Scale(gauche, from_=0, to=1, orient="horizontal",
                                    variable=self.var_pos, label="Image de la vidéo",
                                    command=lambda v: self.apercu(), length=LARGEUR_MAX)
        self.curseur_pos.pack(fill="x")
        self.barre = ttk.Progressbar(gauche, length=LARGEUR_MAX)
        self.barre.pack(fill="x", pady=(4, 0))
        self.statut = tk.Label(gauche, text="Ouvrez une vidéo pour commencer.", anchor="w")
        self.statut.pack(fill="x")

        # --- Vidéo
        f = tk.LabelFrame(droite, text="Vidéo")
        f.pack(fill="x", pady=3)
        tk.Button(f, text="Ouvrir une vidéo", command=self.ouvrir).pack(fill="x")
        ligne = tk.Frame(f)
        ligne.pack(fill="x")
        tk.Label(ligne, text="fps réels (ralenti) :").pack(side="left")
        self.var_fps = tk.StringVar()
        tk.Entry(ligne, textvariable=self.var_fps, width=7).pack(side="left")
        self.lbl_fps = tk.Label(f, text="", fg="gray")
        self.lbl_fps.pack(anchor="w")

        # --- Mode
        # --- Sélection
        f = tk.LabelFrame(droite, text="Sélection (à la souris sur l'image)")
        f.pack(fill="x", pady=3)
        tk.Button(f, text="1. Choisir la zone de travail",
                  command=lambda: self._commencer_selection("zone")).pack(fill="x")
        self.btn_objet = tk.Button(f, text="2. Sélectionner le cylindre",
                                   command=lambda: self._commencer_selection("objet"))
        self.btn_objet.pack(fill="x")
        tk.Button(f, text="Effacer les sélections", command=self.effacer).pack(fill="x")

        bas = tk.Frame(gauche)
        bas.pack(fill="x", pady=(6, 0))

        # --- Réglages (sous la vidéo)
        f = tk.LabelFrame(bas, text="Réglages de l'image")
        f.pack(side="left", fill="both", expand=True)
        self.var_contraste = tk.DoubleVar(value=1.0)
        self.var_lum = tk.IntVar(value=0)
        self.var_seuil = tk.IntVar(value=0)
        self.var_tol = tk.IntVar(value=30)
        reglages = [(self.var_contraste, "Contraste", 0.2, 5, 0.1),
                    (self.var_lum, "Luminosité", -100, 100, 1),
                    (self.var_seuil, "Seuil (0 = auto, sans sélection du cylindre)", 0, 255, 1),
                    (self.var_tol, "Tolérance couleur (avec sélection du cylindre)", 1, 150, 1)]
        for k, (var, txt, a, b, res) in enumerate(reglages):
            tk.Scale(f, variable=var, label=txt, from_=a, to=b, resolution=res,
                     orient="horizontal", length=290,
                     command=lambda v: self.apercu()).grid(row=k // 2, column=k % 2, padx=4)
        self.var_vue = tk.BooleanVar(value=False)
        tk.Checkbutton(f, text="Voir l'image traitée (ce que voit le programme)",
                       variable=self.var_vue, command=self._basculer_vue_reglage
                       ).grid(row=2, column=0, columnspan=2, sticky="w", padx=4)

        # --- Portion analysée (sous la vidéo)
        f = tk.LabelFrame(bas, text="Portion analysée")
        f.pack(side="left", fill="y", padx=(6, 0))
        self.var_debut = tk.StringVar(value="0")
        self.var_fin = tk.StringVar(value="")
        for txt, var in [("Début (s)", self.var_debut), ("Fin (s)", self.var_fin)]:
            ligne = tk.Frame(f)
            ligne.pack(fill="x")
            tk.Label(ligne, text=txt, width=9, anchor="w").pack(side="left")
            tk.Entry(ligne, textvariable=var, width=8).pack(side="left")
            tk.Button(ligne, text="= image affichée",
                      command=lambda v=var: v.set(f"{self.var_pos.get() / self.fps():.3f}")
                      ).pack(side="left", padx=3)

        # --- Lancement
        f = tk.LabelFrame(droite, text="Analyse")
        f.pack(fill="x", pady=3)
        self.var_enreg = tk.BooleanVar(value=False)
        tk.Checkbutton(f, text="Enregistrer la vidéo annotée",
                       variable=self.var_enreg).pack(anchor="w")
        self.btn_demarrer = tk.Button(f, text="Démarrer", bg="#2e7d32", fg="white",
                                      font=("", 11, "bold"), command=self.demarrer)
        self.btn_demarrer.pack(fill="x", pady=2)
        self.btn_arreter = tk.Button(f, text="Arrêter", bg="#c62828", fg="white",
                                     state="disabled", command=self.arreter)
        self.btn_arreter.pack(fill="x")

        # --- Résultat
        f = tk.LabelFrame(droite, text="Résultat")
        f.pack(fill="both", expand=True, pady=3)
        self.lbl_T = tk.Label(f, text="T = —", font=("", 16, "bold"), fg="#1565c0")
        self.lbl_T.pack(pady=4)
        self.txt = tk.Text(f, width=34, height=10, font=("Courier", 9))
        self.txt.pack(fill="both", expand=True)

    def message(self, texte):
        self.statut.config(text=texte)

    # ------------------------------------------------------------ vidéo
    def ouvrir(self):
        chemin = filedialog.askopenfilename(
            title="Choisir une vidéo",
            filetypes=[("Vidéos", "*.mp4 *.mov *.avi *.mkv *.MP4 *.MOV"), ("Tous", "*.*")])
        if chemin:
            self.charger(chemin)

    def charger(self, chemin):
        cap = cv2.VideoCapture(chemin)
        if not cap.isOpened():
            messagebox.showerror("Erreur", f"Impossible d'ouvrir :\n{chemin}")
            return
        if self.cap:
            self.cap.release()
        self.cap, self.chemin = cap, chemin
        self.fps_fichier = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.ech = min(1.0, LARGEUR_MAX / self.W, HAUTEUR_MAX / self.H)
        self.canvas.config(width=int(self.W * self.ech), height=int(self.H * self.ech))
        self.curseur_pos.config(to=max(0, self.n - 1))
        self.var_pos.set(0)
        self.var_fin.set(f"{self.n / self.fps_fichier:.2f}")
        self.lbl_fps.config(text=f"{os.path.basename(chemin)} : {self.n} images, "
                                 f"{self.fps_fichier:.1f} fps")
        self.effacer()
        self.message("Étape 1 : cliquez sur « Choisir la zone de travail ».")

    def fps(self):
        try:
            return float(self.var_fps.get().replace(",", "."))
        except ValueError:
            return getattr(self, "fps_fichier", 30.0)

    def lire(self, i):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, im = self.cap.read()
        return im if ok else None

    def afficher(self, image):
        petit = cv2.resize(image, None, fx=self.ech, fy=self.ech) if self.ech < 1 else image
        ok, ppm = cv2.imencode(".ppm", petit)
        self.photo = tk.PhotoImage(data=ppm.tobytes())
        self.canvas.itemconfig(self.item_image, image=self.photo)
        self.canvas.delete("sel")
        if not self.en_cours:
            for rect, coul in [(self.zone, "cyan"), (self.objet, "yellow")]:
                if rect:
                    x, y, w, h = (v * self.ech for v in rect)
                    self.canvas.create_rectangle(x, y, x + w, y + h, outline=coul,
                                                 width=2, dash=(4, 2), tags="sel")

    # ------------------------------------------------------------ souris
    def _commencer_selection(self, quoi):
        if not self.cap:
            return self.message("Ouvrez d'abord une vidéo.")
        self.selection = quoi
        self.canvas.config(cursor="crosshair")
        if quoi == "zone":
            self.message("Tracez un rectangle autour du demi-cylindre et de son mouvement.")
        else:
            self.message("Tracez un petit rectangle À L'INTÉRIEUR du demi-cylindre.")

    def _souris_appui(self, e):
        if self.selection:
            self.p0 = (e.x, e.y)
            self.canvas.delete("trace")
            self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="lime", width=2,
                                         tags="trace")

    def _souris_glisse(self, e):
        if self.selection:
            self.canvas.coords("trace", *self.p0, e.x, e.y)

    def _souris_relache(self, e):
        if not self.selection:
            return
        self.canvas.delete("trace")
        x0, y0 = min(self.p0[0], e.x), min(self.p0[1], e.y)
        x1, y1 = max(self.p0[0], e.x), max(self.p0[1], e.y)
        rect = tuple(int(round(v / self.ech)) for v in (x0, y0, x1 - x0, y1 - y0))
        quoi, self.selection = self.selection, None
        self.canvas.config(cursor="")
        if rect[2] < 4 or rect[3] < 4:
            return self.message("Rectangle trop petit, recommencez.")
        if quoi == "zone":
            self.zone = rect
            self.objet = None
            self.message("Étape 2 (conseillée) : « Sélectionner le cylindre ». "
                         "Ou réglez le seuil puis Démarrer.")
        else:
            if not self._dans_zone(rect):
                return self.message("Le rectangle doit être à l'intérieur de la zone de travail.")
            self.objet = rect
            self.img_objet = self.image.copy()
            essai = ai.SuiviAngle(self.img_objet, self._zone(), self.var_contraste.get(),
                                  self.var_lum.get())
            essai.selectionner_objet(self.img_objet, rect, bavard=False)
            self.var_tol.set(essai.tolerance)
            self.message("Vérifiez le contour vert (curseur « Image »), ajustez, "
                         "puis Démarrer.")
        self.apercu()

    def _zone(self):
        return self.zone or (0, 0, self.W, self.H)

    def _dans_zone(self, r):
        zx, zy, zw, zh = self._zone()
        return r[0] >= zx and r[1] >= zy and r[0] + r[2] <= zx + zw and r[1] + r[3] <= zy + zh

    def effacer(self):
        self.zone = self.objet = self.img_objet = None
        self.apercu()

    # ------------------------------------------------------------ suivi
    def creer_suivi(self, image):
        s = ai.SuiviAngle(image, self._zone(), self.var_contraste.get(),
                          self.var_lum.get(), self.var_seuil.get())
        if self.objet:
            s.selectionner_objet(self.img_objet, self.objet, bavard=False)
            s.tolerance = self.var_tol.get()
        return s

    def apercu(self):
        if not self.cap or self.en_cours:
            return
        im = self.lire(self.var_pos.get())
        if im is None:
            return
        self.image = im
        vis = im.copy()
        suivi = self.creer_suivi(im)
        _, info = suivi.mesure(im)
        suivi.dessiner(vis, info)
        annoter_temps(vis, self.var_pos.get() / self.fps())
        self.afficher(vis)
        self.maj_vue_reglage(im, suivi)

    # ------------------------------------------------------------ vue de réglage
    def _basculer_vue_reglage(self):
        if self.var_vue.get():
            self.ouvrir_vue_reglage()
        else:
            self.fermer_vue_reglage()

    def fermer_vue_reglage(self):
        self.var_vue.set(False)
        if self.fen_reglage is not None and self.fen_reglage.winfo_exists():
            self.fen_reglage.destroy()
        self.fen_reglage = None

    def ouvrir_vue_reglage(self):
        if not self.cap:
            self.var_vue.set(False)
            return self.message("Ouvrez d'abord une vidéo.")
        if self.fen_reglage is not None and self.fen_reglage.winfo_exists():
            self.fen_reglage.lift()
            return
        self.fen_reglage = tk.Toplevel(self.r)
        self.fen_reglage.title("Vue de réglage : ce que voit le programme")
        self.fen_reglage.protocol("WM_DELETE_WINDOW", self.fermer_vue_reglage)
        entete = tk.Frame(self.fen_reglage)
        entete.pack(fill="x")
        tk.Label(entete, text="Image après contraste / luminosité",
                 font=("", 10, "bold")).pack(side="left", expand=True)
        tk.Label(entete, text="Détection (blanc = demi-cylindre)",
                 font=("", 10, "bold")).pack(side="left", expand=True)
        self.lbl_reglage = tk.Label(self.fen_reglage, bg="black")
        self.lbl_reglage.pack()
        tk.Label(self.fen_reglage, justify="left", fg="#444", text=(
            "Réglez les curseurs de la fenêtre principale jusqu'à ce que, à droite, "
            "le demi-cylindre soit\nentièrement blanc et que le fond et l'ombre "
            "soient noirs. Vérifiez sur plusieurs images.")).pack(pady=4)
        self.apercu()

    def maj_vue_reglage(self, image, suivi):
        if self.fen_reglage is None or not self.fen_reglage.winfo_exists():
            return
        x, y, w, h = suivi.roi
        traitee = cv2.convertScaleAbs(image[y:y + h, x:x + w], alpha=suivi.contraste,
                                      beta=128 * (1 - suivi.contraste) + suivi.luminosite)
        masque = cv2.cvtColor(suivi.masque(image), cv2.COLOR_GRAY2BGR)
        separation = np.full((h, 6, 3), 128, np.uint8)
        vue = np.hstack([traitee, separation, masque])
        e = min(1.0, 1000 / vue.shape[1], 450 / vue.shape[0])
        if e < 1:
            vue = cv2.resize(vue, None, fx=e, fy=e)
        ok, ppm = cv2.imencode(".ppm", vue)
        self.photo_reglage = tk.PhotoImage(data=ppm.tobytes())
        self.lbl_reglage.config(image=self.photo_reglage)

    # ------------------------------------------------------------ aide
    def ouvrir_aide(self):
        if self.fen_aide is not None and self.fen_aide.winfo_exists():
            self.fen_aide.lift()
            return
        self.fen_aide = tk.Toplevel(self.r)
        self.fen_aide.title("Aide")
        cadre = tk.Frame(self.fen_aide)
        cadre.pack(fill="both", expand=True)
        barre = tk.Scrollbar(cadre)
        barre.pack(side="right", fill="y")
        txt = tk.Text(cadre, width=80, height=34, wrap="word", padx=12, pady=10,
                      yscrollcommand=barre.set, font=("", 10))
        txt.pack(side="left", fill="both", expand=True)
        barre.config(command=txt.yview)
        txt.tag_config("titre", font=("", 13, "bold"), spacing1=10, spacing3=4)
        for ligne in TEXTE_AIDE.strip().split("\n"):
            if ligne.startswith("# "):
                txt.insert("end", ligne[2:] + "\n", "titre")
            else:
                txt.insert("end", ligne + "\n")
        txt.config(state="disabled")
        tk.Button(self.fen_aide, text="Fermer", command=self.fen_aide.destroy).pack(pady=6)

    # ------------------------------------------------------------ analyse
    def demarrer(self):
        if not self.cap:
            return self.message("Ouvrez d'abord une vidéo.")
        fps = self.fps()
        try:
            debut = float(self.var_debut.get().replace(",", ".") or 0)
            fin = float(self.var_fin.get().replace(",", ".")) if self.var_fin.get() else None
        except ValueError:
            return self.message("Début / fin : entrez des nombres (en secondes).")
        self.i = max(0, int(round(debut * fps)))
        self.i_debut = self.i
        self.i_fin = min(self.n, int(round(fin * fps))) if fin else self.n
        im = self.lire(self.i)
        if im is None:
            return self.message("Impossible de lire la vidéo à cet instant.")
        self.suivi = self.creer_suivi(im)
        self.image_courante = im
        self.t, self.s = [], []
        self.ecrivain = None
        if self.var_enreg.get():
            sortie = os.path.splitext(self.chemin)[0] + "_suivi.mp4"
            self.ecrivain = cv2.VideoWriter(sortie, cv2.VideoWriter_fourcc(*"mp4v"),
                                            self.fps_fichier, (self.W, self.H))
            self.sortie = sortie
        self.en_cours = True
        self.btn_demarrer.config(state="disabled")
        self.btn_arreter.config(state="normal")
        self.lbl_T.config(text="Analyse…")
        self.txt.delete("1.0", "end")
        self.message("Analyse en cours…")
        self.r.after(1, self._etape)

    def _etape(self):
        if not self.en_cours:
            return self._terminer(interrompu=True)
        fps = self.fps()
        t0 = time.time()
        vis = None
        # traite plusieurs images d'affilée (environ 40 ms) puis rafraîchit l'écran
        while self.i < self.i_fin and time.time() - t0 < 0.04:
            im = self.image_courante
            val, info = self.suivi.mesure(im)
            self.t.append(self.i / fps)
            self.s.append(val)
            vis = im.copy()
            self.suivi.dessiner(vis, info)
            annoter_temps(vis, self.i / fps)
            if self.ecrivain is not None:
                self.ecrivain.write(vis)
            ok, self.image_courante = self.cap.read()
            self.i += 1
            if not ok:
                self.i_fin = self.i
        if vis is not None:
            self.afficher(vis)
        total = max(1, self.i_fin - self.i_debut)
        self.barre["value"] = 100 * (self.i - self.i_debut) / total
        if self.i >= self.i_fin:
            return self._terminer()
        self.r.after(1, self._etape)

    def arreter(self):
        self.en_cours = False

    def _terminer(self, interrompu=False):
        self.en_cours = False
        self.btn_demarrer.config(state="normal")
        self.btn_arreter.config(state="disabled")
        if self.ecrivain is not None:
            self.ecrivain.release()
        t, s = np.array(self.t), np.array(self.s, dtype=float)
        ok = np.isfinite(s)
        if ok.sum() < 10:
            self.lbl_T.config(text="T = —")
            return self.message("L'objet n'a pas été suivi : revoyez la sélection / les réglages.")
        s = np.interp(t, t[ok], s[ok])
        maxima, minima = ai.instants_extremes(t, s)
        pmax, pmin = np.diff(maxima), np.diff(minima)
        periodes = np.concatenate([pmax, pmin])
        if len(periodes) == 0:
            self.lbl_T.config(text="T = —")
            return self.message("Moins de deux oscillations détectées.")
        T = periodes.mean()
        u = periodes.std(ddof=1) / np.sqrt(len(periodes)) if len(periodes) > 1 else 1 / self.fps()
        self.lbl_T.config(text=f"T = {T:.3f} ± {u:.3f} s")
        lignes = [f"{len(periodes)} périodes mesurées",
                  f"suivi réussi sur {100 * ok.mean():.0f} % des images", "",
                  "Entre maxima (s) :"] + [f"  {p:.3f}" for p in pmax] + \
                 ["Entre minima (s) :"] + [f"  {p:.3f}" for p in pmin]
        self.txt.insert("end", "\n".join(lignes))
        msg = "Analyse arrêtée (résultat sur la partie analysée)." if interrompu \
            else "Analyse terminée."
        if self.ecrivain is not None:
            msg += f"  Vidéo annotée : {os.path.basename(self.sortie)}"
        self.message(msg)


def main():
    racine = tk.Tk()
    Application(racine, sys.argv[1] if len(sys.argv) > 1 else None)
    racine.mainloop()


if __name__ == "__main__":
    main()

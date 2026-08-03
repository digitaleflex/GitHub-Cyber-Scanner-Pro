# HashCode Decision OS — Product Manifesto

---

## 1. Quel problème fondamental résolvons-nous ?

Les professionnels de la cybersécurité sont noyés sous un torrent d'informations — CVE,
bulletins, exploits, IOC, alertes — et passent l'essentiel de leur temps à trier ce flot pour
trouver ce qui les concerne vraiment. Les plateformes existantes poussent des données ;
elles ne prennent pas de décisions. Le résultat est une fatigue décisionnelle chronique :
trop de bruit, pas assez de signal, jamais certain d'avoir ignoré la bonne alerte.

> **Nous résolvons le problème de la fatigue décisionnelle en cybersécurité.**

---

## 2. Quelle est notre promesse en une phrase ?

> **HashCode transforme des millions d'événements de cybersécurité en quelques décisions
> fiables, personnalisées et immédiatement actionnables, pour chaque personne de
> l'organisation.**

---

## 3. Quels principes ne compromettrons-nous jamais ?

### I. La décision avant la donnée

Aucune information ne doit apparaître si elle n'influence pas une décision.
Montrer des données n'est pas notre métier ; produire des résultats l'est.

### II. Le contexte avant le contenu

Une CVE n'existe jamais seule. Elle est toujours reliée à un asset, une technologie,
un rôle, un secteur, un impact. Sans contexte, une alerte est du bruit.

### III. La justification avant la confiance

Chaque recommandation s'accompagne de son raisonnement : sources, facteurs de
priorité, niveau de confiance, risque si ignorée. Nous ne demandons jamais à
l'utilisateur de nous croire sur parole.

### IV. L'organisation avant l'individu

Le contexte de vérité est celui de l'organisation : ses assets, ses technologies,
son secteur, sa conformité. Le profil personnel est une vue ; l'organisation est
la source. Un RSSI et un développeur voient des choses différentes de la même
infrastructure.

### V. L'action à la place de l'information

L'utilisateur ne veut pas savoir quoi faire. Il veut que ce soit fait. Chaque
décision débouche sur une action concrète — patcher, bloquer, escalader,
documenter, former — et l'action est traçable, vérifiable, délégable.

### VI. La boucle, pas la ligne droite

Chaque décision, chaque action, chaque résultat alimente le moteur qui améliore la
décision suivante. Nous construisons une boucle d'apprentissage, pas un flux
unidirectionnel.

---

## 4. Quelles capacités devront toujours exister, même dans dix ans ?

| Capacité | Définition |
|---|---|
| **Comprendre mon contexte** | La plateforme connaît l'organisation, ses assets, ses technologies, ses rôles et ses objectifs — sans que l'utilisateur ait à les redécouvrir à chaque connexion. |
| **Décider** | Le moteur transforme le flot d'événements en un petit nombre de décisions priorisées, justifiées et adaptées au contexte de chaque personne. |
| **Agir** | Chaque décision s'accompagne d'une ou plusieurs actions concrètes, préparables et traçables — du patch technique au rapport de conformité. |
| **Coordonner** | Les actions sont assignables aux bonnes personnes, au bon moment, avec le bon niveau d'information. |
| **Vérifier** | La plateforme confirme que l'action a eu l'effet escompté : le risque a baissé, l'écart de conformité s'est réduit, la vulnérabilité est résolue. |
| **Apprendre** | Chaque boucle de décision améliore le contexte de la suivante. Le moteur devient plus pertinent à mesure qu'il est utilisé, et n'oublie jamais ce que l'utilisateur n'a pas encore vu. |

---

*Ce manifeste est la constitution du produit. Toute décision — fonctionnalité, API,
interface, infrastructure — doit pouvoir être reliée à au moins une capacité et ne
jamais violer un principe. Si un ajout ne sert aucune capacité ou enfreint un principe,
il n'a pas sa place dans le produit.*

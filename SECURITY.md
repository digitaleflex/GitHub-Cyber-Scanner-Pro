# Politique de Securite

## Signaler une vulnerabilite

Si vous decouvrez une vulnerabilite de securite dans ce projet, merci de ne pas la signaler publiquement.

### Comment signaler

1. Envoyez un email a **security@example.com** avec :
   - Une description de la vulnerabilite
   - Les etapes pour la reproduire
   - L'impact potentiel
   - Suggestions de correction (optionnel)

2. Vous recevrez une reponse sous 48 heures

3. Nous travaillerons ensemble pour corriger le probleme avant toute publication

## Ce que nous ne considerons pas comme une vulnerabilite

- Les problemes lies au rate limiting de l'API GitHub
- Les faux positifs dans les resultats de scan
- Les problemes de performance du script

## Securite du code

Ce projet scanne uniquement l'API GitHub publique. Il ne :
- Ne clone pas de repos
- N'execute pas de code externe
- Ne collecte pas de donnees personnelles
- N'envoie pas de donnees vers des services tiers

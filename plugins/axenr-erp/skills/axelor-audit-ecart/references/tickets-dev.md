# Écrire un ticket Jira pour un développeur (à partir d'un audit)

Un audit débouche souvent sur des tickets de dev. Un ticket utile pour un développeur n'est ni une
liste de tâches techniques sèches (« ajouter le champ X, créer l'action Y »), ni une dissertation
métier sans ancrage. Le dev a besoin de **comprendre le pourquoi** ET de **savoir où démarrer**.

## La structure

### 1. Contexte
La situation métier réelle, concrète. D'où vient le besoin, quel problème terrain on résout.
Pour AxENR : ancrer dans le réel du client (ex. installateur PV multi-sites, délais d'approvisionnement,
stocks chez des prestataires logistiques…). C'est ce qui donne du sens et évite les choix techniques à côté.

### 2. But / ce qu'il faut comprendre
La **logique** de la fonctionnalité, pas son implémentation. Quel comportement on veut, et surtout
**pourquoi**. Dégager les 2-3 idées clés que le dev doit avoir en tête pour bien concevoir.
C'est la partie que les tickets oublient le plus souvent, et celle qui manque le plus aux devs.

### 3. Repères techniques (points d'accroche existants)
Ce qui existe déjà et **où ça se branche** — comme des repères, pas un mode d'emploi :
- les objets/champs concernés constatés (avec leur vrai nom, vérifié),
- ce qui est réutilisable (un import, un service, un batch déjà là),
- ce qui manque réellement (vérifié fichiers + base),
- les pièges connus (ex. champ en low-code Studio → attention au rebuild).

Donner les noms exacts **vérifiés**, mais **ne pas écrire l'implémentation** : le dev choisit le comment.
Préfixer cette section d'un « constats vérifiés le <date> — repères, conception laissée à ton appréciation ».

### 4. À clarifier
Les questions ouvertes à trancher avec le métier (intitulés, seuils, règles de gestion, cas limites)
avant de figer. Isoler ces questions pour que le dev ne reste pas bloqué et sache à qui demander.

## L'équilibre à viser

| Travers | Effet sur le dev |
|---|---|
| Que du technique (« ajouter champ X ») | Il exécute sans comprendre la logique → choix à côté du besoin |
| Que du métier (prose, zéro repère) | Il comprend le pourquoi mais repart de zéro à chercher où brancher |
| **Contexte + but + repères** | Il comprend ET sait démarrer, tout en gardant le choix du comment |

## Règle d'or

**Un bon ticket fait comprendre le problème avant de parler de solution.** Et il ne dicte jamais le
code : il donne les repères, le dev décide de l'implémentation. Si on se surprend à écrire l'algorithme
ou à nommer chaque méthode à créer, c'est qu'on est repassé en mode « liste de tâches » — revenir au but.

## Mini-exemple (forme)

```
## Contexte
[Situation métier réelle, le problème terrain.]

## But / ce qu'il faut comprendre
[La logique, le pourquoi. Les 2-3 idées clés.]

## Repères techniques (points d'accroche existants)
> Constats vérifiés le JJ/MM — repères, conception laissée à ton appréciation.
- [Objet/champ existant réutilisable + son vrai nom]
- [Ce qui manque réellement, vérifié fichiers + base]
- [Piège éventuel, ex. low-code Studio / rebuild]

## À clarifier
- [Question métier 1] (à voir avec <référent>)
- [Question métier 2]
```

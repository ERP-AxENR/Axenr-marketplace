> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Référentiels : ce qui change d'un modèle à l'autre

Prouvé sur AOS 9.1.6 / AOP EE 8.2.3 le 25/09/2026 (essais internes Axelor sur une instance jetable). Sur un autre
modèle : relève ses champs (`ee_api.py fields`), ses clés (`ee_api.py keys`) et lis le `save()` de son
repository avant d'écrire le gabarit.

## Article (`Product`)

- **Une seule table pour deux choses.** Les lignes « article par société » (`ProductCompany`) héritent de
  `Product` : un export non filtré les sort comme des articles vides à clé `product-<id>`, et un compte
  par table les mélange (sur une instance réelle vue le 25/09/2026, près d'un quart des « articles »
  comptés étaient des lignes par société). Filtre `self.dtype = 'Product'` à l'export comme au comptage.
- **`compute` sur `Product`, toujours.** Il pose `fullName` (« [code] nom »), `serialNumber` (= code) et
  crée la ligne par société (une seule, rejeu compris : vérifié) ; sans lui, rien de cela et l'article est invisible dans les sélecteurs. Le
  code par séquence n'est posé que si l'app Base a « générer la séquence produit » actif **et** que le
  code est vide (lecture de `ProductBaseRepository.save`, non rejoué).
- **Clés de relation relevées** : famille `productFamily.code`, catégorie `productCategory.code`, devise
  `saleCurrency.codeISO` / `purchaseCurrency.codeISO` ; unité **uniquement** `unit.importId` (aucune clé
  unique). Une unité sans clé d'import se pointe par la clé locale que donne `keys` (`unit-40`) : valable
  seulement dans le classeur généré pour cette base — d'où le générateur rejoué avec les `keys` de la
  recette (import-ee-templates.md §5-§7).
- **Pointer un article** depuis un autre onglet (catalogue, liste de prix, nomenclature) : `product.code`
  ne résout pas (unique mais non requis) → `product.importId`.
- Champs de prix par société : si l'app Base les déclare « par société » sans afficher les sociétés, ils
  disparaissent de la fiche ; vérifier sur l'env cible avant de promettre la colonne.

## Utilisateur (`User`)

- **Aucune colonne mot de passe.** `password` est écrit en clair en base, le compte ne se connecte pas,
  et un rejeu écrase un mot de passe chiffré ; `transientPassword` est perdu par la seconde passe.
  Après import : mot de passe par l'API REST
  (`POST /ws/rest/com.axelor.auth.db.User/<id>` avec `{"id","version","password"}` → chiffré), ou
  « mot de passe oublié » par chaque utilisateur si l'instance l'autorise
  (`application.resetPasswordEnabled`, lu par `ee_api.py info`). Politique de mot de passe : ne pas
  contenir le login.
- **Bloqué par défaut.** Sans colonne `blocked`, le compte arrive bloqué. Mettre `blocked` = `false`
  explicitement pour les comptes à ouvrir.
- **Sièges de licence.** Plafond lisible en lecture (`ee_api.py info` → `AppLicense.licenses`, au format
  « <nom de la licence> (<n>) »). Licence pleine : un compte importé `blocked = false` est **rebloqué dès
  l'enregistrement** par l'écouteur de la licence, rapport vert, seul un WARN GUARDIAN au journal ;
  `plan` annonce lesquels. Chaque compte non bloqué prend un siège ; la carte des sièges n'est relue qu'au
  **redémarrage**, et une connexion tentée avant rebloque le compte avec un refus qui ressemble à un
  mauvais mot de passe. Compter les comptes non bloqués contre les
  sièges de la licence cible **avant** l'import ; prévoir le redémarrage et ne tester la connexion
  qu'après.
- **Plus de comptes que de sièges : import en deux temps.** Classeur 1 = les comptes à ouvrir, choisis
  par le client (`blocked` = `false`, ≤ sièges libres) ; classeur 2 = tous les autres, `blocked` = `true`. Un
  compte bloqué ne consomme pas de siège (l'écouteur de licence ignore un compte inactif, le décompte ne
  porte que sur les non bloqués) : les comptes existent, on les ouvre plus tard un par un.
- **`compute` sur `User`** : utile (e-mail repris du tiers lié), mais la langue par défaut n'est **pas**
  posée (logique de création) : colonne `language` explicite (`fr`).
- **Un login existant écrase le compte.** L'utilisateur se retrouve par `code` (login, requis-unique)
  avant la clé d'import : une ligne au login `admin` ou d'un compte de démo met à jour CE compte et réécrit
  sa clé. `ee_api.py plan` avant tout import.
- **Clés** : `email` est unique mais non
  requis → un lien `user.email` ne résout pas, `user.code` oui. Groupe par `group.code` (résout même vers
  un groupe sans clé d'import), société active par `activeCompany.code`, rôles par l'onglet de liaison
  `User.roles` (`importId`, `roles.name`), sociétés autorisées par l'onglet `User.companySet` (non rejoué le 25/09 : à prouver en répétition).
- **Profils et droits** : le gabarit rattache un groupe existant ; concevoir un profil ou ses droits
  relève de `axelor-droits-expert`.
- Lien salarié (`employee`) et tiers (`partner`) : par `employee.importId` / `partner.partnerSeq`
  (clé requise-unique du tiers à vérifier sur la version cible) ; les salariés s'importent avant.

## Tiers et contacts (`Partner`)

Lu dans le code AOS 9.1.x, non rejoué : les sources locales ne correspondaient pas exactement aux
bibliothèques qui tournaient. À prouver en répétition.

- **Contact** : `isContact` = `true`, `partnerTypeSelect` = `2`, `mainPartner.importId`. L'import ne l'ajoute
  pas à la liste des contacts de l'entreprise (`addContactToPartner` n'est appelé que par l'écran) → onglet de
  liaison `Partner.contactPartnerSet` (`importId` de l'entreprise, `contactPartnerSet.importId`).
- **E-mail** : relation un-à-un vers `EmailAddress` (onglet dédié, `address` + `name` requis) ; une fiche e-mail
  par tiers, sinon refus au save (`PARTNER_EMAIL_EXIST`).
- **Adresse principale** : avec **une seule** adresse, le save la marque par défaut, de livraison et de
  facturation (`PartnerServiceImpl.setDefaultPartnerAddress`). Avec plusieurs adresses, rien n'est posé :
  fournir `isDefaultAddr`, `isDeliveryAddr` et `isInvoicingAddr` en colonnes.
- **Numéro du tiers** (`partnerSeq`) : généré seulement s'il est vide et que l'app Base génère la séquence
  (`generatePartnerSequence`) → fournir le code du client.

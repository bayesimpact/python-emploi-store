# Change Log

## v0.9.1 [2020-03-03]

* Ship the type stubs with the PyPi package.

## v0.9.0 [2020-03-02]

* Fix call to OAuth2 /access_token endpoint to send the realm parameter in the URL.

## v0.8.1 [2018-08-16]

Not a real release, only updated testing and documentation.

## v0.8.0 [2018-06-08]

* Added support for the ["Match via Soft Skills" API](https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-matchviasoftskills-v1.html).

## v0.7.0 [2018-05-23]

* Added support for the `contract` parameter of ["La Bonne Boite" API](https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-la-bonne-boite-v1/rechercher-des-entreprises.html) which accesses the data served at ["La Bonne Alternance"](https://labonnealternance.pole-emploi.fr/).

## v0.6.0 [2018-02-08]

* Added support for the ["Salons en lignes" Events API](https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-evenements-pole-emploi-v1.html).

## v0.5.2 [2018-02-02]

* Added the length of the records list in a resource without listing them all.
* Added an argument to the to_csv method to modify records before saving them.

## v0.5.0 [2018-02-01]

* Added support for the ["Catalogue des services" API](https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-catalogueemploistore-v1.html).

## v0.4.0 [2017-08-03]

* Added support for the ["Retour à l'emploi suite formation"
  API](https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-retouralemploiformation-v1.html).

## v0.3.2 [2017-07-12]

* Added support for selecting versioned resource by its PE version number.

## v0.3.1 [2017-03-15]

* Added support for requesting LBB companies close to a city by its INSEE ID.

## v0.3.0 [2017-03-13]

* Convert the authentication method to use scope as required by Emploi Store
  Dev since 2017-01-20, see [their
  announcement](https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/utiliser-les-api/changements-20-janvier-2017.html).

# Schéma — soretrak_gtfs.db

## Faits sur les données (vérifiés)

- Réseau surtout régional : Kairouan + liaisons vers Sousse, Tunis, Mahdia, Monastir… (132 arrêts sur 192 à plus de 20 km de Kairouan).
- **34 lignes sur 95 ont des horaires.** Une ligne présente dans `routes` mais absente des vues n'a pas d'horaires → `aucune_donnee`, pas `impossible`.
- 189 arrêts sur 192 sont desservis.
- Un seul calendrier, valable tous les jours : aucune distinction semaine / week-end.
- Heures en texte `HH:MM:SS` (05:00:00 → 18:35:00) : comparer et trier directement. `arrival_time` = `departure_time`.
- **Un départ = un trajet** (`trip_id`), pas un passage à un arrêt. « Nombre de départs d'une ligne » = `COUNT(DISTINCT trip_id)` ; `COUNT(*)` sur `v_departures` compte les passages (un trajet × ses arrêts).
- **Durée : ne jamais soustraire deux heures directement** (`'06:46:00' - '06:30:00'` vaut 0 : seules les heures sont soustraites). Pour un trajet de A à B, utiliser `v_trajets.duree_min` ; sinon `(strftime('%s', fin) - strftime('%s', debut)) / 60`.
- Souvent un seul sens (`direction_id` 0 ou 1) est renseigné.
- `route_id` = numéro de ligne (« la 21 » → `route_id = '21'`).
- Noms d'arrêts hétérogènes : passer par `resolve_place`, ne jamais filtrer `stop_name` par `=` ou `LIKE`.

## Tables

- `routes(route_id, route_short_name, route_long_name, route_type)` : les lignes.
- `stops(stop_id, stop_name, stop_lat, stop_lon)` : les arrêts.
- `trips(trip_id, route_id, direction_id, trip_headsign)` : un trajet par horaire et par sens ; `trip_headsign` = destination.
- `stop_times(trip_id, stop_id, stop_sequence, departure_time)` : passage d'un trajet à un arrêt.
- `agency` (SORETRAK : nom, site, téléphone), `calendar` (une ligne), `shapes` (tracés GPS, inutile pour répondre).

## Vues

- `v_departures(stop_id, stop_name, route_id, route_short_name, route_long_name, trip_id, trip_headsign, direction_id, departure_time, stop_sequence)` : un passage. Pour prochains départs, horaires, lignes d'un arrêt, comptages.
- `v_route_stops(route_id, route_short_name, direction_id, stop_sequence, stop_id, stop_name)` : arrêts d'une ligne. Toujours ajouter `ORDER BY stop_sequence`.
- `v_trajets(depart_id, depart_nom, arrivee_id, arrivee_nom, route_id, direction_id, trip_id, heure_depart, heure_arrivee, duree_min, nb_arrets)` : un trajet direct possible, de l'arrêt A (départ) à l'arrêt B (arrivée), sur le même bus. A est toujours avant B, `duree_min` est déjà en minutes. **Toute question « de A à B » passe par cette vue** : liaisons directes, horaires, prochains bus, durée, nombre d'arrêts entre A et B.

## Limites

Une seule requête SELECT / WITH, 50 lignes au plus : pour compter, `COUNT(*)` ou `COUNT(DISTINCT …)`.

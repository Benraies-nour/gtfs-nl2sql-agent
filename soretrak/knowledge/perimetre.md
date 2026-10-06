# Fiche périmètre

Source unique de ce que l'assistant sait faire. Utilisée par le Router
(intent `hors_perimetre`) et par le SQL Agent (statut `impossible`).

| Répondable avec nos données | Pas répondable (v1) |
|---|---|
| Lignes qui passent par un arrêt | Prix des tickets, abonnements |
| Arrêts d'une ligne | Temps réel : position du bus, retards |
| Horaires théoriques | Autres opérateurs : trains, louages, métro de Tunis |
| Prochains départs (théoriques) | Autres réseaux de bus (bus urbains de Sousse, de Tunis…) |
| Durée entre deux arrêts d'une même ligne | Itinéraires avec correspondance |
| Liaisons directes entre deux arrêts | Accessibilité, équipements des bus |
| Lignes régionales SORETRAK au départ de Kairouan (Sousse, Tunis, Mahdia, Monastir…) | |

Contact SORETRAK (Société Régionale de Transport de Kairouan), pour ce qui n'est pas
dans les données (prix, abonnements, agences, réclamations, retards) :
site www.soretrak.com.tn, téléphone +216 77 226 321.

Seules 34 lignes sur 95 ont des horaires dans les données. Pour les
autres, la réponse honnête est « cette ligne existe, mais ses horaires
ne sont pas dans les données disponibles » — pas « cette ligne n'existe
pas ».

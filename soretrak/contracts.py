"""Types shared between modules.

- Pydantic models: validated data (LLM outputs, agent and query results).
- TypedDict: structures passed around as dicts (LangGraph state, interface);
  they document the keys without changing anything at runtime.
"""

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field, model_validator


PlaceType = Literal["arret", "ligne", "ville"]
PlaceStatus = Literal["trouve", "ambigu", "introuvable"]


class Candidate(BaseModel):
    """A place proposed by resolve_place. `nom` is the raw name from the database."""

    type: Literal["arret", "ligne"]
    id: str
    nom: str
    score: int
    raison: str


class PlaceResult(BaseModel):
    """Result of a place resolution."""

    statut: PlaceStatus
    candidats: list[Candidate] = Field(default_factory=list)


Intent = Literal[
    "transport",
    "conversation",
    "trop_vague",
    "hors_perimetre",
    "hors_sujet",
]


class RouterDecision(BaseModel):
    """Router output: the rewritten question for `transport`, otherwise the text to display."""

    intent: Intent
    question_autonome: str | None = None
    reponse: str | None = None
    # For transport: places and lines mentioned, copied as the user wrote them.
    lieux: list[str] = Field(default_factory=list)
    # True only when the user explicitly requests a map.
    carte: bool = False
    # True only when the user explicitly requests a chart.
    graphique: bool = False

    @model_validator(mode="after")
    def _coherent(self):
        if self.intent == "transport" and not (self.question_autonome or "").strip():
            raise ValueError("intent transport : question_autonome est obligatoire")
        if self.intent != "transport" and not (self.reponse or "").strip():
            raise ValueError(f"intent {self.intent} : reponse est obligatoire")
        return self


# `echec` is reserved to the code: the agent cannot choose it.
AgentStatus = Literal[
    "repondu",
    "aucune_donnee",
    "ambigu",
    "impossible",
    "echec",
]


class AgentResult(BaseModel):
    """SQL Agent conclusion: a status and the ids of the queries used as evidence."""

    statut: AgentStatus
    preuves: list[str] = Field(default_factory=list)
    note: str | None = None
    clarification: list[Candidate] = Field(default_factory=list)
    # True when the LLM provider rate limit was reached.
    quota: bool = False


class Response(BaseModel):
    """Response returned to the interface."""

    texte: str
    chemin: str                 # Router intent or agent status
    details: dict[str, Any] = Field(default_factory=dict)   # TurnDetails (see below)


class QueryResult(BaseModel):
    """Result of a SQL query. `error` is filled instead of raising an exception."""

    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0          # number of rows returned (at most max_rows)
    truncated: bool = False     # True if more rows existed beyond max_rows
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class QueryRecord(TypedDict):
    """SQL query and its result."""

    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool
    error: str | None


class PlaceFacts(TypedDict, total=False):
    """Facts associated with a place candidate."""

    type: Literal["arret", "ligne"]
    id: str
    nom: str
    score: int
    lignes: list[str]          # stop: lines that serve it
    nb_arrets: int             # line: number of stops in the data
    a_horaires: bool           # line: present in the timetables
    sens: list[int]            # line: directions available (0, 1)


class ResolvedPlace(TypedDict):
    """Place resolved from the user request."""

    texte: str
    statut: PlaceStatus
    candidats: list[PlaceFacts]


class AgentRun(TypedDict):
    """Information about an SQL agent run."""

    resultat: dict[str, Any]
    requetes: dict[str, QueryRecord]
    trace: list[dict[str, Any]]
    nb_appels: int


class TurnContext(TypedDict):
    """Context from the current transport conversation turn."""

    question: str
    lieux: list[dict[str, str]]
    lignes: list[str]
    arrets: list[str]
    statut: str


class MapPoint(TypedDict):
    """Point displayed on the map."""

    nom: str
    lat: float
    lon: float
    role: Literal["depart", "arrivee", "intermediaire", "arret"]


class MapData(TypedDict):
    """Data used to display a map."""

    titre: str
    points: list[MapPoint]
    chemin: list[list[float]]
    trace: Literal["gps", "approx"] | None
    note: str | None


class ChartData(TypedDict):
    """Data used to display a bar chart."""

    titre: str
    axe_libelle: str
    axe_valeur: str
    orientation: Literal["horizontale", "verticale"]
    donnees: list[dict[str, Any]]
    tronque: bool
    note: str | None


class TurnDetails(TypedDict):
    """Details associated with a response."""

    decision: dict[str, Any] | None
    agent: AgentRun | None
    entites_confirmees: list[dict[str, Any]]
    lieux: list[ResolvedPlace]
    carte: MapData | None
    graphique: ChartData | None
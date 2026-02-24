# Querying Roam Research

## Roam database

Roam Research stores its graph in **[Datomic](https://www.datomic.com/)/[DataScript](https://github.com/tonsky/datascript)**. Roam Research acts as a bridge between the frontend and backend by using _DataScript_ as a local "mirror" of a _Datomic_ backend. Both store data as **Datoms** -- atomic facts. Whether a piece of data is in the cloud or in your browser, it looks exactly the same. 

A datom is a 4-tuple of:
- **E (Entity ID):** The unique ID of a block.
- **A (Attribute):** The property (e.g., `:block/string` or `:block/children`).
- **V (Value):** The actual content or the ID of a child block.
- **T (Transaction ID):** The "when" and "who" of the change.

Every node in the Roam graph (page or block) is an *entity*; every property of that
node is an *attribute* asserted against it. 

![Roam database](./roam_database.png)

## Key Roam Attributes

These are the attributes most relevant to this project's queries and data model:

| Attribute | Present on | Notes |
|---|---|---|
| `:db/id` | all entities | Datomic internal id; **not stable** across exports |
| `:block/uid` | all entities | 9-char alphanumeric; **stable** identifier |
| `:node/title` | pages only | Distinguishes pages from blocks |
| `:block/string` | blocks only | Raw Markdown text of the block |
| `:block/order` | child blocks | Zero-based sibling position |
| `:block/heading` | heading blocks | 1, 2, or 3; absent means normal text |
| `:block/children` | blocks/pages | List of `IdObject` stubs (`:db/id` only) |
| `:block/parents` | blocks | All ancestor stubs up to page root |
| `:block/refs` | blocks | Pages/blocks referenced via `[[...]]` |
| `:block/page` | blocks | Containing page stub |
| `:entity/attrs` | some entities | Structured attribute assertions (`LinkObject`) |

The full attribute schema discovered from a live graph is in [roam-schema.md](./roam-schema.md)

## Datalog query language
_Datomic_/_DataScript_ use [Datalog](https://en.wikipedia.org/wiki/Datalog) as the query language. _Datalog_ is a syntactic subset of Prolog, which is commonly used to interact with **deductive dabases**.

## Datalog Query Structure

Queries follow standard Datomic Datalog syntax:

```
[:find  <find-spec>
 :in    $ <binding> ...      ; optional; $ is always the implicit db
 :where <clause> ...]
```

### Clauses

**Entity-attribute-value triple** — the fundamental constraint:

```
[?entity :attribute ?value]
```

- `?entity`, `?value` — logic variables (bound or free)
- `:attribute` — a namespaced keyword from the Roam schema (e.g. `:node/title`)
- `_` — wildcard; matches any entity/value without binding

**Built-in predicate** — called inside `[( ... )]`:

```
[(namespace ?attr) ?namespace]
```

Extracts the namespace portion of a keyword attribute (e.g. `:block/string` → `"block"`).

**Pull expression** — returns a map of attributes for a matched entity:

```
(pull ?entity [<pull-pattern>])
```

Common pull patterns used in this project:

| Pattern | Meaning |
|---|---|
| `[*]` | All attributes of the entity |
| `[:block/uid :block/string]` | Only those two attributes |

## Queries Used in This Project

### 1. Page fetch — `FetchRoamPage.DATALOG_PAGE_QUERY`

```datalog
[:find (pull ?page [*])
 :in $ ?title
 :where
 [?page :node/title ?title]]
```

- Input binding: `?title` — the exact page title string (passed as `args[1]`).
- Finds the entity whose `:node/title` equals the title, then pulls all its attributes.
- Returns `result[0][0]` — the full PullBlock dict stored in `RoamPage.pull_block`.
- Returns an empty `result` list (`[]`) when no page has that title → `FetchRoamPage.fetch`
  returns `None`.

### 2. Schema introspection — `FetchRoamSchema.DATALOG_SCHEMA_QUERY`

```datalog
[:find ?namespace ?attr
 :where
 [_ ?attr]
 [(namespace ?attr) ?namespace]]
```

- No input bindings; scans every attribute asserted on any entity (`_` wildcard).
- `(namespace ?attr)` extracts the namespace portion of each attribute keyword.
- Returns `[["block", :block/string], ["node", :node/title], ...]` — the full live schema.
- Results documented in `docs/roam-schema.md`.

### 3. Block fetch by page (experimental, in `test_roam_model.py`)

```datalog
[:find (pull ?block [:block/uid :block/string])
 :in $ [?title ?uid]
 :where
 [?page :block/children ?block]
 [?page :block/uid ?uid]]
 [?page :node/title ?title]]
```

- Input binding: `[?title ?uid]` — a **collection binding** (both values supplied together
  as a two-element list in `args[1]`).
- Finds direct child blocks of a page identified by both title and uid, pulling only
  `:block/uid` and `:block/string` for each child.
- Note: this query has a structural bug (mismatched brackets) and is not yet used in
  production code.

## Input Binding Forms

| `:in` syntax | `args` value | Meaning |
|---|---|---|
| `?scalar` | `"string"` or number | Single scalar bound to the variable |
| `[?a ?b]` | `["val-a", "val-b"]` | Tuple binding — both values supplied together |
| `[?x ...]` | `["v1", "v2", ...]` | Collection binding — query runs once per element |

The database reference `$` is always `args[0]` implicitly; explicit bindings start at
`args[1]`.

## Pull Result Shape and Normalization

`pull [*]` returns a flat dict with **namespaced keyword keys** — but Roam's Local API
strips the leading colon and namespace slash, returning plain string keys:

```json
{ "uid": "abc123xyz", "title": "My Page", "children": [{"id": 42}] }
```

Nested references (`:block/children`, `:block/refs`, `:block/page`, `:block/parents`) are
returned as **`IdObject` stubs** — `{"id": <db-id>}` — not fully pulled sub-entities.
Resolving stubs to stable UIDs requires a second query pass or a recursive pull pattern.

The `Id2UidMap` type (`dict[str, OrderedUid]`) in `roam_model.py` is built during the
normalization pass to resolve these stubs in a single pass, sorting children by
`:block/order`.

## Datalog Rules

Rules are named, reusable Horn clauses that enable recursive queries. Syntax:

```datalog
[(rule-name ?var ...)
 <body-clause> ...]
```

The `DATALOG_RULE` constant in `test_roam_model.py` shows the pattern:

```datalog
[(actor-movie ?name ?title)
    [?p :person/name ?name]
    [?m :movie/cast ?p]
    [?m :movie/title ?title]]
```

Rules are passed as an additional element of the `args` array and referenced in the
`:where` clause by name. They are the mechanism used for recursive graph traversal
(corresponding to `FollowLinksDirective.DEEP` in `roam_model.py`).

## API

Programmatically fetching (or exporting) content from Roam can only be done through the [Roam Alpha API](https://roamresearch.com/#/app/developer-documentation/page/tIaOPdXCj) if the graph is _encrypted_. The _Roam Alpha API_ is only accessible to [roam/js](https://roamresearch.com/#/app/developer-documentation/page/QE0bxjUwk) scripts that run within the Roam client. Because the client has access to the encryption key for the graph, so too does the _Roam Alpha API_, so that it can return clear-text content through its api. The [Roam Local API](https://roamresearch.com/#/app/developer-documentation/page/8ikgtLSXz) proxies the _Roam Alpha API_ through the running Roam Desktop app over HTTP.


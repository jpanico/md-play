"""YAML fixture for the 'Test Article' NodeNetwork.

Captured from a live ``FetchRoamNodes.fetch_by_page_title`` call against the
SCFH graph on 2026-03-01.  Serialised with ``yaml.dump(..., exclude_none=True,
default_flow_style=False, allow_unicode=True, sort_keys=False)``.
"""

TEST_ARTICLE_NODES_YAML: str = """\
- uid: yFUau9Cpg
  id: 4025
  time: 1771515468425
  user:
    id: 3
  string: Section 2.1.1
  order: 1
  children:
  - id: 4028
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3329
- uid: mPCzedeKx
  id: 3336
  time: 1770569707883
  user:
    id: 3
  string: '![A flower](https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2FSCFH%2F-9owRBegJ8.jpeg.enc?alt=media&token=9b673aae-8089-4a91-84df-9dac152a7f94)'
  order: 0
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3328
  - id: 3331
  - id: 3334
- uid: FL32hVyCv
  id: 4029
  time: 1771538823824
  user:
    id: 3
  string: 'AI assistant (Claude Opus 4.6): '
  order: 1
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3328
- uid: 0EgPyHSZi
  id: 3328
  time: 1770568919008
  user:
    id: 3
  string: Section 1
  order: 0
  heading: 2
  children:
  - id: 3331
  - id: 4029
  page:
    id: 3327
  open: true
  parents:
  - id: 3327
- uid: 40bvW14UU
  id: 3330
  time: 1770568926764
  user:
    id: 3
  string: Section 3
  order: 2
  heading: 2
  children:
  - id: 3333
  page:
    id: 3327
  open: true
  parents:
  - id: 3327
- uid: TaN67WqnA
  id: 3334
  time: 1771512875819
  user:
    id: 3
  string: illustration 1.1
  order: 0
  children:
  - id: 3336
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3328
  - id: 3331
- uid: wdMgyBiP9
  id: 3329
  time: 1770568922821
  user:
    id: 3
  string: Section 2
  order: 1
  heading: 2
  children:
  - id: 3332
  - id: 4025
  - id: 4026
  page:
    id: 3327
  open: true
  parents:
  - id: 3327
- uid: 3BX-iWc-p
  id: 3331
  time: 1770568958676
  user:
    id: 3
  string: Section 1.1
  order: 0
  heading: 3
  children:
  - id: 3334
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3328
- uid: bxkcECGwN
  id: 4028
  time: 1771536625311
  user:
    id: 3
  string: Section 2.1.1.1
  order: 0
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3329
  - id: 4025
- uid: drtANJYTg
  id: 3332
  time: 1770568965850
  user:
    id: 3
  string: Section 2.1
  order: 0
  heading: 3
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3329
- uid: 5f1ahOFdp
  id: 4026
  time: 1771513571056
  user:
    id: 3
  string: Section 2.1.2
  order: 2
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3329
- uid: 6olpFWiw1
  id: 3327
  time: 1770568893569
  user:
    id: 3
  children:
  - id: 3328
  - id: 3329
  - id: 3330
  title: Test Article
  sidebar: 18
- uid: JW5PswS6v
  id: 3333
  time: 1770568971504
  user:
    id: 3
  string: Section 3.1
  order: 0
  heading: 3
  page:
    id: 3327
  open: false
  parents:
  - id: 3327
  - id: 3330
"""

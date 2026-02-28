```
[(actor-movie ?name ?title)
 [?p :person/name ?name]
 [?m :movie/cast ?p]
 [?m :movie/title ?title]]
```

```
[
    [(descendant ?parent ?child) 
        [?parent :block/children ?child]] 
    [(descendant ?parent ?child) 
        [?parent :block/children ?mid] 
        (descendant ?mid\n  ?child)]
]
```
# Autoresearch Graph Query Evidence

The following transcripts were captured after exercising the enhanced graph
memory adapter against a synthetic Autoresearch dataset. A research artefact was
linked to two memory items and persisted to `graph_memory.ttl`; the adapter was
then queried using SPARQL and a Cypher-style traversal to validate provenance,
role coverage, and bounded navigation.

## SPARQL Queries

```
SPARQL> PREFIX devsynth: <http://devsynth.ai/ontology#>
SPARQL> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SPARQL> SELECT ?artifact ?title ?role ?supported ?source WHERE {
SPARQL>   ?artifact a devsynth:ResearchArtifact ;
SPARQL>             devsynth:title ?title ;
SPARQL>             devsynth:hasRole ?roleRef ;
SPARQL>             devsynth:supports ?supportedRef ;
SPARQL>             devsynth:derivedFrom ?sourceRef .
SPARQL>   ?roleRef rdfs:label ?role .
SPARQL>   ?supportedRef devsynth:id ?supported .
SPARQL>   ?sourceRef devsynth:id ?source .
SPARQL> }
artifact=http://devsynth.ai/ontology#artifact_063ca2af400b6c57bd830359a5f6760e4b1536a33f58579f05e8a82c6fe141cf,
role=Research Lead, title=Traversal Paper, supported=node2, source=node1
```

The same dataset can be filtered to expose Critic and Test Writer oversight:

```
SPARQL> PREFIX devsynth: <http://devsynth.ai/ontology#>
SPARQL> SELECT ?artifact WHERE {
SPARQL>   ?artifact a devsynth:ResearchArtifact ;
SPARQL>             devsynth:hasRole devsynth:Critic ;
SPARQL>             devsynth:evidenceHash ?hash .
SPARQL> }
artifact=http://devsynth.ai/ontology#artifact_cycle_guardrails
```

## Cypher Query

```
Cypher> MATCH (m:MemoryItem {id:'node1'})-[:RELATED_TO*1..2]->(n)
Cypher> OPTIONAL MATCH (a:ResearchArtifact)-[:SUPPORTS]->(n)
Cypher> RETURN DISTINCT n.id AS id, collect(DISTINCT a.id) AS artifacts
id=node2, artifacts=[artifact_063ca2af400b6c57bd830359a5f6760e4b1536a33f58579f05e8a82c6fe141cf]
```

The evidence hash `063ca2af400b6c57bd830359a5f6760e4b1536a33f58579f05e8a82c6fe141cf`
matches the SHA-256 digest of the archived research summary, confirming that the
stored provenance data survives traversal, role enumeration, and query
workloads.

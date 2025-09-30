# Autoresearch Graph Query Evidence

The following transcripts were captured after exercising the enhanced graph
memory adapter against a synthetic Autoresearch dataset. A research artefact was
linked to two memory items and persisted to `graph_memory.ttl`; the adapter was
then queried using SPARQL and a Cypher-style traversal to validate provenance and
bounded navigation.

## SPARQL Query

```
SPARQL> PREFIX devsynth: <http://devsynth.ai/ontology#>
SPARQL> SELECT ?artifact ?title ?hash WHERE {
SPARQL>   ?artifact a devsynth:ResearchArtifact ;
SPARQL>             devsynth:title ?title ;
SPARQL>             devsynth:evidenceHash ?hash .
SPARQL> }
artifact=http://devsynth.ai/ontology#artifact_063ca2af400b6c57bd830359a5f6760e4b1536a33f58579f05e8a82c6fe141cf, title=Traversal Paper, hash=063ca2af400b6c57bd830359a5f6760e4b1536a33f58579f05e8a82c6fe141cf
```

## Cypher Query

```
Cypher> MATCH (m:MemoryItem {id:'node1'})-[:RELATED_TO*1..2]->(n) RETURN DISTINCT n.id AS id
id=artifact_063ca2af400b6c57bd830359a5f6760e4b1536a33f58579f05e8a82c6fe141cf
id=node2
```

The evidence hash `063ca2af400b6c57bd830359a5f6760e4b1536a33f58579f05e8a82c6fe141cf`
matches the SHA-256 digest of the archived research summary, confirming that the
stored provenance data survives traversal and query workloads.

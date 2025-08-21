# Performance and Scalability

## Empirical Results

Baseline workload of 100000 operations completed in approximately 0.0112 seconds (≈8.9e6 ops/s).

Scalability measurements:

| workload | duration (s) | throughput (ops/s) |
|---------:|-------------:|-------------------:|
|   10000  |     0.00106  |      9.40e6        |
|  100000  |     0.01093  |      9.15e6        |
| 1000000  |     0.11344  |      8.82e6        |

## Scalability Formula

Observed durations scale linearly with workload.

T ≈ 1.10e-7 × N

where T is time in seconds and N is the number of operations. This corresponds to an approximate throughput of 9.1e6 operations per second.

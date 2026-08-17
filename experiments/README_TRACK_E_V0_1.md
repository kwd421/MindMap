# Track E v0.1 experiment source

The exact standard-library experiment is committed as:

```text
track_e_fault_observability_v0_1.py.gz
```

Decompress and run:

```bash
gzip -dk experiments/track_e_fault_observability_v0_1.py.gz
python experiments/track_e_fault_observability_v0_1.py \
  --renamings 20 \
  --output-dir results/track_e_fault_observability_v0_1
```

The uncompressed script SHA-256 is recorded in `results/track_e_fault_observability_v0_1/metadata.json`.

The compressed form is temporary because the connector used to publish this branch has a practical text-payload limit. A later repository-side cleanup may replace it with the ordinary `.py` source without changing the recorded script hash or results.
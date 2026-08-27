from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "audit_gatemem_official.py"
)
SPEC = importlib.util.spec_from_file_location("audit_gatemem_official", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load audit module from {MODULE_PATH}")
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class JsonInventoryTest(unittest.TestCase):
    def test_counts_keys_without_using_json_values_as_counter_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_root = Path(temporary_directory)
            data_file = data_root / "medical" / "sample.json"
            data_file.parent.mkdir(parents=True)
            data_file.write_text(
                json.dumps(
                    {
                        "episode_id": "episode-1",
                        "checkpoints": [
                            {"checkpoint_id": "checkpoint-1", "query": "first"},
                            {"checkpoint_id": "checkpoint-2", "query": "second"},
                        ],
                        "metadata": {"label": "alpha", "count": 7},
                    }
                ),
                encoding="utf-8",
            )

            inventory = AUDIT._json_inventory([data_file], data_root)

        self.assertEqual(inventory["parse_failures"], [])
        self.assertEqual(inventory["files_by_domain"], {"medical": 1})
        self.assertEqual(inventory["unique_explicit_checkpoint_ids"], 2)
        self.assertEqual(inventory["checkpoint_container_total"], 2)
        key_counts = dict(inventory["most_common_keys"])
        self.assertEqual(key_counts["checkpoint_id"], 2)
        self.assertEqual(key_counts["query"], 2)
        self.assertEqual(key_counts["episode_id"], 1)
        self.assertEqual(key_counts["label"], 1)
        self.assertEqual(key_counts["count"], 1)


if __name__ == "__main__":
    unittest.main()

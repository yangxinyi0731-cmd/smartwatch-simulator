from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.early_risk.contracts import ResearchRecordBundle


def main() -> None:
    parser = argparse.ArgumentParser(description="校验已批准离线夹具的时间与身份合同。")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    bundle = ResearchRecordBundle.model_validate(payload)
    print(
        json.dumps(
            {
                "bundle_id": bundle.bundle_id,
                "segment_count": len(bundle.segments),
                "annotation_count": len(bundle.annotations),
                "accepted_for_second_scale": all(
                    segment.quality.accepted_for_second_scale
                    for segment in bundle.segments
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

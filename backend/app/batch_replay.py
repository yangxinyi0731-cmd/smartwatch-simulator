from __future__ import annotations

import asyncio
from contextlib import suppress

from .database import BatchReplayTaskRecord, Database
from .replay import build_replay_preview
from .schemas import (
    BatchReplayItem,
    BatchReplayTaskResponse,
    BatchReplayTaskSummary,
)


def summarize_batch_task(record: BatchReplayTaskRecord) -> BatchReplayTaskSummary:
    return BatchReplayTaskSummary(
        task_id=record.task_id,
        client_request_id=record.client_request_id,
        state=record.state,
        total_count=record.total_count,
        completed_count=record.completed_count,
        failed_count=record.failed_count,
        recovery_count=record.recovery_count,
        current_case_id=record.current_case_id,
        error_message=record.error_message,
        progress=(record.completed_count + record.failed_count) / record.total_count,
        created_at=record.created_at,
        updated_at=record.updated_at,
        completed_at=record.completed_at,
    )


def batch_task_response(record: BatchReplayTaskRecord) -> BatchReplayTaskResponse:
    summary = summarize_batch_task(record)
    return BatchReplayTaskResponse(
        **summary.model_dump(),
        items=tuple(
            BatchReplayItem(
                sequence=item.sequence,
                case_id=item.case_id,
                model_kind=item.model_kind,
                state=item.state,
                result_summary=item.result_summary,
                error_message=item.error_message,
                started_at=item.started_at,
                completed_at=item.completed_at,
            )
            for item in record.items
        ),
    )


def _preview_summary(preview) -> dict[str, object]:
    base: dict[str, object] = {
        "truth_category": preview.case.truth_category.value,
        "duration_ms": preview.duration_ms,
        "ground_truth_event_count": len(preview.ground_truth_events),
    }
    if preview.activity_result is not None:
        return {
            **base,
            "model_kind": "ACTIVITY_RECOGNITION",
            "manifest_id": preview.activity_result.manifest_id,
            "predicted_label": preview.activity_result.predicted_label,
            "probabilities": preview.activity_result.probabilities.model_dump(),
            "meaning": "四类活动候选概率；不是医学状态。",
        }
    if preview.routine_profile is not None:
        anomaly_count = sum(
            assessment.status != "WITHIN_ROUTINE"
            for day in preview.routine_days
            for assessment in day.assessments
        )
        return {
            **base,
            "model_kind": "ROUTINE_ANOMALY",
            "profile_id": preview.routine_profile.profile_id,
            "history_days": preview.routine_profile.history_days,
            "event_count": preview.routine_profile.event_count,
            "rule_deviation_count": anomaly_count,
            "meaning": "确定性合成规律规则结果；不是准确率或医学风险。",
        }
    if preview.fall_manifest_id is not None:
        max_probability = max(
            (window.fall_probability for window in preview.fall_windows),
            default=0.0,
        )
        return {
            **base,
            "model_kind": "FALL_DETECTION",
            "manifest_id": preview.fall_manifest_id,
            "window_count": len(preview.fall_windows),
            "candidate_alarm_episode_count": len(preview.fall_alarm_episodes),
            "max_fall_candidate_probability": max_probability,
            "meaning": "候选告警行为摘要；受控模拟跌倒不是真实老人跌倒。",
        }
    raise ValueError("案例没有可保存的独立模型结果。")


def run_batch_replay_task(database: Database, task_id: str) -> BatchReplayTaskRecord:
    try:
        while True:
            item = database.claim_next_batch_replay_item(task_id)
            if item is None:
                break
            try:
                bundle = database.get_case_runtime_bundle(item.case_id)
                if bundle is None:
                    raise ValueError("案例不存在。")
                preview = build_replay_preview(bundle)
                summary = _preview_summary(preview)
                if summary["model_kind"] != item.model_kind:
                    raise ValueError("案例允许模型与实际回放模型不一致。")
                database.finish_batch_replay_item(
                    task_id=task_id,
                    sequence=item.sequence,
                    result_summary=summary,
                )
            except (OSError, RuntimeError, ValueError, KeyError):
                database.finish_batch_replay_item(
                    task_id=task_id,
                    sequence=item.sequence,
                    error_message="案例回放失败；请核对本地来源文件、哈希和模型资产。",
                )
        return database.finalize_batch_replay_task(task_id)
    except Exception:
        database.fail_batch_replay_task(
            task_id,
            "批量任务执行中断；可查看已完成项并重新创建任务。",
        )
        raise


async def batch_replay_worker(database: Database, wake_event: asyncio.Event) -> None:
    while True:
        task_id = await asyncio.to_thread(database.claim_next_batch_replay_task)
        if task_id is None:
            wake_event.clear()
            try:
                await asyncio.wait_for(wake_event.wait(), timeout=1.0)
            except TimeoutError:
                pass
            continue
        with suppress(Exception):
            await asyncio.to_thread(run_batch_replay_task, database, task_id)

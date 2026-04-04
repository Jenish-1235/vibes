from __future__ import annotations

import json
import logging
from pathlib import Path

import anthropic

from awscope.config import get_anthropic_settings
from awscope.models import AwsResource, ClaudeBatch, ResourceGroup

log = logging.getLogger(__name__)

_PROMPT_FILE = Path(__file__).parent / "prompts" / "system_grouping.md"
_BATCH_SIZE = 200
_MISCELLANEOUS = "miscellaneous"


def _load_system_prompt() -> str:
    if not _PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {_PROMPT_FILE}\n"
            "Ensure awscope/prompts/system_grouping.md exists."
        )
    return _PROMPT_FILE.read_text()


def _build_user_message(resources: list[AwsResource]) -> str:
    items = [
        {
            "resource_id": r.resource_id,
            "name": r.name,
            "resource_type": r.resource_type,
            "tags": r.tags,
        }
        for r in resources
    ]
    return json.dumps(items)


def _parse_response(raw: str, resource_ids: set[str]) -> tuple[dict[str, str], bool]:
    try:
        # Strip markdown fences if Claude wrapped the response anyway
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        parsed = json.loads(text)
        mapping = {item["resource_id"]: item["group_name"] for item in parsed}
        # Any resource_id missing from response → miscellaneous
        for rid in resource_ids:
            if rid not in mapping:
                log.warning("resource_id %r missing from Claude response — assigning miscellaneous", rid)
                mapping[rid] = _MISCELLANEOUS
        return mapping, True
    except Exception as e:
        log.warning("Failed to parse Claude response (%s) — assigning entire batch to miscellaneous", e)
        return {rid: _MISCELLANEOUS for rid in resource_ids}, False


def group_resources(
    resources: list[AwsResource],
    progress_callback=None,
) -> tuple[list[ResourceGroup], list[ClaudeBatch]]:
    settings = get_anthropic_settings()

    if not settings["api_key"]:
        log.warning("ANTHROPIC_API_KEY not set — skipping AI grouping, assigning all to miscellaneous")
        group = ResourceGroup(group_name=_MISCELLANEOUS, resources=list(resources))
        return [group], []

    system_prompt = _load_system_prompt()
    client = anthropic.Anthropic(
        api_key=settings["api_key"],
        **({"base_url": settings["base_url"]} if settings["base_url"] else {}),
    )
    model = settings["model"]

    # Split into batches
    batches = [resources[i: i + _BATCH_SIZE] for i in range(0, len(resources), _BATCH_SIZE)]
    mapping: dict[str, str] = {}
    claude_batches: list[ClaudeBatch] = []

    for batch_num, batch in enumerate(batches, 1):
        if progress_callback:
            progress_callback(f"Grouping batch {batch_num}/{len(batches)} ({len(batch)} resources)...")

        user_message = _build_user_message(batch)
        resource_ids = {r.resource_id for r in batch}

        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            raw_response = response.content[0].text
            batch_mapping, parsed_ok = _parse_response(raw_response, resource_ids)
        except Exception as e:
            log.warning("Claude API call failed for batch %d: %s — assigning to miscellaneous", batch_num, e)
            raw_response = ""
            batch_mapping = {rid: _MISCELLANEOUS for rid in resource_ids}
            parsed_ok = False

        mapping.update(batch_mapping)
        claude_batches.append(ClaudeBatch(
            batch_number=batch_num,
            prompt_sent=user_message,
            raw_response=raw_response,
            parsed=parsed_ok,
            resource_count=len(batch),
        ))

    # Assemble ResourceGroups
    groups_map: dict[str, list[AwsResource]] = {}
    for resource in resources:
        group_name = mapping.get(resource.resource_id, _MISCELLANEOUS)
        groups_map.setdefault(group_name, []).append(resource)

    groups = [
        ResourceGroup(group_name=name, resources=members)
        for name, members in sorted(groups_map.items())
    ]
    return groups, claude_batches

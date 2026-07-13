"""apply: replace text inside cloned slide shapes while keeping frames editable.

``_set_container_text`` is the shared text-writing primitive and is also reused
by ``table_fill`` for table-cell edits.
"""

from __future__ import annotations

import copy
from typing import Any
from xml.etree import ElementTree as ET

from .ooxml import NS, _qn, _shape_identity, _text_containers
from .selectors import _replacement_text


def _new_paragraph_run(paragraph: ET.Element) -> ET.Element:
    """Create an ``a:r`` positioned before ``a:endParaRPr`` (schema: endParaRPr is last).

    A trailing run appended after ``a:endParaRPr`` is dropped by PowerPoint's
    renderer, silently losing the paragraph text. ``endParaRPr`` also declares the
    formatting intended for text typed into the empty paragraph, so it is carried
    over as the new run's ``rPr``.
    """
    run = ET.Element(_qn(NS["a"], "r"))
    end_pr = paragraph.find("a:endParaRPr", NS)
    if end_pr is not None:
        r_pr = copy.deepcopy(end_pr)
        r_pr.tag = _qn(NS["a"], "rPr")
        run.append(r_pr)
        paragraph.insert(list(paragraph).index(end_pr), run)
    else:
        paragraph.append(run)
    return run


def _shape_key_maps(slide_root: ET.Element, source_slide: int) -> dict[str, ET.Element]:
    maps: dict[str, ET.Element] = {}
    for order, container in enumerate(_text_containers(slide_root), start=1):
        shape_id, shape_name = _shape_identity(container, order)
        maps[f"slot_id:s{source_slide:02d}_sh{shape_id}"] = container
        maps[f"shape_id:{shape_id}"] = container
        if shape_name:
            maps[f"shape_name:{shape_name}"] = container
    return maps


def _ensure_text_nodes(container: ET.Element) -> list[ET.Element]:
    text_nodes = container.findall(".//a:t", NS)
    if text_nodes:
        return text_nodes
    tx_body = container.find(".//p:txBody", NS)
    if tx_body is None:
        tx_body = container.find(".//a:txBody", NS)
    if tx_body is None:
        return []
    paragraph = tx_body.find("a:p", NS)
    if paragraph is None:
        paragraph = ET.SubElement(tx_body, _qn(NS["a"], "p"))
    run = paragraph.find("a:r", NS)
    if run is None:
        run = _new_paragraph_run(paragraph)
    text_node = run.find("a:t", NS)
    if text_node is None:
        text_node = ET.SubElement(run, _qn(NS["a"], "t"))
    return [text_node]


def _ensure_paragraph_text_node(paragraph: ET.Element) -> list[ET.Element]:
    text_nodes = paragraph.findall(".//a:t", NS)
    if text_nodes:
        return text_nodes
    run = paragraph.find("a:r", NS)
    if run is None:
        run = _new_paragraph_run(paragraph)
    text_node = run.find("a:t", NS)
    if text_node is None:
        text_node = ET.SubElement(run, _qn(NS["a"], "t"))
    return [text_node]


def _set_paragraph_text(paragraph: ET.Element, text: str) -> None:
    text_nodes = _ensure_paragraph_text_node(paragraph)
    text_nodes[0].text = text
    for node in text_nodes[1:]:
        node.text = ""


def _set_container_text(container: ET.Element, text: str) -> None:
    lines = text.splitlines() or [""]
    paragraphs = container.findall(".//a:p", NS)
    # Map replacement lines onto text-bearing paragraphs only. Run-less paragraphs
    # are spacer lines (e.g. 3pt gap paragraphs between content blocks) — the
    # analyzer's paragraph_count never included them, so plan lines must not land
    # there; writing into one renders the line at the spacer's tiny end-paragraph
    # size and shifts every following line off its intended formatting.
    text_paragraphs = [p for p in paragraphs if p.find("a:r", NS) is not None] or paragraphs
    if len(lines) > 1 and text_paragraphs:
        for index, paragraph in enumerate(text_paragraphs):
            if index < len(lines):
                _set_paragraph_text(paragraph, lines[index])
            else:
                _set_paragraph_text(paragraph, "")
        if len(lines) > len(text_paragraphs):
            _set_paragraph_text(text_paragraphs[-1], "\n".join(lines[len(text_paragraphs) - 1 :]))
        return

    text_nodes = _ensure_text_nodes(container)
    if not text_nodes:
        raise RuntimeError("Matched shape does not contain a text body")
    if len(lines) <= len(text_nodes):
        for index, node in enumerate(text_nodes):
            node.text = lines[index] if index < len(lines) else ""
        return
    text_nodes[0].text = text
    for node in text_nodes[1:]:
        node.text = ""


def _apply_replacements_to_slide(
    slide_root: ET.Element,
    *,
    source_slide: int,
    replacements: list[dict[str, Any]],
) -> None:
    maps = _shape_key_maps(slide_root, source_slide)
    errors: list[str] = []
    for replacement in replacements:
        selectors = []
        if replacement.get("slot_id"):
            selectors.append(f"slot_id:{replacement['slot_id']}")
        if replacement.get("shape_id"):
            selectors.append(f"shape_id:{replacement['shape_id']}")
        if replacement.get("shape_name"):
            selectors.append(f"shape_name:{replacement['shape_name']}")
        container = next((maps[key] for key in selectors if key in maps), None)
        if container is None:
            if replacement.get("optional"):
                continue
            errors.append(", ".join(selectors) or "<missing selector>")
            continue
        _set_container_text(container, _replacement_text(replacement))
    if errors:
        raise RuntimeError(f"Missing replacement target(s) on slide {source_slide}: {'; '.join(errors)}")

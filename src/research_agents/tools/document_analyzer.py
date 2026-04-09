"""Tool handlers for the Document Analyzer agent."""

from __future__ import annotations

import json

from research_agents.services.container import ServiceContainer
from research_agents.services.document_store import DocumentNotFoundError


def handle_parse_document(input_dict: dict, services: ServiceContainer) -> str:
    doc_id = input_dict.get("doc_id", "")
    if not doc_id:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "parse_document",
            "message": "doc_id is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        doc = services.document_store.get_document(doc_id)
        return json.dumps({
            "status": "success",
            "data": {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "section_count": len(doc.sections),
                "sections": [{"heading": s.heading} for s in doc.sections],
                "citation_count": len(doc.citations),
                "reliability": doc.reliability.value,
            },
        })
    except DocumentNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": f"document_store:{doc_id}",
            "message": f"Document not found: {doc_id}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })


def handle_extract_sections(input_dict: dict, services: ServiceContainer) -> str:
    doc_id = input_dict.get("doc_id", "")
    heading = input_dict.get("heading", "")
    if not doc_id:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "extract_sections",
            "message": "doc_id is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        doc = services.document_store.get_document(doc_id)
        sections = doc.sections
        if heading:
            heading_lower = heading.lower()
            sections = [s for s in sections if heading_lower in s.heading.lower()]
        return json.dumps({
            "status": "success",
            "data": [
                {
                    "heading": s.heading,
                    "content": s.content,
                    "claims": s.claims,
                }
                for s in sections
            ],
        })
    except DocumentNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": f"document_store:{doc_id}",
            "message": f"Document not found: {doc_id}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })


def handle_identify_claims(input_dict: dict, services: ServiceContainer) -> str:
    doc_id = input_dict.get("doc_id", "")
    if not doc_id:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "identify_claims",
            "message": "doc_id is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        doc = services.document_store.get_document(doc_id)
        all_claims = []
        for section in doc.sections:
            all_claims.extend(section.claims)
        return json.dumps({
            "status": "success",
            "data": {"doc_id": doc.doc_id, "title": doc.title, "claims": all_claims},
        })
    except DocumentNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": f"document_store:{doc_id}",
            "message": f"Document not found: {doc_id}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })


def handle_check_citations(input_dict: dict, services: ServiceContainer) -> str:
    doc_id = input_dict.get("doc_id", "")
    if not doc_id:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "check_citations",
            "message": "doc_id is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        doc = services.document_store.get_document(doc_id)
        return json.dumps({
            "status": "success",
            "data": {
                "doc_id": doc.doc_id,
                "citations": doc.citations,
                "citation_count": len(doc.citations),
                "issues": [] if doc.citations else ["No citations found"],
            },
        })
    except DocumentNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": f"document_store:{doc_id}",
            "message": f"Document not found: {doc_id}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })

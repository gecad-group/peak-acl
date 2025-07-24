# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

# src/peak_acl/fipa_am.py
"""
Python objects for the FIPA Agent Management ontology (FIPA-AM) and helpers to
serialize/deserialize them to/from the SL0 subset handled by ``peak_acl.sl0``.

This is a convenience layer on top of the ``sl0`` module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from .message.aid import AgentIdentifier
from . import sl0


# ------------------------------------------------------------------ #
# High-level dataclasses (external API)
# ------------------------------------------------------------------ #
@dataclass
class Property:
    """Simple name/value pair used inside :class:`ServiceDescription`."""
    name: str
    value: str


@dataclass
class ServiceDescription:
    """Service descriptor in FIPA-AM terms."""
    name: Optional[str] = None
    type: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    ontologies: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)


@dataclass
class AgentDescription:
    """Agent descriptor (wrapper around an :class:`AgentIdentifier`)."""
    name: Optional[AgentIdentifier] = None
    languages: List[str] = field(default_factory=list)
    ontologies: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    ownership: List[str] = field(default_factory=list)
    services: List[ServiceDescription] = field(default_factory=list)


# ------------------------------------------------------------------ #
# Convenience constructors
# ------------------------------------------------------------------ #
def build_agent_description(
    *,
    aid: AgentIdentifier,
    services: Sequence[ServiceDescription] = (),
    languages: Sequence[str] = (),
    ontologies: Sequence[str] = (),
    protocols: Sequence[str] = (),
    ownership: Sequence[str] = (),
) -> AgentDescription:
    """Create an :class:`AgentDescription` from simple sequences."""
    return AgentDescription(
        name=aid,
        services=list(services),
        languages=list(languages),
        ontologies=list(ontologies),
        protocols=list(protocols),
        ownership=list(ownership),
    )


# ------------------------------------------------------------------ #
# ALTO -> SL0 conversion
# ------------------------------------------------------------------ #
def _svc_to_sl0(sd: ServiceDescription) -> sl0.ServiceDescription:
    """Internal: convert high-level service to SL0 structure."""
    return sl0.ServiceDescription(
        name=sd.name,
        type=sd.type,
        languages=list(sd.languages),
        ontologies=list(sd.ontologies),
        protocols=list(sd.protocols),
        properties=[(p.name, p.value) for p in sd.properties],
    )


def _ad_to_sl0(ad: AgentDescription) -> sl0.DfAgentDescription:
    """Internal: convert high-level agent description to SL0 structure."""
    return sl0.DfAgentDescription(
        name=ad.name,
        services=[_svc_to_sl0(s) for s in ad.services],
        languages=list(ad.languages),
        ontologies=list(ad.ontologies),
        protocols=list(ad.protocols),
        ownership=list(ad.ownership),
    )


def render_register_content(
    df_aid: AgentIdentifier,
    agent_desc: AgentDescription,
) -> str:
    """
    Build an SL0 string *without quotes* and *without outer parentheses*; the
    ACL serializer will wrap it in a ContentElementList.

    Returns
    -------
    str
        Serialized SL0 action for ``(register ...)``.
    """
    inner = sl0.Action(actor=df_aid, act=sl0.Register(_ad_to_sl0(agent_desc)))
    return sl0.dumps(inner)


# ------------------------------------------------------------------ #
# SL0 -> ALTO conversion
# ------------------------------------------------------------------ #
def _svc_from_sl0(sd: sl0.ServiceDescription) -> ServiceDescription:
    """Internal: convert SL0 service to high-level object."""
    return ServiceDescription(
        name=sd.name,
        type=sd.type,
        languages=list(sd.languages),
        ontologies=list(sd.ontologies),
        protocols=list(sd.protocols),
        properties=[Property(n, v) for (n, v) in sd.properties],
    )


def _ad_from_sl0(ad: sl0.DfAgentDescription) -> AgentDescription:
    """Internal: convert SL0 agent description to high-level object."""
    return AgentDescription(
        name=ad.name,
        services=[_svc_from_sl0(s) for s in ad.services],
        languages=list(ad.languages),
        ontologies=list(ad.ontologies),
        protocols=list(ad.protocols),
        ownership=list(ad.ownership),
    )


def from_sl0(obj):
    """
    Convert an SL0 AST node (DfAgentDescription, Result, etc.) into the
    corresponding high-level dataclasses when applicable.

    Returns
    -------
    AgentDescription | ServiceDescription | list[AgentDescription] | Any
        Converted object(s) or the original ``obj`` if no conversion applied.
    """
    if isinstance(obj, sl0.DfAgentDescription):
        return _ad_from_sl0(obj)
    if isinstance(obj, sl0.ServiceDescription):
        return _svc_from_sl0(obj)
    if isinstance(obj, sl0.Result):
        # DF search usually returns Result(_, value=(set ...dfads...))
        value = obj.value
        if isinstance(value, list):
            ads = []
            for v in value:
                v = from_sl0(v)
                if isinstance(v, AgentDescription):
                    ads.append(v)
            return ads
        v2 = from_sl0(value)
        return [v2] if isinstance(v2, AgentDescription) else v2
    return obj

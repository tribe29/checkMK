#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import copy
from typing import cast

from cmk.utils.type_defs import AgentRawDataSection, SectionName

from cmk.fetchers.cache import PersistedSections


class MockStore:
    def __init__(self, data):
        super().__init__()
        self._data = data

    def store(self, data):
        self._data = copy.copy(data)

    def load(self):
        return copy.copy(self._data)


class TestPersistedSections:
    def test_from_sections(self):
        section_a = SectionName("section_a")
        content_a = [["first", "line"], ["second", "line"]]
        section_b = SectionName("section_b")
        content_b = [["third", "line"], ["forth", "line"]]
        sections = {section_a: content_a, section_b: content_b}
        cached_at = 69
        fetch_interval = 42
        interval_lookup = {section_a: fetch_interval, section_b: None}

        persisted_sections = PersistedSections[AgentRawDataSection].from_sections(
            sections,
            interval_lookup,
            cached_at=cached_at,
        )

        assert persisted_sections == {  # type: ignore[comparison-overlap]
            section_a: (cached_at, fetch_interval, content_a)
        }

    def test_update_and_store_without_persisted(self):
        # having functions here is a bit redundant with the copy.copy above,
        # but better safe than sorry.
        stored = lambda: {SectionName("foo"): (0, 1, cast(AgentRawDataSection, []))}

        store = MockStore(stored())
        persisted_sections = PersistedSections[AgentRawDataSection]({})

        assert persisted_sections != store.load()

        persisted_sections.update_and_store(store, keep_outdated=True)  # type: ignore[arg-type]

        assert persisted_sections == store.load()
        assert persisted_sections == PersistedSections[AgentRawDataSection](stored())

    def test_update_and_store_without_store(self):
        # having functions here is a bit redundant with the copy.copy above,
        # but better safe than sorry.
        persisted = lambda: {SectionName("foo"): (0, 1, cast(AgentRawDataSection, []))}

        store = MockStore({})
        persisted_sections = PersistedSections[AgentRawDataSection](persisted())

        assert persisted_sections != store.load()

        persisted_sections.update_and_store(store, keep_outdated=True)  # type: ignore[arg-type]

        assert persisted_sections == store.load()
        assert persisted_sections == PersistedSections[AgentRawDataSection](persisted())

    def test_update_and_store_keeps_new(self):
        # having functions here is a bit redundant with the copy.copy above,
        # but better safe than sorry.
        stored = lambda: {SectionName("foo"): (0, 1, cast(AgentRawDataSection, []))}
        persisted = lambda: {SectionName("foo"): (1, 2, cast(AgentRawDataSection, []))}

        store = MockStore(stored())
        persisted_sections = PersistedSections[AgentRawDataSection](persisted())

        assert persisted_sections != store.load()

        persisted_sections.update_and_store(store, keep_outdated=True)  # type: ignore[arg-type]

        assert persisted_sections == store.load()
        assert persisted_sections == PersistedSections[AgentRawDataSection](persisted())

    def test_update_and_store_accumulate(self):
        # having functions here is a bit redundant with the copy.copy above,
        # but better safe than sorry.
        stored = lambda: {SectionName("foo"): (0, 1, cast(AgentRawDataSection, []))}
        persisted = lambda: {SectionName("bar"): (1, 2, cast(AgentRawDataSection, []))}
        acc = stored()
        acc.update(persisted())

        store = MockStore(stored())
        persisted_sections = PersistedSections[AgentRawDataSection](persisted())

        assert persisted_sections != store.load()

        persisted_sections.update_and_store(store, keep_outdated=True)  # type: ignore[arg-type]

        assert persisted_sections == store.load()
        assert persisted_sections == PersistedSections[AgentRawDataSection](acc)
        assert len(acc) == 2
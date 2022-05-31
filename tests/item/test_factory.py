# AutoTransform
# Large scale, component based code modification library
#
# Licensed under the MIT License <http://opensource.org/licenses/MIT>
# SPDX-License-Identifier: MIT
# Copyright (c) 2022-present Nathan Rockenbach <http://github.com/nathro>

# @black_format

"""Tests that the Item's factory is correctly setup."""

import json
from typing import Dict, List

from autotransform.item.base import FACTORY, Item, ItemName
from autotransform.item.file import FileItem


def test_all_enum_values_present():
    """Ensures that all values from the enum are present in the factory map,
    and only enum values are present."""

    missing_values = [
        item_name for item_name in ItemName if item_name not in FACTORY.get_components()
    ]
    assert not missing_values, "Names missing from factory: " + ", ".join(missing_values)

    extra_values = [
        item_name for item_name in FACTORY.get_components() if item_name not in ItemName
    ]
    assert not extra_values, "Extra names in factory: " + ", ".join(extra_values)


def test_fetching_components():
    """Ensures that all components can be fetched correctly."""

    for component_name in FACTORY.get_components():
        component_class = FACTORY.get_class(component_name)
        assert (
            component_class.name == component_name
        ), f"Component {component_name} has wrong name {component_class.name}"

    for component_name in FACTORY.get_custom_components(strict=True):
        component_class = FACTORY.get_class(component_name)
        assert (
            f"custom/{component_class.name}" == component_name
        ), f"Component {component_name} has wrong name {component_class.name}"


def test_encoding_and_decoding():
    """Tests the encoding and decoding of components."""

    test_components: Dict[ItemName, List[Item]] = {
        ItemName.FILE: [
            FileItem(key="foo"),
            FileItem(key="foo", extra_data={"body": "bar"}),
        ],
        ItemName.GENERIC: [
            Item(key="foo"),
            Item(key="foo", extra_data={"body": "bar"}),
        ],
    }

    for name in ItemName:
        assert name in test_components, f"No test components for Item {name}"

    for name, components in test_components.items():
        assert name in ItemName, f"{name} is not a valid ItemName"
        for component in components:
            assert component.name == name, f"Testing item of name {component.name} for name {name}"
            assert (
                FACTORY.get_instance(json.loads(json.dumps(component.bundle()))) == component
            ), f"Component {component} does not bundle and unbundle correctly"

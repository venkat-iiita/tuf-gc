# Copyright 2020, New York University and the TUF contributors
# SPDX-License-Identifier: MIT OR Apache-2.0

# *****************Garbage Collection******************

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from copy import copy, deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import ClassVar

from securesystemslib import exceptions as sslib_exceptions
from securesystemslib import hash as sslib_hash

from tests import utils
from tuf.api import exceptions
from tuf.api.dsse import SimpleEnvelope
from tuf.api.metadata import (
    TOP_LEVEL_ROLE_NAMES,
    DelegatedRole,
    Delegations,
    Metadata,
    MetaFile,
    Root,
    RootVerificationResult,
    Signature,
    Snapshot,
    SuccinctRoles,
    TargetFile,
    Targets,
    Timestamp,
    VerificationResult,
)


class Target:
    def __init__(self, delete: bool = False, filename: str = ""):
        self.delete = delete
        self.filename = filename
    def __str__(self):
        return f"{self.filename}, {self.delete}"

class TargetsMetadata:
    def __init__(self, version: int = 0, targets: Targets = None, delete: bool = False, filename: str = ""):
        self.version = version
        self.targets = targets or dict()
        self.delete = delete
        self.filename = filename
    def get_targets(self):
        return self.targets
    def __str__(self):
        return f"{self.filename}, {self.delete}"


expired_snapshots = {}
unexpired_snapshots = {}


def sorted_file(directory: str):
    wildcard = "snapshot"
    with os.scandir(directory) as entries:
        matching_entries = [
            entry for entry in entries if entry.is_file() and wildcard in entry.name
        ]
        sorted_entries = sorted(matching_entries, key=lambda entry: entry.name, reverse=True)
        sorted_items = [entry.name for entry in sorted_entries]
    return sorted_items

def day_difference(time_now: datetime, metatime: datetime) -> int:
    diff_days = time_now - metatime
    return diff_days.days


def mark(threshold: int) -> None:
    #TODO - uncomment the following line for the automatic path
    #path = os.path.join(self.repo_dir, "metadata")
    #TODO - Delete following line for the automatic path
    path = "/home/iiita/supplychain/python-tuf/examples/manual_repo/tmpsp2y1znf"
    global expired_snapshots
    sorted_items = sorted_file(path)
    time_now = datetime.now(timezone.utc)
    for item in sorted_items:
        snapshot = Metadata[Snapshot].from_file(os.path.join(path, item)).signed
        snapshot_expiry = snapshot.expires
        snapshot_version = snapshot.version
        snapshot_days_diff = day_difference(time_now, snapshot_expiry)
        if(snapshot_days_diff > threshold):
            expired_snapshots[snapshot_version] = {}
            for targets_in_snapshot in snapshot.meta:
                targets_meta = Metadata[Targets].from_file(os.path.join(path, targets_in_snapshot)).signed
                targets_expiry = targets_meta.expires
                targets_version = targets_meta.version
                targets_days_diff = day_difference(time_now, targets_expiry)
                if(targets_days_diff > threshold):
                    expired_snapshots[snapshot_version][targets_in_snapshot] = TargetsMetadata(targets_version, {}, True, targets_in_snapshot)
                    for targets_file in targets_meta.targets:
                        expired_snapshots[snapshot_version][targets_in_snapshot].targets[targets_file] =  Target(True, targets_file)
                else:
                    expired_snapshots[snapshot_version][targets_in_snapshot] = TargetsMetadata(targets_version, {}, False, targets_in_snapshot)
                    for targets_file in targets_meta.targets:
                        expired_snapshots[snapshot_version][targets_in_snapshot].targets[targets_file] =  Target(False, targets_file)
        else:
            unexpired_snapshots[snapshot_version] = {}
            for targets_in_snapshot in snapshot.meta:
                targets_meta = Metadata[Targets].from_file(os.path.join(path, targets_in_snapshot)).signed
                targets_expiry = targets_meta.expires
                targets_version = targets_meta.version
                targets_days_diff = day_difference(time_now, targets_expiry)
                if(targets_days_diff > threshold):
                    unexpired_snapshots[snapshot_version][targets_in_snapshot] = TargetsMetadata(targets_version, {}, True, targets_in_snapshot)
                    for targets_file in targets_meta.targets:
                        unexpired_snapshots[snapshot_version][targets_in_snapshot].targets[targets_file] =  Target(True, targets_file)
                else:
                    unexpired_snapshots[snapshot_version][targets_in_snapshot] = TargetsMetadata(targets_version, {}, False, targets_in_snapshot)
                    for targets_file in targets_meta.targets:
                        unexpired_snapshots[snapshot_version][targets_in_snapshot].targets[targets_file] =  Target(False, targets_file)

def expired_unexpired_display(snapshot_type: str) -> None:
    snapshot = globals()[snapshot_type]
    for outer_key, inner_dict in snapshot.items():
        print(f"Outer key: {outer_key}")
        for inner_key, value in inner_dict.items():
            print(f"  Inner key: {inner_key}-> {value} ")
            targets = value.get_targets()
            for target, data in targets.items():
                print(f"    Target: {target} -> {data}")

if __name__ == "__main__":
    # A file will be considered as garbage if the expiry is more than or euqal to the threshold number of days
    threshold =  3
    mark(threshold)
    print("----------------Expired List--------------------")
    expired_unexpired_display("expired_snapshots")
    print("---------------Unexpired List-------------------")
    expired_unexpired_display("unexpired_snapshots")



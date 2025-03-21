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
                return f"Target(filename={self.filename}, delete={self.delete})"
Targets = dict[str, Target]

class TargetsMetadata:
    def __init__(self, version: int = 0, targets: Targets = None, delete: bool = False, filename: str = ""):
        self.version = version
        self.targets = targets or dict()
        self.delete = delete
        self.filename = filename
    def get_targets(self):
        return self.targets
    def __str__(self):
        return f"TargetsMetadata({self.filename}, {self.delete})"

unexpired_snapshots = {
    2: {
        "targets.json": TargetsMetadata(2, {
            "target2.txt": Target(),
        }),
        "foo.json": TargetsMetadata(2),
    }
}

expired_snapshots = {
    1: {
            "targets.json": TargetsMetadata(1, {
                    "target2.txt": Target(),
            "target1.txt": Target(),
        }),
            "foo.json": TargetsMetadata(1),
    }
}


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
    #path = os.path.join(self.repo_dir, "metadata")
    path = "/home/iiita/supplychain/python-tuf/examples/manual_repo/tmpsp2y1znf"
    sorted_items = sorted_file(path)
    time_now = datetime.now(timezone.utc)
    for item in sorted_items:
        snapshot = Metadata[Snapshot].from_file(os.path.join(path, item)).signed
        snapshot_expiry = snapshot.expires
        snapshot_version = snapshot.version
        snapshot_days_diff = day_difference(time_now, snapshot_expiry)
        # Verify with snapshot expiry date
        if(snapshot_days_diff > threshold):   
            for snapshot_meta in snapshot.meta:
                version = snapshot.meta[snapshot_meta].version
                targets_meta = Metadata[Targets].from_file(os.path.join(path, snapshot_meta)).signed
                targets_expiry = targets_meta.expires
                targets_days_diff = day_difference(time_now, targets_expiry)
                # Verify with snapshot expiry date
                if(targets_days_diff > threshold):
                    for targets_file in targets_meta.targets:
                        target_meta = unexpired_snapshots[2]["targets.json"]
                        target_meta.targets[targets_file] = Target(True,targets_file)
                        print(unexpired_snapshots[2]["targets.json"].get_targets()[targets_file])
                else:
                    for targets_file in targets_meta.targets:
                        target_meta = expired_snapshots[1]["targets.json"]
                        target_meta.targets[targets_file] = Target(False,target_file)
                        print(expired_snapshots[1]["targets.json"].get_targets()[targets_file])
if __name__ == "__main__":
    # A file will be considered as garbage if the expiry is more than or euqal to the threshold number of days
    threshold =  3
    mark(threshold)

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from jinja2 import FileSystemLoader

from commitizen import changelog, git
from commitizen.changelog_formats import ChangelogFormat
from commitizen.commands.changelog import Changelog
from commitizen.config import BaseConfig
from commitizen.cz.conventional_commits.conventional_commits import (
    ConventionalCommitsCz,
)
from commitizen.exceptions import InvalidConfigurationError
from commitizen.version_schemes import Pep440

COMMITS_DATA: list[dict[str, Any]] = [
    {
        "rev": "141ee441c9c9da0809c554103a558eb17c30ed17",
        "parents": ["6c4948501031b7d6405b54b21d3d635827f9421b"],
        "title": "bump: version 1.1.1 → 1.2.0",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "6c4948501031b7d6405b54b21d3d635827f9421b",
        "parents": ["ddd220ad515502200fe2dde443614c1075d26238"],
        "title": "docs: how to create custom bumps",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "ddd220ad515502200fe2dde443614c1075d26238",
        "parents": ["ad17acff2e3a2e141cbc3c6efd7705e4e6de9bfc"],
        "title": "feat: custom cz plugins now support bumping version",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "ad17acff2e3a2e141cbc3c6efd7705e4e6de9bfc",
        "parents": ["56c8a8da84e42b526bcbe130bd194306f7c7e813"],
        "title": "docs: added bump gif",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "56c8a8da84e42b526bcbe130bd194306f7c7e813",
        "parents": ["74c6134b1b2e6bb8b07ed53410faabe99b204f36"],
        "title": "bump: version 1.1.0 → 1.1.1",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "74c6134b1b2e6bb8b07ed53410faabe99b204f36",
        "parents": ["cbc7b5f22c4e74deff4bc92d14e19bd93524711e"],
        "title": "refactor: changed stdout statements",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "cbc7b5f22c4e74deff4bc92d14e19bd93524711e",
        "parents": ["1ba46f2a63cb9d6e7472eaece21528c8cd28b118"],
        "title": "fix(bump): commit message now fits better with semver",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "1ba46f2a63cb9d6e7472eaece21528c8cd28b118",
        "parents": ["c35dbffd1bb98bb0b3d1593797e79d1c3366af8f"],
        "title": "fix: conventional commit 'breaking change' in body instead of title",
        "body": "closes #16",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "c35dbffd1bb98bb0b3d1593797e79d1c3366af8f",
        "parents": ["25313397a4ac3dc5b5c986017bee2a614399509d"],
        "title": "refactor(schema): command logic removed from commitizen base",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "25313397a4ac3dc5b5c986017bee2a614399509d",
        "parents": ["d2f13ac41b4e48995b3b619d931c82451886e6ff"],
        "title": "refactor(info): command logic removed from commitizen base",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "d2f13ac41b4e48995b3b619d931c82451886e6ff",
        "parents": ["d839e317e5b26671b010584ad8cc6bf362400fa1"],
        "title": "refactor(example): command logic removed from commitizen base",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "d839e317e5b26671b010584ad8cc6bf362400fa1",
        "parents": ["12d0e65beda969f7983c444ceedc2a01584f4e08"],
        "title": "refactor(commit): moved most of the commit logic to the commit command",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "12d0e65beda969f7983c444ceedc2a01584f4e08",
        "parents": ["fb4c85abe51c228e50773e424cbd885a8b6c610d"],
        "title": "docs(README): updated documentation url)",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "fb4c85abe51c228e50773e424cbd885a8b6c610d",
        "parents": ["17efb44d2cd16f6621413691a543e467c7d2dda6"],
        "title": "docs: mkdocs documentation",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "17efb44d2cd16f6621413691a543e467c7d2dda6",
        "parents": ["6012d9eecfce8163d75c8fff179788e9ad5347da"],
        "title": "Bump version 1.0.0 → 1.1.0",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "6012d9eecfce8163d75c8fff179788e9ad5347da",
        "parents": ["0c7fb0ca0168864dfc55d83c210da57771a18319"],
        "title": "test: fixed issues with conf",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "0c7fb0ca0168864dfc55d83c210da57771a18319",
        "parents": ["cb1dd2019d522644da5bdc2594dd6dee17122d7f"],
        "title": "docs(README): some new information about bump",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "cb1dd2019d522644da5bdc2594dd6dee17122d7f",
        "parents": ["9c7450f85df6bf6be508e79abf00855a30c3c73c"],
        "title": "feat: new working bump command",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "9c7450f85df6bf6be508e79abf00855a30c3c73c",
        "parents": ["9f3af3772baab167e3fd8775d37f041440184251"],
        "title": "feat: create version tag",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "9f3af3772baab167e3fd8775d37f041440184251",
        "parents": ["b0d6a3defbfde14e676e7eb34946409297d0221b"],
        "title": "docs: added new changelog",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "b0d6a3defbfde14e676e7eb34946409297d0221b",
        "parents": ["d630d07d912e420f0880551f3ac94e933f9d3beb"],
        "title": "feat: update given files with new version",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "d630d07d912e420f0880551f3ac94e933f9d3beb",
        "parents": ["1792b8980c58787906dbe6836f93f31971b1ec2d"],
        "title": "fix: removed all from commit",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "1792b8980c58787906dbe6836f93f31971b1ec2d",
        "parents": ["52def1ea3555185ba4b936b463311949907e31ec"],
        "title": "feat(config): new set key, used to set version to cfg",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "52def1ea3555185ba4b936b463311949907e31ec",
        "parents": ["3127e05077288a5e2b62893345590bf1096141b7"],
        "title": "feat: support for pyproject.toml",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "3127e05077288a5e2b62893345590bf1096141b7",
        "parents": ["fd480ed90a80a6ffa540549408403d5b60d0e90c"],
        "title": "feat: first semantic version bump implementation",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "fd480ed90a80a6ffa540549408403d5b60d0e90c",
        "parents": ["e4840a059731c0bf488381ffc77e989e85dd81ad"],
        "title": "fix: fix config file not working",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "e4840a059731c0bf488381ffc77e989e85dd81ad",
        "parents": ["aa44a92d68014d0da98965c0c2cb8c07957d4362"],
        "title": "refactor: added commands folder, better integration with decli",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "aa44a92d68014d0da98965c0c2cb8c07957d4362",
        "parents": ["58bb709765380dbd46b74ce6e8978515764eb955"],
        "title": "Bump version: 1.0.0b2 → 1.0.0",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "58bb709765380dbd46b74ce6e8978515764eb955",
        "parents": ["97afb0bb48e72b6feca793091a8a23c706693257"],
        "title": "docs(README): new badges",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "97afb0bb48e72b6feca793091a8a23c706693257",
        "parents": [
            "9cecb9224aa7fa68d4afeac37eba2a25770ef251",
            "e004a90b81ea5b374f118759bce5951202d03d69",
        ],
        "title": "Merge pull request #10 from Woile/feat/decli",
        "body": "Feat/decli",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "9cecb9224aa7fa68d4afeac37eba2a25770ef251",
        "parents": ["f5781d1a2954d71c14ade2a6a1a95b91310b2577"],
        "title": "style: black to files",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "f5781d1a2954d71c14ade2a6a1a95b91310b2577",
        "parents": ["80105fb3c6d45369bc0cbf787bd329fba603864c"],
        "title": "ci: added travis",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "80105fb3c6d45369bc0cbf787bd329fba603864c",
        "parents": ["a96008496ffefb6b1dd9b251cb479eac6a0487f7"],
        "title": "refactor: removed delegator, added decli and many tests",
        "body": "BREAKING CHANGE: API is stable",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "a96008496ffefb6b1dd9b251cb479eac6a0487f7",
        "parents": ["aab33d13110f26604fb786878856ec0b9e5fc32b"],
        "title": "docs: updated test command",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "aab33d13110f26604fb786878856ec0b9e5fc32b",
        "parents": ["b73791563d2f218806786090fb49ef70faa51a3a"],
        "title": "Bump version: 1.0.0b1 → 1.0.0b2",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "b73791563d2f218806786090fb49ef70faa51a3a",
        "parents": ["7aa06a454fb717408b3657faa590731fb4ab3719"],
        "title": "docs(README): updated to reflect current state",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "7aa06a454fb717408b3657faa590731fb4ab3719",
        "parents": [
            "7c7e96b723c2aaa1aec3a52561f680adf0b60e97",
            "9589a65880016996cff156b920472b9d28d771ca",
        ],
        "title": "Merge pull request #9 from Woile/dev",
        "body": "feat: py3 only, tests and conventional commits 1.0",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "7c7e96b723c2aaa1aec3a52561f680adf0b60e97",
        "parents": ["ed830019581c83ba633bfd734720e6758eca6061"],
        "title": "Bump version: 0.9.11 → 1.0.0b1",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "ed830019581c83ba633bfd734720e6758eca6061",
        "parents": ["c52eca6f74f844ab3ffbde61d98ef96071e132b7"],
        "title": "feat: py3 only, tests and conventional commits 1.0",
        "body": "more tests\npyproject instead of Pipfile\nquestionary instead of whaaaaat (promptkit 2.0.0 support)",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "c52eca6f74f844ab3ffbde61d98ef96071e132b7",
        "parents": ["0326652b2657083929507ee66d4d1a0899e861ba"],
        "title": "Bump version: 0.9.10 → 0.9.11",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "0326652b2657083929507ee66d4d1a0899e861ba",
        "parents": ["b3f89892222340150e32631ae6b7aab65230036f"],
        "title": "fix(config): load config reads in order without failing if there is no commitizen section",
        "body": "Closes #8",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "b3f89892222340150e32631ae6b7aab65230036f",
        "parents": ["5e837bf8ef0735193597372cd2d85e31a8f715b9"],
        "title": "Bump version: 0.9.9 → 0.9.10",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "5e837bf8ef0735193597372cd2d85e31a8f715b9",
        "parents": ["684e0259cc95c7c5e94854608cd3dcebbd53219e"],
        "title": "fix: parse scope (this is my punishment for not having tests)",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "684e0259cc95c7c5e94854608cd3dcebbd53219e",
        "parents": ["ca38eac6ff09870851b5c76a6ff0a2a8e5ecda15"],
        "title": "Bump version: 0.9.8 → 0.9.9",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "ca38eac6ff09870851b5c76a6ff0a2a8e5ecda15",
        "parents": ["64168f18d4628718c49689ee16430549e96c5d4b"],
        "title": "fix: parse scope empty",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "64168f18d4628718c49689ee16430549e96c5d4b",
        "parents": ["9d4def716ef235a1fa5ae61614366423fbc8256f"],
        "title": "Bump version: 0.9.7 → 0.9.8",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "9d4def716ef235a1fa5ae61614366423fbc8256f",
        "parents": ["33b0bf1a0a4dc60aac45ed47476d2e5473add09e"],
        "title": "fix(scope): parse correctly again",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "33b0bf1a0a4dc60aac45ed47476d2e5473add09e",
        "parents": ["696885e891ec35775daeb5fec3ba2ab92c2629e1"],
        "title": "Bump version: 0.9.6 → 0.9.7",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "696885e891ec35775daeb5fec3ba2ab92c2629e1",
        "parents": ["bef4a86761a3bda309c962bae5d22ce9b57119e4"],
        "title": "fix(scope): parse correctly",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "bef4a86761a3bda309c962bae5d22ce9b57119e4",
        "parents": ["72472efb80f08ee3fd844660afa012c8cb256e4b"],
        "title": "Bump version: 0.9.5 → 0.9.6",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "72472efb80f08ee3fd844660afa012c8cb256e4b",
        "parents": ["b5561ce0ab3b56bb87712c8f90bcf37cf2474f1b"],
        "title": "refactor(conventionalCommit): moved filters to questions instead of message",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "b5561ce0ab3b56bb87712c8f90bcf37cf2474f1b",
        "parents": ["3e31714dc737029d96898f412e4ecd2be1bcd0ce"],
        "title": "fix(manifest): included missing files",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "3e31714dc737029d96898f412e4ecd2be1bcd0ce",
        "parents": ["9df721e06595fdd216884c36a28770438b4f4a39"],
        "title": "Bump version: 0.9.4 → 0.9.5",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "9df721e06595fdd216884c36a28770438b4f4a39",
        "parents": ["0cf6ada372470c8d09e6c9e68ebf94bbd5a1656f"],
        "title": "fix(config): home path for python versions between 3.0 and 3.5",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "0cf6ada372470c8d09e6c9e68ebf94bbd5a1656f",
        "parents": ["973c6b3e100f6f69a3fe48bd8ee55c135b96c318"],
        "title": "Bump version: 0.9.3 → 0.9.4",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "973c6b3e100f6f69a3fe48bd8ee55c135b96c318",
        "parents": ["dacc86159b260ee98eb5f57941c99ba731a01399"],
        "title": "feat(cli): added version",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "dacc86159b260ee98eb5f57941c99ba731a01399",
        "parents": ["4368f3c3cbfd4a1ced339212230d854bc5bab496"],
        "title": "Bump version: 0.9.2 → 0.9.3",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "4368f3c3cbfd4a1ced339212230d854bc5bab496",
        "parents": ["da94133288727d35dae9b91866a25045038f2d38"],
        "title": "feat(committer): conventional commit is a bit more intelligent now",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "da94133288727d35dae9b91866a25045038f2d38",
        "parents": ["1541f54503d2e1cf39bd777c0ca5ab5eb78772ba"],
        "title": "docs(README): motivation",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "1541f54503d2e1cf39bd777c0ca5ab5eb78772ba",
        "parents": ["ddc855a637b7879108308b8dbd85a0fd27c7e0e7"],
        "title": "Bump version: 0.9.1 → 0.9.2",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "ddc855a637b7879108308b8dbd85a0fd27c7e0e7",
        "parents": ["46e9032e18a819e466618c7a014bcb0e9981af9e"],
        "title": "refactor: renamed conventional_changelog to conventional_commits, not backward compatible",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "46e9032e18a819e466618c7a014bcb0e9981af9e",
        "parents": ["0fef73cd7dc77a25b82e197e7c1d3144a58c1350"],
        "title": "Bump version: 0.9.0 → 0.9.1",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
    {
        "rev": "0fef73cd7dc77a25b82e197e7c1d3144a58c1350",
        "parents": [],
        "title": "fix(setup.py): future is now required for every python version",
        "body": "",
        "author": "Commitizen",
        "author_email": "author@cz.dev",
    },
]


TAGS = [
    ("v1.2.0", "141ee441c9c9da0809c554103a558eb17c30ed17", "2019-04-19"),
    ("v1.1.1", "56c8a8da84e42b526bcbe130bd194306f7c7e813", "2019-04-18"),
    ("v1.1.0", "17efb44d2cd16f6621413691a543e467c7d2dda6", "2019-04-14"),
    ("v1.0.0", "aa44a92d68014d0da98965c0c2cb8c07957d4362", "2019-03-01"),
    ("1.0.0b2", "aab33d13110f26604fb786878856ec0b9e5fc32b", "2019-01-18"),
    ("v1.0.0b1", "7c7e96b723c2aaa1aec3a52561f680adf0b60e97", "2019-01-17"),
    ("v0.9.11", "c52eca6f74f844ab3ffbde61d98ef96071e132b7", "2018-12-17"),
    ("v0.9.10", "b3f89892222340150e32631ae6b7aab65230036f", "2018-09-22"),
    ("v0.9.9", "684e0259cc95c7c5e94854608cd3dcebbd53219e", "2018-09-22"),
    ("v0.9.8", "64168f18d4628718c49689ee16430549e96c5d4b", "2018-09-22"),
    ("v0.9.7", "33b0bf1a0a4dc60aac45ed47476d2e5473add09e", "2018-09-22"),
    ("v0.9.6", "bef4a86761a3bda309c962bae5d22ce9b57119e4", "2018-09-19"),
    ("v0.9.5", "3e31714dc737029d96898f412e4ecd2be1bcd0ce", "2018-08-24"),
    ("v0.9.4", "0cf6ada372470c8d09e6c9e68ebf94bbd5a1656f", "2018-08-02"),
    ("v0.9.3", "dacc86159b260ee98eb5f57941c99ba731a01399", "2018-07-28"),
    ("v0.9.2", "1541f54503d2e1cf39bd777c0ca5ab5eb78772ba", "2017-11-11"),
    ("v0.9.1", "46e9032e18a819e466618c7a014bcb0e9981af9e", "2017-11-11"),
]


@pytest.fixture
def gitcommits() -> list[git.GitCommit]:
    return [
        git.GitCommit(
            commit["rev"],
            commit["title"],
            commit["body"],
            commit["author"],
            commit["author_email"],
            commit["parents"],
        )
        for commit in COMMITS_DATA
    ]


@pytest.fixture
def tags() -> list[git.GitTag]:
    return [git.GitTag(*tag) for tag in TAGS]


@pytest.fixture
def changelog_content() -> str:
    changelog_path = "tests/CHANGELOG_FOR_TEST.md"
    with open(changelog_path, encoding="utf-8") as f:
        return f.read()


def test_get_commit_tag_is_a_version(gitcommits, tags):
    commit = gitcommits[0]
    tag = git.GitTag(*TAGS[0])
    current_key = changelog.get_commit_tag(commit, tags)
    assert current_key == tag


def test_get_commit_tag_is_None(gitcommits, tags):
    commit = gitcommits[1]
    current_key = changelog.get_commit_tag(commit, tags)
    assert current_key is None


@pytest.mark.parametrize("test_input", TAGS)
def test_valid_tag_included_in_changelog(test_input):
    tag = git.GitTag(*test_input)
    rules = changelog.TagRules()
    assert rules.include_in_changelog(tag)


def test_invalid_tag_included_in_changelog():
    tag = git.GitTag("not_a_version", "rev", "date")
    rules = changelog.TagRules()
    assert not rules.include_in_changelog(tag)


COMMITS_TREE = (
    {
        "version": "v1.2.0",
        "date": "2019-04-19",
        "changes": {
            "feat": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "custom cz plugins now support bumping version",
                }
            ]
        },
    },
    {
        "version": "v1.1.1",
        "date": "2019-04-18",
        "changes": {
            "refactor": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "changed stdout statements",
                },
                {
                    "scope": "schema",
                    "breaking": None,
                    "message": "command logic removed from commitizen base",
                },
                {
                    "scope": "info",
                    "breaking": None,
                    "message": "command logic removed from commitizen base",
                },
                {
                    "scope": "example",
                    "breaking": None,
                    "message": "command logic removed from commitizen base",
                },
                {
                    "scope": "commit",
                    "breaking": None,
                    "message": "moved most of the commit logic to the commit command",
                },
            ],
            "fix": [
                {
                    "scope": "bump",
                    "breaking": None,
                    "message": "commit message now fits better with semver",
                },
                {
                    "scope": None,
                    "breaking": None,
                    "message": "conventional commit 'breaking change' in body instead of title",
                },
            ],
        },
    },
    {
        "version": "v1.1.0",
        "date": "2019-04-14",
        "changes": {
            "feat": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "new working bump command",
                },
                {"scope": None, "breaking": None, "message": "create version tag"},
                {
                    "scope": None,
                    "breaking": None,
                    "message": "update given files with new version",
                },
                {
                    "scope": "config",
                    "breaking": None,
                    "message": "new set key, used to set version to cfg",
                },
                {
                    "scope": None,
                    "breaking": None,
                    "message": "support for pyproject.toml",
                },
                {
                    "scope": None,
                    "breaking": None,
                    "message": "first semantic version bump implementation",
                },
            ],
            "fix": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "removed all from commit",
                },
                {
                    "scope": None,
                    "breaking": None,
                    "message": "fix config file not working",
                },
            ],
            "refactor": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "added commands folder, better integration with decli",
                }
            ],
        },
    },
    {
        "version": "v1.0.0",
        "date": "2019-03-01",
        "changes": {
            "refactor": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "removed delegator, added decli and many tests",
                }
            ],
            "BREAKING CHANGE": [
                {"scope": None, "breaking": None, "message": "API is stable"}
            ],
        },
    },
    {"version": "1.0.0b2", "date": "2019-01-18", "changes": {}},
    {
        "version": "v1.0.0b1",
        "date": "2019-01-17",
        "changes": {
            "feat": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "py3 only, tests and conventional commits 1.0",
                }
            ]
        },
    },
    {
        "version": "v0.9.11",
        "date": "2018-12-17",
        "changes": {
            "fix": [
                {
                    "scope": "config",
                    "breaking": None,
                    "message": "load config reads in order without failing if there is no commitizen section",
                }
            ]
        },
    },
    {
        "version": "v0.9.10",
        "date": "2018-09-22",
        "changes": {
            "fix": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "parse scope (this is my punishment for not having tests)",
                }
            ]
        },
    },
    {
        "version": "v0.9.9",
        "date": "2018-09-22",
        "changes": {
            "fix": [{"scope": None, "breaking": None, "message": "parse scope empty"}]
        },
    },
    {
        "version": "v0.9.8",
        "date": "2018-09-22",
        "changes": {
            "fix": [
                {
                    "scope": "scope",
                    "breaking": None,
                    "message": "parse correctly again",
                }
            ]
        },
    },
    {
        "version": "v0.9.7",
        "date": "2018-09-22",
        "changes": {
            "fix": [{"scope": "scope", "breaking": None, "message": "parse correctly"}]
        },
    },
    {
        "version": "v0.9.6",
        "date": "2018-09-19",
        "changes": {
            "refactor": [
                {
                    "scope": "conventionalCommit",
                    "breaking": None,
                    "message": "moved filters to questions instead of message",
                }
            ],
            "fix": [
                {
                    "scope": "manifest",
                    "breaking": None,
                    "message": "included missing files",
                }
            ],
        },
    },
    {
        "version": "v0.9.5",
        "date": "2018-08-24",
        "changes": {
            "fix": [
                {
                    "scope": "config",
                    "breaking": None,
                    "message": "home path for python versions between 3.0 and 3.5",
                }
            ]
        },
    },
    {
        "version": "v0.9.4",
        "date": "2018-08-02",
        "changes": {
            "feat": [{"scope": "cli", "breaking": None, "message": "added version"}]
        },
    },
    {
        "version": "v0.9.3",
        "date": "2018-07-28",
        "changes": {
            "feat": [
                {
                    "scope": "committer",
                    "breaking": None,
                    "message": "conventional commit is a bit more intelligent now",
                }
            ]
        },
    },
    {
        "version": "v0.9.2",
        "date": "2017-11-11",
        "changes": {
            "refactor": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "renamed conventional_changelog to conventional_commits, not backward compatible",
                }
            ]
        },
    },
    {
        "version": "v0.9.1",
        "date": "2017-11-11",
        "changes": {
            "fix": [
                {
                    "scope": "setup.py",
                    "breaking": None,
                    "message": "future is now required for every python version",
                }
            ]
        },
    },
)

COMMITS_TREE_AFTER_MERGED_PRERELEASES = (
    {
        "version": "v1.2.0",
        "date": "2019-04-19",
        "changes": {
            "feat": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "custom cz plugins now support bumping version",
                }
            ]
        },
    },
    {
        "version": "v1.1.1",
        "date": "2019-04-18",
        "changes": {
            "refactor": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "changed stdout statements",
                },
                {
                    "scope": "schema",
                    "breaking": None,
                    "message": "command logic removed from commitizen base",
                },
                {
                    "scope": "info",
                    "breaking": None,
                    "message": "command logic removed from commitizen base",
                },
                {
                    "scope": "example",
                    "breaking": None,
                    "message": "command logic removed from commitizen base",
                },
                {
                    "scope": "commit",
                    "breaking": None,
                    "message": "moved most of the commit logic to the commit command",
                },
            ],
            "fix": [
                {
                    "scope": "bump",
                    "breaking": None,
                    "message": "commit message now fits better with semver",
                },
                {
                    "scope": None,
                    "breaking": None,
                    "message": "conventional commit 'breaking change' in body instead of title",
                },
            ],
        },
    },
    {
        "version": "v1.1.0",
        "date": "2019-04-14",
        "changes": {
            "feat": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "new working bump command",
                },
                {"scope": None, "breaking": None, "message": "create version tag"},
                {
                    "scope": None,
                    "breaking": None,
                    "message": "update given files with new version",
                },
                {
                    "scope": "config",
                    "breaking": None,
                    "message": "new set key, used to set version to cfg",
                },
                {
                    "scope": None,
                    "breaking": None,
                    "message": "support for pyproject.toml",
                },
                {
                    "scope": None,
                    "breaking": None,
                    "message": "first semantic version bump implementation",
                },
            ],
            "fix": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "removed all from commit",
                },
                {
                    "scope": None,
                    "breaking": None,
                    "message": "fix config file not working",
                },
            ],
            "refactor": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "added commands folder, better integration with decli",
                }
            ],
        },
    },
    {
        "version": "v1.0.0",
        "date": "2019-03-01",
        "changes": {
            "refactor": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "removed delegator, added decli and many tests",
                }
            ],
            "feat": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "py3 only, tests and conventional commits 1.0",
                }
            ],
            "BREAKING CHANGE": [
                {"scope": None, "breaking": None, "message": "API is stable"}
            ],
        },
    },
    {
        "version": "v0.9.11",
        "date": "2018-12-17",
        "changes": {
            "fix": [
                {
                    "scope": "config",
                    "breaking": None,
                    "message": "load config reads in order without failing if there is no commitizen section",
                }
            ]
        },
    },
    {
        "version": "v0.9.10",
        "date": "2018-09-22",
        "changes": {
            "fix": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "parse scope (this is my punishment for not having tests)",
                }
            ]
        },
    },
    {
        "version": "v0.9.9",
        "date": "2018-09-22",
        "changes": {
            "fix": [{"scope": None, "breaking": None, "message": "parse scope empty"}]
        },
    },
    {
        "version": "v0.9.8",
        "date": "2018-09-22",
        "changes": {
            "fix": [
                {
                    "scope": "scope",
                    "breaking": None,
                    "message": "parse correctly again",
                }
            ]
        },
    },
    {
        "version": "v0.9.7",
        "date": "2018-09-22",
        "changes": {
            "fix": [{"scope": "scope", "breaking": None, "message": "parse correctly"}]
        },
    },
    {
        "version": "v0.9.6",
        "date": "2018-09-19",
        "changes": {
            "refactor": [
                {
                    "scope": "conventionalCommit",
                    "breaking": None,
                    "message": "moved filters to questions instead of message",
                }
            ],
            "fix": [
                {
                    "scope": "manifest",
                    "breaking": None,
                    "message": "included missing files",
                }
            ],
        },
    },
    {
        "version": "v0.9.5",
        "date": "2018-08-24",
        "changes": {
            "fix": [
                {
                    "scope": "config",
                    "breaking": None,
                    "message": "home path for python versions between 3.0 and 3.5",
                }
            ]
        },
    },
    {
        "version": "v0.9.4",
        "date": "2018-08-02",
        "changes": {
            "feat": [{"scope": "cli", "breaking": None, "message": "added version"}]
        },
    },
    {
        "version": "v0.9.3",
        "date": "2018-07-28",
        "changes": {
            "feat": [
                {
                    "scope": "committer",
                    "breaking": None,
                    "message": "conventional commit is a bit more intelligent now",
                }
            ]
        },
    },
    {
        "version": "v0.9.2",
        "date": "2017-11-11",
        "changes": {
            "refactor": [
                {
                    "scope": None,
                    "breaking": None,
                    "message": "renamed conventional_changelog to conventional_commits, not backward compatible",
                }
            ]
        },
    },
    {
        "version": "v0.9.1",
        "date": "2017-11-11",
        "changes": {
            "fix": [
                {
                    "scope": "setup.py",
                    "breaking": None,
                    "message": "future is now required for every python version",
                }
            ]
        },
    },
)


@pytest.mark.parametrize("merge_prereleases", (True, False))
def test_generate_tree_from_commits(gitcommits, tags, merge_prereleases):
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.bump_pattern
    rules = changelog.TagRules(
        merge_prereleases=merge_prereleases,
    )
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern, rules=rules
    )
    expected = (
        COMMITS_TREE_AFTER_MERGED_PRERELEASES if merge_prereleases else COMMITS_TREE
    )

    for release, expected_release in zip(tree, expected):
        assert release["version"] == expected_release["version"]
        assert release["date"] == expected_release["date"]
        assert release["changes"].keys() == expected_release["changes"].keys()
        for change_type in release["changes"]:
            changes = release["changes"][change_type]
            expected_changes = expected_release["changes"][change_type]
            for change, expected_change in zip(changes, expected_changes):
                assert change["scope"] == expected_change["scope"]
                assert change["breaking"] == expected_change["breaking"]
                assert change["message"] == expected_change["message"]
                assert change["author"] == "Commitizen"
                assert change["author_email"] in "author@cz.dev"
                assert "sha1" in change
                assert "parents" in change


def test_generate_tree_from_commits_with_no_commits(tags):
    gitcommits = []
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.bump_pattern
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern
    )

    assert tuple(tree) == ({"changes": {}, "date": "", "version": "Unreleased"},)


@pytest.mark.parametrize(
    "change_type_order, expected_reordering",
    (
        ([], {}),
        (
            ["BREAKING CHANGE", "refactor"],
            {
                "1.1.0": {
                    "original": ["feat", "fix", "refactor"],
                    "sorted": ["refactor", "feat", "fix"],
                },
                "1.0.0": {
                    "original": ["refactor", "BREAKING CHANGE"],
                    "sorted": ["BREAKING CHANGE", "refactor"],
                },
            },
        ),
    ),
)
def test_generate_ordered_changelog_tree(change_type_order, expected_reordering):
    tree = changelog.generate_ordered_changelog_tree(COMMITS_TREE, change_type_order)

    for index, entry in enumerate(tuple(tree)):
        version = entry["version"]
        if version in expected_reordering:
            # Verify that all keys are present
            assert [*entry.keys()] == [*COMMITS_TREE[index].keys()]
            # Verify that the reorder only impacted the returned dict and not the original
            expected = expected_reordering[version]
            assert [*entry["changes"].keys()] == expected["sorted"]
            assert [*COMMITS_TREE[index]["changes"].keys()] == expected["original"]
        else:
            assert [*entry["changes"].keys()] == [*entry["changes"].keys()]


def test_generate_ordered_changelog_tree_raises():
    change_type_order = ["BREAKING CHANGE", "feat", "refactor", "feat"]
    with pytest.raises(InvalidConfigurationError) as excinfo:
        list(changelog.generate_ordered_changelog_tree(COMMITS_TREE, change_type_order))

    assert "Change types contain duplicated types" in str(excinfo)


def test_render_changelog(
    gitcommits, tags, changelog_content, any_changelog_format: ChangelogFormat
):
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, template)
    assert result == changelog_content


def test_render_changelog_from_default_plugin_values(
    gitcommits, tags, changelog_content, any_changelog_format: ChangelogFormat
):
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, template)
    assert result == changelog_content


def test_render_changelog_override_loader(gitcommits, tags, tmp_path: Path):
    loader = FileSystemLoader(tmp_path)
    template = "tpl.j2"
    tpl = "loader overridden"
    (tmp_path / template).write_text(tpl)
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, template)
    assert result == tpl


def test_render_changelog_override_template_from_cwd(
    gitcommits, tags, chdir: Path, any_changelog_format: ChangelogFormat
):
    tpl = "overridden from cwd"
    template = any_changelog_format.template
    (chdir / template).write_text(tpl)
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, template)
    assert result == tpl


def test_render_changelog_override_template_from_cwd_with_custom_name(
    gitcommits, tags, chdir: Path
):
    tpl = "template overridden from cwd"
    tpl_name = "tpl.j2"
    (chdir / tpl_name).write_text(tpl)
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, tpl_name)
    assert result == tpl


def test_render_changelog_override_loader_and_template(
    gitcommits, tags, tmp_path: Path
):
    loader = FileSystemLoader(tmp_path)
    tpl = "loader and template overridden"
    tpl_name = "tpl.j2"
    (tmp_path / tpl_name).write_text(tpl)
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.bump_pattern
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, tpl_name)
    assert result == tpl


def test_render_changelog_support_arbitrary_kwargs(gitcommits, tags, tmp_path: Path):
    loader = FileSystemLoader(tmp_path)
    tpl_name = "tpl.j2"
    (tmp_path / tpl_name).write_text("{{ key }}")
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, tpl_name, key="value")
    assert result == "value"


def test_render_changelog_unreleased(gitcommits, any_changelog_format: ChangelogFormat):
    some_commits = gitcommits[:7]
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        some_commits, [], parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, template)
    assert "Unreleased" in result


def test_render_changelog_tag_and_unreleased(
    gitcommits, tags, any_changelog_format: ChangelogFormat
):
    some_commits = gitcommits[:7]
    single_tag = [
        tag for tag in tags if tag.rev == "56c8a8da84e42b526bcbe130bd194306f7c7e813"
    ]

    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        some_commits, single_tag, parser, changelog_pattern
    )
    result = changelog.render_changelog(tree, loader, template)

    assert "Unreleased" in result
    assert "## v1.1.1" in result


def test_render_changelog_with_change_type(
    gitcommits, tags, any_changelog_format: ChangelogFormat
):
    new_title = ":some-emoji: feature"
    change_type_map = {"feat": new_title}
    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        gitcommits, tags, parser, changelog_pattern, change_type_map=change_type_map
    )
    result = changelog.render_changelog(tree, loader, template)
    assert new_title in result


def test_render_changelog_with_changelog_message_builder_hook(
    gitcommits, tags, any_changelog_format: ChangelogFormat
):
    def changelog_message_builder_hook(message: dict, commit: git.GitCommit) -> dict:
        message["message"] = (
            f"{message['message']} [link](github.com/232323232) {commit.author} {commit.author_email}"
        )
        return message

    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        gitcommits,
        tags,
        parser,
        changelog_pattern,
        changelog_message_builder_hook=changelog_message_builder_hook,
    )
    result = changelog.render_changelog(tree, loader, template)

    assert "[link](github.com/232323232) Commitizen author@cz.dev" in result


def test_changelog_message_builder_hook_can_remove_commits(
    gitcommits, tags, any_changelog_format: ChangelogFormat
):
    def changelog_message_builder_hook(message: dict, commit: git.GitCommit):
        return None

    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        gitcommits,
        tags,
        parser,
        changelog_pattern,
        changelog_message_builder_hook=changelog_message_builder_hook,
    )
    result = changelog.render_changelog(tree, loader, template)

    RE_HEADER = re.compile(r"^## v?\d+\.\d+\.\d+(\w)* \(\d{4}-\d{2}-\d{2}\)$")
    # Rendered changelog should be empty, only containing version headers
    for no, line in enumerate(result.splitlines()):
        if line := line.strip():
            assert RE_HEADER.match(line), f"Line {no} should not be there: {line}"


def test_render_changelog_with_changelog_message_builder_hook_multiple_entries(
    gitcommits, tags, any_changelog_format: ChangelogFormat
):
    def changelog_message_builder_hook(message: dict, commit: git.GitCommit):
        messages = [message.copy(), message.copy(), message.copy()]
        for idx, msg in enumerate(messages):
            msg["message"] = "Message #{idx}"
        return messages

    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        gitcommits,
        tags,
        parser,
        changelog_pattern,
        changelog_message_builder_hook=changelog_message_builder_hook,
    )
    result = changelog.render_changelog(tree, loader, template)

    for idx in range(3):
        assert "Message #{idx}" in result


def test_changelog_message_builder_hook_can_access_and_modify_change_type(
    gitcommits, tags, any_changelog_format: ChangelogFormat
):
    def changelog_message_builder_hook(message: dict, commit: git.GitCommit):
        assert "change_type" in message
        message["change_type"] = "overridden"
        return message

    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    loader = ConventionalCommitsCz.template_loader
    template = any_changelog_format.template
    tree = changelog.generate_tree_from_commits(
        gitcommits,
        tags,
        parser,
        changelog_pattern,
        changelog_message_builder_hook=changelog_message_builder_hook,
    )
    result = changelog.render_changelog(tree, loader, template)

    RE_HEADER = re.compile(r"^### (?P<type>.+)$")
    # There should be only "overridden" change type headers
    for no, line in enumerate(result.splitlines()):
        if (line := line.strip()) and (match := RE_HEADER.match(line)):
            change_type = match.group("type")
            assert change_type == "overridden", (
                f"Line {no}: type {change_type} should have been overridden"
            )


def test_render_changelog_with_changelog_release_hook(
    gitcommits, tags, any_changelog_format: ChangelogFormat
):
    def changelog_release_hook(release: dict, tag: git.GitTag | None) -> dict:
        release["extra"] = "whatever"
        return release

    parser = ConventionalCommitsCz.commit_parser
    changelog_pattern = ConventionalCommitsCz.changelog_pattern
    tree = changelog.generate_tree_from_commits(
        gitcommits,
        tags,
        parser,
        changelog_pattern,
        changelog_release_hook=changelog_release_hook,
    )
    for release in tree:
        assert release["extra"] == "whatever"


def test_get_smart_tag_range_returns_an_extra_for_a_range(tags):
    start, end = (
        tags[0],
        tags[2],
    )  # len here is 3, but we expect one more tag as designed
    res = changelog.get_smart_tag_range(tags, start.name, end.name)
    assert 4 == len(res)


def test_get_smart_tag_range_returns_an_extra_for_a_single_tag(tags):
    start = tags[0]  # len here is 1, but we expect one more tag as designed
    res = changelog.get_smart_tag_range(tags, start.name)
    assert 2 == len(res)


@dataclass
class TagDef:
    name: str
    is_version: bool
    is_legacy: bool
    is_ignored: bool


TAGS_PARAMS = (
    pytest.param(TagDef("1.2.3", True, False, False), id="version"),
    # We test with `v-` prefix as `v` prefix is a special case kept for backward compatibility
    pytest.param(TagDef("v-1.2.3", False, True, False), id="v-prefix"),
    pytest.param(TagDef("project-1.2.3", False, True, False), id="project-prefix"),
    pytest.param(TagDef("ignored", False, False, True), id="ignored"),
    pytest.param(TagDef("unknown", False, False, False), id="unknown"),
)


@pytest.mark.parametrize("tag", TAGS_PARAMS)
def test_tag_rules_tag_format_only(tag: TagDef):
    rules = changelog.TagRules(Pep440, "$version")
    assert rules.is_version_tag(tag.name) is tag.is_version


@pytest.mark.parametrize("tag", TAGS_PARAMS)
def test_tag_rules_with_legacy_tags(tag: TagDef):
    rules = changelog.TagRules(
        scheme=Pep440,
        tag_format="$version",
        legacy_tag_formats=["v-$version", "project-${version}"],
    )
    assert rules.is_version_tag(tag.name) is tag.is_version or tag.is_legacy


@pytest.mark.parametrize("tag", TAGS_PARAMS)
def test_tag_rules_with_ignored_tags(tag: TagDef):
    rules = changelog.TagRules(
        scheme=Pep440, tag_format="$version", ignored_tag_formats=["ignored"]
    )
    assert rules.is_ignored_tag(tag.name) is tag.is_ignored


def test_tags_rules_get_version_tags(capsys: pytest.CaptureFixture):
    tags = [
        git.GitTag("v1.1.0", "17efb44d2cd16f6621413691a543e467c7d2dda6", "2019-04-14"),
        git.GitTag("v1.0.0", "aa44a92d68014d0da98965c0c2cb8c07957d4362", "2019-03-01"),
        git.GitTag("1.0.0b2", "aab33d13110f26604fb786878856ec0b9e5fc32b", "2019-01-18"),
        git.GitTag(
            "project-not-a-version",
            "7c7e96b723c2aaa1aec3a52561f680adf0b60e97",
            "2019-01-17",
        ),
        git.GitTag(
            "not-a-version", "c52eca6f74f844ab3ffbde61d98ef96071e132b7", "2018-12-17"
        ),
        git.GitTag(
            "star-something", "c52eca6f74f844ab3ffbde61d98fe96071e132b2", "2018-11-12"
        ),
        git.GitTag("known", "b3f89892222340150e32631ae6b7aab65230036f", "2018-09-22"),
        git.GitTag(
            "ignored-0.9.3", "684e0259cc95c7c5e94854608cd3dcebbd53219e", "2018-09-22"
        ),
        git.GitTag(
            "project-0.9.3", "dacc86159b260ee98eb5f57941c99ba731a01399", "2018-07-28"
        ),
        git.GitTag(
            "anything-0.9", "5141f54503d2e1cf39bd666c0ca5ab5eb78772ab", "2018-01-10"
        ),
        git.GitTag(
            "project-0.9.2", "1541f54503d2e1cf39bd777c0ca5ab5eb78772ba", "2017-11-11"
        ),
        git.GitTag(
            "ignored-0.9.1", "46e9032e18a819e466618c7a014bcb0e9981af9e", "2017-11-11"
        ),
    ]

    rules = changelog.TagRules(
        scheme=Pep440,
        tag_format="v$version",
        legacy_tag_formats=["$version", "project-${version}"],
        ignored_tag_formats=[
            "known",
            "ignored-${version}",
            "star-*",
            "*-${major}.${minor}",
        ],
    )

    version_tags = rules.get_version_tags(tags, warn=True)
    assert {t.name for t in version_tags} == {
        "v1.1.0",
        "v1.0.0",
        "1.0.0b2",
        "project-0.9.3",
        "project-0.9.2",
    }

    captured = capsys.readouterr()
    assert captured.err.count("Invalid version tag:") == 2
    assert captured.err.count("not-a-version") == 2


def test_changelog_file_name_from_args_and_config():
    mock_config = Mock(spec=BaseConfig)
    mock_path = Mock(spec=Path)
    mock_path.parent = Path("/my/project")
    mock_config.path = mock_path
    mock_config.settings = {
        "name": "cz_conventional_commits",
        "changelog_file": "CHANGELOG.md",
        "encoding": "utf-8",
        "changelog_start_rev": "v1.0.0",
        "tag_format": "$version",
        "legacy_tag_formats": [],
        "ignored_tag_formats": [],
        "incremental": True,
        "changelog_merge_prerelease": True,
    }

    args = {
        "file_name": "CUSTOM.md",
        "incremental": None,
        "dry_run": False,
        "unreleased_version": "1.0.1",
    }
    changelog = Changelog(mock_config, args)
    assert os.path.normpath(changelog.file_name) == os.path.normpath(
        os.path.join("/my/project", "CUSTOM.md")
    )

    args = {"incremental": None, "dry_run": False, "unreleased_version": "1.0.1"}
    changelog = Changelog(mock_config, args)
    assert os.path.normpath(changelog.file_name) == os.path.normpath(
        os.path.join("/my/project", "CHANGELOG.md")
    )

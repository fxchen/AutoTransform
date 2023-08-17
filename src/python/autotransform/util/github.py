# AutoTransform
# Large scale, component based code modification library
#
# Licensed under the MIT License <http://opensource.org/licenses/MIT>
# SPDX-License-Identifier: MIT
# Copyright (c) 2022-present Nathan Rockenbach <http://github.com/nathro>

# @black_format

"""Github related utilities."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from functools import cached_property
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.error import HTTPError

import pytz
from autotransform.config import get_config
from autotransform.event.debug import DebugEvent
from autotransform.event.handler import EventHandler
from autotransform.event.warning import WarningEvent
from autotransform.repo.git import GitRepo
from fastcore.basics import AttrDict  # type: ignore
from ghapi.all import GhApi, gh2date  # type: ignore


class GithubUtils:
    """A class for utilities used to interact with Github. Stores instances of objects to prevent
    excessive API usage.

    Attributes:
        __instances (Dict[str, GithubUtils]): A mapping of repo names to Util objects.
        _api (GhApi): The API object used to handle requests to Github.
        _fully_qualified_repo (str): The fully qualified name of the Github repo.
        _gists (Dict[str, Gist]): A mapping from id to Gist.
        _pulls (Dict[int, PullRequest]): A mapping from pull number to PullRequest.
    """

    __instances: Dict[str, GithubUtils] = {}

    _api: GhApi
    _fully_qualified_repo: str
    _gists: Dict[str, Gist]
    _pulls: Dict[int, PullRequest]

    BEGIN_SCHEMA: str = "<<<<BEGIN SCHEMA>>>>"
    END_SCHEMA: str = "<<<<END SCHEMA>>>>"

    BEGIN_BATCH: str = "<<<<BEGIN BATCH>>>>"
    END_BATCH: str = "<<<<END BATCH>>>>"

    def __init__(self, fully_qualified_repo: str):
        """A simple constructor.

        Args:
            fully_qualified_repo (str): The fully qualified name of the repo, uses the
                format {owner}/{repo}.
        """

        assert fully_qualified_repo not in GithubUtils.__instances
        token = get_config().github_token
        url = get_config().github_base_url
        repo_parts = fully_qualified_repo.split("/")
        self._api = GhApi(token=token, gh_host=url, owner=repo_parts[0], repo=repo_parts[1])
        self._fully_qualified_repo = fully_qualified_repo
        self._gists: Dict[str, Gist] = {}
        self._pulls: Dict[int, PullRequest] = {}

    @staticmethod
    def get(fully_qualified_repo: str) -> GithubUtils:
        """Gets an instance of the GithubUtils for a specific repo which is stored in a cache.

        Args:
            fully_qualified_repo (str): The fully qualified name of the repo, uses the
                format {owner}/{repo}.

        Returns:
            GithubUtils: A util class with a cached API object for requests.
        """
        return GithubUtils.__instances.setdefault(fully_qualified_repo, GithubUtils(fully_qualified_repo))

    def get_user_id(self) -> int:
        """Gets the user ID of the authenticated user.

        Returns:
            int: The user ID of the authenticated user.
        """

        return self._api.users.get_authenticated().id

    def create_pull_request(self, title: str, body: str, base: str, head: str) -> PullRequest:
        """Create a pull request with the given information.

        Args:
            title (str): The title of the pull request.
            body (str): The body of the pull request.
            base (str): The base branch the pull request is against.
            head (str): The head to apply to the base branch.

        Returns:
            PullRequest: The created pull request.
        """

        pull = self._api.pulls.create(title=title, head=head, base=base, body=body)
        return PullRequest(self._api, pull.number)

    def get_pull_request(self, pull_number: int) -> PullRequest:
        """Gets a pull request.

        Args:
            pull_number (int): The number of the pull request.

        Returns:
            PullRequest: The pull request.
        """

        if pull_number not in self._pulls:
            self._pulls[pull_number] = PullRequest(self._api, pull_number)
        return self._pulls[pull_number]

    def create_gist(
        self, files: Dict[str, Dict[str, str]], description: str, public: bool = True
    ) -> Gist:
        """Creates a Gist containing the supplied information

        Args:
            files (Dict[str, Dict[str, str]]): The files to include in the gist.
            description (str): A simple description of the gist.
            public (bool, optional): Whether the gist should be public. Defaults to True.

        Returns:
            Gist: The created gist.
        """

        res = self._api.gists.create(description=description, files=files, public=public)
        return Gist(self._api, res.id)

    def get_gist(self, gist_id: str) -> Gist:
        """Gets a wrapper around the requested gist.

        Args:
            gist_id (str): The id of the gist.

        Returns:
            Gist: The requested gist.
        """

        if gist_id not in self._gists:
            self._gists[gist_id] = Gist(self._api, gist_id)
        return self._gists[gist_id]

    def get_open_pull_requests(self, base: Optional[str] = None) -> List[PullRequest]:
        """Gets all outstanding pull requests from the repo.

        Args:
            base (Optional[str], optional): The base branch to fetch pull requests against.
                Defaults to None.

        Returns:
            List[PullRequest]: The list of all requests outstanding for the repo.
        """

        username = self._api.users.get_authenticated().login
        query = f"type:pr state:open author:{username} repo:{self._fully_qualified_repo}"
        if base is not None:
            query = f"{query} base:{base}"
        page = 1
        num_per_page = 100
        fetch_more = True
        all_pulls: Set[int] = set()
        while fetch_more:
            prs = self._api.search.issues_and_pull_requests(
                q=query, sort="created", order="desc", per_page=num_per_page, page=page
            )
            fetch_more = len(prs["items"]) == num_per_page
            page = page + 1
            all_pulls = all_pulls.union([pr.number for pr in prs["items"]])

        pulls = [self.get_pull_request(pull_number) for pull_number in all_pulls]

        return [pull for pull in pulls if pull.branch.startswith(GitRepo.BRANCH_NAME_PREFIX)]

    def create_workflow_dispatch(
        self, workflow: str | int, ref: str, inputs: Dict[str, Any]
    ) -> Optional[str]:
        """Creates a workflow dispatch event and runs it.

        Args:
            workflow (str | int): The ID or filename of the workflow to run.
            ref (str): The ref to run the workflow on.
            inputs (Dict[str, Any]): Any inputs the workflow needs.

        Returns:
            Optional[str]: The best guess URL of the workflow run. None if failed.
        """

        try:
            current_time = datetime.now().replace(microsecond=0)
            check_time = current_time - timedelta(days=1)
            self._api.actions.create_workflow_dispatch(workflow_id=workflow, ref=ref, inputs=inputs)
            # We wait a bit to make sure Github's API is updated before printing a best guess of the
            # Workflow run's URL
            time.sleep(2)
            EventHandler.get().handle(DebugEvent({"message": "Checking for workflow run URL"}))
            res = self._api.actions.list_workflow_runs(
                workflow_id=workflow,
                actor=self._api.users.get_authenticated().login,
                branch=ref,
                event="workflow_dispatch",
                created=f">={check_time.isoformat()}",
            )
            if not res.workflow_runs:
                return ""
            return res.workflow_runs[0].html_url
        except HTTPError as err
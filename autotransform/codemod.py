# AutoTransform
# Large scale, component based code modification library
#
# Licensed under the MIT License <http://opensource.org/licenses/MIT
# SPDX-License-Identifier: MIT
# Copyright (c) 2022-present Nathan Rockenbach <http://github.com/nathro>

import argparse
import time

from autotransform.batcher.single import SingleBatcher
from autotransform.common.package import AutoTransformPackage
from autotransform.common.runner import Runner
from autotransform.filter.extension import ExtensionFilter, Extensions
from autotransform.input.directory import DirectoryInput
from autotransform.transformer.regex import RegexTransformer
from autotransform.worker.local import LocalWorker


def parse_arguments():
    parser = argparse.ArgumentParser(description="Runs simple regex based codemods")
    parser.add_argument(
        "-e",
        "--extensions",
        metavar="extensions",
        type=str,
        required=False,
        help="A comma separated list of extensions for files to modify",
    )
    parser.add_argument(
        "-d",
        "--directory",
        metavar="directory",
        type=str,
        required=True,
        help="The directory to search within within for files to modify",
    )
    parser.add_argument("pattern", metavar="pattern", type=str, help="The pattern to be replaced")
    parser.add_argument(
        "replacement", metavar="replacement", type=str, help="What you wish to replace with"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    inp = DirectoryInput({"path": args.directory})
    transformer = RegexTransformer({"pattern": args.pattern, "replacement": args.replacement})
    batcher = SingleBatcher(
        {"metadata": {"title": "Just a test", "summary": "This is just a test", "tests": "This?"}}
    )
    filters = []
    extensions = args.extensions
    if isinstance(extensions, str):
        extensions = extensions.split(",")
        extensions = ["." + extension for extension in extensions]
        for extension in extensions:
            assert Extensions.has_value(extension)
        filters.append(ExtensionFilter({"extensions": extensions}))

    package = AutoTransformPackage(inp, batcher, transformer, filters=filters)
    runner = Runner(package, LocalWorker)
    start_time = time.time()
    runner.start()
    timeout = 30
    while not runner.is_finished() and time.time() <= start_time + timeout:
        time.sleep(1)
    runner.kill()


if __name__ == "__main__":
    main()

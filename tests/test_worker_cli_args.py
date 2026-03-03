from __future__ import annotations

import shlex

from agent_hub.worker_cli import build_arg_parser


def parse_args(argv: str):
    parser = build_arg_parser()
    return parser.parse_args(shlex.split(argv))


def test_worker_cli_defaults():
    args = parse_args("")
    assert args.poll_interval == 5.0
    assert args.batch_size == 10
    assert args.log_level.upper() == "INFO"


def test_worker_cli_custom_values():
    args = parse_args("--poll-interval 1.5 --batch-size 3 --log-level DEBUG")
    assert args.poll_interval == 1.5
    assert args.batch_size == 3
    assert args.log_level.upper() == "DEBUG"

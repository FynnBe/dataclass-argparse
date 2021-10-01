"""example 2: group manually and parse argument groups separately"""

import argparse
from dataclasses import dataclass, field
from typing import ClassVar

from dataclass_argparse import NonEmptyList, TypedNamespace


@dataclass
class ArgsA(TypedNamespace):
    a1: ClassVar[int] = 1
    a2: NonEmptyList[int] = field(default_factory=lambda: [1], metadata={"help": "help for a2."})


parser_a = ArgsA.get_parser("group A")


def func_a(args: ArgsA):
    print("func a", args.a1, args.a2)


@dataclass
class ArgsB(TypedNamespace):
    b1: str = field(metadata={"metavar": "REQ_B1"})
    b2: bool = False


parser_b = ArgsB.get_parser("group B")


def func_b(args: ArgsB):
    print("func b", args.b1, args.b2)


# join created parsers with argparse
joint_parser = argparse.ArgumentParser(parents=[parser_a, parser_b], add_help=False)
# arguments used directly (not part of a typed namespace groups)
general_args = joint_parser.add_argument_group("General")
general_args.add_argument("-h", "--help", action="help", help="show this help message and exit")


if __name__ == "__main__":
    joint_parser.parse_args()  # show help/complain about missing/unknown args, but ignore parse args

    # parse args
    args_a, unused_args = parser_a.parse_known_args()
    args_b, unused_args = parser_b.parse_known_args(unused_args)

    joint_parser.print_help()

    func_a(args_a)
    func_b(args_b)

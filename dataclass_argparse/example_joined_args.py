"""example 1: group arguments with inheritance"""

from dataclasses import dataclass, field
from typing import Tuple

from dataclass_argparse import NonEmptyList, TypedNamespace


@dataclass
class ArgsA(TypedNamespace):
    a1: int = 1
    a2: NonEmptyList[int] = field(default_factory=lambda: [1], metadata={"help": "help for a2."})


@dataclass
class ArgsB(TypedNamespace):
    b1: str = field(metadata={"metavar": "REQ_B1"})
    b2: bool = False
    b3: Tuple[int, int] = field(default=(1, 2), metadata=dict(help="help for b3."))


# join arguments by inheritance
@dataclass
class Args(ArgsA, ArgsB):
    pass


def func_a(args: ArgsA):
    print("func a", args.a1, args.a2)


def func_b(args: ArgsB):
    print("func b", args.b1, args.b2, args.b3)


def func_c(args: Args):
    print("func a", args.a1, args.a2)
    print("func b", args.b1, args.b2, args.b3)


parser = Args.get_parser_grouped_by_parents()

if __name__ == "__main__":
    parsed_args = parser.parse_args()

    parser.print_help()

    func_a(parsed_args)
    func_b(parsed_args)
    func_c(parsed_args)

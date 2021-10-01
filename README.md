# dataclass-argparse
Define command line arguments as type annotated namespace dataclasses.

Advantages:
 - fast, straight forward definition of command line arguments
 - use inheritance to combine argument groups 
 - use inheritance to define sub-parsers
 - keep your parsed args in one joined (or several separate) namespace dataclass instances 

# Example 1: group arguments with inheritance; parse jointly
```python
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

```

# Example 2: group arguments with argparse; parse groups separately
```python
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

```
import argparse
import dataclasses
from typing import Callable, ClassVar, Generic, List, Optional, Sequence, Tuple, Type, TypeVar

try:
    from typing import get_args, get_origin
except ImportError:

    def get_args(obj):
        return obj.__args__

    def get_origin(obj):
        try:
            return obj.__parameters__ or None
        except AttributeError:
            return None


NamespaceType = TypeVar("NamespaceType")


class TypedArgumentParser(argparse.ArgumentParser, Generic[NamespaceType]):
    def __init__(self, *super_args, name_space_class: Type[NamespaceType], **super_kwargs):
        self.name_space_class = name_space_class
        super().__init__(*super_args, **super_kwargs)

    def parse_args(self, args=None, namespace: Optional[NamespaceType] = None) -> NamespaceType:
        if namespace is None:
            namespace = self.name_space_class()

        return super().parse_args(args, namespace)

    def parse_known_args(
        self, args=None, namespace: Optional[NamespaceType] = None
    ) -> Tuple[NamespaceType, Optional[Sequence[str]]]:
        if namespace is None:
            namespace = self.name_space_class()

        return super().parse_known_args(args, namespace)


T = TypeVar("T")


class NonEmptyList(List[T]):
    pass


class REQUIRED_ARG:
    pass


@dataclasses.dataclass
class TypedNamespace:
    """a type annotated namespace.
Define command line arguments in an inheriting class `MyTypedNamespace(TypeNamedSpace)`
and use the `TypedArgumentParser` returned by `MyTypedNamespace.get_parser()`
    
example 1: group arguments with inheritance
```
@dataclasses.dataclass
class ArgsA(TypedNamespace):
    a: int = 1
    c: NonEmptyList[int] = dataclasses.field(default_factory=lambda: [1], metadata={"help": "help for c."})

@dataclasses.dataclass
class ArgsB(TypedNamespace):
    b: bool = False
    d: str = dataclasses.field(default=REQUIRED_ARG, metadata={"metavar": "REQ_D"})

@dataclasses.dataclass
class Args(ArgsA, ArgsB):
    pass

def func_a(args: ArgsA):
    print("func a", args.a, args.c)

def func_b(args: ArgsB):
    print("func b", args.b, args.d)

parser = Args.get_parser_grouped_by_parents()
parsed_args = parser.parse_args()

parser.print_help()

func_a(parsed_args)
func_b(parsed_args)
```

example 2: group manually and parse argument groups separately
```
@dataclasses.dataclass
class ArgsA(TypedNamespace):
    a: ClassVar[int] = 1
    c: NonEmptyList[int] = dataclasses.field(default_factory=lambda: [1], metadata={"help": "help for c."})


parser_a = ArgsA.get_parser("group A")


def func_a(args: ArgsA):
    print("func a", args.a, args.c)


@dataclasses.dataclass
class ArgsB(TypedNamespace):
    b: bool = False
    d: str = dataclasses.field(default=REQUIRED_ARG, metadata={"metavar": "REQ_D"})


parser_b = ArgsB.get_parser("group B")


def func_b(args: ArgsB):
    print("func b", args.b, args.d)


joint_parser = argparse.ArgumentParser(parents=[parser_a, parser_b], add_help=False)
# arguments used directly (not part of a typed namespace groups)
general_args = joint_parser.add_argument_group("General")
general_args.add_argument("-h", "--help", action="help", help="show this help message and exit")


joint_parser.parse_args()  # show help/complain about missing/unknown args, but ignore parse args

# parse args
args_a, unused_args = parser_a.parse_known_args()
args_b, unused_args = parser_b.parse_known_args(unused_args)

joint_parser.print_help()

func_a(args_a)
func_b(args_b)

```
"""

    @classmethod
    def get_parser(
        cls: Type[NamespaceType], group_title: Optional[str] = None, add_help: bool = False
    ) -> TypedArgumentParser[NamespaceType]:
        ret_parser = TypedArgumentParser(name_space_class=cls, add_help=add_help)
        if group_title is None:
            group = ret_parser
        else:
            group = ret_parser.add_argument_group(title=group_title)

        for field in dataclasses.fields(cls):
            arg = field.name
            if arg in ("h", "help"):
                group.add_argument("-h", "--help", action="help", help="show this help message and exit")
                continue

            arg_type = field.type

            type_origin = get_origin(arg_type)
            if type_origin is ClassVar:
                continue

            try:
                default = field.default_factory()
            except TypeError:
                default = field.default

            kwargs = {}
            help_comment = str(field.metadata.get("help", ""))
            if help_comment:
                kwargs["help"] = help_comment

            metavar = str(field.metadata.get("metavar", ""))
            if metavar:
                kwargs["metavar"] = metavar

            if type_origin is None:
                kwargs["type"] = arg_type
            elif (
                type_origin is list or type_origin is NonEmptyList or type_origin is List
            ):  # List case only required for py<3.8
                arg_types = get_args(arg_type)
                if len(arg_types) != 1:
                    raise NotImplementedError(arg_type)

                kwargs["type"] = arg_types[0]
                kwargs["nargs"] = "+" if type_origin is NonEmptyList else "*"
            else:
                raise NotImplementedError(type_origin)

            if default is REQUIRED_ARG:
                kwargs["required"] = True
            elif isinstance(default, bool):
                kwargs["action"] = "store_false" if default else "store_true"
                kwargs.pop("type")
            else:
                kwargs["help"] = f"{kwargs.get('help', '')} default: {default}"

            group.add_argument(f"--{arg}", **kwargs)

        return ret_parser

    @classmethod
    def get_parser_grouped_by_parents(
        cls: Type[NamespaceType],
        add_help: bool = True,
        parent_name_to_group_name: Callable[[str], str] = lambda pname: pname.replace("Namespace", "").replace(
            "Args", ""
        ),
    ) -> TypedArgumentParser[NamespaceType]:
        parent_name_space_classes: List[Type[TypedNamespace]] = [
            parent for parent in cls.__bases__ if issubclass(parent, TypedNamespace)
        ]
        parent_parsers = [
            parent.get_parser(parent_name_to_group_name(parent.__name__)) for parent in parent_name_space_classes
        ]

        ret_parser = TypedArgumentParser(name_space_class=cls, add_help=False, parents=parent_parsers)
        if add_help:
            help_group = ret_parser.add_argument_group("Help")
            help_group.add_argument("-h", "--help", action="help", help="show this help message and exit")

        return ret_parser


if __name__ == "__main__":

    @dataclasses.dataclass
    class ArgsA(TypedNamespace):
        a: int = 1
        c: NonEmptyList[int] = dataclasses.field(default_factory=lambda: [1], metadata={"help": "help for c."})

    @dataclasses.dataclass
    class ArgsB(TypedNamespace):
        b: bool = False
        d: str = dataclasses.field(default=REQUIRED_ARG, metadata={"metavar": "REQ_D"})

    @dataclasses.dataclass
    class Args(ArgsA, ArgsB):
        pass

    def func_a(args: ArgsA):
        print("func a", args.a, args.c)

    def func_b(args: ArgsB):
        print("func b", args.b, args.d)

    parser = Args.get_parser_grouped_by_parents()
    parsed_args = parser.parse_args()

    parser.print_help()

    func_a(parsed_args)
    func_b(parsed_args)

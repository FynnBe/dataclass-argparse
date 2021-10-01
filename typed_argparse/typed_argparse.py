import argparse
import dataclasses
from argparse import _ArgumentGroup
from typing import Any, Callable, ClassVar, Dict, Generic, List, Optional, Sequence, Tuple, Type, TypeVar, Union

try:
    from typing import Annotated  # type: ignore
except ImportError:
    from typing_extensions import Annotated  # type: ignore

try:
    from typing import get_args, get_origin
except ImportError:
    from typing_extensions import Annotated  # type: ignore

    def get_args(obj):  # type: ignore
        return obj.__args__

    def get_origin(obj):  # type: ignore
        try:
            return obj.__parameters__ or None
        except AttributeError:
            return None


NamespaceType = TypeVar("NamespaceType", bound=argparse.Namespace)


class TypedArgumentParser(argparse.ArgumentParser, Generic[NamespaceType]):
    def __init__(self, *super_args, name_space_class: Type[NamespaceType], **super_kwargs):
        self.name_space_class = name_space_class
        super().__init__(*super_args, **super_kwargs)

    def get_required_kwargs_placeholder(self):
        return {
            f.name: None
            for f in dataclasses.fields(self.name_space_class)
            if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
        }

    def parse_args(  # type: ignore
        self, args: Optional[Sequence[str]] = None, namespace: Optional[NamespaceType] = None
    ) -> NamespaceType:
        if namespace is None:
            namespace = self.name_space_class(**self.get_required_kwargs_placeholder())

        return super().parse_args(args, namespace)

    def parse_known_args(  # type: ignore
        self, args=None, namespace: Optional[NamespaceType] = None
    ) -> Tuple[NamespaceType, Optional[Sequence[str]]]:
        if namespace is None:
            namespace = self.name_space_class(**self.get_required_kwargs_placeholder())

        return super().parse_known_args(args, namespace)  # type: ignore


T = TypeVar("T")


# NonEmptyList = NewType("NonEmptyList", List[T])
# class NonEmptyList(Sized, Generic[T]):
#     pass
@dataclasses.dataclass(frozen=True)
class MinLen:
    value: int


NonEmptyList = Annotated[List[T], MinLen(1)]


class REQUIRED:
    pass


@dataclasses.dataclass
class TypedNamespace(argparse.Namespace):
    """a type annotated namespace.

    Define command line arguments in a derived class `MyTypedNamespace(TypeNamedSpace)`
    and use the `TypedArgumentParser` returned by `MyTypedNamespace.get_parser()`
    """

    @classmethod
    def get_parser(
        cls: Type[NamespaceType], group_title: Optional[str] = None, add_help: bool = False
    ) -> TypedArgumentParser[NamespaceType]:
        ret_parser = TypedArgumentParser(name_space_class=cls, add_help=add_help)
        if group_title is None:
            group: Union[TypedArgumentParser, _ArgumentGroup] = ret_parser
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

            if field.default_factory is dataclasses.MISSING:  # type: ignore
                default = field.default
            else:
                default = field.default_factory()  # type: ignore

            kwargs: Dict[str, Any] = {}
            help_comment = str(field.metadata.get("help", ""))
            if help_comment:
                kwargs["help"] = help_comment

            metavar = str(field.metadata.get("metavar", ""))
            if metavar:
                kwargs["metavar"] = metavar

            if type_origin is None:
                kwargs["type"] = arg_type
            elif (
                type_origin is list
                or type_origin is NonEmptyList
                or type_origin is List
                or get_origin(type_origin) is list
                or get_origin(type_origin) is List
            ):  # List case only required for py<3.8
                arg_types = get_args(arg_type)
                if len(arg_types) != 1:
                    raise NotImplementedError(arg_type)

                kwargs["type"] = arg_types[0]
                kwargs["nargs"] = "+" if type_origin is NonEmptyList else "*"
            elif type_origin is tuple or type_origin is Tuple:
                arg_types = get_args(arg_type)
                if len(set(arg_types)) != 1:
                    raise NotImplementedError("Tuple with different types not implemented")

                kwargs["type"] = arg_types[0]
                kwargs["nargs"] = len(arg_types)
            else:
                raise NotImplementedError(type_origin)

            if default is dataclasses.MISSING:
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

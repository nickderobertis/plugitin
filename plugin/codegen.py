from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Optional, List, Type, Any
import importlib.util
import inspect
import astor
import ast

from plugin import PluginSpec


def get_module_from_file(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("temp_module", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_plugin_specs_from_module(mod: ModuleType) -> List[Type[PluginSpec]]:
    specs: List[Type[PluginSpec]] = []
    for val in mod.__dict__.values():
        if not inspect.isclass(val):
            continue
        if issubclass(val, PluginSpec) and not val == PluginSpec:
            specs.append(val)
    return specs


def get_ast_from_file(path: Path) -> ast.Module:
    return ast.parse(path.read_text())


class PluginSpecAstExtractor(ast.NodeVisitor):
    def __init__(self):
        self.class_defs: List[ast.ClassDef] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        for base in node.bases:
            # TODO: make codegen work if PluginSpec is renamed on import
            if base.id == "PluginSpec":
                self.class_defs.append(node)
                break
        self.generic_visit(node)


def get_plugin_spec_asts_from_module_ast(tree: ast.Module) -> List[ast.ClassDef]:
    extractor = PluginSpecAstExtractor()
    extractor.visit(tree)
    return extractor.class_defs


def _ast_method_args_to_call_args(args: ast.arguments) -> str:
    args = deepcopy(args)
    del args.args[0]  # delete self argument
    arg_attrs = (
        "args",
        "posonlyargs",
        "kwonlyargs",
        "vararg",
        "kwarg",
        "kw_defaults",
        "defaults",
    )
    for attr in arg_attrs:
        arg_list = getattr(args, attr)
        if arg_list is None:
            continue
        for arg in arg_list:
            arg.annotation = None
    return args


class PluginTransformer:
    def transform_class_def(
        self,
        node: ast.ClassDef,
        replace_name: str = "Chain",
        plugin_name: str = "ChainPlugin",
    ) -> ast.ClassDef:
        new_node = deepcopy(node)
        plugin_spec_name = node.name
        new_name = plugin_spec_name.replace("Spec", replace_name)
        new_node.name = new_name
        new_bases = []
        for base in node.bases:
            if base.id == "PluginSpec":
                new_base = deepcopy(base)
                new_base.id = plugin_name
                new_bases.append(new_base)
            else:
                new_bases.append(base)
        new_node.bases = new_bases

        new_body = []
        for func_def in node.body:
            if not isinstance(func_def, ast.FunctionDef):
                # Don't modify non-methods
                new_body.append(func_def)
                continue
            new_def = deepcopy(func_def)
            new_def = self.transform_method(new_def)
            new_body.append(new_def)
        new_node.body = new_body
        return new_node

    def transform_method(self, func_def: ast.FunctionDef) -> ast.FunctionDef:
        execute_args = _ast_method_args_to_call_args(func_def.args)
        body_str = (
            f'return self.execute("{func_def.name}", {astor.to_source(execute_args)})'
        )
        ast_return = ast.parse(body_str).body
        func_def.body = ast_return
        return func_def


class ChainPluginTransformer(ast.NodeTransformer, PluginTransformer):
    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        new_node = self.transform_class_def(node, "Chain", "ChainPlugin")
        return new_node


class AggregatePluginTransformer(ast.NodeTransformer, PluginTransformer):
    def transform_method(self, func_def: ast.FunctionDef) -> ast.FunctionDef:
        func_def = super().transform_method(func_def)
        orig_ret = func_def.returns
        if orig_ret is None:
            return func_def
        # Wrap return type annotation in list
        new_ret = ast.Subscript(
            value=ast.Name(id="List"), slice=ast.Index(value=orig_ret)
        )
        func_def.returns = new_ret
        return func_def

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        new_node = self.transform_class_def(node, "Aggregate", "AggregatePlugin")
        return new_node


def plugin_spec_ast_to_chain_definition(tree: ast.ClassDef) -> str:
    tree = deepcopy(tree)
    transformer = ChainPluginTransformer()
    tree = transformer.visit(tree)
    return astor.to_source(tree)


def plugin_spec_ast_to_aggregate_definition(tree: ast.ClassDef) -> str:
    tree = deepcopy(tree)
    transformer = AggregatePluginTransformer()
    tree = transformer.visit(tree)
    return astor.to_source(tree)


def main(file: str, output_file: Optional[str] = None):
    path = Path(file)
    tree = get_ast_from_file(path)
    spec_defs = get_plugin_spec_asts_from_module_ast(tree)
    chain_defs = [plugin_spec_ast_to_chain_definition(spec) for spec in spec_defs]
    agg_defs = [plugin_spec_ast_to_aggregate_definition(spec) for spec in spec_defs]
    all_defs = [*chain_defs, *agg_defs]
    full_str = "\n\n".join(all_defs)
    if output_file is not None:
        output_file = Path(output_file)
        output_file.write_text(full_str)
    else:
        print(full_str)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=str,
        help="Input file which should contain subclass of PluginSpec",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        default=None,
        help="Output file to write generated Plugin classes to. If not specified, writes to stdout",
    )
    args = parser.parse_args()
    main(args.file, args.output)
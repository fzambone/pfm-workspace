#!/usr/bin/env python3
"""
generate-types.py — OpenAPI → TypeScript interface generator for pfm-ui-react.

Reads a Swagger 2.0 spec (local file or HTTPS URL) and emits TypeScript interfaces
following pfm-ui-react conventions:
  - snake_case field names → camelCase
  - integer → number  (money fields get a JSDoc minor-units comment)
  - $ref → resolved interface name
  - array of $ref → InterfaceName[]
  - nullable: true / x-nullable: true → T | null
  - enum values → union literal type ('val1' | 'val2')
  - nested objects → separate named interfaces
  - no `any` types

Usage:
  python3 generate-types.py --spec /path/to/swagger.yaml
  python3 generate-types.py --spec /path/to/swagger.yaml --output ./out
  python3 generate-types.py --spec https://pfm-go-api.zambone.dev/api/v1/openapi.yaml
  python3 generate-types.py --spec /path/to/swagger.yaml --only AccountResponse,UserResponse

Options:
  --spec     Path to swagger.yaml or HTTPS URL (required)
  --output   Directory to write <InterfaceName>.generated.ts files.
             Omit to print all interfaces to stdout.
  --only     Comma-separated list of interface names to generate (default: all)
  --force    Overwrite existing .generated.ts files (default: skip existing)
"""

import argparse
import os
import re
import sys
import urllib.request

try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML is required. Install with: pip3 install pyyaml")


# ---------------------------------------------------------------------------
# Money field heuristic
# Fields whose names match these patterns carry minor-unit monetary values.
# ---------------------------------------------------------------------------
MONEY_FIELD_PATTERNS = re.compile(
    r"^(balance|amount|.*_amount|.*_balance|price|total|subtotal)$",
    re.IGNORECASE,
)


def is_money_field(field_name: str) -> bool:
    return bool(MONEY_FIELD_PATTERNS.match(field_name))


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def def_name_to_interface(def_name: str) -> str:
    """
    Convert a swagger definition name to a TypeScript PascalCase interface name.
    Strips the 'http.' prefix that swag adds and converts to PascalCase.
    e.g. 'http.accountResponse' → 'AccountResponse'
         'http.postTransactionRequest' → 'PostTransactionRequest'
    """
    name = def_name
    if "." in name:
        name = name.split(".")[-1]
    # Already PascalCase if it starts with uppercase; otherwise capitalise first char
    return name[0].upper() + name[1:]


def ref_to_interface(ref: str) -> str:
    """Extract the interface name from a $ref string."""
    # e.g. '#/definitions/http.accountResponse' → 'AccountResponse'
    def_name = ref.split("/")[-1]
    return def_name_to_interface(def_name)


# ---------------------------------------------------------------------------
# Type resolution
# ---------------------------------------------------------------------------

def resolve_field_type(field_name: str, field_schema: dict, definitions: dict) -> tuple[str, str | None]:
    """
    Resolve a field schema to a TypeScript type string and an optional JSDoc comment.
    Returns (ts_type, jsdoc_comment_or_None).
    """
    if not isinstance(field_schema, dict):
        return "unknown", None

    nullable = field_schema.get("nullable") or field_schema.get("x-nullable", False)

    # $ref at field level
    if "$ref" in field_schema:
        ts_type = ref_to_interface(field_schema["$ref"])
        return (f"{ts_type} | null" if nullable else ts_type), None

    json_type = field_schema.get("type")
    enum_values = field_schema.get("enum")

    # Enum → union literals
    if enum_values:
        literals = " | ".join(f"'{v}'" for v in enum_values)
        return (f"({literals}) | null" if nullable else literals), None

    # Array
    if json_type == "array":
        items = field_schema.get("items", {})
        if "$ref" in items:
            elem_type = ref_to_interface(items["$ref"])
        else:
            elem_type, _ = resolve_field_type(field_name, items, definitions)
        ts_type = f"{elem_type}[]"
        return (f"{ts_type} | null" if nullable else ts_type), None

    # Inline object (nested, unnamed) → use `object` and note the limitation
    if json_type == "object":
        ts_type = "Record<string, unknown>"
        return (f"{ts_type} | null" if nullable else ts_type), "// nested object — consider extracting a named interface"

    # Primitive mapping
    primitive_map = {
        "string": "string",
        "boolean": "boolean",
        "number": "number",
        "integer": "number",
    }
    ts_type = primitive_map.get(json_type or "", "unknown")

    comment = None
    if json_type == "integer" and is_money_field(field_name):
        comment = "// minor units (cents/centavos) — never use as float"

    return (f"{ts_type} | null" if nullable else ts_type), comment


# ---------------------------------------------------------------------------
# Interface generation
# ---------------------------------------------------------------------------

def generate_interface(def_name: str, schema: dict, definitions: dict) -> str:
    """Render a single TypeScript interface for the given swagger definition."""
    interface_name = def_name_to_interface(def_name)
    lines: list[str] = []

    lines.append(f"export interface {interface_name} {{")

    properties = schema.get("properties", {})
    if not properties:
        lines.append("  // no properties defined in spec")
    else:
        for field_name, field_schema in properties.items():
            camel_name = snake_to_camel(field_name)
            ts_type, comment = resolve_field_type(field_name, field_schema, definitions)

            field_line = f"  {camel_name}: {ts_type};"
            if comment:
                field_line += f"  {comment}"
            # Note the snake_case → camelCase mapping in a comment when it differs
            if camel_name != field_name:
                field_line += f"  // maps from '{field_name}'"
            lines.append(field_line)

    lines.append("}")
    return "\n".join(lines)


def file_header(spec_source: str) -> str:
    return (
        "/**\n"
        " * Auto-generated from OpenAPI spec.\n"
        f" * Source: {spec_source}\n"
        " *\n"
        " * DO NOT EDIT MANUALLY — re-run generate-types.py to refresh.\n"
        " * Review this file, then copy needed types into your feature's types.ts.\n"
        " */\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_spec(spec_arg: str) -> dict:
    """Load and parse the swagger YAML from a local path or HTTPS URL."""
    if spec_arg.startswith("https://") or spec_arg.startswith("http://"):
        try:
            with urllib.request.urlopen(spec_arg, timeout=10) as resp:
                content = resp.read().decode("utf-8")
        except Exception as e:
            sys.exit(f"ERROR: Could not fetch spec from {spec_arg}: {e}")
        return yaml.safe_load(content)

    if not os.path.exists(spec_arg):
        sys.exit(f"ERROR: Spec file not found: {spec_arg}")
    with open(spec_arg) as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate TypeScript interfaces from an OpenAPI (Swagger 2.0) spec."
    )
    parser.add_argument("--spec", required=True, help="Path to swagger.yaml or HTTPS URL")
    parser.add_argument(
        "--output",
        metavar="DIR",
        help="Directory to write <InterfaceName>.generated.ts files. "
             "Omit to print to stdout.",
    )
    parser.add_argument(
        "--only",
        metavar="NAMES",
        help="Comma-separated interface names to generate (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .generated.ts files",
    )
    args = parser.parse_args()

    spec = load_spec(args.spec)
    definitions: dict = spec.get("definitions", {})

    if not definitions:
        print("No definitions found in spec.", file=sys.stderr)
        sys.exit(0)

    # Filter by --only if provided
    only_set: set[str] | None = None
    if args.only:
        only_set = {n.strip() for n in args.only.split(",")}

    selected: list[tuple[str, dict]] = []
    for def_name, schema in definitions.items():
        interface_name = def_name_to_interface(def_name)
        if only_set and interface_name not in only_set:
            continue
        selected.append((def_name, schema))

    if not selected:
        print("No matching definitions found.", file=sys.stderr)
        sys.exit(0)

    header = file_header(args.spec)

    if args.output:
        # Write each interface to a separate .generated.ts file
        os.makedirs(args.output, exist_ok=True)
        written = 0
        skipped = 0
        for def_name, schema in selected:
            interface_name = def_name_to_interface(def_name)
            out_path = os.path.join(args.output, f"{interface_name}.generated.ts")

            if os.path.exists(out_path) and not args.force:
                print(f"  SKIP  {out_path} (already exists — use --force to overwrite)", file=sys.stderr)
                skipped += 1
                continue

            content = header + "\n" + generate_interface(def_name, schema, definitions) + "\n"
            with open(out_path, "w") as f:
                f.write(content)
            print(f"  WROTE {out_path}", file=sys.stderr)
            written += 1

        print(f"\nDone: {written} written, {skipped} skipped.", file=sys.stderr)
    else:
        # Print all to stdout
        print(header)
        for def_name, schema in selected:
            print(generate_interface(def_name, schema, definitions))
            print()


if __name__ == "__main__":
    main()

"""Command-line interface for Lineart prompt generator."""

import argparse
import sys

from engine import (
    generate_prompt,
    list_characters,
    load_character,
    list_outputs,
)


def main():
    parser = argparse.ArgumentParser(
        prog="lineart",
        description="人物分鏡線稿提示詞生成器 — Anime character design prompt engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── generate ──────────────────────────────────────────────────────
    gen = sub.add_parser("generate", help="Generate a prompt")
    gen.add_argument("character", help="Character ID (e.g. court_lady)")
    gen.add_argument("output", help="Output type (e.g. three_view)")
    gen.add_argument("--model", "-m", default="sd",
                     choices=["sd", "stable_diffusion", "mj", "midjourney",
                              "nai", "novelai"],
                     help="Target AI model (default: sd)")
    gen.add_argument("--lang", "-l", default="zh", choices=["zh", "en"],
                     help="Output language (default: zh)")

    # ── list ──────────────────────────────────────────────────────────
    lst = sub.add_parser("list", help="List available resources")
    lst.add_argument("target", nargs="?", choices=["characters", "outputs"],
                     default="characters",
                     help="What to list (default: characters)")
    lst.add_argument("--character", "-c", help="Character ID (required for 'outputs')")

    args = parser.parse_args()

    # ── Execute ───────────────────────────────────────────────────────
    try:
        if args.command == "generate":
            prompt = generate_prompt(
                char_id=args.character,
                output_type=args.output,
                model=args.model,
                lang=args.lang,
            )
            print(prompt)

        elif args.command == "list":
            if args.target == "characters":
                chars = list_characters()
                if not chars:
                    print("No characters found.")
                    return
                print("Available characters:")
                for c in chars:
                    print(f"  • {c}")
                print(f"\nUse: python cli.py generate <character> <output>")

            elif args.target == "outputs":
                if not args.character:
                    print("Error: --character/-c is required for 'list outputs'")
                    sys.exit(1)
                char_data = load_character(args.character)
                outputs = list_outputs(char_data)
                print(f"Output types for '{args.character}':")
                for o in outputs:
                    label = char_data["outputs"][o]["label"].get("zh", o)
                    print(f"  • {o}  ({label})")
                print(f"\nLanguages: zh, en")
                print(f"Models: sd, mj, nai")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

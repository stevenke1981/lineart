"""Command-line interface for Lineart prompt generator."""

import argparse
import sys

from engine import (
    build_custom_character,
    generate_prompt,
    generate_prompts,
    list_characters,
    list_outputs,
    list_templates,
    load_character,
)

AR_PRESETS = ["3:4", "1:1", "4:3", "16:9", "9:16", "21:9", "9:21"]


def main():
    parser = argparse.ArgumentParser(
        prog="lineart",
        description="人物分鏡線稿提示詞生成器 — Anime character design prompt engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── generate ──────────────────────────────────────────────────────
    gen = sub.add_parser("generate", help="Generate prompt(s)")
    gen.add_argument("character", nargs="?", default="", help="Character ID (omit for --custom)")
    gen.add_argument(
        "--type",
        "-t",
        default="",
        help="Output type(s), comma-separated (e.g. three_view,expressions)",
    )
    gen.add_argument(
        "--model",
        "-m",
        default="sd",
        choices=["sd", "stable_diffusion", "mj", "midjourney", "nai", "novelai"],
        help="Target AI model (default: sd)",
    )
    gen.add_argument(
        "--lang", "-l", default="zh", choices=["zh", "en"], help="Output language (default: zh)"
    )
    gen.add_argument(
        "--ar", default="", choices=AR_PRESETS + [""], help="Aspect ratio (e.g. 3:4, 16:9)"
    )
    gen.add_argument(
        "--custom", action="store_true", help="Enable custom character mode (pass fields below)"
    )
    gen.add_argument("--name", help="Custom character name (zh)")
    gen.add_argument("--name-en", help="Custom character name (en)")
    gen.add_argument("--face", help="Face shape (zh)")
    gen.add_argument("--face-en", help="Face shape (en)")
    gen.add_argument("--eyes", help="Eyes (zh)")
    gen.add_argument("--eyes-en", help="Eyes (en)")
    gen.add_argument("--expression", help="Expression (zh)")
    gen.add_argument("--expression-en", help="Expression (en)")
    gen.add_argument("--mouth", help="Mouth (zh)")
    gen.add_argument("--mouth-en", help="Mouth (en)")
    gen.add_argument("--head-angle", help="Head angle (zh)")
    gen.add_argument("--head-angle-en", help="Head angle (en)")
    gen.add_argument("--action", help="Action/pose (zh)")
    gen.add_argument("--action-en", help="Action/pose (en)")
    gen.add_argument("--hair", help="Hair style (zh)")
    gen.add_argument("--hair-en", help="Hair style (en)")
    gen.add_argument("--hair-acc", help="Hair accessories, comma-separated (zh)")
    gen.add_argument("--hair-acc-en", help="Hair accessories, comma-separated (en)")
    gen.add_argument("--robe", help="Robe/clothing (zh)")
    gen.add_argument("--robe-en", help="Robe/clothing (en)")
    gen.add_argument("--collar", help="Collar (zh)")
    gen.add_argument("--collar-en", help="Collar (en)")
    gen.add_argument("--waist", help="Waist (zh)")
    gen.add_argument("--waist-en", help="Waist (en)")

    # ── list ──────────────────────────────────────────────────────────
    lst = sub.add_parser("list", help="List available resources")
    lst.add_argument(
        "target",
        nargs="?",
        choices=["characters", "outputs", "templates"],
        default="characters",
        help="What to list (default: characters)",
    )
    lst.add_argument("--character", "-c", help="Character ID (required for 'outputs')")

    args = parser.parse_args()

    # ── Execute ───────────────────────────────────────────────────────
    try:
        if args.command == "generate":
            # Build character data
            if args.custom:
                char_data = build_custom_character(
                    {
                        "char_name": args.name or "",
                        "char_name_en": args.name_en or "",
                        "face_shape": args.face or "",
                        "face_shape_en": args.face_en or "",
                        "eyes": args.eyes or "",
                        "eyes_en": args.eyes_en or "",
                        "expression": args.expression or "",
                        "expression_en": args.expression_en or "",
                        "mouth": args.mouth or "",
                        "mouth_en": args.mouth_en or "",
                        "head_angle": args.head_angle or "",
                        "head_angle_en": args.head_angle_en or "",
                        "action": args.action or "",
                        "action_en": args.action_en or "",
                        "hair_style": args.hair or "",
                        "hair_style_en": args.hair_en or "",
                        "hair_acc": args.hair_acc or "",
                        "hair_acc_en": args.hair_acc_en or "",
                        "robe": args.robe or "",
                        "robe_en": args.robe_en or "",
                        "collar": args.collar or "",
                        "collar_en": args.collar_en or "",
                        "waist": args.waist or "",
                        "waist_en": args.waist_en or "",
                    }
                )
                char_id = ""
            else:
                if not args.character:
                    print("Error: specify a character or use --custom", file=sys.stderr)
                    sys.exit(1)
                char_data = None
                char_id = args.character

            # Parse output types (comma-separated)
            if not args.type:
                print("Error: specify --type (e.g. --type three_view,expressions)", file=sys.stderr)
                sys.exit(1)
            output_types = [o.strip() for o in args.type.split(",") if o.strip()]

            if len(output_types) == 1:
                prompt = generate_prompt(
                    output_type=output_types[0],
                    model=args.model,
                    lang=args.lang,
                    ar=args.ar,
                    char_id=char_id,
                    char_data=char_data,
                )
                print(prompt)
            else:
                results = generate_prompts(
                    output_types=output_types,
                    model=args.model,
                    lang=args.lang,
                    ar=args.ar,
                    char_id=char_id,
                    char_data=char_data,
                )
                for ot, prompt in results.items():
                    print(f"═══ {ot} ═══")
                    print(prompt)
                    print()

        elif args.command == "list":
            if args.target == "characters":
                chars = list_characters()
                if not chars:
                    print("No characters found.")
                    return
                print("Available characters:")
                for c in chars:
                    print(f"  • {c}")
                print("\nUse: python cli.py generate <character> <output(s)>")
                print("     python cli.py generate --custom ...")

            elif args.target == "templates":
                tmpls = list_templates()
                print(f"Available templates ({len(tmpls)}):")
                for t in tmpls:
                    print(f"  • {t}")

            elif args.target == "outputs":
                if not args.character:
                    print("Error: --character/-c is required for 'list outputs'")
                    sys.exit(1)
                char_data = load_character(args.character)
                outputs = list_outputs(char_data)
                char_outputs = char_data.get("outputs", {})
                print(f"Output types for '{args.character}' ({len(outputs)}):")
                for o in outputs:
                    if o in char_outputs:
                        label = char_outputs[o]["label"].get("zh", o)
                    else:
                        label = "(通用模板)"
                    print(f"  • {o}  ({label})")
                print("\nLanguages: zh, en")
                print("Models: sd, mj, nai")
                print(f"Aspect ratios: {', '.join(AR_PRESETS)}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

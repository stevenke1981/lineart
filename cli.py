"""Command-line interface for Lineart prompt generator."""

import argparse
import logging
import sys

from batch import load_batch_file, run_batch
from engine import (
    build_custom_character,
    generate_prompt,
    generate_prompts,
    list_characters,
    list_outputs,
    list_templates,
    load_character,
)
from exceptions import LineartError
from history import (
    clear_history,
    delete_prompt,
    export_history,
    get_history,
    get_prompt,
    save_prompt,
)

logger = logging.getLogger(__name__)
AR_PRESETS: list[str] = ["3:4", "1:1", "4:3", "16:9", "9:16", "21:9", "9:21"]
MODEL_CHOICES: list[str] = [
    "sd",
    "stable_diffusion",
    "mj",
    "midjourney",
    "nai",
    "novelai",
    "dalle",
    "dall-e",
    "dall_e",
    "comfyui",
    "comfy",
]


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="lineart",
        description="人物分鏡線稿提示詞生成器 — Anime character design prompt engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── generate ──────────────────────────────────────────────────────
    gen: argparse.ArgumentParser = sub.add_parser("generate", help="Generate prompt(s)")
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
        choices=MODEL_CHOICES,
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
    gen.add_argument("--gender", help="性別 (男/女/中性/無性別)")
    gen.add_argument("--gender-en", help="Gender (male/female/neutral/genderless)")

    # ── batch ─────────────────────────────────────────────────────────
    bat: argparse.ArgumentParser = sub.add_parser("batch", help="Batch generate from JSON/CSV")
    bat.add_argument("file", help="Batch input file (.json or .csv)")
    bat.add_argument(
        "--output",
        "-o",
        default="",
        help="Optional output JSON file for results",
    )
    bat.add_argument(
        "--no-save",
        action="store_true",
        help="Skip saving results to history",
    )

    # ── list ──────────────────────────────────────────────────────────
    lst: argparse.ArgumentParser = sub.add_parser("list", help="List available resources")
    lst.add_argument(
        "target",
        nargs="?",
        choices=["characters", "outputs", "templates"],
        default="characters",
        help="What to list (default: characters)",
    )
    lst.add_argument("--character", "-c", help="Character ID (required for 'outputs')")

    # ── history ────────────────────────────────────────────────────────
    hist: argparse.ArgumentParser = sub.add_parser("history", help="Manage prompt history")
    hist_sub = hist.add_subparsers(dest="history_cmd", required=True)

    # history list
    hist_list = hist_sub.add_parser("list", help="List history records")
    hist_list.add_argument("--page", type=int, default=1, help="Page number")
    hist_list.add_argument("--model", default="", help="Filter by model")
    hist_list.add_argument("--type", dest="output_type", default="", help="Filter by output type")

    # history show
    hist_show = hist_sub.add_parser("show", help="Show a single record")
    hist_show.add_argument("id", type=int, help="Record ID")

    # history delete
    hist_del = hist_sub.add_parser("delete", help="Delete a record")
    hist_del.add_argument("id", type=int, help="Record ID")

    # history clear
    hist_sub.add_parser("clear", help="Clear all records")

    # history export
    hist_export = hist_sub.add_parser("export", help="Export history")
    hist_export.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Export format"
    )
    hist_export.add_argument("--output", default="", help="Output file path")

    return parser


def _build_form(args: argparse.Namespace) -> dict[str, str]:
    """Build form dict from parsed CLI arguments."""
    return {
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
        "gender": args.gender or "",
        "gender_en": args.gender_en or "",
    }


def _handle_generate(args: argparse.Namespace) -> None:
    """Handle the 'generate' subcommand."""
    if args.custom:
        char_data = build_custom_character(_build_form(args))
        char_id = ""
        char_label = char_data.get("label", {}).get("zh", "")
    else:
        if not args.character:
            print("Error: specify a character or use --custom", file=sys.stderr)
            sys.exit(1)
        char_data = None
        char_id = args.character
        tmp = load_character(char_id)
        char_label = tmp.get("label", {}).get("zh", char_id)

    if not args.type:
        print("Error: specify --type (e.g. --type three_view,expressions)", file=sys.stderr)
        sys.exit(1)

    output_types: list[str] = [o.strip() for o in args.type.split(",") if o.strip()]

    def _save(ot: str, prompt: str) -> None:
        try:
            gender = ""
            if char_data:
                gender = char_data.get("gender", {}).get("zh", "")
            save_prompt(
                mode="custom" if args.custom else "prebuilt",
                character=char_id,
                char_label=char_label,
                gender=gender,
                model=args.model,
                lang=args.lang,
                ar=args.ar,
                output_type=ot,
                prompt=prompt,
            )
        except Exception:
            logger.warning("Failed to save prompt to history", exc_info=True)

    if len(output_types) == 1:
        prompt = generate_prompt(
            output_type=output_types[0],
            model=args.model,
            lang=args.lang,
            ar=args.ar,
            char_id=char_id,
            char_data=char_data,
        )
        _save(output_types[0], prompt)
        print(prompt)
    else:
        results: dict[str, str] = generate_prompts(
            output_types=output_types,
            model=args.model,
            lang=args.lang,
            ar=args.ar,
            char_id=char_id,
            char_data=char_data,
        )
        for ot, prompt in results.items():
            _save(ot, prompt)
            print(f"═══ {ot} ═══")
            print(prompt)
            print()


def _handle_batch(args: argparse.Namespace) -> None:
    """Handle the 'batch' subcommand."""
    import json
    from pathlib import Path

    jobs = load_batch_file(args.file)
    results = run_batch(jobs)

    if not args.no_save:
        for row in results:
            try:
                save_prompt(
                    mode="prebuilt",
                    character=row["character"],
                    char_label=row["char_label"],
                    gender="",
                    model=row["model"],
                    lang=row["lang"],
                    ar=row["ar"],
                    output_type=row["output_type"],
                    prompt=row["prompt"],
                )
            except Exception:
                logger.warning("Failed to save batch result to history", exc_info=True)

    for row in results:
        print(f"═══ {row['character']} / {row['output_type']} ({row['model']}) ═══")
        print(row["prompt"])
        print()

    if args.output:
        Path(args.output).write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Results written to {args.output}")


def _handle_list(args: argparse.Namespace) -> None:
    """Handle the 'list' subcommand."""
    if args.target == "characters":
        chars: list[str] = list_characters()
        if not chars:
            print("No characters found.")
            return
        print("Available characters:")
        for c in chars:
            print(f"  • {c}")
        print("\nUse: python cli.py generate <character> <output(s)>")
        print("     python cli.py generate --custom ...")

    elif args.target == "templates":
        tmpls: list[str] = list_templates()
        print(f"Available templates ({len(tmpls)}):")
        for t in tmpls:
            print(f"  • {t}")

    elif args.target == "outputs":
        if not args.character:
            print("Error: --character/-c is required for 'list outputs'")
            sys.exit(1)
        char_data: dict = load_character(args.character)
        outputs: list[str] = list_outputs(char_data)
        char_outputs: dict = char_data.get("outputs", {})
        print(f"Output types for '{args.character}' ({len(outputs)}):")
        for o in outputs:
            if o in char_outputs:
                label: str = char_outputs[o]["label"].get("zh", o)
            else:
                label = "(通用模板)"
            print(f"  • {o}  ({label})")
        print("\nLanguages: zh, en")
        print("Models: sd, mj, nai, dalle, comfyui")
        print(f"Aspect ratios: {', '.join(AR_PRESETS)}")


def _handle_history(args: argparse.Namespace) -> None:
    """Handle the 'history' subcommand."""
    cmd = args.history_cmd

    if cmd == "list":
        model = args.model or None
        output_type = args.output_type or None
        data = get_history(page=args.page, model=model, output_type=output_type)
        records = data["items"]
        if not records:
            print("No history records found.")
            return
        print(f"History (page {data['page']}/{data['pages']}, {data['total']} total):")
        for r in records:
            preview = r["prompt"][:60] + "..." if len(r["prompt"]) > 60 else r["prompt"]
            char_name = r["char_label"] or r["character"] or ""
            print(
                f"  [{r['id']:4d}] {r['created_at']} | {char_name:<20s} | "
                f"{r['model']:3s} | {r['output_type']:<18s} | {preview}"
            )

    elif cmd == "show":
        prompt_data = get_prompt(args.id)
        if not prompt_data:
            print(f"Record #{args.id} not found.", file=sys.stderr)
            sys.exit(1)
        print(f"ID:          {prompt_data['id']}")
        print(f"Created:     {prompt_data['created_at']}")
        print(f"Mode:        {prompt_data['mode']}")
        print(f"Character:   {prompt_data['char_label'] or prompt_data['character']}")
        print(f"Gender:      {prompt_data['gender']}")
        print(f"Model:       {prompt_data['model']}")
        print(f"Language:    {prompt_data['lang']}")
        print(f"Aspect:      {prompt_data['ar']}")
        print(f"Output:      {prompt_data['output_type']}")
        print("Prompt:")
        print(prompt_data["prompt"])

    elif cmd == "delete":
        if delete_prompt(args.id):
            print(f"Record #{args.id} deleted.")
        else:
            print(f"Record #{args.id} not found.", file=sys.stderr)
            sys.exit(1)

    elif cmd == "clear":
        count = clear_history()
        print(f"Cleared {count} history record(s).")

    elif cmd == "export":
        filepath = args.output or None
        content = export_history(format=args.format, filepath=filepath)
        if filepath:
            print(f"Exported to {filepath}")
        else:
            print(content)


def main() -> None:
    """Main entry point for CLI."""
    parser = _build_arg_parser()
    args: argparse.Namespace = parser.parse_args()

    try:
        if args.command == "generate":
            _handle_generate(args)
        elif args.command == "batch":
            _handle_batch(args)
        elif args.command == "list":
            _handle_list(args)
        elif args.command == "history":
            _handle_history(args)
    except LineartError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

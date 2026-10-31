#!/usr/bin/env python3
"""Tale of Immortal GM command PREVIEW builder for research.

Important: This tool does NOT execute commands in the game and does not patch an APK.
Some command examples were mined from metadata and remain unverified at runtime.
"""
from __future__ import annotations
import argparse
import re

SAFE_ALNUM = re.compile(r"^[A-Za-z0-9-]{1,64}$")
SAFE_STAT = re.compile(r"^[a-zA-Z][a-zA-Z0-9]{0,31}$")

class InvalidCommand(ValueError):
    pass


def bounded_int(value: str, label: str, lo: int = 1, hi: int = 1_000_000_000) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as e:
        raise InvalidCommand(f"{label} must be an integer") from e
    if not lo <= parsed <= hi:
        raise InvalidCommand(f"{label} must be between {lo} and {hi}")
    return parsed


def validated_id(raw: str) -> str:
    if not SAFE_ALNUM.fullmatch(raw or ""):
        raise InvalidCommand("ID must contain only ASCII letters, numbers, and hyphens")
    return raw


def validated_stat(raw: str) -> str:
    if not SAFE_STAT.fullmatch(raw or ""):
        raise InvalidCommand("Stat must use ASCII alphanumeric characters starting with a letter")
    return raw


def build_command(action: str, args: list[str], *, backup_ack: bool = False) -> tuple[str, str]:
    """Return (GM command text, safety note). No side effects."""
    if action == "recover_stamina":
        if args: raise InvalidCommand("recover_stamina takes no arguments")
        return "huifu", "Recovery effect described in metadata; verify in-game."
    if action == "add_exp":
        if len(args) != 1: raise InvalidCommand("add_exp needs amount")
        n = bounded_int(args[0], "EXP")
        return f"jingyan_{n}", "This adds EXP once, not a continuous EXP multiplier."
    if action == "add_player_stat":
        if len(args) != 2: raise InvalidCommand("add_player_stat needs stat amount")
        stat,n=validated_stat(args[0]),bounded_int(args[1],"stat addition")
        return f"shuxing_{stat}_{n}", "Stat keys beyond 'hp' are NOT confirmed; negative values are intentionally excluded."
    if action in {"add_npc_stat", "set_npc_realm", "set_player_realm", "resize_bag", "add_item"}:
        if not backup_ack:
            raise InvalidCommand(f"{action} modifies persistent game state; use --ack-backup after saving a backup")
    if action == "add_npc_stat":
        if len(args) != 3: raise InvalidCommand("add_npc_stat needs unit_id stat amount")
        ident,stat,n=validated_id(args[0]),validated_stat(args[1]),bounded_int(args[2],"NPC stat addition")
        return f"npcshuxing_{ident}_{stat}_{n}", "NPC ID and stat handling must be validated in game."
    if action == "set_npc_realm":
        if len(args) != 2: raise InvalidCommand("set_npc_realm needs unit_id realm_id")
        ident,n=validated_id(args[0]),bounded_int(args[1],"realm ID",1,100)
        return f"jingjienpc_{ident}_{n}", "HIGH RISK: NPC realm mutation; back up save, test month rollover and save/load."
    if action == "set_player_realm":
        if len(args) != 1: raise InvalidCommand("set_player_realm needs realm_id")
        n=bounded_int(args[0],"realm ID",1,100)
        return f"jingjie_{n}", "HIGH RISK: player realm mutation; back up save and check progression."
    if action == "resize_bag":
        if len(args) != 1: raise InvalidCommand("resize_bag needs size parameter")
        n=bounded_int(args[0],"bag parameter",1,10000)
        return f"beibao_{n}", "Unverified whether bag argument means SET or ADD; test on a copy of save."
    if action == "add_item":
        if len(args) < 2: raise InvalidCommand("add_item needs item_id followed by one or more raw data values")
        item_id=bounded_int(args[0],"item ID")
        params=[str(bounded_int(x,f"item data {i}",0,1_000_000_000)) for i,x in enumerate(args[1:],1)]
        return "daoju_"+str(item_id)+"_"+"_".join(params), "HIGH RISK: raw item-data parameter semantics not confirmed; 'data1' is NOT guaranteed to mean quantity."
    raise InvalidCommand(f"Unsupported action {action}. Recipe unlock and live multipliers are not implemented.")


def main():
    p=argparse.ArgumentParser(description="Generate GM command previews only. Never executes or modifies files.")
    p.add_argument("action", choices=["recover_stamina","add_exp","add_player_stat","add_npc_stat","set_npc_realm","set_player_realm","resize_bag","add_item"])
    p.add_argument("values", nargs="*")
    p.add_argument("--ack-backup", action="store_true", help="Confirm you made a save backup before any persistent-state test")
    opts=p.parse_args()
    try:
        command,note=build_command(opts.action,opts.values,backup_ack=opts.ack_backup)
    except InvalidCommand as e:
        p.error(str(e))
    print('GM command preview:',command)
    print('Note:',note)
    print('Status: TEXT PREVIEW ONLY — not hooked into APK or executed.')
if __name__=="__main__":main()

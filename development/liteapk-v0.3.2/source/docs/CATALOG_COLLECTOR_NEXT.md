# Next collector after the first phone JSONL

**MAPPED ONLY / NOT IMPLEMENTED.** This release exports every row returned by the existing unfiltered native catalog; it does not add a new configuration reader. Native indexing skips `ConfItemPropsItem.hide != 0`. The reported ~11 Manual entries are user observations of the current browser, not proof that the game has only 11 manuals. Names/categories remain incomplete.

The four-column transport provides ID, displayed name, raw `props_type` and level. It does not carry the original key for successfully localized rows, separate language strings, descriptions, className/subtype, grade, rarity or colors. The exporter retains known `item_name...` fallback keys and marks the other fields unknown. An ordinary displayed name is not assigned an English/Chinese language or declared definitively localized. The existing transport also sanitizes tab/newline characters in displayed names; the JSONL reflects those displayed names rather than raw text assets.

After a genuine Android JSONL is received, run `python3 tools/build_catalog_from_dump.py dump.jsonl /private/catalog-review`. Inspect real counts, duplicate/invalid IDs, missing keys and categories. Do not upload raw game assets, save data, or private paths to the public repository. Host fixtures are synthetic tests, not a substitute for that phone dump.

Then implement a separately versioned, bounded native collector using current ManagedAccess/main-thread dispatch and explicit generation on each page:

| Source | What to collect | Keep distinct |
|---|---|---|
| ConfItemProps | Original key, description key, raw category/className/level and hidden flag | Hidden config rows versus usable inventory items |
| ConfLocalText | Exact key, English, Chinese, Traditional Chinese, Korean | Missing/empty translations versus known text; bounded dictionary/list batches |
| ConfItemBook | Actual book fields and item joins | Recipe item acquisition versus recipe knowledge; book rows versus all manuals |
| ConfItemHorse | Mount joins, descriptions and verified grade | Static mount configuration versus ownership/state |
| ConfItemSkill | Skill type, grade/realm, contribution/cost fields | Configuration rows versus generated learnable manuals |
| ConfClothItem | Outfit appearance fields, model, color and costs | Appearance IDs versus inventory IDs until the join is verified |
| ConfBattleSkillBase / Level | Base template, martial/spiritual category, skill levels/grades | Static combat template versus actual Manual instance |
| Skill prefix name/value | Localized affix names, values, requirements and grade rules | Template possibilities versus affixes present on an owned manual |
| MartialInfoData | Read-only inspection of valid existing instances | Instance baseID/grade/prefixes versus catalog item ID; no NewMartial/Study calls |

Original metadata tokens, fields and their unverified status are retained in `reference_exporter_v4/docs/{method_targets_v3.csv,field_targets_v3.csv,PLAN_NATIVE_V5.md}`. Tokens are metadata identities, never RVAs. Validate owner/signature/runtime layout before reading new fields. Follow the real grade/color rendering relationship; item level is not a rarity proxy. Do not introduce speculative manual creation, learning or inventory actions during collection.

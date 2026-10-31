# Exact native blocker and separate reader contract

**Extended native collector: NOT IMPLEMENTED. No new .so is delivered.** v0.3.6's DEX-only path is functional for the existing four-column item catalog and full provenance schema. It cannot supply additional native values merely by adding a Java button.

## Existing boundary

NativeBridge.request and takeGameResults remain the unchanged protocol 4 / 19-method JNI API. Runtime::queueGameRequest accepts a fixed allowlist; catalog accepts only @TYPE|TERM|OFFSET. GameEditors::catalog returns 40-row receipts containing item ID, displayed name, raw ConfItemPropsItem.type and level. It skips hide != 0. The original native cache has key/English/Chinese/subtype/stackable members, but these are not serialized into that receipt. controlDiagnostics exports control state/generation, not configuration tables or a generic invocation facility.

Consequently, ordinary Java reflection cannot retrieve ConfRoleGrade, dictionaries, descriptions, field offsets or IL2CPP objects through this API. Tokens from metadata are not callable Java functions, runtime RVAs or object pointers. No unsafe screen automation, arbitrary memory bridge or speculative GM command is substituted.

## What has been verified statically

The matching supplied ELF/metadata hashes remain c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099 and 9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3. config/catalog_metadata_v036.json records 14 unambiguous global Assembly-CSharp schema types and six PropsType constants; config/native_collector_requirements_v036.json records 30 getter/list/instance method identities, signatures and MethodDef tokens. Runtime locations/calls remain unverified/null. The global MartialInfoData is type index 7962; an unrelated nested type of the same short name is excluded.

ConfRoleGradeItem has independent grade/gradeName, phase/phaseName and quality/qualityName fields, plus progression fields. This proves field existence/type, not their configured Realm values or an item relationship. ConfItemType and ConfItemTypeFixed likewise have schema fields, not transported rows. Item level does not establish Grade/Rarity/Realm. Cultivation quality does not establish item rarity.

PropsType metadata constants are Money=0, Pill=1, Martial=2, Equip=3, Material=5, Other=6. Current raw item types also contain 7 and 8. The relationship between ConfItemProps.type and that enum is not established as an official category join. PropsData.get_propsType actually returns a different enum, PropsDataType; its signature cannot be used to claim this missing join. The export keeps observed types and metadata enums in separate namespaces and leaves the item type label unknown.

## Smallest future extension

A separately versioned native read-only RPC should reuse the current verified Unity callback, ManagedAccess, request mailbox and generation cancellation. It needs no new combat hook or gameplay patch. The proposed independent capability/catalog data version is `full_catalog_v1`; the core JNI4 ABI can remain compatible if a new request kind and explicit capability marker are added. The current DEX does not submit this unsupported request or advertise it as installed.

- Preserve the legacy four-column catalog path for item browsing and Add Item.
- Add a strictly read-only per-table page request with a validated table key/offset, record and byte bounds, schema version, generation and explicit next offset.
- First serialize already cached original key/localized language candidates/className alongside raw item fields. To include hidden rows, use a separate enumerator rather than altering the existing Add Item cache/filter.
- Resolve the pinned ConfMgr getter and allConfList signatures, validate actual runtime classes/field types, read bounded slices on the Unity thread and root or reacquire managed objects rather than retaining unrooted pointers.
- Collect ConfRoleGrade, ConfItemType/Fixed, ConfLocalText, ConfItemBook/Horse/Skill/Cloth and battle-skill/prefix tables as separate namespaces. Preserve raw keys, identifiers and field evidence. Only apply verified configuration joins.
- Keep item Grade/Rarity/color rules UNKNOWN until their real rendering/configuration relationship is validated; an arbitrary UI prefab tint is not a rarity map.
- Existing generated manuals require a separate verified path through valid player-owned MartialInfoData instances. Base template ID and unique instance identity must remain separate. No NewMartial, Study, AddItem or NPC action is part of collection.
- A failed table must produce an explicit per-table error; it must not mutate data or disable existing gameplay features. Compare old hook/policy/editor bodies, run host mocks and then phone-test the optional component separately.

That implementation requires a new native binary and native runtime initialization/functional validation. This milestone deliberately retains the proven SO; it supplies the working DEX-first portion and exact outstanding reader requirements rather than pretending metadata schemas are complete runtime datasets. No full APK is needed to implement or test a separately delivered native component later.

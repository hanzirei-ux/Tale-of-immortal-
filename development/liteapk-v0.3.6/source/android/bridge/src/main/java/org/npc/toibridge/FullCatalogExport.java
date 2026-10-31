package org.npc.toibridge;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Map;
import java.util.TreeMap;

/** Versioned full schema over the existing four-column native catalog.
 * Unsupported tables/fields stay explicitly BLOCKED_NATIVE/UNKNOWN. No new JNI.
 */
public final class FullCatalogExport extends ReadOnlyCatalogExport {
    public static final String WARNING="JNI4 limit: Realm, subtype, rarity, translations, descriptions and skill/manual data need a native reader.";
    private final int[] reference;
    private final boolean[] seen;
    private final long snapshotGeneration;
    private int matched,extraRecords;
    private final TreeMap<Integer,Integer> observedTypes=new TreeMap<Integer,Integer>();
    public FullCatalogExport(File output,int cap,long generation)throws IOException{
        this(output,cap,generation,CatalogDefinitions.REFERENCE_IDS);
    }
    public FullCatalogExport(File output,int cap,long generation,int[] expectedIds)throws IOException{
        super(output,cap,generation);snapshotGeneration=generation;
        reference=expectedIds==null?new int[0]:expectedIds.clone();seen=new boolean[reference.length];
        try{
            if(expectedIds==null||generation<0)throw new IOException("Missing reference IDs or world generation");
            for(int i=0;i<reference.length;i++)if(reference[i]<=0||i>0&&reference[i]<=reference[i-1])throw new IOException("Invalid reference ID set");
            emit("{\"kind\":\"catalog_manifest\",\"stage\":\"begin\",\"schema_version\":\"0.3.6\",\"collector_version\":\"0.3.6\",\"protocol\":4,\"metadata_sha256\":"+quote(CatalogDefinitions.METADATA_SHA256)+",\"reference_dump_sha256\":"+quote(CatalogDefinitions.REFERENCE_SHA256)+",\"reference_item_count\":"+reference.length+",\"snapshot_generation\":"+generation+",\"scope\":\"EXISTING_JNI4_NONHIDDEN_ITEMS_WITH_METADATA_SCHEMAS\",\"sections\":{\"items\":\"SUPPORTED_FOUR_COLUMNS_NONHIDDEN\",\"item_types\":\"OBSERVED_RAW_IDS_AND_SEPARATE_METADATA_ENUM\",\"realms\":\"BLOCKED_NATIVE\",\"grades\":\"BLOCKED_NATIVE\",\"rarity\":\"BLOCKED_NATIVE\",\"localization\":\"BLOCKED_NATIVE\",\"books\":\"BLOCKED_NATIVE\",\"skill_templates\":\"BLOCKED_NATIVE\",\"manual_templates\":\"BLOCKED_NATIVE\",\"manual_instances\":\"BLOCKED_NATIVE\"},\"warning\":"+quote(WARNING)+"}");
            for(String record:CatalogDefinitions.TYPE_RECORDS)emit(record);
            for(String record:CatalogDefinitions.CONTRACT_RECORDS)emit(record);
        }catch(IOException ex){discard();throw ex;}
    }
    private void emit(String json)throws IOException{writeRecord(json);extraRecords++;}
    @Override public boolean fullSchema(){return true;}
    @Override public int recordCount(){return rowsWritten()+extraRecords;}
    @Override protected String itemJson(int id,String name,String type,String level,long generation){
        int at=Arrays.binarySearch(reference,id);if(at>=0&&!seen[at]){seen[at]=true;matched++;}
        int rawType=Integer.parseInt(type);Integer n=observedTypes.get(rawType);observedTypes.put(rawType,n==null?1:n+1);
        String key=name.matches("item_name[0-9]+")?name:null;
        boolean fallback=key!=null||name.equals("#"+id);
        StringBuilder s=new StringBuilder(1900);
        s.append("{\"kind\":\"item\",\"schema_version\":\"0.3.6\",\"collector_version\":\"0.3.6\",\"id\":").append(id)
            .append(",\"identity_namespace\":\"ConfItemProps\",\"display_name\":").append(quote(name))
            .append(",\"internal_name\":null,\"name_key\":").append(key==null?"null":quote(key))
            .append(",\"name_en\":null,\"name_ch\":null,\"description\":null,\"props_type\":").append(type)
            .append(",\"type_namespace\":\"ConfItemProps.type\",\"type_name\":null,\"subtype\":null,\"level\":").append(level)
            .append(",\"grade\":null,\"rarity\":null,\"rarity_color\":null,\"realm_id\":null,\"realm_requirement\":null,\"cultivation_quality\":null")
            .append(",\"hidden\":0,\"source_table\":\"ConfItemProps\",\"source\":\"JNI4.catalog\",\"snapshot_generation\":").append(generation)
            .append(",\"display_name_is_localization_fallback\":").append(fallback?"true":"null")
            .append(",\"name_status\":").append(quote(fallback?"unresolved_fallback":"display_only_localization_unverified"))
            .append(",\"book_template_id\":null,\"skill_template_id\":null,\"manual_instance_id\":null,\"spawnable\":null,\"relationships\":[]")
            .append(",\"field_status\":{\"id\":\"VERIFIED_RUNTIME\",\"display_name\":\"VERIFIED_RUNTIME\",\"props_type\":\"VERIFIED_RUNTIME\",\"level\":\"VERIFIED_RUNTIME\",\"snapshot_generation\":\"VERIFIED_RUNTIME\",\"hidden\":\"VERIFIED_JOIN\",\"source_table\":\"VERIFIED_JOIN\",\"identity_namespace\":\"VERIFIED_JOIN\",\"type_namespace\":\"VERIFIED_JOIN\",\"name_key\":")
            .append(quote(key==null?"UNKNOWN":"INFERRED"))
            .append(",\"display_name_is_localization_fallback\":").append(quote(fallback?"INFERRED":"UNKNOWN"))
            .append(",\"name_status\":\"INFERRED\",\"relationships\":\"UNKNOWN\",\"source\":\"VERIFIED_JOIN\"");
        for(String field:new String[]{"internal_name","name_en","name_ch","description","type_name","subtype","grade","rarity","rarity_color","realm_id","realm_requirement","cultivation_quality","book_template_id","skill_template_id","manual_instance_id","spawnable"})s.append(',').append(quote(field)).append(":\"UNKNOWN\"");
        s.append("},\"field_sources\":{\"runtime\":\"Four-column JNI4 catalog receipt\",\"hidden\":\"Validated existing native filter excludes ConfItemPropsItem.hide != 0; not a new direct field read\",\"name_key\":\"Visible fallback-pattern inference only; original key not transported\",\"type_name\":\"No proven ConfItemType/PropsType join\"}}");
        return s.toString();
    }
    @Override protected void beforeCommit()throws IOException{
        if(matched!=reference.length)throw new IOException("REFERENCE_ID_GAP: "+matched+" / "+reference.length+" baseline IDs retained. No full-schema snapshot committed; use legacy Item IDs export to inspect differences.");
        for(Map.Entry<Integer,Integer> entry:observedTypes.entrySet())emit("{\"kind\":\"item_type\",\"id\":"+entry.getKey()+",\"name\":null,\"source_table\":\"ConfItemProps.type\",\"item_count\":"+entry.getValue()+",\"status\":\"VERIFIED_RUNTIME\",\"field_status\":{\"id\":\"VERIFIED_RUNTIME\",\"name\":\"UNKNOWN\",\"item_count\":\"VERIFIED_JOIN\",\"source_table\":\"VERIFIED_JOIN\"},\"note\":\"Observed raw type; no official category label inferred\"}");
        emit("{\"kind\":\"catalog_manifest\",\"stage\":\"complete\",\"schema_version\":\"0.3.6\",\"completion_status\":\"COMPLETE_SUPPORTED_SCOPE\",\"all_native_tables_collected\":false,\"item_count\":"+rowsWritten()+",\"record_count\":"+(recordCount()+1)+",\"baseline_ids_preserved\":"+matched+",\"additional_item_ids\":"+(rowsWritten()-matched)+",\"snapshot_generation\":"+snapshotGeneration+",\"warning\":"+quote(WARNING)+"}");
    }
}

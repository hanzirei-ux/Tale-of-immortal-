import org.npc.toibridge.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

public final class FullCatalogExportTest {
    static int checks;
    interface Checked{void run()throws Exception;}
    static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
    static void fail(Checked run,String why)throws Exception{try{run.run();throw new AssertionError("Expected "+why);}catch(IOException ex){checks++;}}
    public static void main(String[] args)throws Exception{
        Path dir=Files.createTempDirectory("toi-full-test-");
        try{
            File out=dir.resolve("full.jsonl").toFile();
            try(FullCatalogExport full=new FullCatalogExport(out,100,7,new int[]{1,2,3})){
                check(full.fullSchema(),"distinct full-schema mode");
                check(full.acceptPage("CATALOG\t3\t0\t40\n1\tName 漢字\t7\t5\n2\titem_name1041161\t1\t1\n3\tBook\t2\t6\n")==-1,"paged completion");
                check(full.isComplete()&&full.rowsWritten()==3,"native item count retained");
                check(Files.readAllLines(out.toPath()).size()==full.recordCount(),"all records counted separately");
            }
            String text=new String(Files.readAllBytes(out.toPath()),StandardCharsets.UTF_8);
            for(String expected:new String[]{"COMPLETE_SUPPORTED_SCOPE","BLOCKED_NATIVE","VERIFIED_RUNTIME","VERIFIED_METADATA","VERIFIED_JOIN","INFERRED","UNKNOWN","\"realm_id\":null","\"grade\":null","\"rarity\":null","\"level\":5","\"name_key\":\"item_name1041161\"","\"source_table\":\"ConfItemProps.type\"","\"owner\":\"ConfRoleGradeItem\"","\"data_values_available\":false"})check(text.contains(expected),expected);
            check(!text.contains("\"kind\":\"manual_instance\""),"inventory book is not a manual instance");
            check(!text.contains("\"kind\":\"realm\""),"realm schema is not a realm data row");
            File gap=dir.resolve("gap.jsonl").toFile();
            try(FullCatalogExport full=new FullCatalogExport(gap,100,7,new int[]{1,2,3})){
                fail(()->full.acceptPage("CATALOG\t2\t0\t40\n1\tx\t1\t1\n2\ty\t1\t2\n"),"missing baseline ID");
                check(!gap.isFile(),"gapped full export never committed");
            }
            check(!Files.exists(dir.resolve("gap.jsonl.partial")),"failed reference cleanup");
            File invalid=dir.resolve("invalid.jsonl").toFile();
            fail(()->new FullCatalogExport(invalid,100,7,new int[]{2,1}),"bad reference ordering");
            check(!Files.exists(dir.resolve("invalid.jsonl.partial")),"constructor failure cleanup");
            File cancel=dir.resolve("cancel.jsonl").toFile();
            try(FullCatalogExport full=new FullCatalogExport(cancel,100,7,new int[]{1})){
                full.acceptPage("CATALOG\t1\t0\t40\n1\tx\t8\t6\n");full.discard();check(!cancel.exists(),"cancel after final rename");
            }
            check(CatalogDefinitions.REFERENCE_IDS.length==3284,"all phone reference IDs embedded");
            check(CatalogDefinitions.TYPE_IDS.length==6,"actual enum size");
            check(CatalogDefinitions.CONTRACT_RECORDS.length==14,"only unambiguous global schema types; nested MartialInfoData excluded");
            System.out.println("PASS v0.3.6: "+checks+" full-schema writer checks; no device test");
            if(args.length>0){Files.createDirectories(Paths.get(args[0]));Files.copy(out.toPath(),Paths.get(args[0],"full_fixture.jsonl"));}
        }finally{try(java.util.stream.Stream<Path> files=Files.walk(dir)){files.sorted(java.util.Comparator.reverseOrder()).forEach(p->{try{Files.deleteIfExists(p);}catch(IOException ex){throw new RuntimeException(ex);}});}}
    }
}

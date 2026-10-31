import org.npc.toibridge.ReadOnlyCatalogExport;
import org.npc.toibridge.CatalogExportGuard;
import org.npc.toibridge.CatalogFileCopy;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

public final class CatalogExportRegressionTest {
    static int checks;
    interface Checked {void run()throws Exception;}
    static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    static void fail(Checked action,String message)throws Exception{try{action.run();throw new AssertionError("Expected failure: "+message);}catch(IOException expected){checks++;}}
    static String page(int total,int offset,int n){
        StringBuilder s=new StringBuilder("CATALOG\t"+total+"\t"+offset+"\t40\n");
        for(int i=0;i<n;i++)s.append(offset+i+1).append("\tName 漢字 \\\" ").append(offset+i+1).append("\t").append(i%7).append("\t5\n");
        return s.toString();
    }
    public static void main(String[] args)throws Exception{
        Path dir=Files.createTempDirectory("toi-export-v032-");
        try{
            File output=dir.resolve("large.jsonl").toFile();
            try(ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(output,100000,77)){
                for(int off=0;off<1643;off+=40){int n=Math.min(40,1643-off);int next=e.acceptPage(page(1643,off,n));check(next==(off+n==1643?-1:off+n),"sequential offset");}
                check(e.rowsWritten()==1643&&e.isComplete(),"actual full paged count");
                fail(()->e.acceptPage(page(1643,1640,3)),"completed export rejects more pages");
            }
            check(Files.readAllLines(output.toPath()).size()==1643,"all rows persisted");
            File names=dir.resolve("names.jsonl").toFile();
            try(ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(names,100,77)){
                e.acceptPage("CATALOG\t3\t0\t40\n1041161\titem_name1041161\t3\t5\n1041162\titem_name1041162\t1\t7\n1041163\tResolved name\t2\t9\n");
            }
            String text=new String(Files.readAllBytes(names.toPath()),StandardCharsets.UTF_8);
            check(text.contains("\"name_key\":\"item_name1041161\""),"exact fallback key 1041161");
            check(text.contains("\"name_key\":\"item_name1041162\""),"exact fallback key 1041162");
            check(text.contains("\"display_name_is_localization_fallback\":true"),"known fallback flagged");
            check(text.contains("\"name_key\":null"),"resolved source key remains unknown");
            check(text.contains("\"display_name_is_localization_fallback\":null"),"unknown is not asserted as localized");
            check(text.contains("\"rarity\":null")&&text.contains("\"name_en\":null")&&text.contains("\"description\":null"),"unknown fields explicit");
            check(text.contains("\"source_table\":\"ConfItemProps\"")&&text.contains("\"snapshot_generation\":77"),"actual source and generation");
            try(ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(dir.resolve("guards.jsonl").toFile(),100,77)){
                fail(()->e.acceptPage("CATALOG\t2\t0\t40\n1\tx\t1\t5\n1\ty\t3\t5\n"),"duplicate within page");
                fail(()->e.acceptPage("CATALOG\t2\t0\t40\n01\tx\t1\t5\n2\ty\t3\t5\n"),"noncanonical JSON integer");
                fail(()->e.acceptPage("CATALOG\t2\t0\t40\n1\tx\t1\t5\n"),"truncated page");
                check(e.rowsWritten()==0,"whole page validated before any write");
            }
            check(!Files.exists(dir.resolve("guards.jsonl.partial")),"failure partial cleaned");
            try(ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(dir.resolve("dup.jsonl").toFile(),100)){
                e.acceptPage(page(41,0,40));
                fail(()->e.acceptPage("CATALOG\t41\t40\t40\n1\tDuplicate\t2\t5\n"),"duplicate across pages");
                fail(()->e.acceptPage(page(42,40,2)),"changed catalog total");
            }
            try(ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(dir.resolve("bounds.jsonl").toFile(),100)){
                fail(()->e.acceptPage(page(101,0,40)),"row cap");
                fail(()->e.acceptPage("CATALOG\t1\t0\t39\n1\tx\t1\t5\n"),"page size");
                fail(()->e.acceptPage("CATALOG\t1\t0\t40\n1\tx\t2147483648\t5\n"),"Int32 type overflow");
                fail(()->e.acceptPage("CATALOG\t1\t0\t40\n1\tx\t1\t-2147483649\n"),"Int32 level overflow");
                fail(()->e.acceptPage("FAILED\t0\t0\t40\n"),"wrong header");
                fail(()->e.acceptPage(null),"null page");
                char[] large=new char[65537];fail(()->e.acceptPage(new String(large)),"bounded receipt size");
            }
            File sentinels=dir.resolve("sentinels.jsonl").toFile();
            try(ReadOnlyCatalogExport raw=new ReadOnlyCatalogExport(sentinels,100)){raw.acceptPage("CATALOG\t1\t0\t40\n1\tx\t65536\t-1\n");}
            check(new String(Files.readAllBytes(sentinels.toPath()),StandardCharsets.UTF_8).contains("\"props_type\":65536,\"level\":-1"),"unknown Int32 types/sentinel levels retained without invented editing limits");
            File cancel=dir.resolve("cancel.jsonl").toFile();
            ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(cancel,100);e.acceptPage(page(1,0,1));check(cancel.isFile(),"last page committed");
            e.discard();check(!cancel.exists(),"cancel racing final commit discards unpublished output");e.discard();e.close();checks++;
            ExecutorService worker=Executors.newSingleThreadExecutor();
            File queued=dir.resolve("queued.jsonl").toFile();final ReadOnlyCatalogExport[] slot=new ReadOnlyCatalogExport[1];
            worker.submit(()->{try{slot[0]=new ReadOnlyCatalogExport(queued,100);slot[0].acceptPage(page(1,0,1));}catch(IOException ex){throw new RuntimeException(ex);}});
            worker.submit(()->{try{slot[0].discard();}catch(IOException ex){throw new RuntimeException(ex);}}).get();worker.shutdown();
            check(!queued.exists()&&!Files.exists(dir.resolve("queued.jsonl.partial")),"queued cleanup follows in-flight writer");
            CatalogExportGuard g=new CatalogExportGuard(77,1000);g.check(77,true,1001);g.queued(12,0,1002);
            check(g.owns(12)&&!g.owns(13),"request receipt ownership");
            fail(()->g.queued(13,40,1003),"only one pending request");
            fail(()->g.receive(12,78,"catalog","@-1||0","CATALOG",1004),"world reload on receipt");
            fail(()->g.receive(12,77,"item","@-1||0","CATALOG",1004),"wrong receipt kind");
            fail(()->g.receive(12,77,"catalog","@1||0","CATALOG",1004),"wrong filter key");
            fail(()->g.receive(12,77,"catalog","@-1||0","BLOCKED",1004),"native failure");
            g.receive(12,77,"catalog","@-1||0","CATALOG",1004);
            check(!g.owns(12),"receipt consumed once");
            fail(()->g.queued(13,40,1005),"wait for IO before next request");
            g.written(1005);g.queued(13,40,1006);g.cancel();
            fail(()->g.receive(13,77,"catalog","@-1||40","CATALOG",1007),"late cancelled receipt");
            CatalogExportGuard other=new CatalogExportGuard(77,0);
            fail(()->other.check(78,true,1),"same counts cannot hide a generation change");
            fail(()->other.check(77,false,1),"unloaded player");
            fail(()->other.check(77,true,45001),"timeout");
            fail(()->new CatalogExportGuard(-1,0),"missing generation");
            byte[] bytes=new byte[140000];for(int i=0;i<bytes.length;i++)bytes[i]=(byte)i;
            ByteArrayOutputStream copied=new ByteArrayOutputStream();check(CatalogFileCopy.copy(new ByteArrayInputStream(bytes),copied,bytes.length)==bytes.length,"bounded document copy");
            check(java.util.Arrays.equals(bytes,copied.toByteArray()),"document copy bytes identical");
            fail(()->CatalogFileCopy.copy(new ByteArrayInputStream(bytes),new ByteArrayOutputStream(),bytes.length-1),"growing file");
            fail(()->CatalogFileCopy.copy(new ByteArrayInputStream(bytes),new ByteArrayOutputStream(),bytes.length+1),"truncated file");
            fail(()->CatalogFileCopy.copy(new ByteArrayInputStream(bytes),null,bytes.length),"null provider stream");
            fail(()->CatalogFileCopy.copy(new ByteArrayInputStream(bytes),new ByteArrayOutputStream(),64L*1024*1024+1),"copy size cap");
            System.out.println("PASS v0.3.2: "+checks+" exporter/guard/file-copy checks; NOT DEVICE TESTED");
            if(args.length>0){Files.createDirectories(Paths.get(args[0]));Files.copy(names.toPath(),Paths.get(args[0],"host_names_fixture.jsonl"),StandardCopyOption.REPLACE_EXISTING);Files.copy(output.toPath(),Paths.get(args[0],"host_large_fixture.jsonl"),StandardCopyOption.REPLACE_EXISTING);}
        }finally{
            try(java.util.stream.Stream<Path> paths=Files.walk(dir)){paths.sorted(java.util.Comparator.reverseOrder()).forEach(p->{try{Files.deleteIfExists(p);}catch(IOException ex){throw new RuntimeException(ex);}});}
        }
    }
}

import org.npc.toibridge.ReadOnlyCatalogExport;
import java.nio.file.*;
import java.io.*;
public final class ReadOnlyCatalogExportTest {
  private static void expect(boolean p,String msg){ if(!p)throw new AssertionError(msg); }
  private static String page(int total,int offset,int n){
    StringBuilder s=new StringBuilder("CATALOG\t"+total+"\t"+offset+"\t40\n");
    for(int i=0;i<n;i++)s.append(offset+i+1).append("\tName ").append(offset+i+1).append(" \"漢字\"\t2\t5\n");
    return s.toString();
  }
  private static void fail(ReadOnlyCatalogExport exp,String p){try{exp.acceptPage(p);throw new AssertionError("Expected exception");}catch(IOException ok){}}
  public static void main(String[] args)throws Exception{
    Path dir=Files.createTempDirectory("toi-catalog-test");
    File out=dir.resolve("dump.jsonl").toFile();
    try(ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(out,300)){
      expect(e.acceptPage(page(83,0,40))==40,"page0");
      expect(e.acceptPage(page(83,40,40))==80,"page1");
      expect(e.acceptPage(page(83,80,3))==-1,"page2");
      expect(e.isComplete()&&e.rowsWritten()==83,"completed count");
    }
    String json=Files.readString(out.toPath());
    expect(json.split("\\n").length==83,"jsonl lines");
    expect(json.contains("Name 1 \\\"漢字\\\""),"escaped quote");
    try(ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(dir.resolve("fail.jsonl").toFile(),100)){
      fail(e,page(120,0,40));
      fail(e,page(20,1,19));
      expect(e.acceptPage(page(20,0,20))==-1,"recover page");
    }
    try(ReadOnlyCatalogExport e=new ReadOnlyCatalogExport(dir.resolve("dup.jsonl").toFile(),100)){
      e.acceptPage(page(41,0,40));
      fail(e,"CATALOG\t41\t40\t40\n1\tDuplicate\t2\t5\n");
    }
    expect(!Files.exists(dir.resolve("dup.jsonl.partial")),"temporary file cleanup");
    System.out.println("PASS: 83-row export, JSON quoting, size/offset guards, incomplete-page recovery, duplicate guard, partial cleanup");
  }
}

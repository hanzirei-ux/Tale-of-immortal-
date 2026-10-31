import org.npc.toibridge.*;
import java.io.File;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
public final class CatalogPhoneReplay {
    public static void main(String[] args)throws Exception{
        List<Path> pages=new ArrayList<Path>();try(java.nio.file.DirectoryStream<Path> list=Files.newDirectoryStream(Paths.get(args[0]),"*.page")){for(Path p:list)pages.add(p);}Collections.sort(pages);
        try(FullCatalogExport out=new FullCatalogExport(new File(args[1]),100000,2)){
            for(Path p:pages)out.acceptPage(new String(Files.readAllBytes(p),StandardCharsets.UTF_8));
            if(out.rowsWritten()!=3284||!out.isComplete())throw new AssertionError("Phone reference coverage failed");
            System.out.println("PASS host replay: "+out.rowsWritten()+" original device item IDs, "+out.recordCount()+" full-schema records; new Android collector NOT device tested");
        }
    }
}

import org.npc.toibridge.ReadOnlyCatalogExport;
import java.io.File;
public final class CatalogLegacyParity {
    public static void main(String[] args)throws Exception{
        try(ReadOnlyCatalogExport out=new ReadOnlyCatalogExport(new File(args[0]),100,9)){
            out.acceptPage("CATALOG\t3\t0\t40\n1\tName 漢字 \\\"\\\\\t7\t5\n1041161\titem_name1041161\t1\t1\n1041162\titem_name1041162\t3\t6\n");
        }
    }
}

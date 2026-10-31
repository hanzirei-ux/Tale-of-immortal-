package org.npc.toibridge;

import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;

/**
 * v0.3.1 catalog transport consumer. No Android APIs, no IL2CPP calls, no writes to saves.
 * The caller requests @-1||OFFSET on the verified Unity thread through NativeBridge.
 * Only original item-catalog output is available; this is NOT a manual-skill generator.
 */
public final class ReadOnlyCatalogExport implements Closeable {
    private final File destination, partial;
    private final BufferedWriter writer;
    private final HashSet<Integer> ids = new HashSet<Integer>();
    private final int maxRows;
    private boolean complete, closed;
    private int expectedOffset, total=-1, count;

    public ReadOnlyCatalogExport(File destination, int maxRows) throws IOException {
        if (destination == null || maxRows <= 0 || maxRows > 100000)
            throw new IllegalArgumentException("Invalid output or row cap");
        this.destination = destination;
        this.maxRows = maxRows;
        this.partial = new File(destination.getAbsolutePath() + ".partial");
        if (destination.isFile() || partial.exists()) throw new IOException("Output already exists");
        File parent = destination.getAbsoluteFile().getParentFile();
        if (parent == null || (!parent.isDirectory() && !parent.mkdirs())) throw new IOException("Output folder unavailable");
        writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(partial), StandardCharsets.UTF_8), 32768);
    }
    public int expectedOffset() { return expectedOffset; }
    public int rowsWritten() { return count; }
    public int total() { return total; }
    public boolean isComplete() { return complete; }
    public File outputFile() { return destination; }

    /** Native receipt: CATALOG<TAB>total<TAB>offset<TAB>pageSize<NEWLINE>id<TAB>name<TAB>type<TAB>level. */
    public int acceptPage(String receipt) throws IOException {
        if (closed || complete) throw new IOException("Export session is closed");
        if (receipt == null || receipt.length() > 65536) throw new IOException("Native catalog page too large");
        String[] lines = receipt.split("\\n", -1);
        String[] h = lines[0].split("\\t", -1);
        if (h.length != 4 || !"CATALOG".equals(h[0])) throw new IOException("Unexpected catalog receipt header");
        int pageTotal = decimal(h[1]), offset = decimal(h[2]), pageSize = decimal(h[3]);
        if (pageTotal < 0 || pageTotal > maxRows || offset != expectedOffset || pageSize != 40)
            throw new IOException("Catalog count/offset/page mismatch");
        if (total < 0) total = pageTotal;
        else if (total != pageTotal) throw new IOException("Catalog changed during export");
        int pageRows = 0;
        // Validate whole page BEFORE writing so malformed rows never cause a partial page commit.
        int[] pageIds = new int[lines.length];
        String[][] pageCols = new String[lines.length][];
        HashSet<Integer> pageUnique = new HashSet<Integer>();
        for (int i=1;i<lines.length;i++) {
            if (lines[i].isEmpty()) continue;
            String[] col = lines[i].split("\\t",-1);
            if (col.length != 4) throw new IOException("Unexpected catalog column count");
            int id=decimal(col[0]), type=decimal(col[2]), level=decimal(col[3]);
            if (id<=0 || type>255 || level>100000 || !pageUnique.add(id) || ids.contains(id))
                throw new IOException("Invalid or duplicate item ID on page");
            if (++pageRows>40 || count+pageRows>total) throw new IOException("Catalog page exceeds declared total");
            pageIds[i]=id;pageCols[i]=col;
        }
        if (pageRows != Math.min(pageSize, total-offset))
            throw new IOException("Short or incomplete catalog page");
        for (int i=1;i<lines.length;i++) if (pageCols[i]!=null) {
            String[] col=pageCols[i];ids.add(pageIds[i]);
            String unresolvedKey=col[1].matches("item_name[0-9]+") ? col[1] : null;
            writer.write("{\"kind\":\"item\",\"id\":"+col[0]+",\"props_type\":"+col[2]+
                ",\"level\":"+col[3]+",\"display_name\":"+quote(col[1])+
                ",\"name_key\":"+(unresolvedKey==null?"null":quote(unresolvedKey))+
                ",\"source\":\"LiteAPK-v0.3.1 catalog read-only\"}\n");
            count++;
        }
        expectedOffset += pageRows;
        if (count==total) {
            writer.flush(); writer.close();closed=true;
            if (!partial.renameTo(destination)) {partial.delete();throw new IOException("Could not commit completed catalog export");}
            complete=true;return -1;
        }
        return expectedOffset;
    }
    private static int decimal(String s) throws IOException {
        if (s.isEmpty() || s.length()>10) throw new IOException("Invalid integer length");
        for (int i=0;i<s.length();i++) if (s.charAt(i)<'0'||s.charAt(i)>'9')throw new IOException("Expected decimal integer");
        try { return Integer.parseInt(s); } catch (NumberFormatException e) { throw new IOException("Invalid integer",e); }
    }
    private static String quote(String s) {
        StringBuilder out = new StringBuilder("\"");
        for (int i=0;i<s.length();i++){
            char c=s.charAt(i);
            if(c=='\\'||c=='\"')out.append('\\').append(c);
            else if(c=='\n')out.append("\\n");
            else if(c=='\r')out.append("\\r");
            else if(c=='\t')out.append("\\t");
            else if(c<0x20)out.append(String.format("\\u%04x",(int)c));
            else out.append(c);
        }
        return out.append('"').toString();
    }
    @Override public void close() throws IOException {
        if (closed) return;
        closed=true;writer.close();
        if(!complete && partial.exists() && !partial.delete())throw new IOException("Could not remove incomplete export");
    }
}

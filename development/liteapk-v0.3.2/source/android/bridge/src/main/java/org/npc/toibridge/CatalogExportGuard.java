package org.npc.toibridge;

import java.io.IOException;

/** UI-thread transport guard. The one existing receipt consumer owns request routing. */
public final class CatalogExportGuard {
    public final long generation;
    private long requestId,deadline;
    private String requestKey;
    private boolean active=true,writing;
    public CatalogExportGuard(long generation,long now)throws IOException{
        if(generation<0)throw new IOException("Missing world generation");
        this.generation=generation;deadline=now+45000;
    }
    public void check(long currentGeneration,boolean playerLoaded,long now)throws IOException{
        if(!active)throw new IOException("Export cancelled");
        if(currentGeneration!=generation||!playerLoaded)throw new IOException("World/save changed; restart the export");
        if(now>deadline)throw new IOException("Catalog export timed out; no automatic retry");
    }
    public void queued(long id,int offset,long now)throws IOException{
        if(!active||requestId!=0||writing||id<=0||offset<0)throw new IOException("Invalid or concurrent catalog request");
        requestId=id;requestKey="@-1||"+offset;deadline=now+45000;
    }
    public boolean owns(long id){return active&&id>0&&id==requestId;}
    public void receive(long id,long receiptGeneration,String kind,String key,String state,long now)throws IOException{
        if(!owns(id)||writing)throw new IOException("Unexpected export receipt ID");
        check(receiptGeneration,true,now);
        if(!"catalog".equals(kind)||!requestKey.equals(key)||!"CATALOG".equals(state))
            throw new IOException("Native export receipt rejected: "+kind+" / "+state);
        requestId=0;writing=true;deadline=now+45000;
    }
    public void written(long now)throws IOException{
        if(!active||!writing)throw new IOException("Unexpected export completion");
        writing=false;deadline=now+45000;
    }
    public void cancel(){active=false;requestId=0;}
}

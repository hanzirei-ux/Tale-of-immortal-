package org.npc.toibridge;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/** Bounded copy of a completed export only. Caller owns/always closes both streams. */
public final class CatalogFileCopy {
    private CatalogFileCopy(){}
    public static long copy(InputStream input,OutputStream output,long expected)throws IOException{
        if(input==null||output==null||expected<0||expected>64L*1024*1024)throw new IOException("Invalid export size/stream");
        byte[] buffer=new byte[65536];long count=0;int n;
        while((n=input.read(buffer))!=-1){
            if(n==0)throw new IOException("Export stream stalled");
            if(count+n>expected)throw new IOException("Export grew during copy");
            output.write(buffer,0,n);count+=n;
        }
        if(count!=expected)throw new IOException("Export truncated during copy");
        output.flush();return count;
    }
}

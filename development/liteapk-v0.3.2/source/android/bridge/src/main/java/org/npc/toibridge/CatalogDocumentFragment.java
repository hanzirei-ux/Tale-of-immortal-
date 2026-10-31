package org.npc.toibridge;

import android.app.Activity;
import android.app.Fragment;
import android.app.FragmentManager;
import android.content.Intent;
import android.content.ContentResolver;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;

/** Invisible platform Fragment: SAF result routing without manifest/Activity modifications. */
@SuppressWarnings("deprecation")
public final class CatalogDocumentFragment extends Fragment {
    private static final String TAG="toi.catalog.document.v032";
    private static final int CREATE_DOCUMENT=0x7132;
    private String sourcePath;
    private boolean busy;
    private boolean copying;
    private String restoredWarning;
    public CatalogDocumentFragment(){}
    public static void save(Activity activity,File completed){
        try{
            if(activity.isFinishing()||activity.isDestroyed())throw new IOException("Activity closing");
            FragmentManager fm=activity.getFragmentManager();
            CatalogDocumentFragment f=(CatalogDocumentFragment)fm.findFragmentByTag(TAG);
            if(f==null){f=new CatalogDocumentFragment();fm.beginTransaction().add(f,TAG).commit();fm.executePendingTransactions();}
            f.launch(completed);
        }catch(Exception ex){ModMenu.catalogDocumentResult(activity,"Save JSONL unavailable: "+ex.getClass().getSimpleName()+": "+ex.getMessage());}
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);setRetainInstance(true);
        if(state!=null){sourcePath=state.getString("source");busy=state.getBoolean("busy",false);
            if(state.getBoolean("copying",false)){busy=false;restoredWarning="Previous save copy was interrupted. Original JSONL is retained; retry Save JSONL and remove any incomplete destination in Files.";}}
    }
    @Override public void onResume(){super.onResume();if(restoredWarning!=null){report(restoredWarning);restoredWarning=null;}}
    @Override public void onSaveInstanceState(Bundle out){super.onSaveInstanceState(out);out.putString("source",sourcePath);out.putBoolean("busy",busy);out.putBoolean("copying",copying);}
    private void launch(File completed)throws IOException{
        if(busy)throw new IOException("A Save JSONL operation is already open");
        if(!completed.isFile()||completed.getName().endsWith(".partial"))throw new IOException("Completed export unavailable");
        sourcePath=completed.getAbsolutePath();busy=true;
        Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/jsonl");intent.putExtra(Intent.EXTRA_TITLE,completed.getName());
        try{startActivityForResult(intent,CREATE_DOCUMENT);}catch(RuntimeException ex){busy=false;throw ex;}
    }
    private void report(String message){Activity a=getActivity();if(a!=null)ModMenu.catalogDocumentResult(a,message);}
    @Override public void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);if(request!=CREATE_DOCUMENT)return;
        if(result!=Activity.RESULT_OK||data==null||data.getData()==null){busy=false;report("Save cancelled. Completed JSONL remains in app storage; tap Save JSONL again.");return;}
        final Uri uri=data.getData();final Activity activity=getActivity();
        if(activity==null||sourcePath==null){busy=false;report("Save failed: Activity/source unavailable. Original export retained.");return;}
        final ContentResolver resolver=activity.getApplicationContext().getContentResolver();final File source=new File(sourcePath);copying=true;
        report("Saving JSONL to the selected document...");
        new Thread(new Runnable(){public void run(){String message;
            try(InputStream in=new FileInputStream(source);OutputStream out=resolver.openOutputStream(uri,"w")){
                long bytes=CatalogFileCopy.copy(in,out,source.length());message="Saved JSONL ("+bytes+" bytes) to "+uri+". You can share this file from Files.";
            }catch(Exception ex){
                message="Save failed: "+ex.getClass().getSimpleName()+": "+ex.getMessage()+". Original completed export retained.";
                try{if(!android.provider.DocumentsContract.deleteDocument(resolver,uri))message+=" Remove the incomplete destination in Files.";}catch(Exception ignored){message+=" Remove the incomplete destination in Files.";}
            }
            final String text=message;new Handler(Looper.getMainLooper()).post(new Runnable(){public void run(){busy=false;copying=false;report(text);}});
        }},"TOI-CatalogCopy").start();
    }
}

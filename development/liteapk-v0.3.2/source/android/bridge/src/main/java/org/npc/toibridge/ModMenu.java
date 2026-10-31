package org.npc.toibridge;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.content.res.ColorStateList;
import android.graphics.drawable.GradientDrawable;
import android.text.Editable;
import android.text.TextWatcher;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.*;
import java.io.*;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.zip.ZipFile;
import java.util.zip.ZipEntry;

/** In-Activity UI for the compiled native implementation. No system overlay permission. */
public final class ModMenu {
    private static ModMenu instance;
    private final Activity activity;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final SharedPreferences prefs;
    private final FrameLayout overlay;
    private final Button launcher;
    private final LinearLayout panel, page;
    private final TextView status, result;
    private final CheckBox backup;
    private final Spinner category;
    private final ArrayList<View> runtimeInputs = new ArrayList<View>();
    private final ControlUiState controlUi=new ControlUiState();
    private final ControlRow[] controlRows=new ControlRow[22];
    private JSONObject nativeSnapshot;
    private JSONArray nativeControls;
    private boolean schemaMatched;
    private long lastSnapshotTime;
    private final ScrollView contentScroll;
    private ScrollView itemScroll;
    private Button resultToggle;
    private boolean resultExpanded;
    private static final class Ticket {final long epoch;Ticket(long e){epoch=e;}}
    private static final class ControlRow {int id;CheckBox toggle;EditText input;Button apply;TextView receipt;boolean confirmed;double confirmedValue;}
    private static final String[] KEYS={"god_mode","unlimited_hp","unlimited_energy","all_damage","martial_damage","spiritual_damage","skill_damage","ultimate_damage","all_defense","martial_resistance","spiritual_resistance","critical_rating","critical_damage","critical_resistance_rating","attack_speed","movement_speed","skill_cooldown","energy_consumption","global_exp","cultivation_spot_exp","manual_exp","skill_exp"};
    private boolean busy, initialized, ready;
    private boolean pendingCatalog, activeCombine, catalogRefreshNeeded;
    private EditText itemSearch, itemIdField;
    private Spinner itemTypeFilter;
    private LinearLayout itemList;
    private TextView itemInfo, itemSelected;
    private int catalogOffset=0, catalogTotal=0;
    private String selectedItemName="", selectedItemId="", catalogRequestKey="", lastDiagnostic="No operation logged yet";
    private long catalogRequestId;
    private static final class ExportJob {
        final CatalogExportGuard guard;
        volatile ReadOnlyCatalogExport writer;
        volatile boolean cancelled;
        ExportJob(CatalogExportGuard g){guard=g;}
    }
    private ExportJob catalogExport;
    private final java.util.concurrent.ExecutorService exportWorker=java.util.concurrent.Executors.newSingleThreadExecutor(new java.util.concurrent.ThreadFactory(){public Thread newThread(Runnable r){Thread t=new Thread(r,"TOI-CatalogFile");t.setDaemon(true);return t;}});
    private TextView exportInfo;
    private Button exportStart,exportCancel,exportSave;
    private String exportMessage="Read-only: current catalog only; skill/manual coverage is incomplete.";
    private File completedCatalog;
    private final android.app.Application.ActivityLifecycleCallbacks exportLifecycle=new android.app.Application.ActivityLifecycleCallbacks(){
        public void onActivityPaused(Activity a){if(a==activity&&catalogExport!=null)endReadOnlyCatalogExport("Export cancelled: application paused. Restart when back in game.",false);}
        public void onActivityDestroyed(Activity a){if(a==activity&&!disposed)release();}
        public void onActivityCreated(Activity a,android.os.Bundle b){}
        public void onActivityStarted(Activity a){}
        public void onActivityResumed(Activity a){}
        public void onActivityStopped(Activity a){}
        public void onActivitySaveInstanceState(Activity a,android.os.Bundle b){}
    };
    private final LinkedHashMap<Long,Ticket> pendingActions=new LinkedHashMap<Long,Ticket>();
    private Spinner currencyType;
    private TextView currencyCurrent;
    private static final String[] CURRENCY_KEYS={"money","contribution","city_token","immortal_token","sect_funds","sect_reputation","sect_faith"};
    private static final String[] CURRENCY_LABELS={"Spirit Stones / player money","Personal Sect Contribution","City Token","Immortal Store Token","Sect Funds (treasury)","Sect Reputation","Sect Faith Currency"};
    private final Runnable searchDebounce=new Runnable(){public void run(){submitCatalog();}};
    private static final int BG=Color.rgb(23,27,35), SURFACE=Color.rgb(48,59,74), FG=Color.rgb(244,248,255), MUTED=Color.rgb(184,203,223);
    private volatile boolean disposed;
    private boolean schemaWarningShown;
    private String bootStatus = "Initializing native component...";
    private int selected;
    private final Runnable pollTask=new Runnable(){public void run(){updatePoll();}};
    private static final String[] LABELS = {
        "God Mode", "Unlimited HP", "Unlimited Energy", "All damage", "Martial damage", "Spiritual damage",
        "Skill damage", "Ultimate damage", "Defense", "Martial resistance", "Spiritual resistance",
        "CRIT rating (not %)", "Critical damage", "Guard rating (not %)",
        "Attack speed", "Movement speed", "Cooldown factor", "Energy cost factor",
        "Global EXP", "Cultivation spot EXP", "Manual training EXP", "Combat skill EXP"
    };
    private static final double[] MIN={0,0,0,.1,.1,.1,.1,.1,.1,.1,.1,0,.1,0,1,1,0,0,1,1,1,1};
    private static final double[] MAX={1,1,1,100,100,100,100,100,100,100,100,100,100,100,10,10,1,1,100,100,100,100};
    private static final String[] STATS={"hp","hpMax","mp","mpMax","attack","defense","crit","critValue","guard","guardValue","phycicalFree","magicFree","moveSpeed","luck","life","health","healthMax","energy","energyMax","mood","moodMax","talent","abilityPoint","basisFire","basisFroze","basisThunder","basisWind","basisEarth","basisWood","basisBlade","basisSpear","basisSword","basisFist","basisPalm","basisFinger","refineElixir","refineWeapon","geomancy","symbol","herbal","mine"};

    public static void install(final Activity activity) {
        activity.runOnUiThread(new Runnable(){public void run(){
            if(instance!=null && instance.activity==activity)return;
            if(instance!=null)instance.release();
            instance=new ModMenu(activity);
        }});
    }
    public static void detach(Activity a){if(instance!=null&&instance.activity==a){instance.release();instance=null;}}
    private void release(){if(disposed)return;disposed=true;endReadOnlyCatalogExport("Export cancelled: Activity closed",false);activity.getApplication().unregisterActivityLifecycleCallbacks(exportLifecycle);exportWorker.shutdown();ui.removeCallbacksAndMessages(null);if(initialized)try{NativeBridge.closeMenu();}catch(Throwable ignored){}if(overlay.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)overlay.getParent()).removeView(overlay);}
    private ModMenu(Activity a) {
        activity=a;prefs=a.getSharedPreferences("toi_modmenu_v02",0);
        activity.getApplication().registerActivityLifecycleCallbacks(exportLifecycle);
        FrameLayout decor=(FrameLayout)a.getWindow().getDecorView();
        overlay=new FrameLayout(a);overlay.setElevation(dp(100));overlay.setClipChildren(false);
        decor.addView(overlay,new FrameLayout.LayoutParams(-1,-1));
        launcher=button("TOI",null);launcher.setElevation(dp(102));launcher.setTextSize(14);launcher.setAlpha(.88f);
        final FrameLayout.LayoutParams iconParams=new FrameLayout.LayoutParams(dp(56),dp(48));
        overlay.addView(launcher,iconParams);
        panel=new LinearLayout(a);panel.setOrientation(LinearLayout.VERTICAL);panel.setPadding(dp(6),dp(4),dp(6),dp(4));
        panel.setClickable(true);panel.setFocusable(true);panel.setBackgroundColor(Color.argb(251,23,27,35));panel.setElevation(dp(101));
        FrameLayout.LayoutParams panelParams=new FrameLayout.LayoutParams(dp(390),dp(420),Gravity.TOP|Gravity.RIGHT);panelParams.setMargins(dp(4),dp(4),dp(4),dp(4));
        overlay.addView(panel,panelParams);panel.setVisibility(View.GONE);
        LinearLayout header=row(panel);
        TextView title=new TextView(a);title.setText("TOI v0.3.2 · player");title.setTextColor(FG);title.setTextSize(13);title.setGravity(Gravity.CENTER_VERTICAL);title.setIncludeFontPadding(false);
        header.addView(title,new LinearLayout.LayoutParams(0,dp(36),1));
        headerButton(header,"Reset",new View.OnClickListener(){public void onClick(View v){resetRuntime();}});
        headerButton(header,"Load",new View.OnClickListener(){public void onClick(View v){loadSaved();buildPage();}});
        headerButton(header,"Hide",new View.OnClickListener(){public void onClick(View v){panel.setVisibility(View.GONE);}});
        category=new Spinner(a);
        category.setAdapter(spinnerAdapter(new String[]{"Combat","EXP / Cultivation","Player Stats / Inventory","Items / Recipes","Skills / Artifacts","Currency & Contribution","Diagnostics"}));
        category.setMinimumHeight(0);category.setBackground(boxBackground(SURFACE));panel.addView(category,new LinearLayout.LayoutParams(-1,dp(34)));
        category.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,View v,int position,long id){selected=position;buildPage();}public void onNothingSelected(AdapterView<?> p){}});
        backup=new CheckBox(a);backup.setText("Save backup ready · permanent edits");backup.setTextColor(FG);backup.setButtonTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));backup.setTextSize(11);backup.setMinimumHeight(0);backup.setPadding(0,0,0,0);panel.addView(backup,new LinearLayout.LayoutParams(-1,dp(28)));
        status=text(panel,bootStatus,10);status.setSingleLine(true);status.setEllipsize(android.text.TextUtils.TruncateAt.END);
        contentScroll=new ScrollView(a);page=new LinearLayout(a);page.setOrientation(LinearLayout.VERTICAL);contentScroll.addView(page);panel.addView(contentScroll,new LinearLayout.LayoutParams(-1,0,1));
        contentScroll.addOnLayoutChangeListener(new View.OnLayoutChangeListener(){public void onLayoutChange(View v,int l,int t,int r,int b,int ol,int ot,int or,int ob){if(b-t!=ob-ot)resizeItemList();}});
        resultToggle=button("Last result · tap for details ▸",new View.OnClickListener(){public void onClick(View v){resultExpanded=!resultExpanded;result.setVisibility(resultExpanded?View.VISIBLE:View.GONE);resultToggle.setText(resultExpanded?"Details ▾ (tap to collapse)":"Details ▸ (tap to expand)");}});
        resultToggle.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);resultToggle.setTextSize(10);resultToggle.setSingleLine(true);resultToggle.setEllipsize(android.text.TextUtils.TruncateAt.END);panel.addView(resultToggle,new LinearLayout.LayoutParams(-1,dp(26)));
        result=text(panel,"No operation applied yet",11);result.setMovementMethod(new android.text.method.ScrollingMovementMethod());result.setTextIsSelectable(true);result.setTextColor(MUTED);result.setLayoutParams(new LinearLayout.LayoutParams(-1,dp(66)));result.setVisibility(View.GONE);
        launcher.setOnTouchListener(new View.OnTouchListener(){float sx,sy,ox,oy;boolean moved;
            public boolean onTouch(View v,MotionEvent e){
                if(e.getAction()==MotionEvent.ACTION_DOWN){sx=e.getRawX();sy=e.getRawY();ox=v.getX();oy=v.getY();moved=false;return true;}
                if(e.getAction()==MotionEvent.ACTION_MOVE){float dx=e.getRawX()-sx,dy=e.getRawY()-sy;if(Math.abs(dx)+Math.abs(dy)>dp(6))moved=true;v.setX(clamp(ox+dx,0,overlay.getWidth()-v.getWidth()));v.setY(clamp(oy+dy,0,overlay.getHeight()-v.getHeight()));return true;}
                if(e.getAction()==MotionEvent.ACTION_UP){if(!moved){panel.setVisibility(panel.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE);panel.bringToFront();launcher.bringToFront();poll();}prefs.edit().putFloat("icon_x",v.getX()/Math.max(1,overlay.getWidth()-v.getWidth())).putFloat("icon_y",v.getY()/Math.max(1,overlay.getHeight()-v.getHeight())).apply();return true;}return true;
            }});
        overlay.addOnLayoutChangeListener(new View.OnLayoutChangeListener(){public void onLayoutChange(View v,int l,int t,int r,int b,int ol,int ot,int or,int ob){if((r-l)!=(or-ol)||(b-t)!=(ob-ot))layout();}});
        ui.post(new Runnable(){public void run(){layout();beginInitialization();}});
    }
    private int dp(float v){return (int)(activity.getResources().getDisplayMetrics().density*v+.5f);}
    private float clamp(float value,float min,float max){return Math.max(min,Math.min(Math.max(min,max),value));}
    private void layout(){
        launcher.setX(clamp(prefs.getFloat("icon_x",.02f)*(overlay.getWidth()-launcher.getWidth()),0,overlay.getWidth()-launcher.getWidth()));
        launcher.setY(clamp(prefs.getFloat("icon_y",.2f)*(overlay.getHeight()-launcher.getHeight()),0,overlay.getHeight()-launcher.getHeight()));
        FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)panel.getLayoutParams();p.width=Math.min(overlay.getWidth()-dp(8),Math.max(dp(280),Math.min(dp(420),(int)(overlay.getWidth()*.48f))));p.height=Math.max(1,overlay.getHeight()-dp(8));panel.setLayoutParams(p);overlay.bringToFront();launcher.bringToFront();
    }
    private LinearLayout row(LinearLayout parent){LinearLayout l=new LinearLayout(activity);l.setOrientation(LinearLayout.HORIZONTAL);parent.addView(l,new LinearLayout.LayoutParams(-1,-2));return l;}
    private GradientDrawable boxBackground(int color){
        GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(5));
        d.setStroke(dp(1),Color.rgb(87,109,130));return d;
    }
    private TextView text(LinearLayout parent,String value,int size){
        TextView t=new TextView(activity);t.setText(value);t.setTextColor(FG);t.setTextSize(size);
        t.setIncludeFontPadding(false);t.setPadding(dp(2),dp(2),dp(2),dp(2));parent.addView(t);return t;
    }
    private Button button(String label,View.OnClickListener click){
        Button b=new Button(activity);b.setText(label);b.setAllCaps(false);b.setTextColor(FG);
        b.setTextSize(12);b.setMinHeight(0);b.setMinimumHeight(0);b.setMinWidth(0);b.setMinimumWidth(0);b.setIncludeFontPadding(false);b.setPadding(dp(5),0,dp(5),0);b.setBackground(boxBackground(SURFACE));
        if(click!=null)b.setOnClickListener(click);return b;
    }
    private Button button(LinearLayout parent,String label,View.OnClickListener click){
        Button b=button(label,click);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(36),1);
        lp.setMargins(dp(1),dp(1),dp(1),dp(1));parent.addView(b,lp);return b;
    }
    private EditText edit(LinearLayout parent,String value,boolean numeric){
        EditText e=new EditText(activity);e.setSingleLine(true);e.setTextColor(FG);e.setHintTextColor(MUTED);
        e.setTextSize(13);e.setMinHeight(0);e.setMinimumHeight(0);e.setIncludeFontPadding(false);e.setPadding(dp(7),0,dp(7),0);e.setBackground(boxBackground(SURFACE));
        e.setInputType(numeric?InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL|InputType.TYPE_NUMBER_FLAG_SIGNED:InputType.TYPE_CLASS_TEXT);
        e.setText(value);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(36));lp.setMargins(dp(1),dp(1),dp(1),dp(2));parent.addView(e,lp);return e;
    }
    private EditText number(LinearLayout parent,String value){return edit(parent,value,true);}
    private ArrayAdapter<String> spinnerAdapter(String[] labels){
        return new ArrayAdapter<String>(activity,android.R.layout.simple_spinner_item,labels){
            @Override public View getView(int pos,View recycled,android.view.ViewGroup parent){
                TextView v=(TextView)super.getView(pos,recycled,parent);v.setTextColor(FG);v.setTextSize(13);
                v.setPadding(dp(6),0,dp(4),0);v.setSingleLine(true);v.setEllipsize(android.text.TextUtils.TruncateAt.END);v.setGravity(Gravity.CENTER_VERTICAL);v.setText(labels[pos]+"  ▾");return v;
            }
            @Override public View getDropDownView(int pos,View recycled,android.view.ViewGroup parent){
                TextView v=(TextView)super.getDropDownView(pos,recycled,parent);v.setTextColor(FG);
                v.setTextSize(13);v.setPadding(dp(8),dp(6),dp(6),dp(6));v.setMinHeight(dp(38));v.setBackgroundColor(SURFACE);return v;
            }
        };
    }
    private Spinner spinner(LinearLayout parent,String[] labels){
        Spinner s=new Spinner(activity);s.setMinimumHeight(0);s.setAdapter(spinnerAdapter(labels));s.setBackground(boxBackground(SURFACE));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(34));lp.setMargins(dp(1),dp(1),dp(1),dp(1));parent.addView(s,lp);return s;
    }
    private void buildPage(){
        if(page==null)return;
        ui.removeCallbacks(searchDebounce);
        page.removeAllViews();runtimeInputs.clear();for(int i=0;i<controlRows.length;i++)controlRows[i]=null;
        if(backup!=null)backup.setVisibility(selected>=2&&selected<=5?View.VISIBLE:View.GONE);
        itemList=null;itemInfo=null;itemSelected=null;itemSearch=null;itemTypeFilter=null;itemIdField=null;
        exportInfo=null;exportStart=null;exportCancel=null;exportSave=null;
        currencyType=null;currencyCurrent=null;itemScroll=null;
        if(selected==0||selected==1){
            text(page,"Enable + value + Apply. Reset affects runtime cheats only; Load is explicit.",10);
            int start=selected==0?0:18,end=selected==0?18:22;
            for(int id=start;id<end;id++)controlRow(id);
            final CheckBox combine=new CheckBox(activity);combine.setButtonTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));combine.setText("Multiply global × category (cap ×100)");combine.setTextColor(FG);combine.setChecked(activeCombine);
            combine.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener(){public void onCheckedChanged(CompoundButton b,boolean c){if(ready&&NativeBridge.setCombine(c?1:0)){activeCombine=c;prefs.edit().putBoolean("combine",c).apply();}}});page.addView(combine);
            text(page,"Specific category overrides global by default. CRIT/Guard are ratings, not %.",10);
        }else if(selected==2){
            text(page,"Base-stat edits are permanent. Current/max HP and battle modifiers are separate. Back up your save first.",12);
            final Spinner stat=spinner(page,STATS),operation=spinner(page,new String[]{"SET","ADD","SUBTRACT","MULTIPLY"});final EditText value=number(page,"100");
            LinearLayout buttons=row(page);button(buttons,"Read",new View.OnClickListener(){public void onClick(View v){request("read",STATS[stat.getSelectedItemPosition()],0,0,false);}});
            button(buttons,"Apply",new View.OnClickListener(){public void onClick(View v){try{request("stat",STATS[stat.getSelectedItemPosition()],operation.getSelectedItemPosition(),Double.parseDouble(value.getText().toString()),true);}catch(NumberFormatException ex){showResult("Enter a valid number");}}});
            text(page,"INVENTORY CAPACITY — Effective slots, including ring/plugin bonuses. SET/ADD/SUBTRACT protects occupied slots. Limit: 2,000.",13);
            final Spinner slotMode=spinner(page,new String[]{"SET","ADD","SUBTRACT"});slotMode.setSelection(1);
            final EditText slots=number(page,"50");slots.setHint("Slot amount (whole number)");
            LinearLayout slotButtons=row(page);
            button(slotButtons,"READ capacity",new View.OnClickListener(){public void onClick(View v){request("capacity","slots",-1,0,false);}});
            button(slotButtons,"APPLY",new View.OnClickListener(){public void onClick(View v){
                try{int amount=Integer.parseInt(slots.getText().toString().trim());if(amount<0||amount>2000)throw new NumberFormatException();
                    request("capacity","slots",slotMode.getSelectedItemPosition(),amount,true);
                }catch(NumberFormatException ex){showResult("Enter a whole number 0..2000");}
            }});
            text(page,"The saved bonus belongs to this player. Reset only disables runtime cheats. Save/load persistence needs testing; do not remove this library while using expanded storage.",12);
        }else if(selected==3){
            buildItemBrowser();
        }else if(selected==4){
            final EditText exp=number(page,"100");
            button(row(page),"Add cultivation EXP",new View.OnClickListener(){public void onClick(View v){try{int n=Integer.parseInt(exp.getText().toString());if(n<1||n>9999999)throw new NumberFormatException();request("gm","jingyan_"+n,0,0,true);}catch(NumberFormatException e){showResult("EXP must be 1..9999999");}}});
            gmButton("Recover stamina","huifu");gmButton("Learn manuals already in bag","xueximiji");gmButton("Max manual cultivation","xiulianmiji");gmButton("Max bag manual entries","citiaomanji");gmButton("Add grade-1 breakthrough materials","tupocailiao_1");gmButton("Repair player's artifacts","xiulifabao_0");
            final EditText jade=number(page,"1000");button(row(page),"Set Bagua Jade protection points",new View.OnClickListener(){public void onClick(View v){try{int n=Integer.parseInt(jade.getText().toString());if(n<0||n>9999999)throw new NumberFormatException();request("gm","shuangyupei_"+n,0,0,true);}catch(NumberFormatException e){showResult("Points must be 0..9999999");}}});
            gmButton("Unlock Eye of Providence skills","haotianyanjiesuojineng");
            text(page,"Each button invokes the game's GM implementation. Results still need device/save-load testing. NPC editing is excluded.",12);
        }else if(selected==5){
            buildCurrencyEditor();
        }else{
            buildDiagnostics();
        }
    }
    private long queuedId(String reply){if(reply==null||!reply.startsWith("QUEUED:"))return 0;try{return Long.parseLong(reply.substring(7));}catch(NumberFormatException e){return 0;}}
    private void confirm(String title,String message,final Runnable action){
        TextView heading=new TextView(activity);heading.setText(title);heading.setTextColor(FG);heading.setTextSize(18);heading.setPadding(dp(20),dp(16),dp(20),dp(4));heading.setBackgroundColor(BG);
        TextView body=new TextView(activity);body.setText(message);body.setTextColor(FG);body.setTextSize(16);body.setPadding(dp(20),dp(12),dp(20),dp(16));body.setBackgroundColor(BG);
        final AlertDialog dialog=new AlertDialog.Builder(activity,android.R.style.Theme_Material_Dialog_Alert).setCustomTitle(heading).setView(body)
            .setNegativeButton("Cancel",null).setPositiveButton("Confirm",new android.content.DialogInterface.OnClickListener(){public void onClick(android.content.DialogInterface d,int which){action.run();}}).create();
        dialog.setOnShowListener(new android.content.DialogInterface.OnShowListener(){public void onShow(android.content.DialogInterface d){dialog.getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(BG));dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(FG);dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setTextColor(MUTED);}});dialog.show();
    }
    private void buildCurrencyEditor(){
        text(page,"Personal balances and sect treasury are separate. READ shows the actual player/sect target. Changes use native game transactions.",13);
        currencyType=spinner(page,CURRENCY_LABELS);currencyCurrent=text(page,"Select a resource, then READ.",14);currencyCurrent.setTextIsSelectable(true);
        final Spinner mode=spinner(page,new String[]{"SET","ADD","SUBTRACT"});mode.setSelection(1);
        final EditText amount=number(page,"100000");amount.setHint("Non-negative whole amount");LinearLayout actions=row(page);
        button(actions,"READ / Refresh",new View.OnClickListener(){public void onClick(View v){request("currency",CURRENCY_KEYS[currencyType.getSelectedItemPosition()],-1,0,false);}});
        button(actions,"APPLY",new View.OnClickListener(){public void onClick(View v){try{
            final int index=currencyType.getSelectedItemPosition(),op=mode.getSelectedItemPosition();
            final long value=Long.parseLong(amount.getText().toString().trim());long max=index==4||index==6?1000000000000L:2000000000L;if(value<0||value>max)throw new NumberFormatException();
            final String key=CURRENCY_KEYS[index];confirm("Confirm resource edit",CURRENCY_LABELS[index]+"\n"+(op==0?"SET":op==1?"ADD":"SUBTRACT")+" "+value+"\nSect treasury edits require READ first.",new Runnable(){public void run(){request("currency",key,op,value,true);}});
        }catch(NumberFormatException ex){showResult("Whole amount required. Personal/reputation limit: 2 billion; treasury/faith: 1 trillion.");}}});
        currencyType.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,View v,int pos,long id){if(currencyCurrent!=null)currencyCurrent.setText("READ "+CURRENCY_LABELS[pos]+" to inspect its balance and target.");}public void onNothingSelected(AdapterView<?> p){}});
        text(page,"Personal contribution uses #10011; sect treasury uses Int64. City and Immortal Store tokens are separate. Lifetime earned totals/achievement counters are excluded. Check persistence after save/load.",12);
    }
    private void appendDiagnostic(String message){logDiagnostic(message,true);}
    private void logDiagnostic(String message,boolean latest){
        if(latest)lastDiagnostic=message;android.util.Log.i("TOIModMenu",message);File file=new File(activity.getFilesDir(),"toimod-v03-diagnostics.txt");
        try{if(file.length()>131072)file.delete();FileOutputStream out=new FileOutputStream(file,true);try{out.write((System.currentTimeMillis()+" "+message+"\n\n").getBytes("UTF-8"));}finally{out.close();}}catch(IOException ignored){}
    }
    /** Actual item configuration, 40 rows per page. Only a tapped row selects an ID. */
    private void buildItemBrowser(){
        LinearLayout filters=row(page);
        itemTypeFilter=spinner(filters,new String[]{"All Types","Pills","Manuals","Equipment","Materials","Other","Alchemy recipes"});
        itemTypeFilter.setLayoutParams(new LinearLayout.LayoutParams(dp(138),dp(34)));itemTypeFilter.setDropDownWidth(dp(230));
        itemSearch=edit(filters,"",false);itemSearch.setHint("Name / key / ID");itemSearch.setLayoutParams(new LinearLayout.LayoutParams(0,dp(34),1));
        itemInfo=text(page,"Loading actual catalog...",10);itemInfo.setSingleLine(true);itemInfo.setEllipsize(android.text.TextUtils.TruncateAt.END);itemInfo.setTextColor(MUTED);
        itemScroll=new ScrollView(activity);itemScroll.setFillViewport(false);itemList=new LinearLayout(activity);itemList.setOrientation(LinearLayout.VERTICAL);itemScroll.addView(itemList);page.addView(itemScroll,new LinearLayout.LayoutParams(-1,dp(112)));
        itemSelected=text(page,selectedItemId.isEmpty()?"Tap an item to select it":selectedItemName+" (#"+selectedItemId+")",11);itemSelected.setMaxLines(2);
        itemIdField=number(page,selectedItemId);itemIdField.setVisibility(View.GONE);
        LinearLayout actions=row(page);
        button(actions,"Prev",new View.OnClickListener(){public void onClick(View v){catalogOffset=Math.max(0,catalogOffset-40);scheduleCatalog();}});
        button(actions,"Next",new View.OnClickListener(){public void onClick(View v){if(catalogOffset+40<catalogTotal){catalogOffset+=40;scheduleCatalog();}}});
        final EditText qty=number(actions,"1");qty.setHint("Qty");qty.setLayoutParams(new LinearLayout.LayoutParams(dp(56),dp(36)));
        button(actions,"Add item",new View.OnClickListener(){public void onClick(View v){
            try{final int quantity=Integer.parseInt(qty.getText().toString().trim());if(quantity<1||quantity>9999)throw new NumberFormatException();
                final String id=selectedItemId,name=selectedItemName;if(id.isEmpty()){showResult("Select a real item before adding it");return;}
                confirm("Add item",name+" (#"+id+")\nQuantity: "+quantity,new Runnable(){public void run(){request("item",id,0,quantity,true);}});
            }catch(NumberFormatException ex){showResult("Quantity must be a whole number 1..9999");}
        }});
        LinearLayout exports=row(page);
        exportStart=button(exports,"Export ALL item IDs (read-only)",new View.OnClickListener(){public void onClick(View v){startReadOnlyCatalogExport();}});exportStart.setTextSize(10);exportStart.setMaxLines(2);exportStart.setLayoutParams(new LinearLayout.LayoutParams(0,dp(36),3));
        exportCancel=button(exports,"Cancel",new View.OnClickListener(){public void onClick(View v){endReadOnlyCatalogExport("Export cancelled by user; incomplete output cleanup queued.",false);}});exportCancel.setTextSize(10);
        exportSave=button(exports,"Save JSONL",new View.OnClickListener(){public void onClick(View v){saveCatalogDocument();}});exportSave.setTextSize(10);
        exportInfo=text(page,exportMessage,10);exportInfo.setMaxLines(2);exportInfo.setTextIsSelectable(true);updateExportWidgets();
        itemTypeFilter.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,View v,int pos,long id){catalogOffset=0;scheduleCatalog();}public void onNothingSelected(AdapterView<?> p){}});
        itemSearch.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int count,int after){}public void onTextChanged(CharSequence s,int st,int before,int count){catalogOffset=0;scheduleCatalog();}public void afterTextChanged(Editable e){}});
        ui.post(new Runnable(){public void run(){resizeItemList();}});scheduleCatalog();
    }
    private void resizeItemList(){
        if(itemScroll==null||contentScroll==null)return;int space=contentScroll.getHeight();if(space<=0)return;
        int height=Math.max(dp(80),Math.min(dp(260),space-dp(180)));android.view.ViewGroup.LayoutParams p=itemScroll.getLayoutParams();
        if(p.height!=height){p.height=height;itemScroll.setLayoutParams(p);}
    }
    private void scheduleCatalog(){
        if(selected!=3 || itemSearch==null)return;
        ui.removeCallbacks(searchDebounce);
        if(itemInfo!=null)itemInfo.setText("Searching actual catalog...");
        ui.postDelayed(searchDebounce,330);
    }

    // Read-only export: one existing Unity-thread request per page; file IO on one worker.
    private File catalogExportDirectory(){
        File dir=null;try{dir=activity.getExternalFilesDir("toi_catalog_exports");}catch(SecurityException ignored){}
        return dir!=null?dir:new File(activity.getFilesDir(),"toi_catalog_exports");
    }
    private File lastCatalogFile(){
        try{
            File f=completedCatalog!=null?completedCatalog:new File(prefs.getString("catalog_export_file",""));
            if(f.isFile()&&f.getParentFile()!=null&&f.getParentFile().getCanonicalFile().equals(catalogExportDirectory().getCanonicalFile())&&f.getName().matches("toi_item_catalog_[0-9]+_[a-zA-Z0-9-]+\\.jsonl"))return f;
        }catch(IOException ignored){}
        return null;
    }
    private void updateExportWidgets(){
        if(exportStart!=null)exportStart.setEnabled(catalogExport==null);
        if(exportCancel!=null)exportCancel.setEnabled(catalogExport!=null);
        if(exportSave!=null)exportSave.setEnabled(catalogExport==null&&lastCatalogFile()!=null);
        if(exportInfo!=null)exportInfo.setText(exportMessage);
    }
    private void exportProgress(String message){exportMessage=message;updateExportWidgets();}
    private void checkExportContext(ExportJob job)throws IOException{
        refreshNativeSnapshot(true);
        if(!ready||!schemaMatched||nativeSnapshot==null)throw new IOException("Native catalog is not initialized or protocol mismatched");
        job.guard.check(nativeSnapshot.optLong("generation",-1),nativeSnapshot.optBoolean("player_loaded",false),android.os.SystemClock.uptimeMillis());
    }
    private void startReadOnlyCatalogExport(){
        if(catalogExport!=null){showResult("Export already in progress");return;}
        refreshNativeSnapshot(true);
        if(!ready||!schemaMatched||nativeSnapshot==null||!nativeSnapshot.optBoolean("player_loaded",false)){showResult("Load a player save and wait for the matching native catalog");return;}
        try{
            final ExportJob job=new ExportJob(new CatalogExportGuard(nativeSnapshot.optLong("generation",-1),android.os.SystemClock.uptimeMillis()));
            final File dir=catalogExportDirectory();
            final File destination=new File(dir,"toi_item_catalog_"+System.currentTimeMillis()+"_"+java.util.UUID.randomUUID().toString()+".jsonl");
            catalogExport=job;exportProgress("Starting read-only export. Keep the game in the foreground.");
            exportWorker.execute(new Runnable(){public void run(){try{
                // Process death can leave an orphan. Only remove this exporter's incomplete files.
                File[] old=dir.listFiles();if(old!=null)for(File f:old)if(f.getName().matches("toi_item_catalog_[0-9]+_[a-zA-Z0-9-]+\\.jsonl\\.partial")&&!f.delete())throw new IOException("Could not clean an incomplete export");
                job.writer=new ReadOnlyCatalogExport(destination,100000,job.guard.generation);
                if(job.cancelled){job.writer.discard();return;}
                ui.post(new Runnable(){public void run(){if(!disposed&&catalogExport==job&&!job.cancelled)sendReadOnlyCatalogPage(0);}});
            }catch(final Exception ex){exportWorkerFailure(job,"Export could not start: "+ex.getMessage());}}});
            poll();
        }catch(Exception ex){String message="Export could not start: "+ex.getMessage();if(catalogExport!=null)endReadOnlyCatalogExport(message,false);else showResult(message);}
    }
    private void sendReadOnlyCatalogPage(int offset){
        final ExportJob job=catalogExport;if(job==null)return;
        try{
            checkExportContext(job);
            String reply=NativeBridge.request("catalog","@-1||"+offset,0,0,false);
            long id=queuedId(reply);if(id==0)throw new IOException("Catalog request rejected: "+reply);
            job.guard.queued(id,offset,android.os.SystemClock.uptimeMillis());poll();
        }catch(Exception ex){endReadOnlyCatalogExport("Export stopped: "+ex.getMessage(),false);}
    }
    private void receiveReadOnlyCatalogPage(JSONObject receipt){
        final ExportJob job=catalogExport;if(job==null)return;
        try{
            checkExportContext(job);
            job.guard.receive(receipt.getLong("id"),receipt.optLong("generation",-1),receipt.getString("kind"),receipt.getString("key"),receipt.getString("state"),android.os.SystemClock.uptimeMillis());
            final String message=receipt.getString("message");
            exportWorker.execute(new Runnable(){public void run(){try{
                if(job.cancelled)return;
                final int next=job.writer.acceptPage(message),written=job.writer.rowsWritten(),total=job.writer.total();
                if(job.cancelled){job.writer.discard();return;}
                ui.post(new Runnable(){public void run(){if(disposed||catalogExport!=job||job.cancelled)return;
                    try{
                        checkExportContext(job);job.guard.written(android.os.SystemClock.uptimeMillis());
                        if(next<0){completedCatalog=job.writer.outputFile();prefs.edit().putString("catalog_export_file",completedCatalog.getAbsolutePath()).apply();endReadOnlyCatalogExport("Exported "+written+" catalog items: "+completedCatalog.getAbsolutePath()+". Tap Save JSONL to retrieve it.",true);}
                        else{exportProgress("Exporting "+written+" / "+total+" catalog items (read-only)");sendReadOnlyCatalogPage(next);}
                    }catch(Exception ex){endReadOnlyCatalogExport("Export aborted: "+ex.getMessage(),false);}
                }});
            }catch(final Exception ex){exportWorkerFailure(job,"Catalog export aborted: "+ex.getMessage());}}});
        }catch(Exception ex){String detail=receipt.optString("message","");if(detail.length()>240)detail=detail.substring(0,240);endReadOnlyCatalogExport("Export aborted: "+ex.getMessage()+" — "+detail,false);}
    }
    private void exportWorkerFailure(final ExportJob job,final String message){
        String cleanup="";try{if(job.writer!=null)job.writer.discard();}catch(IOException ex){cleanup="; cleanup failed: "+ex.getMessage();}
        final String full=message+cleanup;ui.post(new Runnable(){public void run(){if(!disposed&&catalogExport==job)endReadOnlyCatalogExport(full,false);}});
    }
    private void endReadOnlyCatalogExport(String message,final boolean completed){
        final ExportJob job=catalogExport;if(job==null)return;
        catalogExport=null;job.cancelled=true;job.guard.cancel();
        // Queue cleanup after any in-flight file write, including a final rename racing Cancel.
        exportWorker.execute(new Runnable(){public void run(){try{if(job.writer!=null){if(completed)job.writer.close();else job.writer.discard();}}catch(final IOException ex){android.util.Log.e("TOIModMenu","Catalog cleanup failed",ex);ui.post(new Runnable(){public void run(){if(!disposed){showResult("Catalog cleanup failed: "+ex.getMessage());appendDiagnostic("Catalog cleanup failed: "+ex.getMessage());}}});}}});
        if(!disposed){exportProgress(message);showResult(message);appendDiagnostic(message);}
    }
    private void saveCatalogDocument(){
        File file=lastCatalogFile();if(file==null){showResult("Complete an export first");return;}
        CatalogDocumentFragment.save(activity,file);
    }
    public static void catalogDocumentResult(Activity a,String message){
        if(instance!=null&&instance.activity==a&&!instance.disposed){instance.exportProgress(message);instance.showResult(message);instance.appendDiagnostic(message);}
    }
    private void submitCatalog(){
        if(selected!=3||itemTypeFilter==null||itemSearch==null||itemList==null)return;
        if(!ready){if(itemInfo!=null)itemInfo.setText("Waiting for Unity native adapter...");return;}
        if(pendingCatalog){catalogRefreshNeeded=true;return;}
        int[] types={-1,1,2,3,5,6,254};
        int filter=types[Math.max(0,Math.min(types.length-1,itemTypeFilter.getSelectedItemPosition()))];
        String search=itemSearch.getText().toString().trim().replace('|',' ');
        if(search.length()>80)search=search.substring(0,80);
        String key="@"+filter+"|"+search+"|"+catalogOffset;
        String reply=NativeBridge.request("catalog",key,0,0,false);
        catalogRequestId=queuedId(reply);catalogRequestKey=key;pendingCatalog=catalogRequestId!=0;
        if(itemInfo!=null)itemInfo.setText(pendingCatalog?"Loading matching items...":reply);
        if(pendingCatalog)poll();
    }
    private void renderCatalog(String receipt){
        if(itemList==null||itemInfo==null||selected!=3)return;
        String[] lines=receipt.split("\n",-1);
        String[] header=lines[0].split("\t",-1);
        if(header.length!=4){itemInfo.setText("Malformed native catalog header");return;}
        try{catalogTotal=Integer.parseInt(header[1]);catalogOffset=Integer.parseInt(header[2]);}
        catch(NumberFormatException ex){itemInfo.setText("Malformed native catalog count");return;}
        itemList.removeAllViews();
        int displayed=0;
        for(int i=1;i<lines.length;i++){
            if(lines[i].isEmpty())continue;
            final String[] col=lines[i].split("\t",-1);
            if(col.length<4||!col[0].matches("[0-9]+"))continue;
            final String id=col[0],name=col[1];
            String label=(name.isEmpty()?"#"+id:name)+"  #"+id+" · Lv "+col[3];
            Button choose=button(label,new View.OnClickListener(){public void onClick(View v){
                if(itemIdField!=null)itemIdField.setText(id);
                selectedItemName=name;selectedItemId=id;
                if(itemSelected!=null)itemSelected.setText("Selected: "+name+" (#"+id+")");
            }});
            choose.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);choose.setTextSize(12);choose.setMaxLines(2);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(36));lp.setMargins(0,dp(1),0,dp(1));
            itemList.addView(choose,lp);displayed++;
        }
        if(catalogTotal==0)itemInfo.setText("No items match this category/search");
        else itemInfo.setText("Showing "+(catalogOffset+1)+"–"+(catalogOffset+displayed)+" of "+catalogTotal+" items · scroll to choose");
        if(displayed==0)text(itemList,"No matching items.",12);
    }
    private void controlRow(final int id){
        final ControlRow r=new ControlRow();r.id=id;controlRows[id]=r;
        JSONObject n=nativeControl(id);r.confirmed=n!=null&&n.optBoolean("enabled",false);r.confirmedValue=n!=null?n.optDouble("value",1):1;
        LinearLayout controls=row(page);
        r.toggle=new CheckBox(activity);r.toggle.setTextColor(FG);r.toggle.setTextSize(12);r.toggle.setMinimumHeight(0);r.toggle.setPadding(0,0,0,0);r.toggle.setButtonTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));r.toggle.setChecked(r.confirmed);setControlLabel(r);
        controls.addView(r.toggle,new LinearLayout.LayoutParams(0,dp(40),1));
        r.input=number(controls,prefs.getString("v"+id,defaultValue(id)));r.input.setTextSize(13);r.input.setLayoutParams(new LinearLayout.LayoutParams(dp(65),dp(38)));if(id<3)r.input.setVisibility(View.GONE);
        r.apply=button("Apply",new View.OnClickListener(){public void onClick(View v){if(controlAvailable(id)||r.confirmed)applyRow(r,r.toggle.isChecked(),false);else explainUnavailable(id);}});controls.addView(r.apply,new LinearLayout.LayoutParams(dp(55),dp(40)));
        r.receipt=text(page,controlUi.last(id),10);r.receipt.setVisibility("NOT_APPLIED".equals(controlUi.last(id))?View.GONE:View.VISIBLE);r.receipt.setMaxLines(2);
        r.toggle.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener(){public void onCheckedChanged(CompoundButton b,boolean on){if(controlUi.callbacksAllowed())applyRow(r,on,true);}});
        if(id==16||id==17){
            final SeekBar slider=new SeekBar(activity);slider.setMax(100);slider.setProgress((int)(Math.max(0,Math.min(1,r.confirmedValue))*100));slider.setProgressTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));slider.setThumbTintList(ColorStateList.valueOf(FG));slider.setLayoutParams(new LinearLayout.LayoutParams(-1,dp(18)));page.addView(slider);
            slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar s,int progress,boolean user){if(user)r.input.setText(Double.toString(progress/100.0));}public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){}});
        }
        updateEnabled();
    }
    private JSONObject nativeControl(int id){return nativeControls!=null&&id>=0&&id<nativeControls.length()?nativeControls.optJSONObject(id):null;}
    private boolean controlAvailable(int id){JSONObject n=nativeControl(id);return ready&&schemaMatched&&n!=null&&n.optBoolean("capability",false);}
    private void setControlLabel(ControlRow r){r.toggle.setText(LABELS[r.id]+(r.confirmed?" · ON":" · OFF"));}
    private void applyRow(final ControlRow r,boolean on,boolean fromToggle){
        controlUi.beginOperation();double value=1;
        if(r.id>=3){if(fromToggle&&!on)value=r.confirmedValue;else try{value=Double.parseDouble(r.input.getText().toString().trim());}catch(NumberFormatException ex){value=Double.NaN;}}
        try{
            JSONObject reply=new JSONObject(NativeBridge.applyControl(r.id,KEYS[r.id],on,value));
            String code=reply.optString("result","NATIVE_REJECTED");boolean actual=reply.optBoolean("enabled",NativeBridge.controlEnabled(r.id));double observed=reply.optDouble("value",r.confirmedValue);
            r.confirmed=actual;r.confirmedValue=observed;controlUi.programmatic(new Runnable(){public void run(){r.toggle.setChecked(r.confirmed);}});setControlLabel(r);
            String requested=Double.isNaN(value)?r.input.getText().toString():Double.toString(value);
            String detail=LABELS[r.id]+" [id="+r.id+", "+KEYS[r.id]+"] — "+code+"\nRequested "+requested+"; allowed "+MIN[r.id]+".."+MAX[r.id]+"; capability="+reply.optBoolean("capability",false)+"\nNative: "+(actual?"ON":"OFF")+" value="+observed+"; "+reply.optString("detail","");
            controlUi.record(r.id,code+" · "+(actual?"ON":"OFF")+" · "+observed);r.receipt.setText(controlUi.last(r.id));r.receipt.setVisibility(View.VISIBLE);r.receipt.setTextColor("APPLIED".equals(code)?MUTED:Color.rgb(255,174,164));
            showResult(detail);result.setTextColor("APPLIED".equals(code)?MUTED:Color.rgb(255,174,164));appendDiagnostic(detail);
            if("APPLIED".equals(code))prefs.edit().putBoolean("e"+r.id,actual).putString("v"+r.id,Double.toString(observed)).apply();
            refreshNativeSnapshot(true);
        }catch(Throwable ex){
            controlUi.programmatic(new Runnable(){public void run(){r.toggle.setChecked(r.confirmed);}});
            String detail=LABELS[r.id]+" [id="+r.id+"] — NATIVE_REJECTED: "+ex.getClass().getSimpleName()+": "+ex.getMessage();controlUi.record(r.id,detail);r.receipt.setText(detail);r.receipt.setVisibility(View.VISIBLE);showResult(detail);appendDiagnostic(detail);
        }
    }
    private void explainUnavailable(int id){
        refreshNativeSnapshot(true);JSONObject n=nativeControl(id);
        String code=!schemaMatched?"CONTROL_ID_MISMATCH":!ready?"NOT_INITIALIZED":nativeSnapshot!=null&&!nativeSnapshot.optBoolean("player_loaded",false)?"PLAYER_NOT_LOADED":n!=null&&n.optBoolean("capability",false)?"READY":n!=null&&!n.optBoolean("hooks_installed",false)?"HOOK_UNAVAILABLE":"CAPABILITY_DISABLED";
        String detail=LABELS[id]+" [id="+id+", bit="+id+"] — "+code+"\nAllowed "+MIN[id]+".."+MAX[id]+"; "+(n==null?"No native schema":n.optString("required_hooks",""));
        showResult(detail);appendDiagnostic(detail);
    }
    private void updateEnabled(){
        for(final ControlRow r:controlRows)if(r!=null){
            boolean available=controlAvailable(r.id);r.toggle.setEnabled(schemaMatched&&(available||r.confirmed));r.input.setEnabled(available);r.apply.setEnabled(initialized);r.apply.setText(available||r.confirmed?"Apply":"Why?");
        }
    }
    private String defaultValue(int id){return id==11||id==13?"0":"1";}
    private void resetRuntime(){if(!initialized)return;NativeBridge.resetControls();for(int i=0;i<22;i++)controlUi.record(i,"RESET · OFF");activeCombine=false;SharedPreferences.Editor e=prefs.edit().putBoolean("combine",false);for(int i=0;i<22;i++)e.putBoolean("e"+i,false).putString("v"+i,defaultValue(i));e.apply();refreshNativeSnapshot(true);showResult("Reset: runtime controls OFF. Persistent currency, items and capacity were not repeated or reverted.");buildPage();}
    private void loadSaved(){
        if(!ready||!schemaMatched){showResult("NOT_INITIALIZED: wait for the matching native control schema");return;}
        int accepted=0,failed=0;
        for(int i=0;i<22;i++)try{
            boolean on=prefs.getBoolean("e"+i,false);JSONObject current=nativeControl(i);double value=Double.parseDouble(prefs.getString("v"+i,defaultValue(i)));
            if(!on&&current!=null)value=current.optDouble("value",1);
            JSONObject r=new JSONObject(NativeBridge.applyControl(i,KEYS[i],on,value));String code=r.optString("result","NATIVE_REJECTED");controlUi.record(i,code+" · "+LABELS[i]);
            if("APPLIED".equals(code))accepted++;else{failed++;appendDiagnostic("Load "+LABELS[i]+" id="+i+": "+r.toString());}
        }catch(Exception ex){failed++;controlUi.record(i,"INVALID_VALUE · "+LABELS[i]);}
        activeCombine=prefs.getBoolean("combine",false);NativeBridge.setCombine(activeCombine?1:0);refreshNativeSnapshot(true);showResult("Load runtime settings: accepted="+accepted+", failed="+failed+". Inspect per-control Diagnostics. Persistent edits were not replayed.");
    }
    private void gmButton(String label,final String command){button(row(page),label,new View.OnClickListener(){public void onClick(View v){request("gm",command,0,0,true);}});}
    private void request(final String kind,final String key,final int operation,final double value,boolean persistent){
        controlUi.beginOperation();
        if(!ready){showResult("NOT_INITIALIZED: native adapters are not ready");return;}
        if(persistent&&!backup.isChecked()){showResult("Back up the save, then check the acknowledgment");return;}
        String reply=NativeBridge.request(kind,key,operation,value,backup.isChecked());
        showResult(reply);
        long id=queuedId(reply);if(id!=0)pendingActions.put(Long.valueOf(id),new Ticket(controlUi.beginOperation()));
        poll();
    }
    private void headerButton(LinearLayout parent,String label,View.OnClickListener listener){Button b=button(label,listener);b.setTextSize(11);parent.addView(b,new LinearLayout.LayoutParams(dp(44),dp(34)));}
    private void showResult(String message){
        controlUi.beginOperation();if(result!=null){result.setText(message);result.setTextColor(MUTED);}
        if(resultToggle!=null){String first=message==null?"":message.split("\n",2)[0];resultToggle.setText((resultExpanded?"▾ ":"▸ ")+first);}
    }
    private void refreshNativeSnapshot(boolean force){
        if(!initialized)return;long now=android.os.SystemClock.uptimeMillis();if(!force&&now-lastSnapshotTime<1000)return;lastSnapshotTime=now;
        try{
            JSONObject next=new JSONObject(NativeBridge.controlDiagnostics());JSONArray controls=next.optJSONArray("controls");boolean match=next.optInt("protocol",0)==4&&controls!=null&&controls.length()==KEYS.length;
            if(match)for(int i=0;i<KEYS.length;i++){JSONObject c=controls.getJSONObject(i);if(c.getInt("id")!=i||!KEYS[i].equals(c.getString("key"))||c.getDouble("minimum")!=MIN[i]||c.getDouble("maximum")!=MAX[i]){match=false;break;}}
            schemaMatched=match;nativeSnapshot=next;nativeControls=controls;ready=next.optBoolean("initialized",false)&&!next.optBoolean("failed",false);
            if(!match&&!schemaWarningShown){schemaWarningShown=true;showResult("CONTROL_ID_MISMATCH: Java/native IDs or ranges differ. Runtime control edits disabled.");}if(match)schemaWarningShown=false;
            for(final ControlRow row:controlRows)if(row!=null){JSONObject c=nativeControl(row.id);if(c!=null){row.confirmed=c.optBoolean("enabled",false);row.confirmedValue=c.optDouble("value",row.confirmedValue);controlUi.programmatic(new Runnable(){public void run(){row.toggle.setChecked(row.confirmed);}});setControlLabel(row);}}
        }catch(Throwable ex){schemaMatched=false;ready=false;bootStatus="Diagnostic protocol failed: "+ex.getClass().getSimpleName();}
    }
    private void buildDiagnostics(){
        refreshNativeSnapshot(true);
        LinearLayout actions=row(page);button(actions,"Refresh",new View.OnClickListener(){public void onClick(View v){refreshNativeSnapshot(true);buildPage();}});
        button(actions,"Copy report",new View.OnClickListener(){public void onClick(View v){String report=nativeSnapshot==null?lastDiagnostic:nativeSnapshot.toString();android.content.ClipboardManager c=(android.content.ClipboardManager)activity.getSystemService(android.content.Context.CLIPBOARD_SERVICE);if(c!=null)c.setPrimaryClip(android.content.ClipData.newPlainText("TOI v0.3.2 diagnostics",report));}});
        text(page,"Policy APPLIED is not a device gameplay verification. Caps and hooks are reported separately.",11);
        if(nativeSnapshot==null){text(page,bootStatus,12);return;}
        text(page,"Ready="+ready+" · player="+nativeSnapshot.optBoolean("player_loaded",false)+" · combat bound="+nativeSnapshot.optBoolean("combat_bound",false)+"\nHooks="+nativeSnapshot.optInt("hook_count",0)+" · capability mask="+nativeSnapshot.optString("capability_mask","?")+" · schema="+schemaMatched,11);
        TextView catalog=text(page,nativeSnapshot.optString("catalog",""),11);catalog.setTextIsSelectable(true);
        JSONArray hooks=nativeSnapshot.optJSONArray("hooks");if(hooks!=null)for(int i=0;i<hooks.length();i++){JSONObject h=hooks.optJSONObject(i);if(h!=null)text(page,h.optString("name")+": "+h.optString("status")+" · "+h.optString("detail"),10);}
        for(int i=0;i<22;i++){JSONObject c=nativeControl(i);if(c==null)continue;JSONObject last=c.optJSONObject("last_apply");
            String lastText=last==null||last.optLong("request_id",0)==0?"NOT_APPLIED":last.optString("result")+" #"+last.optLong("request_id");
            text(page,LABELS[i]+" [id="+i+"] · "+(c.optBoolean("enabled")?"ON":"OFF")+" · value "+c.optDouble("value"),12);
            TextView detail=text(page,"Need: "+c.optString("required_hooks")+"\nInstalled="+c.optBoolean("hooks_installed")+" · capability bit "+i+"="+(c.optBoolean("capability")?"1":"0")+" · allowed "+MIN[i]+".."+MAX[i]+"\nLast: "+lastText+(last==null?"":" · "+last.optString("detail")),10);detail.setTextIsSelectable(true);
        }
        TextView last=text(page,lastDiagnostic,10);last.setTextIsSelectable(true);
        button(row(page),"Retry initialization",new View.OnClickListener(){public void onClick(View v){beginInitialization();}});
    }
    private void beginInitialization(){
        if(busy)return;busy=true;
        new Thread(new Runnable(){public void run(){String message;
            try{
                if(NativeBridge.bridgeVersion()!=4)throw new IOException("CONTROL_ID_MISMATCH: retain the v0.3.1 native library (protocol 4)");
                File lib=new File(activity.getApplicationInfo().nativeLibraryDir,"libil2cpp.so");
                if(!lib.isFile()){
                    lib=new File(activity.getCacheDir(),"toi_baseline_libil2cpp.so");
                    if(!lib.isFile()||lib.length()!=144951312L){
                        String[] splits=activity.getApplicationInfo().splitSourceDirs;
                        ArrayList<String> apks=new ArrayList<String>();apks.add(activity.getApplicationInfo().sourceDir);
                        if(splits!=null)for(String split:splits)apks.add(split);
                        boolean copied=false;
                        for(String apk:apks){ZipFile z=new ZipFile(apk);try{ZipEntry entry=z.getEntry("lib/arm64-v8a/libil2cpp.so");if(entry!=null){InputStream in=z.getInputStream(entry);FileOutputStream out=new FileOutputStream(lib);try{byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}finally{in.close();out.close();}copied=true;break;}}finally{z.close();}}
                        if(!copied)throw new IOException("ARM64 IL2CPP not found in APK or ABI splits");
                    }
                }
                File metadata=new File(activity.getFilesDir(),"toimod/global-metadata.dat");
                if(!metadata.isFile()){
                    metadata=new File(activity.getCacheDir(),"toi_baseline_metadata.dat");
                    if(!metadata.isFile()||metadata.length()!=42923616L){
                        InputStream in=null;String[] paths={"bin/Data/Managed/Metadata/global-metadata.dat","toimod/global-metadata.dat"};
                        for(String path:paths)try{in=activity.getAssets().open(path);break;}catch(IOException ignored){}
                        if(in==null)throw new IOException("Metadata asset missing; see installation instructions");
                        FileOutputStream out=new FileOutputStream(metadata);try{byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}finally{in.close();out.close();}
                    }
                }
                message=NativeBridge.prepare(lib.getAbsolutePath(),metadata.getAbsolutePath());initialized=message.startsWith("BASELINE_MATCHED");
            }catch(Throwable e){message="INIT FAILED: "+e.getClass().getSimpleName()+": "+e.getMessage();}
            final String resultMessage=message;ui.post(new Runnable(){public void run(){if(disposed)return;bootStatus=resultMessage;status.setText(bootStatus);busy=false;poll();}});
        }},"TOI-Prepare").start();
    }
    private void poll(){
        ui.removeCallbacks(pollTask);ui.post(pollTask);
    }
    private void updatePoll(){
        if(disposed)return;
        if(initialized){String s=NativeBridge.status();
            boolean previousReady=ready;refreshNativeSnapshot(false);status.setText(s);updateEnabled();
            if(!previousReady&&ready&&selected==3)scheduleCatalog();
            if(catalogExport!=null)try{checkExportContext(catalogExport);}catch(IOException ex){endReadOnlyCatalogExport("Export aborted: "+ex.getMessage(),false);}
            try{
                JSONArray replies=new JSONArray(NativeBridge.takeGameResults());
                for(int i=0;i<replies.length();i++){
                    JSONObject r=replies.getJSONObject(i);long id=r.getLong("id");
                    String kind=r.getString("kind"),key=r.getString("key"),state=r.getString("state"),message=r.getString("message");
                    if(catalogExport!=null&&catalogExport.guard.owns(id)){
                        receiveReadOnlyCatalogPage(r);
                        continue;
                    }
                    if("catalog".equals(kind)){
                        if(id!=catalogRequestId)continue;pendingCatalog=false;
                        if(!catalogRefreshNeeded&&key.equals(catalogRequestKey)){
                            if("CATALOG".equals(state))renderCatalog(message);else if(itemInfo!=null){itemInfo.setText(state+": catalog error — see Diagnostics");showResult(state+": "+message);appendDiagnostic("catalog ["+key+"] "+message);}
                        }
                        if(catalogRefreshNeeded){catalogRefreshNeeded=false;submitCatalog();}
                    }else{
                        Ticket ticket=pendingActions.remove(Long.valueOf(id));boolean latest=ticket!=null&&controlUi.isLatest(ticket.epoch);
                        if(latest){showResult(kind+" — "+state+"\n"+message);result.setTextColor("FAILED".equals(state)||"BLOCKED".equals(state)||"REJECTED".equals(state)?Color.rgb(255,174,164):MUTED);}
                        if("currency".equals(kind)&&currencyCurrent!=null&&currencyType!=null&&key.equals(CURRENCY_KEYS[currencyType.getSelectedItemPosition()]))currencyCurrent.setText(state+"\n"+message);
                        logDiagnostic(kind+" ["+key+"] "+state+"\n"+message,latest);
                    }
                }
            }catch(Exception ex){if(catalogExport!=null)endReadOnlyCatalogExport("Export aborted: malformed native receipt — "+ex.getMessage(),false);showResult("Receipt decode error: "+ex.getClass().getSimpleName()+": "+ex.getMessage());}

        }
        if((panel.getVisibility()==View.VISIBLE||catalogExport!=null)&&!activity.isFinishing())ui.postDelayed(pollTask,pendingCatalog||!pendingActions.isEmpty()||catalogExport!=null?100:1000);
    }
}

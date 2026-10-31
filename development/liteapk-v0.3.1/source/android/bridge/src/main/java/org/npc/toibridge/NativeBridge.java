package org.npc.toibridge;

/**
 * JNI boundary used by the in-Activity ModMenu; not a standalone application.
 * Call prepare off the Android UI thread (it hashes about 188 MB).
 * Settings are snapshotted on Unity's verified scripting callback. Persistent
 * requests are queued and executed there, never on an Android UI/worker thread.
 * Do not map pump to Activity.runOnUiThread or UnityPlayer.queueGLThread.
 */
public final class NativeBridge {
    private NativeBridge() {}
    static { System.loadLibrary("toimodmenu"); }
    public static native int bridgeVersion();
    public static native String applyControl(int id,String key,boolean enabled,double value);
    public static native String controlDiagnostics();
    public static native String takeGameResults();
    public static native long capabilities();
    public static native boolean controlEnabled(int id);
    public static native boolean setControl(int id, boolean enabled, double value);
    public static native boolean setCombine(int mode);
    public static native void resetControls();
    public static native void closeMenu();
    public static native String request(String kind, String key, int operation, double value, boolean backupAcknowledged);
    public static native String result();
    public static native String prepare(String il2cppFile, String metadataFile);
    public static native String armExperiment(String worldSession, boolean backupAcknowledged,
                                               boolean experimentalDispatchAcknowledged);
    public static native String enqueueExpProbe(long amount, String worldSession);
    public static native String enqueueHpProbe(long amount, String worldSession);
    public static native String status();
    public static native String takeReceipts();
    public static native void disarm();
}

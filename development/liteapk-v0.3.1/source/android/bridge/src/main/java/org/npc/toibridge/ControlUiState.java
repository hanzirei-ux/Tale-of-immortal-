package org.npc.toibridge;

/** Android-independent guard used by the real checkbox/result bindings. */
public final class ControlUiState {
    private int programmaticDepth;
    private long epoch;
    private final String[] lastResult = new String[22];
    public boolean callbacksAllowed() { return programmaticDepth == 0; }
    public void programmatic(Runnable setter) {
        programmaticDepth++;
        try { setter.run(); } finally { programmaticDepth--; }
    }
    public long beginOperation() { return ++epoch; }
    public boolean isLatest(long operation) { return operation == epoch; }
    public void record(int id,String result) {
        if(id<0||id>=lastResult.length)throw new IllegalArgumentException("control id");
        lastResult[id]=result;
    }
    public String last(int id) { return lastResult[id]==null?"NOT_APPLIED":lastResult[id]; }
}

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryPoolMXBean;
import java.lang.management.MemoryType;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Locale;

/**
 * Naive dense matrix multiplication in Java (Assignment 1).
 *
 * <p>Storage layout: idiomatic {@code double[][]} (an array of row arrays; each row is a separate,
 * contiguous heap object). Loop order ijk with a scalar accumulator, identical to the C and Python
 * versions, so the floating-point evaluation order is the same in the three languages.
 *
 * <p>Usage: {@code java MatMulNaive --a A.bin --b B.bin --n N [--warmup W] [--reps R]
 * [--min-sample-time T] [--out-c C.bin]}
 *
 * <p>Protocol (same as the C and Python drivers): inputs are loaded and C is allocated outside the
 * timed region; W in-process warm-up repetitions (needed for JIT compilation) are followed by R
 * measured repetitions; each repetition times a batch of kernel calls with System.nanoTime() and
 * reports time per call; the checksum sum(C) is printed after every repetition (it consumes the
 * result, so the JIT cannot remove the computation). One JSON line per repetition on stdout.
 */
public final class MatMulNaive {

    /** C[i][j] = sum_k A[i][k] * B[k][j], k increasing. C is fully overwritten. */
    static void multiply(double[][] a, double[][] b, double[][] c, int n) {
        for (int i = 0; i < n; i++) {
            double[] ai = a[i];   // row of A (same row hoisting as in the Python version)
            double[] ci = c[i];
            for (int j = 0; j < n; j++) {
                double s = 0.0;
                for (int k = 0; k < n; k++) {
                    s += ai[k] * b[k][j];   // B is walked down a column: one row object per k
                }
                ci[j] = s;
            }
        }
    }

    /** Reads an n x n little-endian float64 row-major file, one row at a time (small buffer). */
    static double[][] readMatrix(String path, int n) throws IOException {
        double[][] m = new double[n][n];
        try (FileChannel ch = FileChannel.open(Path.of(path), StandardOpenOption.READ)) {
            if (ch.size() != 8L * n * n) {
                throw new IOException(path + ": expected exactly " + ((long) n * n) + " float64 values");
            }
            ByteBuffer buf = ByteBuffer.allocate(8 * n).order(ByteOrder.LITTLE_ENDIAN);
            for (int i = 0; i < n; i++) {
                buf.clear();
                while (buf.hasRemaining()) {
                    if (ch.read(buf) < 0) throw new IOException(path + ": unexpected end of file");
                }
                buf.flip();
                buf.asDoubleBuffer().get(m[i]);
            }
        }
        return m;
    }

    static void writeMatrix(String path, double[][] m, int n) throws IOException {
        try (FileChannel ch = FileChannel.open(Path.of(path), StandardOpenOption.CREATE,
                StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING)) {
            ByteBuffer buf = ByteBuffer.allocate(8 * n).order(ByteOrder.LITTLE_ENDIAN);
            for (int i = 0; i < n; i++) {
                buf.clear();
                buf.asDoubleBuffer().put(m[i]);
                buf.limit(8 * n);
                while (buf.hasRemaining()) ch.write(buf);
            }
        }
    }

    static double checksum(double[][] c, int n) {
        double s = 0.0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) s += c[i][j];
        }
        return s;
    }

    /** Sum over heap memory pools of the peak used bytes since JVM start (MemoryPoolMXBean). */
    static long heapPeakUsed() {
        long total = 0;
        for (MemoryPoolMXBean pool : ManagementFactory.getMemoryPoolMXBeans()) {
            if (pool.getType() == MemoryType.HEAP && pool.getPeakUsage() != null) {
                total += pool.getPeakUsage().getUsed();
            }
        }
        return total;
    }

    private static void usage() {
        System.err.println("usage: MatMulNaive --a A.bin --b B.bin --n N [--warmup W] [--reps R]"
                + " [--min-sample-time T] [--out-c C.bin]");
        System.exit(2);
    }

    public static void main(String[] args) throws IOException {
        String aPath = null, bPath = null, cOut = null;
        int n = -1, warmup = 0, reps = 1;
        double minSample = 0.0;
        for (int i = 0; i < args.length; i++) {
            if (i + 1 >= args.length) usage();
            switch (args[i]) {
                case "--a" -> aPath = args[++i];
                case "--b" -> bPath = args[++i];
                case "--n" -> n = Integer.parseInt(args[++i]);
                case "--warmup" -> warmup = Integer.parseInt(args[++i]);
                case "--reps" -> reps = Integer.parseInt(args[++i]);
                case "--min-sample-time" -> minSample = Double.parseDouble(args[++i]);
                case "--out-c" -> cOut = args[++i];
                default -> usage();
            }
        }
        if (aPath == null || bPath == null || n < 1 || warmup < 0 || reps < 0) usage();

        double[][] a = readMatrix(aPath, n);
        double[][] b = readMatrix(bPath, n);
        double[][] c = new double[n][n];   // allocated (and zero-filled by the JVM) outside timing

        long batch = 1;
        for (int r = 0; r < warmup + reps; r++) {
            boolean isWarm = r < warmup;
            long calls = isWarm ? 1 : batch;
            long t0 = System.nanoTime();
            for (long k = 0; k < calls; k++) multiply(a, b, c, n);
            double t = (System.nanoTime() - t0) * 1e-9 / calls;
            System.out.println(String.format(Locale.ROOT,
                    "{\"time_s\": %.9e, \"timer_boundary\": \"kernel\", \"repetition\": %d, "
                    + "\"is_warmup\": %b, \"checksum\": %s, \"memory_metric\": \"jvm_heap_peak_used_bytes\", "
                    + "\"memory_bytes\": %d, \"batch\": %d, \"language_impl\": \"Java %s\"}",
                    t, r, isWarm, Double.toString(checksum(c, n)), heapPeakUsed(), calls,
                    System.getProperty("java.vm.version")));
            if (r == warmup - 1 && minSample > 0.0 && t > 0.0) {
                batch = Math.max(1, Math.min(100000, (long) Math.ceil(minSample / t)));
            }
        }
        if (reps == 0 && warmup == 0) multiply(a, b, c, n);   // --out-c only
        if (cOut != null) writeMatrix(cOut, c, n);
    }
}

# Execution environment

Captured: 2026-10-27T22:47:18+00:00 on host `daniel-Creator-15M-A9SD`

## CPU (lscpu)

```
Architecture:                            x86_64
CPU(s):                                  12
Model name:                              Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz
Thread(s) per core:                      2
Core(s) per socket:                      6
Socket(s):                               1
CPU(s) scaling MHz:                      78%
CPU max MHz:                             4500.0000
CPU min MHz:                             800.0000
L1d cache:                               192 KiB (6 instances)
L1i cache:                               192 KiB (6 instances)
L2 cache:                                1.5 MiB (6 instances)
L3 cache:                                12 MiB (1 instance)
NUMA node(s):                            1
SIMD flags: avx avx2 fma sse4_2 
nproc (online logical CPUs): 12
```

## Frequency scaling / turbo

```
governor(cpu0): powersave
intel_pstate no_turbo: 0
AC power online (1=plugged): 1
```

## Memory

```
               total       usado       libre  compartido   búf/caché  disponible
Mem:            15Gi       4,9Gi       1,8Gi       594Mi       9,7Gi        10Gi
Inter:         7,6Gi       320Ki       7,6Gi
```

## Operating system

```
Linux daniel-Creator-15M-A9SD 7.0.0-38-generic #38~24.04.4-Ubuntu SMP PREEMPT_DYNAMIC Mon Sep 14 16:37:11 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
PRETTY_NAME="Ubuntu 24.04.5 LTS"
VERSION_ID="24.04"
```

## Toolchain versions

```
gcc           gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
clang         not installed
java          openjdk version "21.0.12.1" 2026-08-18
javac         javac 21.0.12.1
mvn           Apache Maven 3.8.7
python3       Python 3.12.3
pip           pip 24.0 from /home/daniel/Documentos/Universidad/4Year/Big_Data/Teoria/Assigments/Assignment01_Basic_MatMul_Languages/.venv/lib/python3.12/site-packages/pip (python 3.12)
docker        Docker version 28.3.3, build 980b856
mpicc         not installed
mpirun        not installed
spark-submit  not installed
perf          perf version 7.0.14
```

## Python packages (active interpreter: /home/daniel/Documentos/Universidad/4Year/Big_Data/Teoria/Assigments/Assignment01_Basic_MatMul_Languages/.venv/bin/python3)

```
contourpy==1.4.0
cycler==0.12.1
fonttools==4.68.0
kiwisolver==1.5.1
matplotlib==3.11.2
numpy==2.5.4
packaging==26.3
pandas==3.1.0
pillow==13.0.0
pyparsing==3.3.3
python-dateutil==3.0.0
scipy==1.18.1
six==1.17.0
tzdata==2026.5
```

## Threading-related environment variables

```
(none set)
```

## Load at capture time

```
 22:47:19 up  6:33,  1 user,  load average: 2,11, 1,90, 1,06
```

## Assignment 1 build and runtime settings

```
C compiler:      gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
C flags:         -O2 -std=c11 -Wall -Wextra (default x86-64 target, no -march, no -ffast-math, single thread)
gcc -O2 target:   -march= 		x86-64
JDK:             OpenJDK Runtime Environment (build 21.0.12.1+1-1-24.04.4-Ubuntu)
JVM:             OpenJDK 64-Bit Server VM (build 21.0.12.1+1-1-24.04.4-Ubuntu, mixed mode, sharing)
JVM flags:       -Xms1g -Xmx4g -XX:+UseG1GC (default tiered JIT compilation)
Java GC/JIT threads: JVM default (background threads; the kernel itself runs on the main thread)
Python (bench):  CPython 3.12.3 - /home/daniel/Documentos/Universidad/4Year/Big_Data/Teoria/Assigments/Assignment01_Basic_MatMul_Languages/.venv/bin/python
Python packages (venv): contourpy==1.4.0 cycler==0.12.1 fonttools==4.68.0 kiwisolver==1.5.1 matplotlib==3.11.2 numpy==2.5.4 packaging==26.3 pandas==3.1.0 pillow==13.0.0 pyparsing==3.3.3 python-dateutil==3.0.0 scipy==1.18.1 six==1.17.0 tzdata==2026.5 
perf_event_paranoid: 4 (hardware counters not available)
GNU time:        time (GNU Time) UNKNOWN
Thread env for runs: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
```

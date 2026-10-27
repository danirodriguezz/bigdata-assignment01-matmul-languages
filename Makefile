# Reproducibility pipeline — Assignment 01 (Daniel Rodríguez Alonso, Big Data ULPGC 2026-2027)
# Naive dense matrix multiplication in C, Java and Python.
NN      := 01
NAME    := Assignment$(NN)_RodriguezAlonso
VENV    := .venv
PY      := $(VENV)/bin/python
SKILLS  := .claude/skills
CFLAGS  := -O2 -std=c11 -Wall -Wextra
C_SRC   := src/c/bench_naive.c src/c/matmul_naive.c src/c/matrix_io.c
C_BIN   := build/c/matmul_naive_c
J_CLASS := build/java/MatMulNaive.class

.PHONY: all setup build test inputs pilot bench env analysis report package clean

all: setup test inputs bench analysis report package

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -r requirements.txt
	$(PY) -m pip freeze > requirements-lock.txt
	touch $(VENV)/bin/activate

$(C_BIN): $(C_SRC) src/c/matmul_naive.h src/c/matrix_io.h
	mkdir -p build/c
	gcc $(CFLAGS) -o $@ $(C_SRC) -lm

$(J_CLASS): src/java/MatMulNaive.java
	mkdir -p build/java
	javac --release 21 -d build/java $<

# gcc flag variants for the separate (optional) c_flags experiment
build/c/matmul_naive_c_O0: $(C_SRC)
	mkdir -p build/c && gcc -O0 -std=c11 -Wall -Wextra -o $@ $(C_SRC) -lm
build/c/matmul_naive_c_O3: $(C_SRC)
	mkdir -p build/c && gcc -O3 -std=c11 -Wall -Wextra -o $@ $(C_SRC) -lm
build/c/matmul_naive_c_O3_native: $(C_SRC)
	mkdir -p build/c && gcc -O3 -march=native -std=c11 -Wall -Wextra -o $@ $(C_SRC) -lm
C_VARIANTS := build/c/matmul_naive_c_O0 build/c/matmul_naive_c_O3 build/c/matmul_naive_c_O3_native

build: $(C_BIN) $(J_CLASS) $(C_VARIANTS)   ## compile C (+ flag variants) and Java (Python needs no build)

setup: $(VENV)/bin/activate build    ## venv + compile implementations

test: setup                          ## correctness tests — must pass before any benchmark
	$(PY) tests/test_correctness.py

inputs: setup                        ## shared input files + checksums (seed 42)
	$(PY) scripts/gen_inputs.py --config configs/experiment.json

env:                                 ## environment snapshot (venv first in PATH -> its packages)
	PATH="$(CURDIR)/$(VENV)/bin:$$PATH" bash $(SKILLS)/benchmark-protocol/scripts/capture_env.sh results/environment.md
	bash scripts/env_extra.sh >> results/environment.md

pilot: test inputs                   ## quick end-to-end smoke run (small n)
	$(PY) scripts/run_experiments.py --experiment pilot

bench: test inputs                   ## full experiment (~75 min; serialised by the machine-wide lock)
	bash scripts/run_all_benchmarks.sh

analysis: setup                      ## results/raw -> results/summary, report/figures, report/generated
	$(PY) analysis/make_all.py

report:                              ## compile PDF and copy to deliverables/
	cd report && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
	mkdir -p deliverables && cp report/main.pdf deliverables/$(NAME)_Report.pdf

package: report                      ## materials zip from the committed git tree
	bash $(SKILLS)/reproducibility-package/templates/package.sh $(NN)

clean:
	cd report && latexmk -C || true
	rm -rf build target

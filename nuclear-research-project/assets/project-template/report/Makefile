.PHONY: all clean

all:
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex

clean:
	latexmk -C -outdir=build main.tex

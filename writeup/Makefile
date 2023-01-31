ts := $(shell /bin/date "+%Y-%m-%d---%H-%M-%S")
project_name = llm_ask

plots =

plots += plots/hiring_tradeoff.pdf
plots/hiring_tradeoff.pdf: ../analysis/horton.R ../data/horton.db
	cd ../analysis && Rscript horton.R

plots += plots/kkt.pdf
plots/kkt.pdf: ../analysis/kkt.R ../data/kkt.db
	cd ../analysis && Rscript kkt.R

plots += plots/score_distro.pdf
plots/score_distro.pdf: ../analysis/sqb.R
	cd ../analysis && Rscript sqb.R

plots += plots/charness_rabin.pdf ../data/charness_rabin.db
plots/charness_rabin.pdf: ../analysis/charness_rabin.R
	cd ../analysis && Rscript charness_rabin.R

$(project_name).pdf: $(project_name).tex
	pdflatex -shell-escape -interaction=batchmode $(project_name)
	pdflatex -shell-escape -interaction=batchmode $(project_name)
	bibtex $(project_name) 
	pdflatex -shell-escape -interaction=batchmode $(project_name)
	pdflatex -shell-escape -interaction=batchmode $(project_name)
	gs -q -dNOPAUSE -dBATCH -dPDFSETTINGS=/prepress -sDEVICE=pdfwrite -sOutputFile=tmp.pdf $(project_name).pdf
	mv tmp.pdf $(project_name).pdf

aeri: $(project_name).pdf
	pdftk $(project_name).pdf cat 2-14 output word_count.pdf

toread: $(project_name).pdf
	 cp $(project_name).pdf ~/Dropbox/toread/$(project_name)_$(ts).pdf 

website: $(project_name).pdf
	scp $(project_name).pdf johnjhorton@johnjhorton.ssh.wpengine.net:/home/wpe-user/sites/johnjhorton/papers

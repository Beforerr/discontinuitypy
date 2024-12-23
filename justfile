import "files/quarto.just"

default:
    just --list

ensure-env:
    pixi install
    pre-commit install

publish-qrcode:
    segno "https://beforerr.github.io/discontinuitypy" -o=images/qrcode.png --light transparent --scale 10

publish: pypi-publish quarto-publish

pypi-publish: export
    nbdev_readme --path notebooks/index.qmd
    pdm publish

test:
    nbdev_test --n_workers 4 --do_print
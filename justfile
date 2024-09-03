import "files/quarto.just"

default:
  just --list

ensure-env:
  pre-commit install

publish-qrcode:
  segno "https://beforerr.github.io/discontinuitypy" -o=images/qrcode.png --light transparent --scale 10

publish: pypi-publish quarto-publish

pypi-publish: export
  pdm publish
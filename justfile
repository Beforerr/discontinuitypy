import "files/quarto.just"

default:
  just --list

ensure_env:
  pre-commit install

publish-qrcode:
  segno "https://beforerr.github.io/ids_finder" -o=images/qrcode.png --light transparent --scale 10

publish: pypi-publish quarto-publish

pypi-publish: export
  pdm publish
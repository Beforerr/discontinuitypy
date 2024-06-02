setup-agu:
  quarto add quarto-journals/agu --no-prompt

preview: export
  #!/usr/bin/env sh
  if command -v nbdev_preview &> /dev/null; then
    nbdev_preview
  else
    quarto preview
  fi

quarto-publish:
  #!/usr/bin/env sh
  if command -v nbdev_proc_nbs &> /dev/null; then
    nbdev_prepare
    nbdev_proc_nbs && cd _proc
  fi
  if ! quarto publish gh-pages --no-render --no-prompt; then
    echo "quarto publish gh-pages failed"
    quarto publish gh-pages
  fi

export:
  -nbdev_export
  -nbdev_export --path notebooks/__init__.ipynb

render-man:
  quarto render --profile man
  cp -r _manuscript _site/
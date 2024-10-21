#!/bin/sh
cd docs/data && poetry run python3 plot.py && cd ../../
DEPLOY=true poetry run mkdocs build
rm -rf ../jiegec.github.io/*
cp -r site/* ../jiegec.github.io/
cd ../jiegec.github.io/
ln -s feed_rss_updated.xml feed.xml
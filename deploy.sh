#!/bin/sh
poetry run mkdocs build
rm -rf ../jiegec.github.io/*
cp -r site/* ../jiegec.github.io/
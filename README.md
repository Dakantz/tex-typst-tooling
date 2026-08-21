# Tex + Typst CLI tooling

Just a collection of common scripts I use in a bundled CLI system.


Install and use it:

```sh
pip install texty-tool
texty-tool restructure-bib cleanup bibliography.bib
```

## Available Tools
[Full Documentation](DOCS.md)

### Bibliography Cleanup

```sh
texty-tool restructure-bib cleanup in.bib  out.bib [args]
```
>  Convert a BibTeX file by resolving DOIs and reformatting entries.                                                                        
### Check Runts (small overhangs)

```sh
texty-tool runts check-overhangs main.pdf
```
> Checks for small paragraph overhangs in PDFs. Thanks to @MrP01! 

### Convert the acronyms to typst acronyms

```sh
texty-tool convert-acronyms convert acronyms.tex 
```
> Takes an acronyms-only file (of the `glossaries` package) and converts it to typst-`glossarium` entries


### Preparing your paper form submission

```sh
texty-tool prepare-submission sources --force --verify --rerun
```
> Packages all sources touched by `latexmk` and `tikz-externalize`, ZIPs it and may additionally verify it!

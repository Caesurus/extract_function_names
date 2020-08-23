# extract_function_names

Converted pdf to txt with (pdfminer):
```
pdf2txt.py -o vxworks_kernel_programmers_guide_6.6.txt vxworks_kernel_programmers_guide_6.6.pdf
``` 

Run the extraction:
```
./pdf_text_scraper.py -f vxworks_kernel_programmers_guide_6.6.txt -o tables.json
```


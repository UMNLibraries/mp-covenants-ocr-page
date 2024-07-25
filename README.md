# mp-covenants-ocr-page

This AWS Lambda function is part of [Mapping Prejudice's](https://mappingprejudice.umn.edu/) Deed Machine application. This component receives a link to an s3 image key and runs Textract's detect_document_text method to create creates 3 new files: a Textract JSON file, a simple TXT file containing a text blob of all text found, and a stats json, which contains basic statistics like the amount of the page that is estimated to be handwritten, the number of lines, and number of words. Output of this function is sent to a parallel step that will use the OCRed text to search for racial covenant terms, and another that will create a web-friendly version of the image. This is the second Lambda in the Deed Machine initial processing Step Function.

The [Deed Machine](https://github.com/UMNLibraries/racial_covenants_processor/) is a multi-language set of tools that use OCR and crowdsourced transcription to identify racially restrictive covenant language, then map the results.

The Lambda components of the Deed Machine are built using Amazon's Serverless Application Model (SAM) and the AWS SAM CLI tool.

## Key links
- [License](https://github.com/UMNLibraries/racial_covenants_processor/blob/main/LICENSE)
- [Component documentation](https://the-deed-machine.readthedocs.io/en/latest/modules/lambdas/mp-covenants-ocr-page.html)
- [Documentation home](https://the-deed-machine.readthedocs.io/en/latest/)
- [Downloadable Racial covenants data](https://github.com/umnlibraries/mp-us-racial-covenants)
- [Mapping Prejudice main site](https://mappingprejudice.umn.edu/)

## Software development requirements
- Pipenv (Can use other virtual environments, but will require fiddling on your part)
- AWS SAM CLI
- Docker
- Python 3

## Quickstart commands

To build the application:

```bash
pipenv install
pipenv shell
sam build
```

To rebuild and deploy the application:

```bash
sam build && sam deploy
```

To run tests:

```bash
pytest
```
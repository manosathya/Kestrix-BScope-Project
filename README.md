# Borescope report parser

Turns borescope reports into structured records.

## Run

```
python main.py
```

Reads every `.txt` file in `Reports/` and prints one `BorescopeReport` per file.

## Output structure

Returns a `BorescopeReport`:

- **Report-level fields:** address, postcode, inspection date, wall type, recommended action, source file, parser version.
- **`observations`:** a list of `Observation` objects, each holding fill status, insulation type (enum plus potential versions of surveyor's raw wording), location, floor, cavity width range, coverage %, voids and debris.
- **`needs_review`:** true when the parser could not determine a fill status.
- **`warnings`:** human-readable notes, e.g. an unparseable date.


## Current Functionality

Having a structured report/observation structure allows a consistent schema across all reports, allowing for reproducibility and consistency when scaled to larger datasets. Report-level fields are kept alongside the parser version and source file, so every record can be traced and reviewed by a person when needed.

At the moment, the parser focuses on colon separated key/value fields, and separates text in this way initially to handle ideally structured data. The parser then moves on to common keywords found in reports relating to insulation types and fills. 

**Unclear or incomplete reports:** If a fill status cannot be determined, the record is returned with `FillStatus.UNKNOWN` and `needs_review=True`. Empty input is flagged the same way. An unparseable date is left as `None` with a note in `warnings`. None of these raise errors.

## Limitations and Potential Improvements

The current stage of the parser separates only on key/value type fields and matches on particular keywords found within the text. Not all text is structured this way and such changes would have to be made to accommodate different formats of text within reports. 

This initial approach has largely been taken due to the limited time to be spent on the project. However, establishing a consistent schema that can be expanded on when more reports are used was deemed to be an important first step. Additionally, using a low-resource method for filtering out easy to parse reports allows for more efficient resource allocation down the line for slightly more complex methods.

Improvements in functionality could include:

- Establishing methodology to split multiple drill points into separate observations if this is common practice.
- NER could be used to better extract details from the borescope reports by tagging spans of text (e.g. width, coverage, insulation type, location) using their surrounding context. The tagged spans are then normalised into the existing schema, for example mapping ‘inconsistent’ to FillStatus.PARTIAL and parsing ‘60-65mm’ into a min and max.
- An LLM could extract data from the reports by being given the output schema (fields and allowed enum values) and returning JSON that is validated against it. Accuracy could be improved with few-shot prompting, using example reports with their correct records, particularly where surveyor styles recur across many reports.
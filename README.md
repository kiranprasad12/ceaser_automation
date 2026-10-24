# iso2cii: Isometric PDF to CAESAR II Neutral File

This tool reads a pipe isometric drawing (PDF) and creates a CAESAR II neutral file (`.CII`).
It works offline on your PC. It uses no AI and needs no API key.

## What it reads from the PDF

- The pipe route (from the heavy lines in the drawing)
- The dimensions (with offline OCR)
- The line number
- The pipe schedule (from the bill of materials)
- The start point (E, S or N, EL from the "CONT'D FROM" or "CONT. ON" note; metres like `E 8313.136M` are converted to mm)
- The elevation at each corner (from the "EL +..." labels), so a sloping pipe gets the right rise

The pipe can be drawn as a thick line or as a thick shape built from many thin lines. Both are found.
Every small dimension mark on a long run becomes a node.
A dimension written with a leader line (a number with a slanted line pointing at a dimension line) is also used.
Example: 668, then 3000 x 8, then the remaining 1317 become separate elements.

## Temperature and pressure from Excel

Every run asks for the Excel line list, right after it asks where to save. Choose the file to fill temperature and pressure. Press Cancel to convert without it (temperature and pressure stay 0).
You can also give it on the command line with `--db "file.xlsx"`. `--no-ask` skips both questions.
The tool finds the row whose line number matches the drawing and writes the values into every element.

- The file needs a header row with a line number column, at least one temperature column and one pressure column.
- If the headers end with the CAESAR II number (for example `OPERATING_TEMP T1`, `DESIGN_PRESSURE P2`), that number is used, up to T9 and P9. Otherwise "design" columns become T1 and P1, "operating" becomes T2 and P2.
- `FV` (full vacuum) in a pressure cell is written as -101.325 kPa and a warning is printed.
- Hydro test pressure columns are ignored.
- Units are read from the header, or from another sheet of the workbook (your file has them on the sheet `CLL`), for example `(°C)` or `(kg/cm2g)`. If the tool cannot tell, it stops and asks for `--press-unit bar|kgcm2|kpa|mpa|psi` (or `--temp-unit C|F`). Pressure must be gauge.
- CAESAR II gets temperature in °C and pressure in kPa, because that is what your neutral file units say.
- The line number is matched ignoring spaces, quote marks and the size prefix. If the line is missing, or two rows disagree, the tool prints a warning and leaves 0.
- The screen shows which Excel column went into which field. Check that list once.

See `process_data_example.xlsx` for the layout.

## What you get

For each drawing, a new folder with three files:

| File | Purpose |
|---|---|
| `name.CII` | The neutral file. Import this into CAESAR II. |
| `name.review.json` | The values the tool read. You can edit it. |
| `name.check.png` | A picture of the route and nodes. Use it to check the result. |

## Setup (only once)

You need Python (Anaconda is fine). Open **Anaconda PowerShell Prompt** and run:

```
conda create -n neutral_convertor python=3.11 -y
conda activate neutral_convertor
pip install pymupdf rapidocr-onnxruntime pillow numpy
```

## How to run

```
conda activate neutral_convertor
cd "folder where iso2cii.py is"
python iso2cii.py "your_drawing.pdf"
```

1. A window opens. Choose where to save the results.
2. Wait about 1 to 2 minutes while the drawing is read.
3. Open the new folder. It is named like the PDF.

If you run it with no file name, a window lets you pick the PDF.

## Check before you import

1. Read the list printed on screen. The lengths of every leg and the node coordinates are shown.
2. Look for the line "End-point check ... OK". It compares the computed end point with the "CONT'D ON" note.
3. Open `name.check.png` and compare it with the drawing.
4. If a message says WARNING, read it before you continue.

## Import into CAESAR II

1. In CAESAR II go to **Tools, External Interfaces, CAESAR II Neutral File**.
2. Choose the option that converts a neutral file to a CAESAR II input file.
3. Select your `.CII` file and convert.
4. Open the job and check the model against the drawing.

## If a number was read wrong

1. Open `name.review.json` in Notepad.
2. Fix the numbers under `parts`. Each number is one pipe element, in order.
3. Save the file and run:

```
python iso2cii.py --from-json "name.review.json"
```

This rebuilds the `.CII` in a second. It does not read the PDF again.

## Useful options

| Option | Meaning |
|---|---|
| `--north up-right` | Use this if North points somewhere else on the sheet. Default is up-left. |
| `--sch 40` | Set the pipe schedule yourself. |
| `--wall 6.35` | Set the wall thickness in mm. |
| `--od 323.85` | Set the outside diameter in mm. |
| `--start E S EL` | Set the start point if the note cannot be read. |
| `--z-is-north` | Use this if your CAESAR II Z axis points North. Default is Z = South. |
| `--out-dir "D:\Results\Sheet6"` | Save straight into this folder and do not ask. |
| `--no-ask` | Do not ask where to save. Use a new folder next to the PDF. |

## What works and what does not

Works (tested on 16 sample PDFs from 2 CAD systems; see `RESULTS.md`):
- Vector PDF isometrics with a single run: straight legs along the isometric axes and bends.
- Pipe drawn as a thick line, or as a thick shape made of many thin lines.
- Dimensions in mm, chains of small dimensions, overall dimensions, and leader-line dimensions.
- Coordinates in mm or in metres (`E 8313.136M`), with a sloping pipe.
- A rotated page.
- 45 degree rolling legs between two axes, read from their two equal dimensions.
- Tee symbols at the start of the line (short end stubs are ignored).
- Red or blue markup on the sheet (only dark lines are taken as pipe).
- Sheets where all lines have the same width (a slower fallback is used).

Not supported yet:
- Branches and tees: the tool stops with a clear message.
- Continuation sheets that only hold a bill of materials: the tool says there is no drawing.
- Tees, branches, reducers, valves, flanges, supports. Only the single run is read.
- Dimensions in feet and inches.
- Pipes that do not follow the three isometric directions.
- Scanned or picture-only PDFs. The tool tries, but the result is not reliable. Check everything.
- Process data (temperature, pressure) and materials. This is phase 1: geometry only.

No tool can promise to read every PDF. This one is built to say clearly when it is unsure:
- If a leg cannot be read, it writes **no** `.CII`. It saves the review file and a picture that marks the leg, and you fill in the numbers and run `--from-json`.
- If the end point or elevation does not match the end note, it prints CHECK FAILED.
- It never writes a pipe piece of zero length.

Other things to know:
- The wall thickness table is ASME B36.10M. Please verify it for your pipe class.
- If the drawing has no text layer and the file name is not the line number, use `--line "..."`.
- Bend radius comes from "BEND RADIUS" notes, or from the bill of materials (for example 1.5D), or is set to 1.5 x pipe diameter.
- Reading a drawing needs about 3 GB of free memory. Do not run several drawings at the same time.
- If a PDF fails, send me the PDF and the file `iso2cii_error.txt` (if one was created) so the tool can be extended.

## Common problems

| Problem | What to do |
|---|---|
| "PyMuPDF is missing" | You are using a different Python. Run `conda activate neutral_convertor` first, or run the script from the same Python where you installed the packages. |
| "OCR package is missing" | Run `pip install rapidocr-onnxruntime` in the same environment. |
| WARNING: end point does not match | A dimension was probably misread, or North is not up-left. Check the list and try `--north up-right`. |
| No dimension found for a leg | Add the numbers by hand in the review JSON and use `--from-json`. |
| CAESAR II shows an error | Note the section name and line number in the message. |

## Line thickness

The tool groups the stroke widths on the sheet and takes as pipe the widest group that forms a clear isometric-angled network. A thicker title block or a dark marker is no longer taken as pipe. Thinner lines that start at the pipe are outlets, and the rest are dimensions. If all widths are about the same it falls back to reading the picture, which is less reliable.

## Branch outlets

If thin pipes leave the main run (for example 1.5 in outlets on a 4 in header), the tool reads them as outlets. Each outlet gets its length and position from its OPEN END note (E, S, EL) and its size from the "NS" label and the bill of materials. They are written as plain pipe elements. Add the tee or branch SIF in CAESAR II. If some outlets cannot be placed, the tool prints "INCOMPLETE"; if none can, it stops.

## Bends and nodes close to a corner

CAESAR II needs a straight pipe of at least R x tan(angle / 2) on both sides of a bend (R for a 90 degree bend). A node closer to the corner than that makes the bend overlap its neighbour.
The tool drops such a node and prints a warning. Example: with a 229 mm bend radius, a 6 mm piece after the bend is joined to the next piece.

## How the tool checks itself

- Both end notes ("CONT'D FROM" and "CONT'D ON") give the start and end point. The tool compares them with the computed end point.
- If a different reading of a leg (an overall dimension versus a chain, or the plane of a 45 degree leg) fits the end note, it uses that reading and says so.
- If one leg cannot be read, its length is calculated from the notes. The screen and the list show it as CALCULATED.
- If the end point still does not match, it prints how many mm are missing in which direction and CHECK FAILED. Do not import before you check.
- Sheets with branches stop with a message. `--ignore-branches` converts only the main run.

See `RESULTS.md` for the sheet-by-sheet table.

# Test results on the 16 sample PDFs

Tested in a Linux sandbox. The OCR package there is older than the one on your PC, so some numbers can differ when you run it.
"Closure" means the computed end point was compared with the "CONT'D ON" note at the other end of the pipe.

## Gives a .CII (9 sheets)

| PDF | Closure | Note |
|---|---|---|
| 6-CH-33803 | Exact (E, S and elevation) | Read fully from the drawing |
| 4-CH-33807 | Exact (E, S and elevation) | One leg (1134 mm) was calculated from the start and end notes because bold text covers its number. The tool says so |
| 4-RJ-33812-1 | Exact (E, S and elevation) | Header with 8 outlets (1.5 in, sch 80, 132 mm each) at the heights of their OPEN END notes. The header length (3333 mm) comes from the start and end notes, because the dimension numbers on this sheet do not add up. A short 1 in piece at the top end is modelled with the 4 in size |
| 6-RJ-33811-2 | Exact (E, S and elevation) | Header with 4 outlets. Header length comes from the notes |
| 6-RJ-33811-1 | Exact (E, S and elevation) | Header length from the notes. Only 9 of 11 outlets could be placed, the tool prints "INCOMPLETE". Do not use as it is |
| 4-RJ-33812-2 | Elevation exact, E is 144 mm short | The 1282 dimension is hidden under bold text. The tool prints the gap and "CHECK FAILED" |
| 12-ST-30108 | Worked on your PC earlier. In the sandbox it fails the closure check | The sandbox OCR reads 3000 as 5000, and the check catches it |
| 6-CH-33804, 6-UP-33601-4, FL-332-2601-L | No end note to check | Check by eye |

## Stops with a message (7 sheets)

| PDF | Reason |
|---|---|
| 6-UP-33601-1, 6-UP-33601-5 | Outlets found but they could not be placed from the OPEN END notes. A file without them would be wrong |
| 6-UP-33601-2 | Branch or tee in the main pipe |
| 6-RJ-33811-3, 6-UP-33601-3, 6-UP-33601-6 | No drawing, only the bill of materials |

## What changed in this round

- Sheets are joined by their connection points, whatever their line numbers. In the folder test, 4-RJ-33812 sheets 2 and 1 merged (end point and elevation exact). 6-CH-33804, 6-RJ-33811-2 and 6-RJ-33811-1 were joined into one file with a 382 mm connecting element and a turned-round sheet. That result has no end check and 13 of 15 outlets, so check it by eye before use.
- (earlier note) Several sheets of one line can be chosen together and are written as one merged file. Tested on 4-RJ-33812 sheets 1 and 2: 25 elements, the end point and elevation match the end note. Sheet 2 is still 144 mm short (hidden dimension), shown as a visible 144 mm connecting element. 6-RJ-33811 sheets 1 and 2 do not join (both end at the same point), so they are converted one by one. 6-UP-33601 has a tee on sheet 2, so its sheets are converted one by one.
- Branch outlets: thin pipes that leave the main run are read as outlets. Their length and position come from the OPEN END notes (E, S, EL). They are written as pipe elements with their own size and wall. Add the tee or branch SIF in CAESAR II.
- Wall thickness now uses the schedule of each size in the bill of materials, including 5S, 10S, 40S and 80S (10S pipe used the STD wall before).
- A single straight run whose dimension numbers do not add up to the start and end notes takes its length from the notes, with a warning.
- 45 degree (rolling) legs are read from their equal pair of dimensions, for example 219 / 219 with 310 on the diagonal, or 125 / 125 with 177.
- Short end stubs at a tee symbol are ignored when that is where the line meets another line.
- Every dimension number is read a second time at high zoom with slightly tilted angles, and the reads vote (718 was read as 118 before).
- The line number written along the pipe is no longer taken as a dimension (this had produced a 53601 mm leg on 6-UP-33601-4).
- If another reading of a leg (overall or chain, or which plane a 45 degree leg is in) makes the end point match the end note, that reading is used.
- If exactly one leg cannot be read, its length is calculated from the notes and labelled "CALCULATED".
- A large elevation difference is no longer hidden as a pipe slope. It is reported instead.

## Still not supported

- Tee and branch SIF data, and reducers (the thinner piece after a reducer is modelled with the main size).
- Branches that are not simple outlets, and sheets where the outlets cannot be matched to OPEN END notes.
- Dimensions covered by bold text or markup.
- Non-isometric directions other than 45 degree legs between two axes.

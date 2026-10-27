#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iso2cii.py  -  pipe isometric PDF  ->  CAESAR II neutral file (.CII)

No AI and no API key. Everything runs offline on your PC:
  * pipe route      : read from the heavy vector lines in the PDF
  * dimensions      : read with the free offline OCR "rapidocr-onnxruntime"
  * line number     : read from the PDF text layer (or OCR as a fallback)
  * start point     : read from the "CONT'D FROM" note (E / S / EL)
  * pipe size / wall: NPS from the line number, schedule from the bill of materials

Phase 1 = geometry only (nodes, lengths, bends, line number).
Not handled yet: tees, branches, reducers, valves, supports, process data.

Install once:
    pip install pymupdf rapidocr-onnxruntime pillow numpy

Use:
    python iso2cii.py drawing.pdf     -> asks where to save, then makes a folder "drawing" there, containing
                                         drawing.CII + drawing.review.json + drawing.check.png
    python iso2cii.py drawing.pdf --north up-left    (default; where North points on the sheet)
    python iso2cii.py drawing.pdf --sch 20 --wall 6.35
    python iso2cii.py --from-json drawing.review.json   (rebuild from the edited review file, no OCR)

ALWAYS open the .check.png and compare it with the drawing before you import.
"""
import argparse
import json
import math
import os
import re
import sys

# --------------------------------------------------------------------------
# Embedded layout, copied from files that CAESAR II imported successfully.
# --------------------------------------------------------------------------
T_VERSION = ['#$ VERSION ',
 '    5.00000      11.0000        1252',
 '    PROJECT:                                                                 ',
 '                                                                             ',
 '    CLIENT :                                                                 ',
 '                                                                             ',
 '    ANALYST:                                                                 ',
 '                                                                             ',
 '    NOTES  :                                                                 ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '                                                                             ',
 '   Data generated by CAESAR II / Neutral file interface Ver 11.00 1/13       ']
T_ELEMENT = ['         50.0         60.0     0.000000     0.000000       3000.0       323.85',
 '         6.35     0.000000     0.000000     0.000000     0.000000     0.000000',
 '     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '        150.0         10.4         12.5         12.5     0.000000        883.0',
 '     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '     0.000000     0.000000     0.000000     0.000000      9999.99      9999.99',
 '     0.000000     0.000000     0.000000     0.000000     0.000000',
 '           0 ',
 '           0 ',
 '             -1           -1',
 '            0            0            0            0            0            0',
 '            0            0            0            0            0            0',
 '            0            0            0']
T_ALLOW = ['#$ ALLOWBLS',
 '       0.000000     0.000000     0.000000     0.000000  1.00000      1.00000    ',
 '    1.00000         0.000000     0.000000  9999.99         0.000000  1.00000    ',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '    1.00000      1.00000      1.00000      1.00000      1.00000      1.00000    ',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000  9999.99         0.000000  1.00000    ',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000',
 '       0.000000     0.000000     0.000000']
T_UNITS = ['#$ UNITS   ',
 '    25.4000      4.44800     0.453600     0.112980     0.112980     0.689500E-02',
 '   0.555600     -17.7778      6.89460     0.689500E-02  27680.0      27680.0    ',
 '    27680.0     0.175120     0.112980     0.175120      1.00000      6894.76    ',
 '    25.4000      25.4000      25.4000      25.4000    ',
 '  SI-Bar         ',
 '  ON ',
 '  mm ',
 '  N  ',
 '  kg ',
 '  N.m   ',
 '  N.m   ',
 '  N/mm2     ',
 '  C',
 '  C',
 '  KPa       ',
 '  N/mm2     ',
 '  kg/m3     ',
 '  kg/m3     ',
 '  kg/m3     ',
 '  N/mm   ',
 '  N.m./deg  ',
 '  N/mm   ',
 "  g's",
 '  N/m2      ',
 '  mm.',
 '  mm.',
 '  mm ',
 '  mm ']
T_TAIL = ['1',
 '0',
 '0',
 '2',
 '0.0000',
 '1',
 '0',
 '0',
 '21.1142',
 '21.5983',
 '0',
 '0',
 '0',
 '0',
 '0',
 '0',
 '0.2500',
 '3',
 '0']


# Pipe data (ASME B36.10M).  OD in inches, wall in mm.  Please verify for your pipe class.
OD_IN = {0.5: 0.840, 0.75: 1.050, 1: 1.315, 1.25: 1.660, 1.5: 1.900, 2: 2.375, 2.5: 2.875,
         3: 3.5, 4: 4.5, 6: 6.625, 8: 8.625, 10: 10.75, 12: 12.75, 14: 14.0, 16: 16.0,
         18: 18.0, 20: 20.0, 24: 24.0, 26: 26.0, 28: 28.0, 30: 30.0, 32: 32.0, 36: 36.0}
WALL_MM = {
    0.5: {'STD': 2.77, '40': 2.77, 'XS': 3.73, '80': 3.73, '160': 4.78, 'XXS': 7.47},
    0.75: {'STD': 2.87, '40': 2.87, 'XS': 3.91, '80': 3.91, '160': 5.56, 'XXS': 7.82},
    1: {'STD': 3.38, '40': 3.38, 'XS': 4.55, '80': 4.55, '160': 6.35, 'XXS': 9.09},
    1.25: {'STD': 3.56, '40': 3.56, 'XS': 4.85, '80': 4.85, '160': 6.35, 'XXS': 9.70},
    1.5: {'STD': 3.68, '40': 3.68, 'XS': 5.08, '80': 5.08, '160': 7.14, 'XXS': 10.15},
    2: {'STD': 3.91, '40': 3.91, 'XS': 5.54, '80': 5.54, '160': 8.74, 'XXS': 11.07},
    2.5: {'STD': 5.16, '40': 5.16, 'XS': 7.01, '80': 7.01, '160': 9.53, 'XXS': 14.02},
    3: {'STD': 5.49, '40': 5.49, 'XS': 7.62, '80': 7.62, '160': 11.13, 'XXS': 15.24},
    4: {'STD': 6.02, '40': 6.02, 'XS': 8.56, '80': 8.56, '120': 11.13, '160': 13.49, 'XXS': 17.12},
    6: {'STD': 7.11, '40': 7.11, 'XS': 10.97, '80': 10.97, '120': 14.27, '160': 18.26, 'XXS': 21.95},
    8: {'20': 6.35, '30': 7.04, 'STD': 8.18, '40': 8.18, '60': 10.31, 'XS': 12.70, '80': 12.70,
        '160': 23.01, 'XXS': 22.23},
    10: {'20': 6.35, '30': 7.80, 'STD': 9.27, '40': 9.27, '60': 12.70, 'XS': 12.70, '80': 15.09,
         '160': 28.58, 'XXS': 25.40},
    12: {'20': 6.35, '30': 8.38, 'STD': 9.53, '40': 10.31, 'XS': 12.70, '60': 14.27, '80': 17.48,
         '160': 33.32, 'XXS': 25.40},
    14: {'10': 6.35, '20': 7.92, '30': 9.53, 'STD': 9.53, '40': 11.13, 'XS': 12.70, '60': 15.09,
         '80': 19.05, '160': 35.71},
    16: {'10': 6.35, '20': 7.92, '30': 9.53, 'STD': 9.53, '40': 12.70, 'XS': 12.70, '60': 16.66,
         '80': 21.44, '160': 40.49},
    18: {'10': 6.35, '20': 7.92, '30': 11.13, 'STD': 9.53, 'XS': 12.70, '40': 14.27, '60': 19.05,
         '80': 23.83},
    20: {'10': 6.35, '20': 9.53, '30': 12.70, 'STD': 9.53, 'XS': 12.70, '40': 15.09, '60': 20.62,
         '80': 26.19},
    24: {'10': 6.35, '20': 9.53, '30': 14.27, 'STD': 9.53, 'XS': 12.70, '40': 17.48, '60': 24.61,
         '80': 30.96},
    26: {'10': 7.92, 'STD': 9.53, 'XS': 12.70, '20': 12.70},
    28: {'10': 7.92, 'STD': 9.53, 'XS': 12.70, '20': 12.70, '30': 15.88},
    30: {'10': 7.92, 'STD': 9.53, 'XS': 12.70, '20': 12.70, '30': 15.88},
    32: {'10': 7.92, 'STD': 9.53, 'XS': 12.70, '20': 12.70, '30': 15.88, '40': 17.48},
    36: {'10': 7.92, 'STD': 9.53, 'XS': 12.70, '20': 12.70, '30': 15.88, '40': 19.05},
}

_WALL_S = {0.5: (1.65, 2.11, 2.77, 3.73), 0.75: (1.65, 2.11, 2.87, 3.91), 1: (1.65, 2.77, 3.38, 4.55),
           1.25: (1.65, 2.77, 3.56, 4.85), 1.5: (1.65, 2.77, 3.68, 5.08), 2: (1.65, 2.77, 3.91, 5.54),
           2.5: (2.11, 3.05, 5.16, 7.01), 3: (2.11, 3.05, 5.49, 7.62), 4: (2.11, 3.05, 6.02, 8.56),
           5: (2.77, 3.40, 6.55, 9.53), 6: (2.77, 3.40, 7.11, 10.97), 8: (2.77, 3.76, 8.18, 12.70),
           10: (3.40, 4.19, 9.27, 12.70), 12: (3.96, 4.57, 9.53, 12.70), 14: (3.96, 4.78, 9.53, 12.70),
           16: (4.19, 4.78, 9.53, 12.70), 18: (4.19, 4.78, 9.53, 12.70), 20: (4.78, 5.54, 9.53, 12.70),
           24: (5.54, 6.35, 9.53, 12.70)}
for _n, _v in _WALL_S.items():
    WALL_MM.setdefault(_n, {}).update({'5S': _v[0], '10S': _v[1], '40S': _v[2], '80S': _v[3]})
NODE_STEP = 10
STUB_MAX = 45.0            # page units: a free stub shorter than this at a tee symbol is dropped
SLOPE_MIN_DEV = 8.0        # degrees away from the 3 isometric axes = a sloped (rolling) leg
ISO_ANGLES = [30, 90, 150, 210, 270, 330]
HORIZONTAL_CYCLE = [150, 30, 330, 210]          # N, E, S, W when North = up-left (clockwise on the sheet)
NORTH_OPTIONS = {'up-left': 150, 'up-right': 30, 'down-right': 330, 'down-left': 210}


class ConvertError(Exception):
    pass


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def fmt_num(x):
    if abs(x) < 1e-9:
        return '0.000000'
    s = ('%.4f' % x).rstrip('0').rstrip('.')
    return s if '.' in s else s + '.0'


def row(vals, w=13):
    return ''.join(str(v).rjust(w) for v in vals)


def ctrl_row(vals):
    # CAESAR II writes the first CONTROL number 15 wide and the others 13 wide
    return str(vals[0]).rjust(15) + ''.join(str(v).rjust(13) for v in vals[1:])


def ang_diff(a, b, mod=360):
    d = abs(a - b) % mod
    return min(d, mod - d)


def snap_iso(phi):
    best = min(ISO_ANGLES, key=lambda a: ang_diff(phi, a))
    return best, ang_diff(phi, best)


def parse_nps(line_no):
    m = re.match(r'\s*(\d+)\s*-\s*(\d)\s*/\s*(\d)', line_no or '')
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    m = re.match(r'\s*(\d)\s*/\s*(\d)', line_no or '')
    if m:
        return int(m.group(1)) / int(m.group(2))
    m = re.match(r'\s*(\d+(?:\.\d+)?)', line_no or '')
    if m:
        v = float(m.group(1))
        return int(v) if v == int(v) else v
    return None


def norm_sch(s):
    s = re.sub(r'[\s.,]', '', (s or '').upper().replace('SCH', ''))
    if re.fullmatch(r'(5|10|40|80)S', s):
        return s                                   # stainless schedules have their own wall (ASME B36.19)
    s = re.sub(r'S$', '', s) if re.fullmatch(r'\d+S', s) else s
    return s


# --------------------------------------------------------------------------
# PDF: geometry
# --------------------------------------------------------------------------
def open_pdf(path, page_no):
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise ConvertError('PyMuPDF is missing.  Run:  pip install pymupdf')
    doc = fitz.open(path)
    page = doc[page_no]
    return fitz, doc, page


def _is_dark(c):
    return c is None or (len(c) >= 3 and max(c[:3]) < 0.35) or (len(c) == 1 and c[0] < 0.35)


def heavy_by_width(page):
    M = page.rotation_matrix
    raw = []
    for d in page.get_drawings():
        w = d.get('width') or 0
        if d.get('color') is None or w <= 0:
            continue
        dark = _is_dark(d.get('color'))
        for it in d['items']:
            if it[0] == 'l':
                a, b = it[1] * M, it[2] * M
                raw.append((w, (a.x, a.y), (b.x, b.y), dark))
    if not raw:
        raise ConvertError('No vector lines found. Is this a scanned PDF?  (needs a vector isometric)')
    # markup in red/blue must not be taken as pipe: use dark strokes when there are enough
    dk = [r for r in raw if r[3]]
    if len(dk) >= 10:
        raw = dk
    widths = sorted(r[0] for r in raw)
    seg_len = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])
    med = widths[len(widths) // 2]
    # group the stroke widths into classes (2.0 and 2.04 are the same class), longest-first by iso-angled length
    classes = []
    for w in sorted(set(round(r[0], 3) for r in raw), reverse=True):
        if classes and w >= 0.92 * classes[-1]['w']:
            classes[-1]['ws'].append(w)
        else:
            classes.append({'w': w, 'ws': [w]})
    for c in classes:
        c['lo'] = min(c['ws'])
        c['hi'] = max(c['ws'])
        iso = tot = 0.0
        for (w, a, b, _) in raw:
            if c['lo'] - 1e-6 <= round(w, 3) <= c['hi'] + 1e-6:
                L = seg_len(a, b)
                tot += L
                ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0])) % 180
                if min(ang_diff(ang, t, 180) for t in (30, 90, 150)) < 8 and L > 12:
                    iso += L
        c['iso'], c['len'] = iso, tot
    cand = [c for c in classes if c['hi'] >= 1.3 * med and c['iso'] >= 100]
    if not cand:
        raise ConvertError('Could not tell the heavy pipe lines from the thin lines (all line widths are similar).')
    # the pipe is the thick class with the most isometric-angled line, not simply the thickest line on the sheet
    # (a thick title block, a dark marker or a hatch can be thicker than the pipe)
    top = max(c['iso'] for c in cand)
    best = max((c for c in cand if c['iso'] >= 0.25 * top), key=lambda c: c['hi'])   # widest class that is clearly pipe
    maxw = best['hi']
    thr = best['lo'] - 1e-6
    heavy_len = sum(seg_len(a, b) for (w, a, b, _) in raw if thr <= w <= maxw + 1e-6)
    sec_lo = 0.45 * maxw
    sec_len = sum(seg_len(a, b) for (w, a, b, _) in raw if sec_lo <= w < thr)
    heavy_by_width.branch_ratio = sec_len / max(heavy_len, 1.0)      # thinner pipe lines = branches
    heavy_by_width.secondary = [(a, b) for (w, a, b, _) in raw if sec_lo <= w < thr]
    return [(a, b) for (w, a, b, _) in raw if thr <= w <= maxw + 1e-6]



def _fit_mask(mask, sc):
    """Fit straight isometric legs to a thick-line mask and chain them into one path.
    Returns (segments in pixels, True if any leg is slanted)."""
    import numpy as np
    ys, xs = np.nonzero(mask)
    P = np.stack([xs, ys], 1).astype(float)
    legs = []
    for a in (30, 90, 150):
        ar = math.radians(a)
        u = np.array([math.cos(ar), -math.sin(ar)])
        nv = np.array([math.sin(ar), math.cos(ar)])
        q, sp = P @ nv, P @ u
        bins = np.floor(q / 2).astype(int)
        cnt = np.bincount(bins - bins.min())
        hot = np.nonzero(cnt >= 25 * sc)[0]
        if len(hot) == 0:
            continue
        for grp in np.split(hot, np.nonzero(np.diff(hot) > 3)[0] + 1):
            lo, hi = (grp[0] + bins.min()) * 2 - 3, (grp[-1] + bins.min()) * 2 + 5
            m = (q >= lo) & (q <= hi)
            if m.sum() < 25 * sc:
                continue
            legs.append({'a': a, 'u': u, 'n': nv, 'q': float(np.mean(q[m])),
                         's0': float(sp[m].min()), 's1': float(sp[m].max())})
    legs.sort(key=lambda l: (l['a'], l['q'], l['s0']))
    merged = []
    for l in legs:
        if merged and merged[-1]['a'] == l['a'] and abs(merged[-1]['q'] - l['q']) < 4 * sc and l['s0'] - merged[-1]['s1'] < 40 * sc:
            merged[-1]['s1'] = max(merged[-1]['s1'], l['s1'])
        else:
            merged.append(dict(l))
    legs = sorted([l for l in merged if l['s1'] - l['s0'] >= 40 * sc], key=lambda l: -(l['s1'] - l['s0']))[:12]
    if len(legs) < 1:
        raise ConvertError('Could not fit any straight pipe legs.')

    def corner(i, j):
        A = np.array([legs[i]['n'], legs[j]['n']])
        if abs(np.linalg.det(A)) < 1e-6:
            return None
        X = np.linalg.solve(A, np.array([legs[i]['q'], legs[j]['q']]))
        tol = 30 * sc       # a corner must lie at an END of both legs (crossings in the middle are not corners)
        for idx in (i, j):
            sx = float(X @ legs[idx]['u'])
            if min(abs(sx - legs[idx]['s0']), abs(sx - legs[idx]['s1'])) > tol:
                return None
        return X
    nl = len(legs)
    adj = {i: {} for i in range(nl)}
    for i in range(nl):
        for j in range(i + 1, nl):
            X = corner(i, j)
            if X is not None:
                adj[i][j] = adj[j][i] = X
    length = [l['s1'] - l['s0'] for l in legs]
    best = (-1, None)

    def dfs(path, total):
        nonlocal best
        if total > best[0]:
            best = (total, list(path))
        for nx in adj[path[-1]]:
            if nx not in path:
                path.append(nx)
                dfs(path, total + length[nx])
                path.pop()
    for i in range(nl):
        dfs([i], length[i])
    order = best[1]
    slanted = any(legs[i]['a'] in (30, 150) for i in order)
    pts = [adj[order[k]][order[k + 1]] for k in range(len(order) - 1)]

    def free_end(idx, near):
        l = legs[idx]
        e0 = l['u'] * l['s0'] + l['n'] * l['q']
        e1 = l['u'] * l['s1'] + l['n'] * l['q']
        if near is None:
            return e0, e1
        return (e1 if np.linalg.norm(e0 - near) < np.linalg.norm(e1 - near) else e0)
    if len(order) == 1:
        e0, e1 = free_end(order[0], None)
        path = [e0, e1]
    else:
        start = free_end(order[0], pts[0])
        end = free_end(order[-1], pts[-1])
        path = [start] + pts + [end]
    segs = [((float(path[k][0]) / sc, float(path[k][1]) / sc), (float(path[k + 1][0]) / sc, float(path[k + 1][1]) / sc))
            for k in range(len(path) - 1)]
    return segs, slanted


def _raster_attempt(page, sc):
    """Draw the page, remove everything thin, and look at the thick components that remain.
    The pipe is the component that can be fitted with isometric legs including a slanted one
    (this skips thick sheet borders and title block lines)."""
    import numpy as np
    try:
        import cv2
    except ImportError:
        raise ConvertError('opencv is missing.  Run:  pip install opencv-python')
    pix = page.get_pixmap(dpi=72 * sc, alpha=False)
    rgb = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    ink = (gray < 140).astype(np.uint8)
    for k in (11, 9, 7, 5, 3):
        er = cv2.erode(ink, np.ones((k, k), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(er, connectivity=8)
        comps = sorted([(math.hypot(st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]), i) for i in range(1, n)],
                       reverse=True)
        for diag, i in comps[:6]:
            if diag < 300 * sc:
                break
            try:
                segs, slanted = _fit_mask(lab == i, sc)
            except ConvertError:
                continue
            if slanted:
                return segs
    raise ConvertError('Could not find the pipe: it is not drawn thicker than the other lines.')


def heavy_by_raster(page):
    last = None
    for sc in (1, 2, 3):
        try:
            segs = _raster_attempt(page, sc)
            if len(segs) >= 1:
                return segs
        except ConvertError as e:
            last = e
    raise last or ConvertError('Could not find the pipe.')


def heavy_segments(page):
    """-> (segments, tolerance for joining their ends)"""
    try:
        return bridge_gaps(heavy_by_width(page)), 1.2
    except ConvertError as e:
        if 'similar' not in str(e) and 'No vector lines' not in str(e):
            raise
    return heavy_by_raster(page), 1.5


def bridge_gaps(segs, max_gap=40.0, tol=1.5):
    """A valve, flange or tee symbol interrupts the heavy line. Join pieces that lie on the same straight
    line when the gap between them is small."""
    segs = list(segs)
    out = list(segs)
    info = []
    for a, b in segs:
        L = math.dist(a, b)
        if L < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        info.append((a, b, ux, uy))
    # one candidate gap per ordered pair of collinear pieces
    for i, (a1, b1, ux1, uy1) in enumerate(info):
        for j, (a2, b2, ux2, uy2) in enumerate(info):
            if j <= i:
                continue
            if abs(ux1 * uy2 - uy1 * ux2) > 0.02:
                continue                                    # not parallel
            # perpendicular distance between the two lines
            if abs((a2[0] - a1[0]) * uy1 - (a2[1] - a1[1]) * ux1) > tol:
                continue
            best = None
            for p in (a1, b1):
                for q in (a2, b2):
                    d = math.dist(p, q)
                    if best is None or d < best[0]:
                        best = (d, p, q)
            d, p, q = best
            if 2.0 < d <= max_gap:
                # the gap must lie outside both pieces (not an overlap)
                mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                if seg_dist(mid, a1, b1)[0] > 1.0 and seg_dist(mid, a2, b2)[0] > 1.0:
                    out.append((p, q))
    return out


def build_path(segs, tol=1.2):
    pts = []

    def pid(p):
        for i, q in enumerate(pts):
            if abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol:
                return i
        pts.append(p)
        return len(pts) - 1

    edges = []
    for a, b in segs:
        i, j = pid(a), pid(b)
        if i != j:
            edges.append((i, j))
    adj = {}
    for i, j in edges:
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)
    # connected components, take the longest
    seen, comps = set(), []
    for s in adj:
        if s in seen:
            continue
        stack, comp = [s], []
        seen.add(s)
        while stack:
            n = stack.pop()
            comp.append(n)
            for m in adj[n]:
                if m not in seen:
                    seen.add(m)
                    stack.append(m)
        comps.append(comp)

    def clen(c):
        cs = set(c)
        return sum(math.dist(pts[i], pts[j]) for i, j in edges if i in cs)
    comp = max(comps, key=clen)
    # short free stubs at a tee symbol (where this line meets another line) are not part of this line
    build_path.stubs = {}
    for m_ in [n for n in comp if len(adj.get(n, ())) >= 3]:
        short = [n for n in adj[m_] if len(adj[n]) == 1 and math.dist(pts[n], pts[m_]) < STUB_MAX]
        if short and len(adj[m_]) - len(short) >= 1:
            for n in short:
                adj[m_].discard(n)
                adj[n].discard(m_)
                comp.remove(n)
                build_path.stubs.setdefault(m_, []).append(pts[n])
    if any(len(adj[n]) > 2 for n in comp):
        raise ConvertError('The pipe has a branch / tee. Phase 1 only handles a single run (no tees).')
    ends = [n for n in comp if len(adj[n]) == 1]
    if len(ends) != 2:
        raise ConvertError('The pipe line is closed or broken (found %d free ends).' % len(ends))
    order, prev, cur = [ends[0]], None, ends[0]
    while True:
        nxt = [m for m in adj[cur] if m != prev]
        if not nxt:
            break
        prev, cur = cur, nxt[0]
        order.append(cur)
    build_path.stubs = {pts[k]: v for k, v in build_path.stubs.items()}
    return [pts[i] for i in order]


# ---------------------------------------------------------------- branches (short stubs on the main run)
def _pt_seg(p, a, b):
    d, t = seg_dist(p, a, b)
    return d, t


def find_stubs(path, secondary, attach_tol=45.0, min_len=20.0):
    """Thinner pipe lines that start at the main run are stubs (branch outlets).
    -> (stubs, ignored).  stub = {'free': pt, 'attach': pt on the main run, 'phi': iso angle, 'leg_pos': (segment, t)}"""
    stubs, ignored = [], 0
    find_stubs.cont = 0
    for a, b in secondary:
        L = math.dist(a, b)
        if L < min_len:
            continue                                     # tiny connector pieces next to the symbols
        best = None
        for k in range(len(path) - 1):
            for end, other in ((a, b), (b, a)):
                d, t = _pt_seg(end, path[k], path[k + 1])
                if d <= attach_tol and (best is None or d < best[0]):
                    best = (d, k, t, end, other)
        if best is None:
            ignored += 1
            continue
        d, k, t, end, free = best
        pa, pb = path[k], path[k + 1]
        if ang_diff(vis_angle(pa, pb) % 180, vis_angle(end, free) % 180, 180) < 15:
            find_stubs.cont = getattr(find_stubs, 'cont', 0) + 1
            continue                                     # runs along the main pipe: a thinner continuation, not an outlet
        att = (pa[0] + t * (pb[0] - pa[0]), pa[1] + t * (pb[1] - pa[1]))
        phi = vis_angle(att, free)
        iso, dev = snap_iso(phi)
        stubs.append({'free': free, 'attach': att, 'phi': iso, 'dev': dev, 'seg': k, 't': t, 'len_page': L})
    return stubs, ignored



def vis_angle(a, b):
    return math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0])) % 360


def path_to_legs(path, warn):
    legs = []
    cur_start, cur_dir = path[0], vis_angle(path[0], path[1])
    last = path[1]
    for k in range(1, len(path) - 1):
        d = vis_angle(path[k], path[k + 1])
        if ang_diff(d, cur_dir) > 3:
            legs.append([cur_start, path[k], cur_dir])
            cur_start, cur_dir = path[k], d
    legs.append([cur_start, path[-1], cur_dir])
    out = []
    for a, b, phi in legs:
        phi = vis_angle(a, b)
        iso, dev = snap_iso(phi)
        if dev > SLOPE_MIN_DEV:
            out.append({'a': a, 'b': b, 'phi': phi, 'len': math.dist(a, b), 'sloped': True})
        else:
            out.append({'a': a, 'b': b, 'phi': iso, 'len': math.dist(a, b)})
    return out


# --------------------------------------------------------------------------
# OCR (offline)
# --------------------------------------------------------------------------
def render_clip(page, fitz, rect, zoom):
    from PIL import Image
    pm = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=fitz.Rect(*rect), alpha=False)
    return Image.frombytes('RGB', (pm.width, pm.height), pm.samples)


def render(page, fitz, zoom):
    from PIL import Image
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)


def run_ocr(img, region, angles, zoom, log):
    """OCR the region of `img` (region in zoomed pixels) at several rotations.
    Returns detections with centre / baseline angle in PAGE (unzoomed, visual) coordinates."""
    import numpy as np
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        raise ConvertError('The OCR package is missing.  Run:  pip install rapidocr-onnxruntime')
    ocr = run_ocr.engine = getattr(run_ocr, 'engine', None) or RapidOCR()
    x0r, y0r, x1r, y1r = [int(v) for v in region]
    base = img.crop((x0r, y0r, x1r, y1r))
    W, H = base.size
    dets = []
    T, S = 1000, 800
    for th in angles:
        im = base.rotate(th, expand=True, fillcolor=(255, 255, 255)) if th else base
        W2, H2 = im.size
        log('  OCR pass at %+d deg (%dx%d px) ...' % (th, W2, H2))
        t = math.radians(th)
        for ty in range(0, H2, S):
            for tx in range(0, W2, S):
                tile = im.crop((tx, ty, min(tx + T, W2), min(ty + T, H2)))
                arr = np.array(tile)
                if (arr < 200).sum() < 200:
                    continue
                out, _ = ocr(arr)
                for box, txt, conf in (out or []):
                    pts = [(tx + p[0], ty + p[1]) for p in box]
                    cx = sum(p[0] for p in pts) / 4
                    cy = sum(p[1] for p in pts) / 4
                    e1 = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
                    e2 = (pts[3][0] - pts[0][0], pts[3][1] - pts[0][1])
                    e = e1 if math.hypot(*e1) >= math.hypot(*e2) else e2
                    aspect = max(math.hypot(*e1), math.hypot(*e2)) / max(1.0, min(math.hypot(*e1), math.hypot(*e2)))
                    phi_rot = math.degrees(math.atan2(-e[1], e[0]))
                    phi = (phi_rot - th) % 180
                    dx, dy = cx - W2 / 2.0, cy - H2 / 2.0
                    ox = dx * math.cos(t) - dy * math.sin(t) + W / 2.0 + x0r
                    oy = dx * math.sin(t) + dy * math.cos(t) + H / 2.0 + y0r
                    dets.append({'text': txt.strip(), 'conf': float(conf), 'x': ox / zoom, 'y': oy / zoom,
                                 'ang': phi, 'aspect': aspect, 'rot': th,
                                 'h': min(math.hypot(*e1), math.hypot(*e2)) / zoom,
                                 'w': max(math.hypot(*e1), math.hypot(*e2)) / zoom})
    return dets


def cluster_numbers(dets, tol=32.0):
    nums = [d for d in dets if re.fullmatch(r'[1-9]\d{1,5}', d['text']) and d['conf'] >= 0.5]
    clusters = []
    for d in sorted(nums, key=lambda d: -d['conf']):
        for c in clusters:
            if math.hypot(c['x'] - d['x'], c['y'] - d['y']) < tol:
                c['members'].append(d)
                break
        else:
            clusters.append({'x': d['x'], 'y': d['y'], 'members': [d]})
    out = []
    for c in clusters:
        votes = {}
        for m in c['members']:
            votes[m['text']] = votes.get(m['text'], 0) + m['conf']
        text = max(votes, key=votes.get)
        good = [m for m in c['members'] if m['text'] == text]
        best = max(good, key=lambda m: (min(ang_diff(m['ang'], a, 180) for a in (30, 150, 0, 90)) < 14, m['conf'] * m['aspect']))
        out.append({'value': int(text), 'x': best['x'], 'y': best['y'], 'ang': best['ang'],
                    'conf': sum(m['conf'] for m in good) / len(good), 'n': len(c['members']),
                    'w': best.get('w', 60), 'h': best.get('h', 25), 'rot': best.get('rot')})
    return out



def drop_note_fragments(clusters, rot0):
    """Remove numbers that are only pieces of horizontal notes (BEND RADIUS 457, E 1291145, line numbers ...).
    Dimension text always runs along an isometric axis, so a number lying inside a horizontal text line is not a dimension."""
    horiz = [d for d in rot0 if d['conf'] >= 0.5 and any(ch.isdigit() for ch in d['text'])
             and (d['ang'] < 12 or d['ang'] > 168)]
    keep = []
    for c in clusters:
        bad = False
        for d in horiz:
            if d['text'] == str(c['value']):
                continue
            if abs(c['y'] - d['y']) < max(d['h'], 20) and abs(c['x'] - d['x']) < d['w'] / 2.0 + 15:
                bad = True
                break
        if not bad:
            keep.append(c)
    return keep

# --------------------------------------------------------------------------
# reading the text notes
# --------------------------------------------------------------------------
LINE_RE = re.compile(r'\d+(?:-\d/\d)?\s*"?\s*-\s*[A-Z]{1,4}\s*-\s*\d{2,6}\s*-\s*[A-Z0-9]{2,8}(?:\s*-\s*[A-Z0-9]{1,4})?')


def read_line_number(page, ocr_lines):
    txt = page.get_text('text')
    cands = [m.group(0).replace(' ', '') for m in LINE_RE.finditer(txt)]
    if not cands:
        cands = [m.group(0).replace(' ', '') for d in ocr_lines for m in LINE_RE.finditer(d['text'])]
    if not cands:
        return None
    return max(set(cands), key=cands.count)


def read_notes(lines):
    """Find E / S|N / EL groups (CONT'D FROM / CONT'D ON notes) in horizontal OCR lines.
    Values are returned in mm.  A value that ends with M, or has decimals, is in metres."""
    es, ss, els = [], [], []

    def mm(num, unit):
        v = float(num)
        return v * 1000.0 if (unit == 'M' or '.' in num) else v
    for d in lines:
        t = d['text'].upper().replace(' ', '')
        m = re.fullmatch(r'E[:=]?(\d{4,8}(?:\.\d+)?)(M?)', t)
        if m and ('.' in m.group(1) or len(m.group(1)) >= 5):
            es.append((mm(m.group(1), m.group(2)), d))
        # the letter S / N can be read wrongly when a leader arrow touches it -> '?' (decided below)
        m = re.fullmatch(r'([SN]|[^A-Z0-9.])?[:=]?(\d{4,8}(?:\.\d+)?)(M?)', t)
        if m and ('.' in m.group(2) or len(m.group(2)) >= 5):
            ss.append((m.group(1) if m.group(1) in ('S', 'N') else '?', mm(m.group(2), m.group(3)), d))
        m = re.fullmatch(r'(?:EL[:=.]*|(?=\+\d{5}))([+\-]?\d+(?:\.\d+)?)(M?)[\-\u2013\u2014_.~]*', t)
        if m:
            els.append((mm(m.group(1), m.group(2)), d))
    groups, used = [], set()
    for ev, ed in es:
        s_all = [x for x in ss if x[2] is not ed and abs(x[1] - ev) > 0.5]
        s_below = [x for x in s_all if 0 < x[2]['y'] - ed['y'] < 40 and abs(x[2]['x'] - ed['x']) < 80]
        s_ = min(s_below or s_all, key=lambda x: math.hypot(x[2]['x'] - ed['x'], x[2]['y'] - ed['y']), default=None)
        # the notes read E, S, EL from top to bottom: take the S just below E and the EL just below that S
        e_below = [x for x in els if s_ and 0 < x[1]['y'] - s_[2]['y'] < 40 and abs(x[1]['x'] - s_[2]['x']) < 100]
        e_ = min(e_below or els, key=lambda x: math.hypot(x[1]['x'] - ed['x'], x[1]['y'] - ed['y']), default=None)
        if s_ and e_ and math.hypot(s_[2]['x'] - ed['x'], s_[2]['y'] - ed['y']) < 150:
            groups.append({'E': ev, 'S_letter': s_[0], 'S': s_[1], 'EL': e_[0], 'x': ed['x'], 'y': ed['y']})
            used.add(id(e_[1]))
    uniq = []
    for g in groups:                       # the same note is seen in several OCR passes
        if not any(abs(g['x'] - u['x']) < 30 and abs(g['y'] - u['y']) < 30 and g['E'] == u['E'] and g['S'] == u['S']
                   and g['EL'] == u['EL'] for u in uniq):
            uniq.append(g)
    groups = uniq
    known = [g['S_letter'] for g in groups if g['S_letter'] in ('S', 'N')]
    for g in groups:
        if g['S_letter'] == '?':
            g['S_letter'] = max(set(known), key=known.count) if known else 'S'
    el_only = [{'EL': v, 'x': d['x'], 'y': d['y']} for v, d in els if id(d) not in used]
    return groups, el_only


def reread(page, fitz, rect, log=None):
    """Read a small part of the sheet again at 4x zoom (clearer digits for the coordinate notes)."""
    from PIL import Image
    pix = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=rect, alpha=False)
    img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    dets = run_ocr(img, (0, 0, pix.width, pix.height), [0], 4.0, lambda m: None)
    for d in dets:
        d['x'] += rect.x0
        d['y'] += rect.y0
    return dets


def _num_tokens(dets, y0, y1):
    """OCR words that look like 8440.433M or +132.489M, top to bottom, without duplicates."""
    toks = []
    for d in sorted(dets, key=lambda d: (d['y'], -d['conf'])):
        t = d['text'].replace(' ', '').upper()
        if d['conf'] >= 0.8 and y0 <= d['y'] <= y1 and re.fullmatch(r'[+\-]?\d{1,8}\.\d{2,3}M?', t):
            if not any(abs(o['y'] - d['y']) < 10 and o['t'] == t for o in toks):
                toks.append({'t': t, 'y': d['y'], 'x': d['x']})
    return toks


def _val_mm(t):
    return float(t.rstrip('M')) * 1000.0


def refine_notes(page, fitz, groups, el_only, warn):
    """Read each coordinate note again at 4x zoom and take the numbers from there (clearer digits)."""
    for g in groups:
        rect = fitz.Rect(g['x'] - 260, g['y'] - 70, g['x'] + 330, g['y'] + 120)
        dets = reread(page, fitz, rect)
        toks = _num_tokens(dets, g['y'] - 14, g['y'] + 95)
        if len(toks) < 3:
            continue
        e_t, s_t, el_t = toks[0], toks[1], toks[2]
        letter = g['S_letter']
        for d in dets:
            if d['text'].strip().upper() in ('N', 'S') and abs(d['y'] - s_t['y']) < 12 and d['x'] < s_t['x']:
                letter = d['text'].strip().upper()
        new = {'E': _val_mm(e_t['t']), 'S': _val_mm(s_t['t']), 'EL': _val_mm(el_t['t']), 'S_letter': letter}
        if any(abs(new[k] - g[k]) > 0.5 for k in ('E', 'S', 'EL')):
            warn('A coordinate note was read differently at higher zoom; using the clearer reading '
                 '(E %.0f / %s %.0f / EL %.0f).' % (new['E'], letter, new['S'], new['EL']))
        g.update(new)
    for e in el_only:
        rect = fitz.Rect(e['x'] - 140, e['y'] - 45, e['x'] + 260, e['y'] + 45)
        toks = _num_tokens(reread(page, fitz, rect), e['y'] - 14, e['y'] + 14)
        if toks:
            e['EL'] = _val_mm(toks[0]['t'])


def read_bend_radius(lines):
    vals = []
    for d in lines:
        m = re.search(r'BEND\s*RADIUS\s*(\d{2,4})', d['text'].upper())
        if m:
            vals.append(int(m.group(1)))
    return max(set(vals), key=vals.count) if vals else None


def _norm_text(t):
    return re.sub(r'(\d)\.\s+(\d)', r'\1.\2', t.upper())


def read_schedule(lines):
    pat = r'SCH\.?[,\s.]*([0-9O]{1,3}S?|STD|XXS|XS)\b'
    for d in lines:
        m = re.search(r'PIPE[^A-Z0-9]*' + pat, d['text'].upper())
        if m:
            return m.group(1).replace('O', '0')
    for d in lines:
        m = re.search(pat, d['text'].upper())
        if m:
            return m.group(1).replace('O', '0')
    for d in lines:                      # e.g. "..., 28 INCH, STD"
        m = re.search(r'INCH\W*(STD|XXS|XS)\b', d['text'].upper())
        if m:
            return m.group(1)
    return None


def parse_nd(t):
    """'1"' -> 1, '1 1/2"' -> 1.5, '3/4"' -> 0.75"""
    t = t.replace('\u201d', '"').replace('\u2033', '"').strip()
    m = re.fullmatch(r'(\d+)\s+(\d)\s*/\s*(\d)\s*"?', t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / float(m.group(3))
    m = re.fullmatch(r'(\d)\s*/\s*(\d)\s*"?', t)
    if m:
        return int(m.group(1)) / float(m.group(2))
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*"', t)
    if m:
        return float(m.group(1))
    return None


def bom_pipes(dets):
    """Bill of materials rows 'PIPE, SCH, 10S ...' with their size column -> {nps: schedule}"""
    out = {}
    nds = [(d, parse_nd(d['text'])) for d in dets]
    nds = [(d, v) for d, v in nds if v]
    for d in dets:
        m = re.search(r'PIPE[^A-Z0-9]*SCH\.?[,\s.]*([0-9O]{1,3}S?|STD|XXS|XS)\b', d['text'].upper())
        if not m:
            continue
        near = [(abs(n['y'] - d['y'] - 10), v) for n, v in nds if -10 <= n['y'] - d['y'] <= 40 and n['x'] > d['x'] + 100]
        if near:
            out.setdefault(min(near)[1], m.group(1).replace('O', '0'))
    return out


def read_nps_bom(lines):
    for d in lines:
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:INCH|")', _norm_text(d['text']))
        if m and 0.5 <= float(m.group(1)) <= 60:
            v = float(m.group(1))
            return int(v) if v == int(v) else v
    return None


def read_bend_factor(lines):
    """Elbow radius in pipe diameters from the bill of materials, e.g. '1.5D'."""
    for d in lines:
        t = _norm_text(d['text'])
        if 'ELBOW' in t or 'ELL' in t:
            if re.search(r'\bSR\b|SHORT\s*RADIUS|SHORT\s*RAD', t):
                return 1.0
            if re.search(r'\bLR\b|LONG\s*RADIUS|LONG\s*RAD', t):
                return 1.5
        if 'BW' in t or 'ELBOW' in t or 'INCH' in t:
            m = re.search(r'(?<![0-9.])(\d(?:\.\d)?)\s*D\b', t)
            if m and 1.0 <= float(m.group(1)) <= 5.0:
                return float(m.group(1))
    return None


def line_from_filename(path):
    name = os.path.splitext(os.path.basename(path))[0]
    name = re.sub(r'[-_ ]?model$', '', name, flags=re.I)
    return name if re.search(r'[A-Za-z]', name) and re.search(r'\d', name) and '-' in name else None


# --------------------------------------------------------------------------
# dimensions -> pieces of each leg
# --------------------------------------------------------------------------
def thin_leader_segments(page):
    """Slanted thin lines (not along an isometric axis, not horizontal/vertical): possible leader lines."""
    M = page.rotation_matrix
    out = []
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] == 'l':
                a, b = it[1] * M, it[2] * M
                L = math.hypot(b.x - a.x, b.y - a.y)
                if L < 40 or L > 700:
                    continue
                phi = vis_angle((a.x, a.y), (b.x, b.y)) % 180
                if min(ang_diff(phi, t, 180) for t in (0, 30, 90, 150)) < 4:
                    continue
                out.append(((a.x, a.y), (b.x, b.y), L))
    return out


def apply_leaders(clusters, segs):
    """A dimension number written horizontally and tied to a dimension line by a leader line:
    use the tip of the leader as the position of the dimension."""
    res = []
    for c in clusters:
        if ang_diff(c['ang'], 0, 180) >= 12:
            res.append(c)
            continue
        hw, hh = c.get('w', 60) / 2.0 + 16, c.get('h', 25) / 2.0 + 16
        best = None
        for a, b, L in segs:
            for p, q in ((a, b), (b, a)):
                if abs(p[0] - c['x']) <= hw and abs(p[1] - c['y']) <= hh and (best is None or L > best[0]):
                    best = (L, q)
        if best:
            c2 = dict(c)
            c2['x0'], c2['y0'] = c['x'], c['y']
            c2['x'], c2['y'] = best[1]
            c2['ang'] = None
            c2['leader'] = True
            res.append(c2)
    return res


def seg_dist(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2)) if L2 else 0
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy)), t


def assign_labels(legs, clusters, max_dist=450.0):
    for lg in legs:
        lg['labels'] = []
    for c in clusters:
        best, bd = None, 1e9
        for lg in legs:
            ok_angles = [lg['phi'] % 180]
            if lg['phi'] % 180 == 90:
                ok_angles = [90, 0]
            if c['ang'] is not None and not any(ang_diff(c['ang'], a, 180) < 12 for a in ok_angles):
                continue
            d, t = seg_dist((c['x'], c['y']), lg['a'], lg['b'])
            if d < bd:
                best, bd, bt = lg, d, t
        if best is not None and bd < max_dist:
            dx, dy = best['b'][0] - best['a'][0], best['b'][1] - best['a'][1]
            n = (-dy / best['len'], dx / best['len'])
            perp = (c['x'] - best['a'][0]) * n[0] + (c['y'] - best['a'][1]) * n[1]
            best['labels'].append({'value': c['value'], 't': bt, 'perp': perp, 'dist': bd, 'conf': c['conf']})


def split_leg(labels, tol=1.5):
    """-> (pieces, note).  pieces are lengths from the start corner to the end corner."""
    if not labels:
        return None, 'no dimension found'
    labels = sorted(labels, key=lambda l: l['t'])
    if len(labels) == 1:
        return [labels[0]['value']], 'single dimension'
    vals = [l['value'] for l in labels]
    vmax = max(vals)
    others = sum(vals) - vmax
    if vmax >= others - tol:
        # overall dimension present; if tied, take the label that sits furthest from the pipe
        top = [l for l in labels if l['value'] == vmax]
        overall = max(top, key=lambda l: abs(l['perp']))
        chain = [l for l in labels if l is not overall]
        total = vmax
    else:
        overall, chain, total = None, labels, sum(vals)
    csum = sum(l['value'] for l in chain)
    rem = total - csum
    if rem < -tol:
        return None, 'dimensions do not add up (%s)' % vals
    mean_t = sum(l['t'] for l in chain) / len(chain)
    chain_vals = [l['value'] for l in chain]
    if mean_t < 0.5:
        pieces = chain_vals + ([rem] if rem > tol else [])
        note = 'chain from start corner'
    else:
        pieces = ([rem] if rem > tol else []) + chain_vals
        note = 'chain from end corner'
    if overall is None:
        note += ', no overall dimension printed'
    else:
        note += ', overall %d' % total
    return pieces, note


# --------------------------------------------------------------------------
# build the model and write the .CII
# --------------------------------------------------------------------------
DIR_VEC = {'E': (1, 0, 0), 'W': (-1, 0, 0), 'N': (0, 0, 1), 'S': (0, 0, -1), 'U': (0, 1, 0), 'D': (0, -1, 0)}
# vectors are (East, Up, North)


def plan_dir_name(phi, north):
    nang = NORTH_OPTIONS[north]
    i = HORIZONTAL_CYCLE.index(nang)
    cyc = {HORIZONTAL_CYCLE[i % 4]: 'N', HORIZONTAL_CYCLE[(i + 1) % 4]: 'E',
           HORIZONTAL_CYCLE[(i + 2) % 4]: 'S', HORIZONTAL_CYCLE[(i + 3) % 4]: 'W'}
    if phi == 90:
        return 'U'
    if phi == 270:
        return 'D'
    return cyc[phi]



# ---------------------------------------------------------------- process data (temperature / pressure) from Excel
def _norm_key(t):
    t = str(t or '').upper()
    for ch in ('”', '“', '″', "''", '’', '‘'):
        t = t.replace(ch, '"')
    return re.sub(r'[\s"\'_\-./\\]+', '', t)


def _core_key(t):
    """line number without the size prefix:  6"-UP-33601-B52-NI -> UP33601B52NI"""
    t = str(t or '').upper()
    for ch in ('”', '“', '″', "''", '’', '‘'):
        t = t.replace(ch, '"')
    t = re.sub(r'^\s*\d+(?:[\s-]*\d+/\d+)?\s*(?:"|IN|INCH|NB|NPS)?\s*[-_ ]\s*', '', t)
    return re.sub(r'[\s"\'_\-./\\]+', '', t)


def _read_table(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.csv', '.txt'):
        import csv
        with open(path, newline='', encoding='utf-8-sig', errors='replace') as f:
            text = f.read()
        try:
            dia = csv.Sniffer().sniff(text[:4096], delimiters=',;\t')
        except Exception:
            dia = csv.excel
        return [[c for c in r] for r in csv.reader(text.splitlines(), dia)]
    try:
        import openpyxl
    except ImportError:
        raise ConvertError('Reading Excel needs openpyxl.  Run:  pip install openpyxl')
    if ext == '.xls':
        raise ConvertError('Old .xls files are not supported. Save the sheet as .xlsx or .csv.')
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    best = []
    for ws in wb.worksheets:
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        if len(rows) > len(best):
            best = rows
        if any(re.search(r'line', str(c or ''), re.I) for r in rows[:40] for c in r):
            return rows
    return best


def _unit_from_text(t, kind):
    t = (t or '').lower()
    if kind == 'T':
        if re.search(r'°\s*f|deg\s*f|\bf\b|fahrenheit', t):
            return 'F'
        if re.search(r'°\s*c|deg\s*c|\bc\b|celsius|\(c\)', t):
            return 'C'
        return None
    if re.search(r'kg\s*/?\s*cm|kgf', t):
        return 'kgcm2'
    if re.search(r'\bkpa\b', t):
        return 'kpa'
    if re.search(r'\bmpa\b', t):
        return 'mpa'
    if re.search(r'\bpsi', t):
        return 'psi'
    if re.search(r'\bbar', t):
        return 'bar'
    return None


P_TO_KPA = {'bar': 100.0, 'kgcm2': 98.0665, 'kpa': 1.0, 'mpa': 1000.0, 'psi': 6.89476}


def _workbook_unit_hint(path, kind):
    """Units are sometimes written on another sheet (e.g. 'Kg/Cm2 (g)', 'Deg.C'). Look there."""
    if os.path.splitext(path)[1].lower() not in ('.xlsx', '.xlsm'):
        return None, None
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        for ws in wb.worksheets:
            for k, r in enumerate(ws.iter_rows(values_only=True)):
                if k > 8:
                    break
                for c in r:
                    u = _unit_from_text(str(c or ''), kind)
                    if u:
                        return u, ws.title
    except Exception:
        pass
    return None, None


def load_process_db(path, temp_unit=None, press_unit=None, warn=print, log=print):
    rows = _read_table(path)
    hdr = None
    for i, r in enumerate(rows[:60]):
        cells = [str(c or '') for c in r]
        if any(re.search(r'line', c, re.I) for c in cells) and any(re.search(r'temp', c, re.I) for c in cells) \
                and any(re.search(r'press', c, re.I) for c in cells):
            hdr = i
            break
    if hdr is None:
        raise ConvertError('Could not find a header row with a "line number", a "temperature" and a "pressure" '
                           'column in %s.' % os.path.basename(path))
    heads = [str(c or '').strip() for c in rows[hdr]]
    # the unit may be on the next row, e.g. "(deg C)" or "kg/cm2(g)"
    nxt = [str(c or '').strip() for c in (rows[hdr + 1] if hdr + 1 < len(rows) else [])]
    nxt += [''] * (len(heads) - len(nxt))
    unit_row = any(_unit_from_text(c, 'T') or _unit_from_text(c, 'P') for c in nxt) and \
        not any(re.search(r'\d{3,}', c) for c in nxt)
    full = [(h + ' ' + (nxt[i] if unit_row else '')).strip() for i, h in enumerate(heads)]
    key_cols = [i for i, h in enumerate(heads) if re.search(r'line[\s_]*(no|number|num|#|tag|id)|^line$|^line[\s_]', h, re.I)]
    if not key_cols:
        key_cols = [i for i, h in enumerate(heads) if re.search(r'line|tag', h, re.I)]
    if not key_cols:
        raise ConvertError('No "line number" column found in the Excel header row.')
    kc = key_cols[0]

    def rank(h):
        h = h.lower()
        if re.search(r'design|max', h):
            return 0
        if re.search(r'oper|normal', h):
            return 1
        return 2
    skip = re.compile(r'hydro|test', re.I)
    tcand = [i for i, h in enumerate(heads) if re.search(r'temp', h, re.I) and i != kc]
    pcand = [i for i, h in enumerate(heads) if re.search(r'press', h, re.I) and i != kc and not skip.search(h)]
    if not tcand or not pcand:
        raise ConvertError('Temperature or pressure column not found in the Excel header row.')

    def explicit(cols, letter):
        """headers that carry the CAESAR II number themselves, e.g. 'OPERATING_TEMP T1', 'DESIGN_PRESSURE P2'"""
        out = {}
        for i in cols:
            m = re.search(r'(?<![A-Za-z])%s\s*([1-9])\s*$' % letter, heads[i], re.I)
            if m:
                out[int(m.group(1))] = i
        return out if len(out) == len(cols) else None
    te, pe = explicit(tcand, 'T'), explicit(pcand, 'P')
    if te:
        tmap = [(k, te[k]) for k in sorted(te)]
    else:
        tmap = [(k + 1, i) for k, i in enumerate(sorted(tcand, key=lambda i: (rank(heads[i]), i))[:3])]
    if pe:
        pmap = [(k, pe[k]) for k in sorted(pe)]
    else:
        pmap = [(k + 1, i) for k, i in enumerate(sorted(pcand, key=lambda i: (rank(heads[i]), i))[:3])]
    tu = temp_unit or _unit_from_text(' '.join(full[i] for _, i in tmap), 'T')
    pu = press_unit or _unit_from_text(' '.join(full[i] for _, i in pmap), 'P')
    src_t = src_p = 'the column header'
    if not tu:
        tu, sh = _workbook_unit_hint(path, 'T')
        src_t = 'sheet "%s"' % sh
    if not pu:
        pu, sh = _workbook_unit_hint(path, 'P')
        src_p = 'sheet "%s"' % sh
    if not tu:
        tu, src_t = 'C', 'assumed'
        warn('Temperature unit not found in the Excel file. Assuming deg C. Use --temp-unit C or F.')
    if not pu:
        raise ConvertError('Pressure unit not found in the Excel file. Run again with --press-unit '
                           'bar, kgcm2, kpa, mpa or psi.  (Pressure is written to CAESAR II in kPa gauge.)')
    if re.search(r'abs|bara', ' '.join(full[i] for _, i in pmap), re.I):
        warn('The pressure looks like ABSOLUTE pressure. CAESAR II needs gauge pressure. Check the values.')
    log('Excel data: %s' % os.path.basename(path))
    log('  line column     : "%s"' % heads[kc])
    for k, i in tmap:
        log('  T%d <- "%s"  (%s, unit from %s)' % (k, full[i], tu, src_t))
    for k, i in pmap:
        log('  P%d <- "%s"  (%s, converted to kPa, unit from %s)' % (k, full[i], pu, src_p))

    def num(v):
        """-> (value or None, is_full_vacuum)"""
        if v is None or v == '':
            return None, False
        if isinstance(v, (int, float)):
            return float(v), False
        if re.fullmatch(r'\s*(FV|F\.V\.?|FULL\s*VAC\w*)\s*', str(v), re.I):
            return None, True
        m = re.search(r'-?\d+(?:[.,]\d+)?', str(v))
        return (float(m.group(0).replace(',', '.')), False) if m else (None, False)

    recs = []
    fv_seen = []
    for r in rows[hdr + 1 + (1 if unit_row else 0):]:
        if kc >= len(r) or r[kc] in (None, ''):
            continue
        ts, ps = {}, {}
        fv = False
        for k, i in tmap:
            v, _ = num(r[i]) if i < len(r) else (None, False)
            if v is not None:
                ts[k] = (v - 32.0) / 1.8 if tu == 'F' else v
        for k, i in pmap:
            v, isfv = num(r[i]) if i < len(r) else (None, False)
            if isfv:
                ps[k] = -101.325          # full vacuum = -1 atm gauge, in kPa
                fv = True
            elif v is not None:
                ps[k] = v * P_TO_KPA[pu]
        if not ts and not ps:
            continue
        T = [ts.get(k, 0.0) for k in range(1, 10)]
        P = [ps.get(k, 0.0) for k in range(1, 10)]
        recs.append({'raw': str(r[kc]).strip(), 'n': _norm_key(r[kc]), 'c': _core_key(r[kc]), 'T': T, 'P': P, 'fv': fv})
    if not recs:
        raise ConvertError('The Excel file has no data rows under the header.')
    log('  %d lines in the file' % len(recs))
    return recs


def lookup_process(recs, line_no, warn):
    """-> {'temps': [...], 'press': [...], 'excel_line': text} or None"""
    if not line_no:
        warn('No line number, so temperature and pressure could not be looked up.')
        return None
    n, c = _norm_key(line_no), _core_key(line_no)
    for how, hit in (('exact', [r for r in recs if r['n'] == n]),
                     ('without size', [r for r in recs if r['c'] and r['c'] == c]),
                     ('partial', [r for r in recs if c and len(c) >= 6 and (c in r['n'] or (len(r['c']) >= 6 and r['c'] in n))])):
        if not hit:
            continue
        vals = {(tuple(r['T']), tuple(r['P'])) for r in hit}
        if len(vals) > 1:
            warn('Line %s matches %d different rows in the Excel file (%s). Temperature and pressure NOT filled. '
                 'Fix the Excel or write them in the review file.' % (line_no, len(hit), ', '.join(r['raw'] for r in hit)))
            return None
        if how == 'partial':
            warn('Line %s matched the Excel row "%s" only partly. Check it.' % (line_no, hit[0]['raw']))
        r = hit[0]
        if r.get('fv'):
            warn('Line %s: the Excel says FV (full vacuum). Written as -101.325 kPa (gauge). Check this case.' % r['raw'])
        return {'temps': r['T'], 'press': r['P'], 'excel_line': r['raw']}
    warn('Line %s was not found in the Excel file. Temperature and pressure left at 0.' % line_no)
    return None



# ---------------------------------------------------------------- sloped (rolling) legs
def rev_leg(l):
    d = dict(l)
    d['a'], d['b'] = l['b'], l['a']
    d['phi'] = (l['phi'] + 180) % 360
    return d


def slope_axes(phi):
    """the two isometric axes (visual angles) that enclose a sloped leg of visual angle phi"""
    lo = int((phi - 30) // 60) * 60 + 30
    return lo % 360, (lo + 60) % 360


def _axis_vec(angle):
    return math.cos(math.radians(angle)), math.sin(math.radians(angle))


def resolve_sloped(g, clusters, north, tol=2.5, max_dist=520.0):
    """A leg that is not on an isometric axis (a 45 deg rolling offset) is written as two equal-ish
    components with the true length on the diagonal, e.g. 219 + 219 and 310.
    -> (comps [(dir, mm), (dir, mm)], hypot, used clusters, note) or None."""
    lo, hi = slope_axes(g['phi'])
    ulo, uhi = _axis_vec(lo), _axis_vec(hi)
    vx, vy = g['b'][0] - g['a'][0], -(g['b'][1] - g['a'][1])
    det = ulo[0] * uhi[1] - ulo[1] * uhi[0]
    s_lo = (vx * uhi[1] - vy * uhi[0]) / det
    s_hi = (ulo[0] * vy - ulo[1] * vx) / det
    if s_lo <= 0 or s_hi <= 0:
        return None
    ratio = s_hi / s_lo                         # drawn ratio hi/lo (a 45 deg offset is about 1)
    okang = [g['phi'] % 180, lo % 180, hi % 180]
    cand = []
    for c in clusters:
        d, _ = seg_dist((c['x'], c['y']), g['a'], g['b'])
        if d < max_dist and c['value'] > 0:
            pen = 0 if c['ang'] is None or any(ang_diff(c['ang'], a, 180) < 16 for a in okang) else 60
            cand.append((d + pen, c))
    best = None

    def consider(cost, ci, cj, ck, a, b):
        nonlocal best
        if best is None or cost < best[0]:
            best = (cost, ci, cj, ck, a, b)
    for i, (di, ci) in enumerate(cand):
        for j, (dj, cj) in enumerate(cand):
            if j <= i:
                continue
            a, b = ci['value'], cj['value']
            hyp = math.hypot(a, b)
            diag = [(dk, ck) for k, (dk, ck) in enumerate(cand)
                    if k not in (i, j) and abs(ck['value'] - hyp) <= max(tol, 0.004 * hyp)]
            equal = abs(a - b) <= tol
            if diag:
                consider(di + dj + diag[0][0] * 0.3 + (0 if equal else 20), ci, cj, diag[0][1], a, b)
            elif equal and 0.6 < ratio < 1.7:
                consider(di + dj + 400, ci, cj, None, a, b)      # clear equal pair on a 45 deg leg, no diagonal read
    # one component and the diagonal were read: the other component follows (equal on a 45 deg leg)
    for i, (di, ci) in enumerate(cand):
        for k, (dk, ck) in enumerate(cand):
            if i == k or ck['value'] <= ci['value'] * 1.05:
                continue
            a_, D = ci['value'], ck['value']
            other = math.sqrt(max(D * D - a_ * a_, 0.0))
            if other < 20:
                continue
            if abs(other - a_) <= max(tol, 0.01 * D):
                consider(di + dk * 0.3 + 150, ci, None, ck, a_, a_)
            elif ci['ang'] is not None:
                near_lo = ang_diff(ci['ang'], lo % 180, 180) < ang_diff(ci['ang'], hi % 180, 180)
                aa, bb = (a_, other) if near_lo else (other, a_)
                if (0.5 < (bb / aa) / ratio < 2.0):
                    consider(di + dk * 0.3 + 250, ci, None, ck, aa, bb)
    if not best:
        return None
    _, ci, cj, ck, a, b = best
    if cj is not None and abs(a - b) > tol:       # unequal: give the bigger value to the axis that is drawn longer
        if (b / a > 1) != (ratio > 1):
            a, b = b, a
    elif abs(a - b) <= tol:
        a = b = (a + b) / 2.0
    axes = [lo, hi]
    vals = [float(a), float(b)]
    alt_axes = None
    vi = [k for k, ax in enumerate(axes) if ax in (90, 270)]
    if len(vi) == 1:
        hk = 1 - vi[0]
        h = axes[hk]
        alt_h = (360 - h) % 360              # the other horizontal axis on the same side of the sheet (E <-> S, N <-> W)
        hz = None
        if cj is not None:
            hz = max((ci, cj), key=lambda c: ang_diff(c['ang'], 90, 180) if c['ang'] is not None else -1)
        elif ci['ang'] is not None and ang_diff(ci['ang'], 90, 180) > 25:
            hz = ci
        if hz is not None and hz['ang'] is not None and ang_diff(hz['ang'], 90, 180) > 25 and \
                ang_diff(hz['ang'], alt_h % 180, 180) < ang_diff(hz['ang'], h % 180, 180) - 10:
            h, alt_h = alt_h, h                # the text angle says the other horizontal axis
        axes[hk] = h
        alt_axes = list(axes)
        alt_axes[hk] = alt_h
    comps = [(plan_dir_name(axes[0], north), vals[0]), (plan_dir_name(axes[1], north), vals[1])]
    alt = None
    if alt_axes:
        alt = [(plan_dir_name(alt_axes[0], north), vals[0]), (plan_dir_name(alt_axes[1], north), vals[1])]
    hyp = math.hypot(a, b) if ck is None else ck['value'] if abs(ck['value'] - math.hypot(a, b)) <= 2.5 else math.hypot(a, b)
    used = [c for c in (ci, cj, ck) if c is not None]
    note = 'sloped leg: %s %g + %s %g%s' % (comps[0][0], vals[0], comps[1][0], vals[1],
                                           ', diagonal %g read' % ck['value'] if ck else ', diagonal NOT read')
    if cj is None:
        note += ', second component calculated from the diagonal'
    return comps, hyp, used, note, alt


def _vert_mm(leg):
    """signed vertical length of a leg that goes up or down (straight, or the vertical part of a sloped leg)"""
    if leg.get('comp'):
        return sum((1 if d == 'U' else -1) * float(v) for d, v in leg['comp'] if d in ('U', 'D'))
    if leg['dir'] in ('U', 'D'):
        return (1 if leg['dir'] == 'U' else -1) * float(sum(leg['parts']))
    return 0.0


def rescue_leg(page, fitz, g, nps, line_no='', log=lambda *a: None, pad=130.0, zoom=4.0):
    """Targeted second look at one leg whose dimension was not read: a tight crop at high zoom,
    read at the rotations a dimension text can have."""
    W, H = page.rect.width, page.rect.height
    x0, x1 = min(g['a'][0], g['b'][0]) - pad, max(g['a'][0], g['b'][0]) + pad
    y0, y1 = min(g['a'][1], g['b'][1]) - pad, max(g['a'][1], g['b'][1]) + pad
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W * 0.69, x1), min(H, y1)
    if x1 - x0 < 20 or y1 - y0 < 20:
        return []
    img = render_clip(page, fitz, (x0, y0, x1, y1), zoom)
    dets = run_ocr(img, (0, 0, img.size[0], img.size[1]), [0, 90, -90, 30, -30, 60, -60], zoom, log)
    for d in dets:
        d['x'] += x0
        d['y'] += y0
    cl = cluster_numbers(dets)
    if nps:
        cl = [c for c in cl if c['value'] != nps]
    ln_tokens = {int(t) for t in re.findall(r'\d{4,}', line_no or '')}
    cl = [c for c in cl if int(c['value']) not in ln_tokens]
    tmp = [dict(g, labels=[])]
    assign_labels(tmp, cl, max_dist=110.0)
    return tmp[0]['labels']


def refine_clusters(page, fitz, clusters, log=lambda *a: None):
    """Read every dimension number again on a small, sharp crop (3x and 5x) and let the reads vote.
    Fixes digit errors such as 718 read as 118."""
    from PIL import Image
    import numpy as np
    changed = 0
    for c in clusters:
        r = fitz.Rect(c['x'] - 38, c['y'] - 38, c['x'] + 38, c['y'] + 38) & page.rect
        if r.is_empty:
            continue
        votes = {c['value']: c['conf'] * max(1, c.get('n', 1))}
        base = c.get('rot')
        angles = [base + j for j in (-10, -5, 0, 5, 10)] if base is not None else [0, 90, -90, 30, -30]
        for z in (3.0, 4.0):
            img = render_clip(page, fitz, (r.x0, r.y0, r.x1, r.y1), z)
            dets = run_ocr(img, (0, 0, img.size[0], img.size[1]), angles, z, lambda m: None)
            for d in dets:
                d['x'] += r.x0
                d['y'] += r.y0
            for d in dets:                      # every read is one vote
                if re.fullmatch(r'[1-9]\d{1,5}', d['text']) and math.hypot(d['x'] - c['x'], d['y'] - c['y']) < 16:
                    votes[int(d['text'])] = votes.get(int(d['text']), 0) + d['conf']
        ctext = str(c['value'])
        votes = {v: w for v, w in votes.items()          # a re-read may only fix a digit or two, never swap the number
                 if v == c['value'] or (len(str(v)) == len(ctext) and sum(p != q for p, q in zip(str(v), ctext)) <= 2)}
        best = max(votes, key=votes.get)
        if best != c['value'] and votes[best] > votes.get(c['value'], 0) * 1.25:
            log('  re-read %d as %d' % (c['value'], best))
            c['value'] = best
            changed += 1
    return changed


def get_pipe_data(model, warn):
    nps = model.get('nps') or parse_nps(model.get('line_number'))
    od = model.get('od_mm')
    wall = model.get('wall_mm')
    if od is None:
        if nps not in OD_IN:
            raise ConvertError('Pipe size %r not in the table. Give --od and --wall.' % (nps,))
        od = OD_IN[nps] * 25.4
    if wall is None:
        sch = norm_sch(model.get('schedule') or 'STD')
        if nps in WALL_MM and sch not in WALL_MM[nps] and sch.endswith('S') and sch[:-1] in WALL_MM[nps]:
            sch = sch[:-1]
        if nps not in WALL_MM or sch not in WALL_MM[nps]:
            raise ConvertError('No wall thickness for NPS %s schedule %s. Give --wall.' % (nps, sch))
        wall = WALL_MM[nps][sch]
    return od, wall


def _leg_extra(lg, R, first=True):
    d = {'R': lg.get('R_mm') or R}
    if first and lg.get('line'):
        d['line'] = lg['line']
    if lg.get('od_mm'):
        d['od'], d['wall'] = lg['od_mm'], lg['wall_mm']
    if lg.get('process'):
        d['proc'] = lg['process']
    return d


def _turns(a, b):
    """True when leg b does not continue straight on from leg a (so there is a bend, not a plain join)"""
    if a.get('gap') or b.get('gap'):
        return False
    ua, ub = _leg_unit(a), _leg_unit(b)
    return sum(x * y for x, y in zip(ua, ub)) < 0.9999


def _leg_unit(lg):
    """direction of a leg as a unit vector (East, Up, North)"""
    if lg.get('comp'):
        v = [0.0, 0.0, 0.0]
        for d_, m_ in lg['comp']:
            for k in range(3):
                v[k] += DIR_VEC[d_][k] * float(m_)
    else:
        v = list(DIR_VEC[lg['dir']])
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / n for c in v]


def fit_bends(legs, R, warn):
    """CAESAR II puts the bend at the corner node and needs a straight pipe of at least the tangent length
    R * tan(angle / 2) on both sides. A node closer to the corner than that makes the bend overlap its
    neighbour and the model looks wrong. Such a node is dropped (its piece is joined to the next one)."""
    legs = [dict(l, parts=list(l.get('parts') or [])) for l in legs]
    for i in range(len(legs) - 1):
        if legs[i].get('gap') or legs[i + 1].get('gap'):
            continue
        a, b = _leg_unit(legs[i]), _leg_unit(legs[i + 1])
        cosd = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
        delta = math.acos(cosd)                       # change of direction at the corner
        R_i = float(legs[i].get('R_mm') or R)
        R_j = float(legs[i + 1].get('R_mm') or R)
        T = max(R_i, R_j) * math.tan(delta / 2.0) if delta < math.radians(179) else 0.0
        if T <= 1:
            continue
        for k, (lg, last) in enumerate(((legs[i], True), (legs[i + 1], False))):
            if lg.get('comp'):
                if float(sum(lg['parts'])) < T - 1:
                    warn('Leg %d is shorter than the bend tangent length (%.0f mm). Use a smaller bend radius.' % (i + 1 + k, T))
                continue
            p = lg['parts']
            while len(p) > 1 and (p[-1] if last else p[0]) < T - 1:
                small = p[-1] if last else p[0]
                if last:
                    p[-2] += p.pop()
                else:
                    first = p.pop(0)
                    p[0] += first
                warn('Leg %d: a node %.0f mm from the bend was dropped (a bend of radius %.0f mm needs %.0f mm of straight pipe on each side).'
                     % (i + 1 + k, small, R, T))
            if p and sum(p) < T - 1:
                warn('Leg %d (%.0f mm) is shorter than the bend tangent length (%.0f mm). The bend will not fit. '
                     'Check the bend radius.' % (i + 1 + k, sum(p), T))
    return legs


def build_cii(model, z_is_north=False, warn=print):
    od, wall = get_pipe_data(model, warn)
    R = model.get('bend_radius_mm')
    if R is None:
        R = 457.2
    inch = R / 25.4
    if abs(inch - round(inch)) < 0.03:
        R = round(inch) * 25.4          # 457 on the drawing means 18 in = 457.2 mm
    legs = fit_bends(model['legs'], R, warn)
    north = model.get('north', 'up-left')
    st = model.get('start') or {}
    E0, EL0 = float(st.get('E', 0)), float(st.get('EL', 0)) * float(model.get('el_scale', 1))
    if 'N' in st:
        Nn = float(st['N'])
    elif 'S' in st:
        Nn = -float(st['S'])
    else:
        Nn = 0.0
    Zs = Nn if z_is_north else -Nn

    elems = []
    node = 10
    outlets = model.get('outlets') or []
    zsg = 1 if z_is_north else -1
    host_node = {}
    for li, lg in enumerate(legs):
        if outlets and not lg.get('comp') and lg.get('parts'):
            px = E0 + sum(e['dx'] for e in elems)
            py = EL0 + sum(e['dy'] for e in elems)
            pz = Zs + sum(e['dz'] for e in elems)
            vec = DIR_VEC[lg['dir']]
            av = (vec[0], vec[1], vec[2] * zsg)
            parts = [float(p) for p in lg['parts']]
            bounds = [0.0]
            for p in parts:
                bounds.append(bounds[-1] + p)
            tot_leg = bounds[-1]
            todo = []
            for oi, o in enumerate(outlets):
                if o['leg'] != li:
                    continue
                nt = o['note']
                Nn_ = float(nt['S']) if nt['S_letter'] == 'N' else -float(nt['S'])
                pn = (float(nt['E']), float(nt['EL']) * float(model.get('el_scale', 1)), Nn_ if z_is_north else -Nn_)
                v = (pn[0] - px, pn[1] - py, pn[2] - pz)
                dv = DIR_VEC[o['dir']]
                dw = (dv[0], dv[1], dv[2] * zsg)
                sv = sum(v[i] * av[i] for i in range(3))
                Lv = sum(v[i] * dw[i] for i in range(3))
                if Lv < -20:       # the OPEN END note lies on the other side: the outlet points the other way
                    o['dir'] = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E', 'U': 'D', 'D': 'U'}[o['dir']]
                    dv = DIR_VEC[o['dir']]
                    dw = (dv[0], dv[1], dv[2] * zsg)
                    Lv = -Lv
                res = math.sqrt(max(0.0, sum(x * x for x in v) - sv * sv - Lv * Lv))
                if Lv < 20 or Lv > 3000 or sv < -15 or sv > tot_leg + 15 or res > 25:
                    warn('Outlet at leg %d: its OPEN END coordinates do not fit the drawing (along %.0f, length %.0f, '
                         'off by %.0f mm). Skipped.' % (li + 1, sv, Lv, res))
                    model['_skipped'] = model.get('_skipped', 0) + 1
                    continue
                sv = min(max(sv, 0.0), tot_leg)
                todo.append((sv, oi, Lv, res))
            for sv, oi, Lv, res in sorted(todo):
                j = min(range(len(bounds)), key=lambda k: abs(bounds[k] - sv))
                if abs(bounds[j] - sv) > 15:
                    bounds.append(sv)
                    bounds.sort()
                    j = bounds.index(sv)
                host_node[oi] = (li, bounds[j], Lv)
            parts = [round(bounds[k + 1] - bounds[k], 3) for k in range(len(bounds) - 1)]
            lg = dict(lg, parts=parts, _bounds=bounds)
            legs[li] = lg
        if lg.get('comp'):
            vx = vy = vz = 0.0
            for d_, v_ in lg['comp']:
                vx += DIR_VEC[d_][0] * float(v_)
                vy += DIR_VEC[d_][1] * float(v_)
                vz += DIR_VEC[d_][2] * float(v_)
            vy += float(lg.get('dy_mm', 0))
            elems.append(dict({'f': node, 't': node + NODE_STEP, 'dx': vx, 'dy': vy,
                               'dz': vz * (1 if z_is_north else -1),
                               'bend': li < len(legs) - 1 and _turns(lg, legs[li + 1])},
                              **_leg_extra(lg, R, True)))
            node += NODE_STEP
            continue
        vec = DIR_VEC[lg['dir']]
        leg_first = node
        for pi, p in enumerate(lg['parts']):
            last = pi == len(lg['parts']) - 1
            dx = vec[0] * p
            tot_leg = float(sum(lg['parts']))
            dy = vec[1] * p + (float(lg.get('dy_mm', 0)) * p / tot_leg if tot_leg else 0.0)
            dz = vec[2] * p * (1 if z_is_north else -1)
            elems.append(dict({'f': node, 't': node + NODE_STEP, 'dx': dx, 'dy': dy, 'dz': dz,
                               'bend': last and li < len(legs) - 1 and _turns(lg, legs[li + 1])},
                              **_leg_extra(lg, R, pi == 0)))
            node += NODE_STEP
        if '_bounds' in lg:
            for oi, hv_ in list(host_node.items()):
                li_, bv, Lv = hv_[0], hv_[1], hv_[2]
                if len(hv_) == 3 and li_ == li:
                    k_ = min(range(len(lg['_bounds'])), key=lambda k: abs(lg['_bounds'][k] - bv))
                    host_node[oi] = (li_, int(leg_first + k_ * NODE_STEP), Lv, True)
    n_main = len(elems)
    out_el = []
    if outlets and host_node:
        nn_ = node + NODE_STEP
        for oi in sorted(host_node):
            hv = host_node[oi]
            if len(hv) < 4:
                continue
            dv = DIR_VEC[outlets[oi]['dir']]
            Lv = hv[2]
            od2, wall2 = get_pipe_data({'nps': outlets[oi].get('nps', model.get('outlet_nps')),
                                        'schedule': outlets[oi].get('sch', model.get('outlet_schedule'))}, warn)
            out_el.append({'f': hv[1], 't': nn_, 'dx': dv[0] * Lv, 'dy': dv[1] * Lv, 'dz': dv[2] * Lv * zsg,
                           'bend': False, 'od': od2, 'wall': wall2, 'R': R,
                           **({'proc': legs[hv[0]]['process']} if legs[hv[0]].get('process') else {})})
            nn_ += NODE_STEP
        if out_el:
            model['outlet_report'] = [(outlets[oi]['dir'], round(host_node[oi][2], 1), host_node[oi][1])
                                      for oi in sorted(host_node) if len(host_node[oi]) >= 4]
    n_found = model.get('outlets_found', len(outlets))
    if n_found and len(out_el) < n_found:
        warn('INCOMPLETE: only %d of %d outlets could be placed. The missing branch pipes are NOT in this file.'
             % (len(out_el), n_found))
    main_elems = elems
    elems = elems + out_el
    n = len(elems)
    nb = sum(e['bend'] for e in elems)
    R = model.get('bend_radius_mm')
    if R is None:
        R = 457.2
    inch = R / 25.4
    if abs(inch - round(inch)) < 0.03:
        R = round(inch) * 25.4          # 457 on the drawing means 18 in = 457.2 mm
    line_no = model.get('line_number') or ''

    out = list(T_VERSION)
    out += ['#$ CONTROL ', ctrl_row([n, 0, 0, 0, 0, 0]), ctrl_row([nb, 0, 0, 0, 0, 0]),
            ctrl_row([0, 0, 0, 1, 0, 0]), ctrl_row([0])]
    out += ['#$ ELEMENTS']
    bi = 0
    for k, e in enumerate(elems):
        b = list(T_ELEMENT)
        b[0] = row([fmt_num(e['f']), fmt_num(e['t']), fmt_num(e['dx']), fmt_num(e['dy']),
                    fmt_num(e['dz']), fmt_num(od)])
        b[0] = row([('%d.0' % e['f']), ('%d.0' % e['t']), fmt_num(e['dx']), fmt_num(e['dy']),
                    fmt_num(e['dz']), fmt_num(e.get('od', od))])
        pr = e.get('proc') or model.get('process') or {}
        tt = [fmt_num(v) if v else '0.000000' for v in (list(pr.get('temps') or []) + [0.0] * 9)[:9]]
        pp = [fmt_num(v) if v else '0.000000' for v in (list(pr.get('press') or []) + [0.0] * 9)[:9]]
        b[1] = row([fmt_num(e.get('wall', wall)), '0.000000', '0.000000'] + tt[:3])
        b[2] = row(tt[3:9])
        b[3] = row(pp[:6])
        b[4] = row(pp[6:9] + ['0.000000'] * 3)
        lt_ = e.get('line') or (line_no if k == 0 else '')
        if lt_:
            b[10] = str(len(lt_)).rjust(12) + ' ' + lt_
        if e['bend']:
            bi += 1
            b[12] = row([bi, 0, 0, 0, 0, 0])
        else:
            b[12] = row([0, 0, 0, 0, 0, 0])
        b[13] = row([0, 0, 0, 1 if k == 0 else 0, 0, 0])
        out += b
    out += ['#$ AUX_DATA', '#$ BEND    ']
    for e in elems:
        if e['bend']:
            nn = e['t']
            out.append(row([fmt_num(e.get('R', R)), '0.000000', '-2.0202', '%d.0' % (nn - 1), '0.000000', '%d.0' % (nn - 2)]))
            out.append(row(['0.000000', '0.000000', '0.000000', fmt_num(e.get('wall', wall)), '0.000000', '0.000000']))
            out.append(row(['0.000000', '0.000000']))
    out += ['#$ RIGID   ', '#$ EXPJT   ', '#$ RESTRANT', '#$ DISPLMNT', '#$ FORCMNT ', '#$ UNIFORM ',
            '#$ WIND    ', '#$ OFFSETS ']
    out += list(T_ALLOW)
    out += ['#$ SIF&TEES', '#$ REDUCERS', '#$ FLANGES ', '#$ EQUIPMNT', '#$ MISCEL_1']
    arr = ['106.000'] * n
    out += [row(arr[i:i + 6]) for i in range(0, n, 6)]          # one value per element, own lines
    out += [row(T_TAIL[i:i + 6]) for i in range(0, len(T_TAIL), 6)]   # tail starts on a NEW line
    out += list(T_UNITS)
    out += ['#$ COORDS  ', row([1]), '10'.rjust(13) + ''.join(('%.3f' % c).rjust(14) for c in (E0, EL0, Zs))]
    text = '\r\n'.join(out) + '\r\n'

    # coordinates of every node (for the report)
    x, y, z = E0, EL0, Zs
    table = [(10, x, y, z)]
    for e in main_elems:
        x += e['dx']; y += e['dy']; z += e['dz']
        table.append((e['t'], x, y, z))
    return text, elems, table, od, wall, R


# --------------------------------------------------------------------------
# debug picture
# --------------------------------------------------------------------------
def draw_check(png_path, page, fitz, legs_geo, model, elems):
    from PIL import ImageDraw
    zoom = 0.6
    img = render(page, fitz, zoom)
    d = ImageDraw.Draw(img)
    cols = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'teal']
    k = 0
    node = 10
    for li, (g, lg) in enumerate(zip(legs_geo, model['legs'])):
        a, b = g['a'], g['b']
        d.line([a[0] * zoom, a[1] * zoom, b[0] * zoom, b[1] * zoom], fill=cols[li % len(cols)], width=4)
        tot = float(sum(lg['parts']))
        if tot <= 0 or (lg.get('comp') and any(float(v) <= 0 for _, v in lg['comp'])):
            tot = 0
            d.line([a[0] * zoom, a[1] * zoom, b[0] * zoom, b[1] * zoom], fill='red', width=6)
            d.text(((a[0] + b[0]) / 2 * zoom, (a[1] + b[1]) / 2 * zoom), 'LEG NOT READ', fill='red')
            continue
        acc = 0.0
        d.text((a[0] * zoom, a[1] * zoom - 14), 'node %d' % node, fill='black')
        for p in lg['parts']:
            acc += p
            f = acc / tot
            px, py = (a[0] + f * (b[0] - a[0])) * zoom, (a[1] + f * (b[1] - a[1])) * zoom
            node += NODE_STEP
            d.ellipse([px - 5, py - 5, px + 5, py + 5], outline='black', fill='yellow')
            d.text((px + 6, py + 4), '%d' % node, fill='black')
        mx, my = (a[0] + b[0]) / 2 * zoom, (a[1] + b[1]) / 2 * zoom
        d.text((mx - 60, my + 24), '%s %s' % (lg['dir'], '+'.join(str(int(p)) if float(p).is_integer() else str(p) for p in lg['parts'])),
               fill=cols[li % len(cols)])
    for o in model.get('outlets') or []:
        d.line([o['attach'][0] * zoom, o['attach'][1] * zoom, o['free'][0] * zoom, o['free'][1] * zoom],
               fill='green', width=4)
        d.text((o['free'][0] * zoom + 4, o['free'][1] * zoom), 'outlet %s' % o['dir'], fill='green')
    img.save(png_path)


# --------------------------------------------------------------------------
# main pipeline
# --------------------------------------------------------------------------
def analyse_pdf(args, log, warn):
    fitz, doc, page = open_pdf(args.pdf, args.page)
    W, H = page.rect.width, page.rect.height
    log('Reading the pipe route from the drawing ...')
    n_vec = sum(len(d['items']) for d in page.get_drawings())
    if n_vec < 200:
        warn('This PDF has almost no vector lines (scanned or picture PDF). The result is NOT reliable. '
             'Check every number against the drawing, or use a vector PDF.')
    try:
        segs, jtol = heavy_segments(page)
        path = build_path(segs, jtol)
    except ConvertError as e:
        if 'not drawn thicker' not in str(e):
            raise
        raise ConvertError('No pipe drawing found on this page. If this is sheet 2 or later of a line, it is '
                           'probably only the bill of materials (continuation sheet). Convert the '
                           'drawing sheet of this line instead.')
    br = getattr(heavy_by_width, 'branch_ratio', 0.0)
    raw_outlets = []
    if br > 0.15:
        raw_outlets, n_ign = find_stubs(path, getattr(heavy_by_width, 'secondary', []))
        if not raw_outlets or n_ign > max(3, len(raw_outlets)):
            msg = ('This sheet has branch lines (thinner pipe lines next to the main pipe, about %d%% of the main '
                   'pipe length) that are not simple outlets from the main run. Phase 1 reads one run with '
                   'short outlets, so the result would be incomplete.' % round(br * 100))
            if not getattr(args, 'ignore_branches', False):
                raise ConvertError(msg + ' Use --ignore-branches to convert only the main run anyway.')
            warn(msg + ' Only the main run is converted.')
            raw_outlets = []
        else:
            log('  found %d outlets (thin branch pipes) on the main run' % len(raw_outlets))
            if find_stubs.cont:
                warn('A thinner pipe also continues along the main run (for example after a reducer). It is modelled '
                     'with the main pipe size. Check the end of the run and add the reducer in CAESAR II.')
    legs_geo = path_to_legs(path, warn)
    log('  found %d legs' % len(legs_geo))
    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    bw, bh = max(xs) - min(xs), max(ys) - min(ys)
    bw, bh = max(bw, 0.6 * bh), max(bh, 0.6 * bw)      # a single vertical or horizontal leg still needs room for its dimensions
    cxm, cym = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    xs, ys = [cxm - bw / 2, cxm + bw / 2], [cym - bh / 2, cym + bh / 2]
    zoom = args.zoom
    wx = max(0.45 * bw, 0.85 * bh) if raw_outlets else 0.45 * bw      # outlets have their notes far to the side
    x0 = max(0, min(xs) - wx)
    x1 = min(W * 0.69, max(xs) + wx)
    y0 = max(0, min(ys) - 0.40 * bh)
    y1 = min(H, max(ys) + 0.40 * bh)
    log('Rendering and reading the text with OCR (takes 1 to 3 minutes) ...')
    img = render(page, fitz, zoom)
    region = (x0 * zoom, y0 * zoom, x1 * zoom, y1 * zoom)
    angs = [0, 30, -30, 90, -90]
    for g in legs_geo:
        if g.get('sloped'):
            a = ((g['phi'] + 90) % 180) - 90               # text along a sloped leg runs in its direction
            if all(ang_diff(a, x, 180) > 12 for x in angs):
                angs.append(int(round(a)))
    dets = run_ocr(img, region, angs, zoom, log)
    bom_region = (W * 0.66 * zoom, 0, W * zoom, H * 0.30 * zoom)
    dets_bom = run_ocr(img, bom_region, [0], zoom, log)
    horiz = [d for d in dets if d['rot'] == 0] + dets_bom
    line_no = args.line or read_line_number(page, [])
    if not line_no:
        line_no = line_from_filename(args.pdf)
        if line_no:
            warn('Line number taken from the PDF file name: %s' % line_no)
    if not line_no:
        line_no = read_line_number(page, horiz)
    if not line_no:
        warn('Line number not found. The element will be written without a line number. Use --line.')
    notes, el_only = read_notes(horiz)
    refine_notes(page, fitz, notes, el_only, warn)
    if os.environ.get('ISO_DEBUG'):
        log('  notes: %r' % [(g['E'], g['S_letter'], g['S'], g['EL'], round(g['x']), round(g['y'])) for g in notes])
    open_dets = [d for d in horiz if 'OPEN' in d['text'].upper()]
    open_notes = [g for g in notes if any(abs(d['x'] - g['x']) < 90 and 0 < g['y'] - d['y'] < 45 for d in open_dets)]
    if open_notes and raw_outlets:
        notes = [g for g in notes if not any(g is o for o in open_notes)]
    nps_bom = read_nps_bom(dets_bom)
    nps = parse_nps(line_no) or nps_bom
    if parse_nps(line_no) and nps_bom and abs(parse_nps(line_no) - nps_bom) > 0.01:
        warn('Pipe size in the line number (%s) and in the bill of materials (%s) differ.' % (parse_nps(line_no), nps_bom))
    if not nps and not (args.od and args.wall):
        raise ConvertError('Pipe size not found. Use --sch/--line, or give --od and --wall.')
    bend_r = read_bend_radius(horiz)
    bend_r_note = bend_r
    if bend_r is None:
        fac = read_bend_factor(dets_bom)
        if fac is None:
            fac = 1.5
            warn('Bend radius not found. Using 1.5 x pipe diameter (long radius elbow).')
        bend_r = fac * (nps * 25.4 if nps else args.od)
    bp = bom_pipes(dets_bom)
    sch = args.sch or bp.get(nps) or read_schedule(dets_bom + horiz)
    if not sch:
        warn('Pipe schedule not found in the bill of materials. Using STD. Use --sch to set it.')
        sch = 'STD'

    # which end of the pipe is the start?  -> the one closest to the "CONT'D FROM" note
    start_pt, end_pt = legs_geo[0]['a'], legs_geo[-1]['b']
    start_note = end_note = None
    if args.start:
        start_note = {'E': args.start[0], 'S_letter': 'S', 'S': args.start[1], 'EL': args.start[2]}
    elif notes:
        stubs = getattr(build_path, 'stubs', {})

        def near(pt):
            st = next((v for k, v in stubs.items() if math.dist(k, pt) < 2.0), None)
            if st and len(st) >= 2:
                # a tee symbol: the line starts at its centre, between the notes at the two stub ends
                ns = []
                for q in st:
                    n_ = min(notes, key=lambda g: math.hypot(g['x'] - q[0], g['y'] - q[1]))
                    if n_ not in ns:
                        ns.append(n_)
                if len(ns) == 2 and ns[0]['S_letter'] == ns[1]['S_letter']:
                    return {'x': pt[0], 'y': pt[1], 'S_letter': ns[0]['S_letter'],
                            'E': (ns[0]['E'] + ns[1]['E']) / 2.0, 'S': (ns[0]['S'] + ns[1]['S']) / 2.0,
                            'EL': (ns[0]['EL'] + ns[1]['EL']) / 2.0}
            return min(notes, key=lambda g: math.hypot(g['x'] - pt[0], g['y'] - pt[1]))
        s_a, s_b = near(start_pt), near(end_pt)
        da = math.hypot(s_a['x'] - start_pt[0], s_a['y'] - start_pt[1])
        db = math.hypot(s_b['x'] - end_pt[0], s_b['y'] - end_pt[1])
        if len(notes) >= 2 and s_a is s_b:
            pass
        if len(notes) >= 2:
            # check whether the path should be reversed
            fwd = math.hypot(s_a['x'] - start_pt[0], s_a['y'] - start_pt[1]) + math.hypot(s_b['x'] - end_pt[0], s_b['y'] - end_pt[1])
            r_a, r_b = near(end_pt), near(start_pt)
            rev = math.hypot(r_a['x'] - end_pt[0], r_a['y'] - end_pt[1]) + math.hypot(r_b['x'] - start_pt[0], r_b['y'] - start_pt[1])
            if rev < fwd - 1:
                legs_geo = [rev_leg(l) for l in reversed(legs_geo)]
                start_pt, end_pt = legs_geo[0]['a'], legs_geo[-1]['b']
                s_a, s_b = near(start_pt), near(end_pt)
            start_note, end_note = s_a, s_b
        else:
            start_note = s_a
    else:
        warn('No "CONT\'D FROM" note with E / S / EL found. Start point set to 0,0,0. Use --start E S EL.')
    if args.reverse:
        legs_geo = [rev_leg(l) for l in reversed(legs_geo)]

    clusters = cluster_numbers(dets)
    clusters = drop_note_fragments(clusters, [d for d in dets if d['rot'] == 0])
    clusters = apply_leaders(clusters, thin_leader_segments(page))
    # a "BEND RADIUS 457" note also has a leader line, but it is not a dimension
    notes_rad = [d for d in dets if d['rot'] == 0 and re.search(r'RAD|BEND', d['text'].upper())]
    clusters = [c for c in clusters if not (c.get('leader') and (
        (bend_r_note and c['value'] == bend_r_note) or
        any(abs(c['y0'] - d['y']) < 30 and d['x'] - d['w'] / 2.0 - 20 <= c['x0'] <= d['x'] + d['w'] / 2.0 + 260 for d in notes_rad)))]
    if nps:      # the pipe size written on the pipe ("28" NS") is not a dimension
        clusters = [c for c in clusters if c['value'] != nps]
    # the line number is also written along the pipe: its digits (e.g. 33803) are not a dimension
    ln_tokens = {int(t) for t in re.findall(r'\d{4,}', line_no or '')}
    clusters = [c for c in clusters if int(c['value']) not in ln_tokens]
    log('Reading each dimension number once more at high zoom ...')
    refine_clusters(page, fitz, clusters, log)
    for g in legs_geo:
        g['labels'] = []
        if g.get('sloped'):
            r = resolve_sloped(g, clusters, args.north)
            g['slope'] = r
            if r:
                clusters = [c for c in clusters if not any(c is u for u in r[2])]
    assign_labels([g for g in legs_geo if not g.get('sloped')], clusters)

    legs, report, alts = [], [], {}
    for i, g in enumerate(legs_geo):
        if g.get('sloped'):
            r = g.get('slope')
            if r:
                comps, hyp, used, note, alt = r
                name = '%s+%s' % (comps[0][0], comps[1][0])
                legs.append({'dir': name, 'parts': [round(hyp, 1)], 'comp': [[d, v] for d, v in comps]})
                if alt:
                    alts[len(legs) - 1] = [{'dir': '%s+%s' % (alt[0][0], alt[1][0]), 'parts': [round(hyp, 1)],
                                            'comp': [[d, v] for d, v in alt]}]
                report.append((i + 1, name, [hyp], note, [c['value'] for c in used]))
                if 'NOT read' in note:
                    warn('Leg %d (%s): the diagonal dimension was not read, only the two equal components. '
                         'Check them in the drawing.' % (i + 1, name))
            else:
                name = 'sloped'
                warn('Leg %d is a sloped (rolling) leg and its dimensions could not be read. Fill in "comp" '
                     'in the review file, e.g. [["D", 125], ["S", 125]].' % (i + 1))
                lo, hi = slope_axes(g['phi'])
                legs.append({'dir': '%s+%s' % (plan_dir_name(lo, args.north), plan_dir_name(hi, args.north)),
                             'parts': [], 'comp': [[plan_dir_name(lo, args.north), 0], [plan_dir_name(hi, args.north), 0]]})
                report.append((i + 1, legs[-1]['dir'], [], 'NOT READ', []))
            continue
        pieces, note = split_leg(g['labels'])
        name = plan_dir_name(g['phi'], args.north)
        if pieces is None:
            log('  leg %d (%s): no dimension found, taking a closer look ...' % (i + 1, name))
            g['labels'] = rescue_leg(page, fitz, g, nps, line_no)
            pieces, note = split_leg(g['labels'])
            if pieces is not None:
                note += ' (found on a second, closer read)'
        if pieces is None:
            warn('Leg %d (%s): %s. Fill in its "parts" in the review file.' % (i + 1, name, note))
            pieces = []
        legs.append({'dir': name, 'parts': pieces})
        report.append((i + 1, name, pieces, note if pieces else 'NOT READ', [l['value'] for l in g['labels']]))
        labs = sorted(g['labels'], key=lambda l: l['t'])
        if pieces and len(labs) >= 2:
            add = [l['value'] for l in labs]
            vs = []
            if [round(p, 1) for p in add] != [round(p, 1) for p in pieces]:
                vs.append({'dir': name, 'parts': add})                  # all numbers are pieces of a chain, no overall
            big = max(labs, key=lambda l: l['value'])
            rest = [l['value'] for l in labs if l is not big]
            if rest and [round(p, 1) for p in rest] not in ([round(p, 1) for p in pieces], [round(p, 1) for p in add]):
                vs.append({'dir': name, 'parts': rest})                 # the largest number was not a dimension
            if vs:
                alts[len(legs) - 1] = vs
    model = {'line_number': line_no, 'nps': nps, 'schedule': sch, 'north': args.north,
             'bend_radius_mm': round(bend_r, 1), 'start': {}, 'legs': legs}
    if raw_outlets:
        outl = []
        ns_re = r'(\d+(?:\s*\d\s*/\s*\d)?|\d\s*/\s*\d)\s*["\u201d\u2033\']{1,2}\s*N[S5]\b'
        cands = []
        for d in horiz:
            m = re.search(ns_re, d['text'].upper())
            if m:
                v = parse_nd(m.group(1).replace(' / ', '/') + '"')
                if v and abs(v - (nps or 0)) > 0.01:
                    cands.append((d, v))
        mids = [((o['attach'][0] + o['free'][0]) / 2, (o['attach'][1] + o['free'][1]) / 2) for o in raw_outlets]
        onps = None
        if cands:
            onps = min(cands, key=lambda c: min(math.hypot(c[0]['x'] - m[0], c[0]['y'] - m[1]) for m in mids))[1]
        else:
            others = sorted(v for v in bp if nps and abs(v - nps) > 0.01)
            if len(others) == 1:
                onps = others[0]
        if not onps:
            # OCR often splits '1 1/2" NS' into pieces: read the area left of every 'NS' again at high zoom
            fz = []
            from PIL import Image, ImageOps, ImageFilter
            others = sorted(v for v in bp if nps and abs(v - nps) > 0.01)
            for d in horiz:
                if d['text'].upper().rstrip('.') in ('NS', 'N5', 'NS"', 'SN'):
                    r_ = fitz.Rect(d['x'] - d['w'] / 2.0 - 70, d['y'] - 11, d['x'] + d['w'] / 2.0 + 4, d['y'] + 11)
                    toks = []
                    for z_, k_ in ((3, 5), (2, 5), (3, 3)):
                        pix = page.get_pixmap(matrix=fitz.Matrix(z_, z_), clip=r_, alpha=False)
                        im_ = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
                        im_ = ImageOps.expand(im_.filter(ImageFilter.MinFilter(k_)), border=40, fill='white')
                        ds_ = sorted((e for e in run_ocr(im_, (0, 0, im_.width, im_.height), [0], float(z_), lambda m: None)
                                      if e['conf'] >= 0.3 and not re.fullmatch(r'[SN][SN5]\.?', e['text'].upper())),
                                     key=lambda e: e['x'])
                        toks.append(re.sub(r'[^0-9/]', '', ''.join(e['text'] for e in ds_)))
                    if os.environ.get('ISO_DEBUG'):
                        log('  size text near NS: %r' % (toks,))
                    v_ = None
                    for t_ in toks:
                        m_ = re.search(r'(\d)?\s*(\d)/(\d)', t_)
                        if m_:
                            f_ = int(m_.group(2)) / float(m_.group(3))
                            ch_ = [v for v in others if abs(v % 1 - f_) < 0.01]
                            if len(ch_) == 1:
                                v_ = ch_[0]
                            elif m_.group(1) and len(t_) >= 3:
                                v_ = int(m_.group(1)) + f_
                            break
                    if v_ is None:
                        for t_ in toks:
                            if re.fullmatch(r'\d{1,2}', t_) and float(t_) in OD_IN and abs(float(t_) - (nps or 0)) > 0.01:
                                v_ = float(t_)
                                break
                    if v_ and abs(v_ - (nps or 0)) > 0.01 and v_ in OD_IN:
                        fz.append((d, v_))
            if fz:
                onps = min(fz, key=lambda c: min(math.hypot(c[0]['x'] - m[0], c[0]['y'] - m[1]) for m in mids))[1]
        if not onps:
            raise ConvertError('Outlets found but their pipe size ("... NS") was not read. Use --ignore-branches '
                               'to convert only the main run.')
        model['outlet_nps'] = onps
        model['outlet_schedule'] = bp.get(onps) or sch
        pairs = sorted((math.hypot(g['x'] - o['free'][0], g['y'] - o['free'][1]), i, j)
                       for i, o in enumerate(raw_outlets) for j, g in enumerate(open_notes))
        if os.environ.get('ISO_DEBUG'):
            log('  outlets: %r' % [(round(o['free'][0]), round(o['free'][1]), o['phi']) for o in raw_outlets])
            log('  open notes: %r' % [(round(g['x']), round(g['y']), g['EL']) for g in open_notes])
        got_o, got_n, assign = set(), set(), {}
        hosts_ = [min(range(len(legs_geo)), key=lambda i: seg_dist(o['attach'], legs_geo[i]['a'], legs_geo[i]['b'])[0])
                  for o in raw_outlets]
        if (len(set(hosts_)) == 1 and len(open_notes) == len(raw_outlets) and legs[hosts_[0]].get('parts')
                and not legs[hosts_[0]].get('comp')):
            # all outlets sit on one straight leg: the n-th outlet along the leg has the n-th OPEN END note along it
            dv_ = DIR_VEC[legs[hosts_[0]]['dir']]
            gh_ = legs_geo[hosts_[0]]
            order_o = sorted(range(len(raw_outlets)), key=lambda i: seg_dist(raw_outlets[i]['attach'], gh_['a'], gh_['b'])[1])
            order_n = sorted(open_notes, key=lambda g: g['E'] * dv_[0] + g['EL'] * dv_[1] +
                             (float(g['S']) if g['S_letter'] == 'N' else -float(g['S'])) * dv_[2])
            assign = dict(zip(order_o, order_n))
        else:
            for dist_, i, j in pairs:
                if i in got_o or j in got_n or dist_ > 260:
                    continue
                got_o.add(i); got_n.add(j); assign[i] = open_notes[j]
        for oi, o in enumerate(raw_outlets):
            bi_, bd_ = None, 1e9
            for i_, g_ in enumerate(legs_geo):
                dd_, tt_ = seg_dist(o['attach'], g_['a'], g_['b'])
                if dd_ < bd_:
                    bi_, bd_, bt_ = i_, dd_, tt_
            if bi_ is None or bd_ > 25 or legs[bi_].get('comp') or not legs[bi_].get('parts'):
                warn('An outlet near the main run could not be placed on a straight, read leg. Skipped.')
                continue
            nt = assign.get(oi)
            if nt is None:
                warn('An outlet has no OPEN END note with coordinates. Skipped.')
                continue
            outl.append({'leg': bi_, 't': round(bt_, 4), 'dir': plan_dir_name(o['phi'], args.north),
                         'nps': onps, 'sch': model['outlet_schedule'],
                         'note': {'E': nt['E'], 'S_letter': nt['S_letter'], 'S': nt['S'], 'EL': nt['EL']},
                         'attach': o['attach'], 'free': o['free']})
        model['outlets'] = outl
        model['outlets_found'] = len(raw_outlets)
    # exactly one leg could not be read, but the notes at both ends give the end point: the missing length is the
    # difference. This is calculated, not read, so it is reported as such.
    unread = [i for i, l in enumerate(legs) if not l.get('parts') and not l.get('comp')]
    if len(unread) == 1 and start_note and end_note:
        k = unread[0]
        tmp_legs = [dict(l) for l in legs]
        tmp_legs[k] = {'dir': legs[k]['dir'], 'parts': [0.0]}
        tmp = dict(model, legs=tmp_legs, start={'E': start_note['E'], start_note['S_letter']: start_note['S'],
                                                'EL': start_note['EL']})
        try:
            _, _, tab, _, _, _ = build_cii(tmp, args.z_is_north, lambda m: None)
        except Exception:
            tab = None
        if tab:
            _, x, y, z = tab[-1]
            sl = end_note['S_letter']
            got = (-z if args.z_is_north else z) if sl == 'S' else (z if args.z_is_north else -z)
            r = {'E': end_note['E'] - x, 'S': end_note['S'] - got, 'EL': end_note['EL'] - y}
            d_ = legs[k]['dir']
            axis = {'E': 'E', 'W': 'E', 'N': 'S', 'S': 'S', 'U': 'EL', 'D': 'EL'}[d_]
            sign = {'E': 1, 'W': -1, 'N': -1 if sl == 'S' else 1, 'S': 1 if sl == 'S' else -1, 'U': 1, 'D': -1}[d_]
            if sl == 'N' and d_ in ('N', 'S'):
                sign = 1 if d_ == 'N' else -1
            others = [a for a in ('E', 'S', 'EL') if a != axis and not (a == 'EL' and axis != 'EL')]
            length = r[axis] * sign
            if length > 5 and all(abs(r[a]) <= 5 for a in others):
                legs[k]['parts'] = [round(length, 1)]
                report[k] = (report[k][0], legs[k]['dir'], legs[k]['parts'],
                             'CALCULATED from the end notes, not read from the drawing', [])
                warn('Leg %d (%s): its dimension could not be read. %.0f mm was calculated from the start and end '
                     'notes. All other legs agree with the notes. No small marks on this leg could be read, so it is '
                     'one element.' % (k + 1, d_, length))

    # when both end notes are known, the end point is a check on the reading. If another reading of an
    # ambiguous leg (overall or chain, which plane a 45 deg leg is in) fits the end note clearly better, use it.
    if alts and start_note and end_note and all(l.get('parts') for l in legs):
        import itertools

        def end_error(variant):
            tmp = dict(model, legs=variant, start={'E': start_note['E'], start_note['S_letter']: start_note['S'],
                                                   'EL': start_note['EL']})
            try:
                _, _, tab, _, _, _ = build_cii(tmp, args.z_is_north, lambda m: None)
            except Exception:
                return None
            _, x, y, z = tab[-1]
            sl = end_note['S_letter']
            got = (-z if args.z_is_north else z) if sl == 'S' else (z if args.z_is_north else -z)
            return abs(x - end_note['E']) + abs(got - end_note['S']) + abs(y - end_note['EL'])
        keys = sorted(alts)[:8]
        base_err = end_error(legs)
        if base_err is not None and base_err > 5:
            best = (base_err, None)
            for combo in itertools.product(*[[None] + list(range(len(alts[k]))) for k in keys]):
                if not any(c is not None for c in combo):
                    continue
                var = list(legs)
                for k, c in zip(keys, combo):
                    if c is not None:
                        var[k] = alts[k][c]
                e = end_error(var)
                if e is not None and e < best[0] - 1e-6:
                    best = (e, combo)
            if best[1] is not None:
                var = list(legs)
                for k, c in zip(keys, best[1]):
                    if c is not None:
                        var[k] = alts[k][c]
                ok_apply = best[0] <= 5.0
                why = ''
                if not ok_apply and best[0] < 0.05 * base_err:
                    # not exact: accept only if what is left is a SHORTFALL in one direction (a dimension that
                    # is missing), never an overshoot (too many numbers added up)
                    tmp = dict(model, legs=var, start={'E': start_note['E'], start_note['S_letter']: start_note['S'],
                                                       'EL': start_note['EL']})
                    _, el_, tab, _, _, _ = build_cii(tmp, args.z_is_north, lambda m: None)
                    _, x, y, z = tab[-1]
                    sl = end_note['S_letter']
                    got = (-z if args.z_is_north else z) if sl == 'S' else (z if args.z_is_north else -z)
                    r = {'E': end_note['E'] - x, 'S': end_note['S'] - got, 'EL': end_note['EL'] - y}
                    big = [k for k in r if abs(r[k]) > 5]
                    if len(big) == 1 and big[0] != 'EL':
                        k = big[0]
                        sgn = 1 if r[k] > 0 else -1
                        prog = 0.0
                        for e in el_:
                            if k == 'E':
                                dlt = e['dx']
                            else:
                                dlt = (-e['dz'] if args.z_is_north else e['dz']) if sl == 'S' else (e['dz'] if args.z_is_north else -e['dz'])
                            prog += max(0.0, dlt * sgn)
                        if prog > abs(r[k]):
                            ok_apply = True
                            why = ' It is %.0f mm short in %s: a dimension is probably missing.' % (abs(r[k]), k)
                if ok_apply:
                    changed = []
                    for k, c in zip(keys, best[1]):
                        if c is not None:
                            legs[k] = alts[k][c]
                            report[k] = (report[k][0], legs[k]['dir'], legs[k]['parts'],
                                         'another reading chosen: the end point fits the end note better',
                                         report[k][4])
                            changed.append(k + 1)
                    log('  Another reading of leg(s) %s fits the end note better (error %.0f mm instead of %.0f mm): used.%s'
                        % (', '.join(map(str, changed)), best[0], base_err, why))
                else:
                    warn('A different reading of some legs would get closer to the end note (error %.0f mm instead of '
                         '%.0f mm), but not exactly, so it was not used. Check the legs in the drawing.' % (best[0], base_err))
    # a single straight run whose dimension numbers do not add up to the two end notes: the notes are exact
    if len(legs) == 1 and start_note and end_note and legs[0].get('parts') and not legs[0].get('comp'):
        sl_ = end_note['S_letter']

        def _north(n_):
            return float(n_['S']) if n_['S_letter'] == 'N' else -float(n_['S'])
        vec_ = (end_note['E'] - start_note['E'], end_note['EL'] - start_note['EL'], _north(end_note) - _north(start_note))
        dv_ = DIR_VEC[legs[0]['dir']]
        ln_ = sum(vec_[i] * dv_[i] for i in range(3))
        res_ = math.sqrt(max(0.0, sum(v * v for v in vec_) - ln_ * ln_))
        if ln_ > 5 and res_ <= 5 and abs(ln_ - sum(legs[0]['parts'])) > 5:
            warn('Leg 1: the dimension numbers read from the drawing add up to %.0f mm, but the start and end notes '
                 'give %.0f mm. The length from the notes is used. The small dimension marks of this leg are not used.'
                 % (sum(legs[0]['parts']), ln_))
            report[0] = (report[0][0], legs[0]['dir'], [round(ln_, 1)],
                         'CALCULATED from the end notes (dimension numbers did not fit)', report[0][4])
            legs[0] = {'dir': legs[0]['dir'], 'parts': [round(ln_, 1)]}
    # elevations: the notes at both ends and the "EL +..." labels next to the corners
    nl = len(legs_geo)
    el, el_d = [None] * (nl + 1), [1e9] * (nl + 1)
    if start_note:
        el[0] = start_note['EL']
    if end_note:
        el[-1] = end_note['EL']
    corners = [g['b'] for g in legs_geo[:-1]]
    for e in el_only:
        if not corners:
            break
        k = min(range(len(corners)), key=lambda i: math.hypot(corners[i][0] - e['x'], corners[i][1] - e['y']))
        dd = math.hypot(corners[k][0] - e['x'], corners[k][1] - e['y'])
        if dd < 450 and dd < el_d[k + 1]:
            el[k + 1], el_d[k + 1] = e['EL'], dd
    known = [i for i in range(nl + 1) if el[i] is not None]
    for i0, i1 in zip(known, known[1:]):
        flat = [j for j in range(i0, i1) if not _vert_mm(legs[j]) and 'U' not in legs[j]['dir'] and 'D' not in legs[j]['dir']]
        tot = el[i1] - el[i0] - sum(_vert_mm(legs[j]) for j in range(i0, i1))
        wsum = float(sum(sum(legs[j]['parts']) for j in flat))
        if abs(tot) > max(3.0, 0.001 * wsum) and wsum > 0:      # a few mm is rounding in the drawing, not a slope
            if abs(tot) > 0.03 * wsum + 30:
                warn('The elevation changes by %.0f mm between two points, but the legs in between are only %.0f mm '
                     'long. That is too steep to be a slope, so a vertical dimension is probably misread. The '
                     'elevation was NOT spread over the legs.' % (abs(tot), wsum))
                continue
            for j in flat:
                legs[j]['dy_mm'] = round(tot * sum(legs[j]['parts']) / wsum, 1)
    if el_only and len(known) < 2:
        warn('Elevation labels found but not matched to corners.')
    if start_note:
        model['start'] = {'E': start_note['E'], start_note['S_letter']: start_note['S'], 'EL': start_note['EL']}
    if args.el_scale != 1:
        model['el_scale'] = args.el_scale
    if args.wall:
        model['wall_mm'] = args.wall
    if args.od:
        model['od_mm'] = args.od
    end_expected = None
    if end_note:
        end_expected = {'E': end_note['E'], end_note['S_letter']: end_note['S'], 'EL': end_note['EL']}
    return model, report, legs_geo, (fitz, page), end_expected


def closure_check(model, table, end_expected, z_is_north, warn, log):
    if not end_expected:
        return
    _, x, y, z = table[-1]
    st = model['start']
    sl = 'N' if 'N' in end_expected else 'S'
    if sl == 'S':
        got = -z if z_is_north else z
    else:
        got = z if z_is_north else -z
    ok = abs(x - end_expected['E']) < 5 and abs(got - end_expected[sl]) < 5
    log('End-point check against the end note:  computed E %.0f %s %.0f   note E %.0f %s %.0f   -> %s'
        % (x, sl, got, end_expected['E'], sl, end_expected[sl], 'OK' if ok else 'MISMATCH'))
    if 'EL' in end_expected:
        ok_el = abs(y - end_expected['EL']) < 5
        log('Elevation check: computed %.0f   note %.0f   -> %s' % (y, end_expected['EL'], 'OK' if ok_el else 'MISMATCH'))
        if not ok_el:
            warn('CHECK FAILED: the computed end elevation does not match the end note.')
    if not ok:
        warn('End point is off by E %+.0f mm and %s %+.0f mm (note minus computed), elevation %+.0f mm. '
             'A missing or misread dimension on a leg in that direction would explain it.'
             % (end_expected['E'] - x, sl, end_expected[sl] - got, end_expected.get('EL', y) - y))
        warn('CHECK FAILED: the computed end point does not match the end note. A dimension was probably misread, '
             'or North is not up-left (try --north up-right). Do not import before you have checked the list and the picture.')



def choose_db(args, warn, log):
    dbp = args.db
    here = os.path.dirname(os.path.abspath(__file__))
    remember = os.path.join(here, 'iso2cii_db_path.txt')
    if not dbp and not args.no_ask and not args.out_dir:
        last = ''
        try:
            if os.path.exists(remember):
                last = open(remember, encoding='utf-8').read().strip()
        except Exception:
            pass
        print('Choose the Excel line list with temperature and pressure (Cancel = convert without it) ...')
        try:
            import tkinter as tk
            from tkinter import filedialog
            r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True)
            dbp = filedialog.askopenfilename(
                title='Excel line list (temperature and pressure). Cancel = convert without it.',
                initialdir=os.path.dirname(last) if last and os.path.exists(last) else None,
                filetypes=[('Excel / CSV', '*.xlsx *.xlsm *.csv')]) or None
            r.destroy()
        except Exception:
            try:
                dbp = input('Path of the Excel file (press Enter to skip): ').strip().strip('"') or None
            except Exception:
                dbp = None
        if dbp:
            try:
                with open(remember, 'w', encoding='utf-8') as f:
                    f.write(dbp)
            except Exception:
                pass
    if dbp and not os.path.exists(dbp):
        warn('The Excel file %s was not found. Converting without temperature and pressure.' % dbp)
        dbp = None
    if dbp:
        log('Using the Excel line list: %s' % dbp)
    else:
        log('No Excel line list used: temperature and pressure are left at 0.')
    return dbp


def ask_save_location(default_dir):
    """Ask the user where to save. Returns a folder path, or None if cancelled."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(parent=root, initialdir=default_dir,
                                         title='Where do you want to save the results? (a new sub-folder is created there)')
        root.destroy()
        return folder or None
    except Exception:
        pass
    try:
        ans = input('Where do you want to save the results?\n'
                    '(type a folder path, or just press Enter to use the PDF folder): ').strip().strip('"')
    except EOFError:
        ans = ''
    return ans or default_dir



# --------------------------------------------------------------------------
# several sheets of one line (continuation sheets)
# --------------------------------------------------------------------------
class JoinError(ConvertError):
    pass


def sheet_key(path):
    """'4-RJ-33812-B52-NI-1-Model.pdf' -> ('4-RJ-33812-B52-NI', 1): sheets of one line share the key"""
    n = os.path.splitext(os.path.basename(path))[0]
    n = re.sub(r'[-_ ]?Model$', '', n, flags=re.I)
    m = re.fullmatch(r'(.*?)[-_ ](\d{1,2})', n)
    if m and re.search(r'[A-Za-z]\d*-?[A-Za-z]*$', m.group(1)) and re.search(r'\d{4,}', m.group(1)):
        return m.group(1), int(m.group(2))
    return n, 0


_OPP = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E', 'U': 'D', 'D': 'U'}


def _note_pt(d):
    """{'E','S' or 'N','EL'} -> (E, EL, North)"""
    north = float(d['N']) if 'N' in d else -float(d.get('S', 0.0))
    return (float(d['E']), float(d['EL']), north)


def _sheet_ends(model, z_is_north):
    """start and end point (E, EL, North) of a sheet, the end computed from its legs"""
    st = _note_pt(model.get('start') or {'E': 0, 'S': 0, 'EL': 0})
    m = dict(model, outlets=[], outlets_found=0)
    _, _, table, _, _, _ = build_cii(m, z_is_north, lambda x: None)
    _, x, y, z = table[-1]
    return st, (x, y, z if z_is_north else -z)


def reverse_sheet(sh, z_is_north):
    m = sh['model']
    if any(l.get('comp') for l in m['legs']):
        return False
    n = len(m['legs'])
    st, en = _sheet_ends(m, z_is_north)
    m['legs'] = [dict(l, dir=_OPP[l['dir']], parts=list(reversed(l['parts'])),
                      dy_mm=-float(l.get('dy_mm', 0)) if l.get('dy_mm') else 0)
                 for l in reversed(m['legs'])]
    for o in m.get('outlets') or []:
        o['leg'] = n - 1 - o['leg']
    m['start'] = {'E': en[0], 'N': en[2], 'EL': en[1]}
    sh['reversed'] = not sh.get('reversed', False)
    return True


def read_sheets(args, pdfs, log, warn):
    """Read every chosen PDF on its own. A sheet that fails keeps its error text."""
    import copy
    sheets = []
    for p in pdfs:
        nm = os.path.basename(p)
        if len(pdfs) > 1:
            log('\n=== Sheet %s ===' % nm)
        a = copy.copy(args)
        a.pdf = p
        sh = {'pdf': p, 'name': nm}
        try:
            model, report, legs_geo, ctx, endx = analyse_pdf(a, log, warn)
        except ConvertError as ex:
            sh['error'] = str(ex)
            sheets.append(sh)
            continue
        sh.update({'model': model, 'report': report, 'geo': legs_geo, 'ctx': ctx, 'end': endx})
        sh['bad'] = [i + 1 for i, l in enumerate(model['legs'])
                     if (l.get('comp') and any(float(v) <= 0 for _, v in l['comp'])) or
                     (not l.get('comp') and (not l['parts'] or any(float(q) <= 0 for q in l['parts'])))]
        sheets.append(sh)
    return sheets


def chain_sheets(sheets, zn, log, warn):
    """Join sheets whose pipes continue into each other (the end point of one is the start point of the next),
    whatever their line numbers are. Returns a list of chains (lists of sheets, in order)."""
    items = [s_ for s_ in sheets if 'model' in s_ and not s_['bad']]
    chains = [[s_] for s_ in items]

    def dist(a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def ends(ch):
        return _sheet_ends(ch[0]['model'], zn)[0], _sheet_ends(ch[-1]['model'], zn)[1]

    def rev_chain(ch):
        for sh in ch:
            if not reverse_sheet(sh, zn):
                return None
        return list(reversed(ch))

    while len(chains) > 1:
        best = None
        for i, A in enumerate(chains):
            for j, B in enumerate(chains):
                if i == j:
                    continue
                sa, ea = ends(A)
                sb, eb = ends(B)
                for ra in (False, True):
                    for rb in (False, True):
                        # the end of A (turned round if ra) meets the start of B (turned round if rb)
                        a_head, a_tail = (ea, sa) if ra else (sa, ea)
                        b_head, b_tail = (eb, sb) if rb else (sb, eb)
                        d = dist(a_tail, b_head)
                        lim = 400 if not (ra or rb) else 20      # turning a sheet round needs an exact join
                        if d > lim or dist(a_head, b_tail) < 150:
                            continue
                        if (ra or rb) and any(l.get('comp') for c_ in ((A if ra else []) + (B if rb else []))
                                              for l in c_['model']['legs']):
                            continue
                        if best is None or (d + (50 if (ra or rb) else 0)) < best[0]:
                            best = (d + (50 if (ra or rb) else 0), i, j, ra, rb)
        if best is None:
            break
        _, i, j, ra, rb = best
        A, B = chains[i], chains[j]
        if ra:
            A = rev_chain(A)
        if rb:
            B = rev_chain(B)
        for sh in (A if ra else []) + (B if rb else []):
            warn('Sheet %s runs against the order of the line, so it was turned round.' % sh['name'])
        chains[i] = A + B
        del chains[j]
    return chains


def merge_chain(args, chain, base, log, warn):
    """Put the sheets of one chain into ONE model. Lines with different line numbers are kept apart per leg."""
    zn = args.z_is_north
    log('\nOrder of the sheets: %s' % ' -> '.join(s_['name'] for s_ in chain))
    legs, outlets, report, sizes = [], [], [], []
    for sh in chain:
        try:
            sizes.append(get_pipe_data(sh['model'], lambda x: None))
        except ConvertError as ex:
            raise ConvertError('Sheet %s: %s' % (sh['name'], ex))
    mixed = len(set(sizes)) > 1
    for k, sh in enumerate(chain):
        m = sh['model']
        if k > 0:
            en_prev = _sheet_ends(chain[k - 1]['model'], zn)[1]
            st_here = _sheet_ends(m, zn)[0]
            gv = tuple(b - a for a, b in zip(en_prev, st_here))
            hyp = math.sqrt(sum(v * v for v in gv))
            if hyp > 5:
                names = [(('E' if gv[0] > 0 else 'W'), abs(gv[0])), (('U' if gv[1] > 0 else 'D'), abs(gv[1])),
                         (('N' if gv[2] > 0 else 'S'), abs(gv[2]))]
                comp = [[d_, round(v_, 1)] for d_, v_ in names if v_ > 1]
                legs.append({'dir': '+'.join(d_ for d_, _ in comp), 'parts': [round(hyp, 1)], 'comp': comp, 'gap': True,
                             'R_mm': m.get('bend_radius_mm')})
                warn('Between %s and %s the pipe is %.0f mm short (a dimension is missing on the first sheet). '
                     'A straight connecting element of %.0f mm was added so the second sheet stays at its true position.'
                     % (chain[k - 1]['name'], sh['name'], hyp, hyp))
        off = len(legs)
        for li_, l in enumerate(m['legs']):
            l = dict(l)
            if mixed:
                l['od_mm'], l['wall_mm'] = sizes[k]
            l['ln'] = m.get('line_number') or ''
            if li_ == 0:
                l['line'] = m.get('line_number') or ''
            l['R_mm'] = m.get('bend_radius_mm')
            legs.append(l)
        for o in m.get('outlets') or []:
            o = dict(o)
            o['leg'] = o['leg'] + off
            o.setdefault('nps', m.get('outlet_nps'))
            o.setdefault('sch', m.get('outlet_schedule'))
            outlets.append(o)
        for (i, name, pieces, note, labs) in (sh['report'] or []):
            report.append((i + off, name, pieces, '[%s] %s' % (sh['name'], note), labs))
    model = dict(chain[0]['model'])
    model['legs'] = legs
    model['outlets'] = outlets
    model['outlets_found'] = sum(sh['model'].get('outlets_found', 0) for sh in chain)
    model.pop('outlet_report', None)
    model.pop('process', None)
    model['sheets'] = [sh['name'] for sh in chain]
    lines = []
    for sh in chain:
        ln = sh['model'].get('line_number') or ''
        if ln not in lines:
            lines.append(ln)
    model['line_numbers'] = lines
    if outlets and not model.get('outlet_nps'):
        model['outlet_nps'], model['outlet_schedule'] = outlets[0]['nps'], outlets[0]['sch']
    if not args.no_image:
        for n_, sh in enumerate(chain, 1):
            if sh.get('ctx'):
                try:
                    draw_check('%s_sheet%d.check.png' % (base, n_), sh['ctx'][1], sh['ctx'][0], sh['geo'],
                               sh['model'], [])
                except Exception as ex:
                    warn('Could not write the check picture of %s: %s' % (sh['name'], ex))
    end_expected = None if chain[-1].get('reversed') else chain[-1].get('end')
    return model, report, end_expected


def main(argv=None):
    ap = argparse.ArgumentParser(description='Isometric PDF -> CAESAR II neutral file (no AI, offline).')
    ap.add_argument('pdf', nargs='*', help='isometric drawing(s) (vector PDF). Several sheets of one line are joined into one file')
    ap.add_argument('-o', '--out', help='output .CII (default: next to the PDF)')
    ap.add_argument('--page', type=int, default=0, help='page number, starting at 0')
    ap.add_argument('--north', choices=list(NORTH_OPTIONS), default='up-left',
                    help='where North points on the sheet (default up-left)')
    ap.add_argument('--z-is-north', action='store_true', help='CAESAR II Z axis = North (default: Z = South)')
    ap.add_argument('--sch', help='pipe schedule, e.g. 20, 40, STD (default: read from the bill of materials)')
    ap.add_argument('--wall', type=float, help='wall thickness in mm (overrides the table)')
    ap.add_argument('--od', type=float, help='outside diameter in mm (overrides the table)')
    ap.add_argument('--line', help='line number text (default: read from the drawing)')
    ap.add_argument('--start', nargs=3, type=float, metavar=('E', 'S', 'EL'),
                    help="start point if the note cannot be read: E S EL")
    ap.add_argument('--el-scale', type=float, default=1.0, help='multiply the EL value (default 1 = use as mm)')
    ap.add_argument('--reverse', action='store_true', help='walk the pipe from the other end')
    ap.add_argument('--zoom', type=float, default=2.0, help='OCR render zoom (default 2.0)')
    ap.add_argument('--out-dir', help='folder for the results (default: a new folder named like the PDF, next to the PDF)')
    ap.add_argument('--no-ask', action='store_true', help='do not ask where to save; use a new folder next to the PDF')
    ap.add_argument('--from-json', help='skip the PDF: build the .CII from a (edited) review json')
    ap.add_argument('--db', help='Excel / CSV file with line number, temperature and pressure (default: a file named '
                                 'process_data.xlsx or .csv next to this script)')
    ap.add_argument('--temp-unit', choices=['C', 'F'], help='temperature unit in the Excel file (default: read from the header)')
    ap.add_argument('--press-unit', choices=sorted(P_TO_KPA), help='pressure unit (gauge) in the Excel file (default: read from the header)')
    ap.add_argument('--ignore-branches', action='store_true', help='convert only the main run even if the sheet has branches')
    ap.add_argument('--no-image', action='store_true', help='do not write the check picture')
    args = ap.parse_args(argv)

    warnings = []

    def warn(m):
        warnings.append(m)
        print('  WARNING: ' + m)

    def log(m):
        print(m)

    pdfs = []
    for p_ in (args.pdf or []):
        if os.path.isdir(p_):
            pdfs += sorted(os.path.join(p_, f_) for f_ in os.listdir(p_) if f_.lower().endswith('.pdf'))
        else:
            pdfs.append(p_)
    if not pdfs and not args.from_json:
        try:
            import tkinter as tk
            from tkinter import filedialog
            r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True)
            pdfs = list(filedialog.askopenfilenames(
                title='Choose the isometric PDF(s). Choose all sheets of a line together to get ONE file.',
                filetypes=[('PDF', '*.pdf')]))
            r.destroy()
            if not pdfs:
                return 1
        except Exception:
            ap.print_help()
            return 1
    pdfs.sort(key=lambda q: (sheet_key(q)[0], sheet_key(q)[1]))
    args.pdf = pdfs[0] if pdfs else None

    parent = None
    if pdfs and not args.from_json and not args.out_dir and not args.no_ask:
        parent = ask_save_location(os.path.dirname(os.path.abspath(args.pdf)))
        if not parent:
            print('Cancelled. Nothing was saved.')
            return 1
        print('Results will be saved in: %s' % parent)

    dbp = choose_db(args, warn, log)

    def convert(item):
        warnings.clear()
        try:
            if args.from_json:
                with open(args.from_json, encoding='utf-8') as f:
                    model = json.load(f)
                model.pop('_report', None)
                base = os.path.splitext(args.from_json)[0].replace('.review', '')
                legs_geo = page_ctx = end_expected = None
                report = None
            else:
                base, model, report, legs_geo, page_ctx, end_expected = (
                    item['base'], item['model'], item['report'], item['geo'], item['ctx'], item['end'])
            out_path = args.out or (base + '.CII')
            bad = [i + 1 for i, l in enumerate(model['legs'])
                   if (l.get('comp') and any(float(v) <= 0 for _, v in l['comp'])) or
                   (not l.get('comp') and (not l['parts'] or any(float(p) <= 0 for p in l['parts'])))]
            if bad:
                if args.from_json:
                    raise ConvertError('Leg(s) %s have no valid "parts" in the review file. Fill them in and run again.' % bad)
                with open(base + '.review.json', 'w', encoding='utf-8') as f:
                    json.dump(model, f, indent=2)
                if not args.no_image and page_ctx:
                    try:
                        draw_check(base + '.check.png', page_ctx[1], page_ctx[0], legs_geo, model, [])
                    except Exception as ex:
                        warn('Could not write the check picture: %s' % ex)
                print('\nThe route was found, but leg(s) %s could not be read completely, so NO .CII was written.' % bad)
                print('  1. Open %s.review.json and fill in the "parts" of those legs (lengths in mm, in order).' % os.path.basename(base))
                print('  2. Run:  python iso2cii.py --from-json "%s.review.json"' % base)
                print('  The picture %s.check.png shows the route and marks the legs that were not read.' % os.path.basename(base))
                return 3
            if dbp:
                recs = load_process_db(dbp, args.temp_unit, args.press_unit, warn, log)
                if model.get('sheets'):          # merged lines: each leg gets the data of its own line number
                    cache_ = {}
                    for lg_ in model['legs']:
                        ln_ = lg_.get('ln')
                        if ln_ is None:
                            continue
                        if ln_ not in cache_:
                            cache_[ln_] = lookup_process(recs, ln_, warn)
                        if cache_[ln_]:
                            lg_['process'] = cache_[ln_]
                    model['process_by_line'] = {k_: v_ for k_, v_ in cache_.items() if v_}
                else:
                    found = lookup_process(recs, model.get('line_number'), warn)
                    if found:
                        model['process'] = found
            text, elems, table, od, wall, R = build_cii(model, args.z_is_north, warn)
            if model.get('outlets_found') and not model.get('outlet_report') and not getattr(args, 'ignore_branches', False):
                raise ConvertError('This sheet has %d branch outlets but none of them could be placed from the OPEN END '
                                   'notes, so the result would be wrong. Use --ignore-branches to convert only the main run.'
                                   % model['outlets_found'])
            with open(out_path, 'w', newline='', encoding='latin-1', errors='replace') as f:
                f.write(text)
            if not args.from_json:
                with open(base + '.review.json', 'w', encoding='utf-8') as f:
                    json.dump(model, f, indent=2)
                if not args.no_image and page_ctx:
                    try:
                        draw_check(base + '.check.png', page_ctx[1], page_ctx[0], legs_geo, model, elems)
                    except Exception as ex:
                        warn('Could not write the check picture: %s' % ex)
            print()
            print('Line number : %s' % ((' , '.join(model['line_numbers'])) if model.get('line_numbers') else (model.get('line_number') or '(none)')))
            if model.get('process'):
                pr = model['process']
                print('Process     : Excel line "%s"  T1..T9 = %s C   P1..P9 = %s kPa' % (
                    pr['excel_line'], [round(v, 1) for v in pr['temps']], [round(v, 1) for v in pr['press']]))
            elif model.get('process_by_line'):
                for ln_, pr in model['process_by_line'].items():
                    print('Process     : %s -> Excel line "%s"  T1 %s C  P1 %s kPa' % (
                        ln_, pr['excel_line'], round(pr['temps'][0], 1), round(pr['press'][0], 1)))
            elif dbp:
                print('Process     : NOT filled (see the warning above)')
            print('Pipe        : OD %.2f mm, wall %.2f mm (schedule %s), bend radius %.1f mm' % (od, wall, model.get('schedule', '?'), R))
            if report:
                print('\nLegs read from the drawing:')
                for i, name, pieces, note, labs in report:
                    print('  leg %d  %s  %-40s  total %-6d [%s]  (labels: %s)' % (
                        i, name, ' + '.join(str(int(p)) for p in pieces), sum(pieces), note, labs))
            print('\nNodes (E, elevation, Z in mm):')
            for nd, x, y, z in table:
                print('  %4d  %12.1f %12.1f %12.1f' % (nd, x, y, z))
            if model.get('outlet_report'):
                print('\nOutlets (branch pipes %s" sch %s, %d of them), direction, length mm, from node:' % (
                    fmt_num(model.get('outlet_nps')), model.get('outlet_schedule'), len(model['outlet_report'])))
                for dname, Lv, hn in model['outlet_report']:
                    print('  %s  %7.1f  node %d' % (dname, Lv, hn))
                print('  (Outlets are plain pipe elements. Add the tee / branch SIF in CAESAR II.)')
            if end_expected:
                closure_check(model, table, end_expected, args.z_is_north, warn, log)
            print('\n%d elements, %d bends written to %s' % (len(elems), sum(e['bend'] for e in elems), out_path))
            if warnings:
                print('\n%d warning(s) above. Check them before you import.' % len(warnings))
            print('Results folder: %s' % os.path.dirname(os.path.abspath(out_path)))
            if model.get('sheets'):
                print('Next: compare the %s_sheet*.check.png pictures with the drawings, then import the .CII in CAESAR II.' % os.path.basename(base))
            else:
                print('Next: compare %s.check.png with the drawing, then import the .CII in CAESAR II.' % os.path.basename(base))
            return 0
        except ConvertError as ex:
            print('\nERROR: %s' % ex)
            return 2
        except Exception as ex:                     # anything unexpected: say it plainly, keep the details for me
            import traceback
            tb = traceback.format_exc()
            print('\nUNEXPECTED ERROR: %s: %s' % (type(ex).__name__, ex))
            try:
                with open('iso2cii_error.txt', 'w', encoding='utf-8') as f:
                    f.write(tb)
                print('Details were saved in iso2cii_error.txt (send this file if you ask for help).')
            except Exception:
                print(tb)
            return 4


    if args.from_json:
        return convert(None)
    sheets = read_sheets(args, pdfs, log, warn)
    rc = 0
    for sh in sheets:
        if 'error' in sh:
            print('\nERROR%s: %s' % ((' (%s)' % sh['name']) if len(pdfs) > 1 else '', sh['error']))
            if len(pdfs) > 1 and 'No pipe drawing found' in sh['error']:
                continue                     # a bill-of-materials sheet in a multi-file run is not a failure
            rc = 2
    chains = chain_sheets(sheets, args.z_is_north, log, warn) if len(pdfs) > 1 else [[s_] for s_ in sheets if 'model' in s_ and not s_['bad']]
    for sh in sheets:
        if 'model' in sh and sh['bad']:        # unread legs: the existing review-file route, one sheet at a time
            chains.append([sh])
    if not chains:
        return rc or 2
    for ch in chains:
        if len(ch) == 1:
            sh = ch[0]
            name = os.path.splitext(os.path.basename(sh['pdf']))[0]
            folder = args.out_dir or os.path.join(parent or os.path.dirname(os.path.abspath(sh['pdf'])), name)
            os.makedirs(folder, exist_ok=True)          # one folder per drawing, named like the PDF
            item = {'base': os.path.join(folder, name), 'model': sh['model'], 'report': sh['report'],
                    'geo': sh['geo'], 'ctx': sh['ctx'], 'end': sh['end']}
        else:
            keys = []
            for sh in ch:
                k_ = sheet_key(sh['pdf'])[0]
                if k_ not in keys:
                    keys.append(k_)
            name = '+'.join(keys)[:90] + '_merged'
            folder = args.out_dir or os.path.join(parent or os.path.dirname(os.path.abspath(ch[0]['pdf'])), name)
            os.makedirs(folder, exist_ok=True)
            base = os.path.join(folder, name)
            print('\n################ %s (%d sheets) ################' % (name, len(ch)))
            try:
                model, report, end_expected = merge_chain(args, ch, base, log, warn)
            except ConvertError as ex:
                print('\nERROR: %s' % ex)
                rc = 2
                continue
            item = {'base': base, 'model': model, 'report': report, 'geo': None, 'ctx': None, 'end': end_expected}
        rc = convert(item) or rc
    return rc


if __name__ == '__main__':
    sys.exit(main())

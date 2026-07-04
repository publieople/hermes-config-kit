#!/usr/bin/env python3
"""Quantitative expression DNA analysis for self-distillation.
Run this on extracted Notion markdown files to get style statistics.

Usage: python3 analyze_dna.py <directory_of_md_files>
"""
import re, os, sys

SLANG_MARKERS = r'主播|省流|干货|冲过|平替|鬼话|死磕|两条腿|木桶效应|保号|兜底'
HEDGING_MARKERS = r'可能|大概|也许|或许|建议|仅供参考|可以考虑|通常|一般|不一定|多数|大多'
CERTAINTY_MARKERS = r'一定|必须|绝对|毫无疑问|当然|所有的|所有|非常|强烈'

def analyze_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    if text.startswith('Traceback') or text.startswith('[EXTRACTION FAILED'):
        return None
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_terms = len(set(re.findall(r'[a-zA-Z][a-zA-Z]+', text)))
    total_len = len(text)
    
    wo = len(re.findall(r'(?<![也你他她])我(?!们)', text))
    women = len(re.findall(r'我们', text))
    questions = len(re.findall(r'[?？]', text))
    exclamations = len(re.findall(r'[!！]', text))
    
    hedging = len(re.findall(HEDGING_MARKERS, text))
    certainty = len(re.findall(CERTAINTY_MARKERS, text))
    slang = len(re.findall(SLANG_MARKERS, text))
    
    return {
        'chinese': chinese_chars, 'english_terms': english_terms, 'total': total_len,
        'wo': wo, 'women': women, 'questions': questions, 'exclamations': exclamations,
        'hedging': hedging, 'certainty': certainty, 'slang': slang,
    }

def main():
    dirpath = sys.argv[1] if len(sys.argv) > 1 else '.'
    files = sorted([f for f in os.listdir(dirpath) if f.endswith('.md')])
    
    print(f"{'File':45s} {'中文':>5s} {'总长':>6s} {'我':>3s} {'?':>3s} {'模糊':>4s} {'确定':>4s} {'口语':>4s}")
    print('-' * 85)
    
    total = dict.fromkeys(['chinese', 'total', 'wo', 'women', 'questions', 'exclamations', 'hedging', 'certainty', 'slang'], 0)
    for fname in files:
        r = analyze_file(os.path.join(dirpath, fname))
        if not r: continue
        for k in total: total[k] += r[k]
        print(f"{fname[:44]:45s} {r['chinese']:5d} {r['total']:6d} {r['wo']:3d} {r['questions']:3d} {r['hedging']:4d} {r['certainty']:4d} {r['slang']:4d}")
    
    print(f"\n=== Aggregate ({len(files)} files) ===")
    print(f"Chinese chars: {total['chinese']}")
    c = max(total['chinese'], 1)
    print(f"First person 我: {total['wo']} ({total['wo']*1000/c:.1f}/千字)")
    print(f"Questions: {total['questions']} ({total['questions']*1000/c:.1f}/千字)")
    print(f"Hedging/Certainty: {total['hedging']}/{total['certainty']} = {total['hedging']/max(total['certainty'],1):.1f}")
    print(f"Slang markers: {total['slang']}")

if __name__ == '__main__':
    main()

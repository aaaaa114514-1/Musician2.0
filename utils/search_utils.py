'''
Search utils
'''

from rapidfuzz import process, fuzz

def fuzzy_match_all(query, string_list, threshold=60):
    matches = process.extract(query, string_list, scorer=fuzz.ratio, score_cutoff=threshold)
    return matches
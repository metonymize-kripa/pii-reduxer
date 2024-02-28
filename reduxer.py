import spacy
import re, time
from collections import Counter

# Load the spaCy model,
# remember to run python -m spacy download en_core_web_sm before first use
nlp = spacy.load("en_core_web_sm")

def anonymize_text_including_proper_nouns_and_addresses(text, pii_config):
    """
    Anonymizes text by replacing occurrences of specific PII types and proper nouns, including potential physical addresses, 
    with unique placeholders. It utilizes both regex for specific PII patterns and spaCy for NER to identify proper nouns.

    Parameters:
    - text: The input text string to be anonymized.
    - pii_config: A dictionary specifying the PII types to anonymize, where each key is a PII type (e.g., 'phone_number') 
      and each value is a tuple containing a regex pattern to identify the PII and a placeholder string for its anonymization.

    Returns:
    - anonymized_text: The text after PII and proper nouns have been anonymized.
    - lookup_table: A dictionary mapping the anonymized placeholders back to the original text strings, enabling potential restoration.
    """
    anonymized_text = text
    lookup_table = {}
    counters = Counter()
    
    # First, handle regex-based PII detection and anonymization
    for pii_type, (pattern, placeholder) in pii_config.items():
        for match in re.finditer(pattern, text):
            original = match.group()
            counters[pii_type] += 1
            placeholder_with_counter = f"{placeholder}{counters[pii_type]}"
            anonymized_text = anonymized_text.replace(original, placeholder_with_counter, 1)
            lookup_table[placeholder_with_counter] = original

    # Process the text with spaCy for NER and part-of-speech tagging
    doc = nlp(anonymized_text)
    # Sort entities and tokens to replace longer phrases first to avoid nested replacement issues
    ents_and_tokens = sorted(list(doc.ents) + [token for token in doc if token.pos_ == "PROPN"], key=lambda x: -len(x.text))

    for ent_or_token in ents_and_tokens:
        if isinstance(ent_or_token, spacy.tokens.Token):
            # For individual proper nouns (tokens), we use the 'PROPN' label
            label = 'PROPN'
        else:
            # For recognized named entities
            label = ent_or_token.label_
        
        if label in ['ORG', 'PERSON', 'GPE', 'LOC', 'FAC', 'PROPN']:  # Extended to include 'FAC' and 'PROPN'
            original = ent_or_token.text
            counters[label] += 1
            placeholder_with_counter = f"[{label}{counters[label]}]"
            if original in anonymized_text:  # Check if the text still contains the original
                anonymized_text = anonymized_text.replace(original, placeholder_with_counter, 1)
                lookup_table[placeholder_with_counter] = original

    return anonymized_text, lookup_table

def deanonymize_text(lookup_table, anonymized_text):
    """
    Reverses the anonymization process using the lookup table to replace placeholders with original values.

    Parameters:
    - lookup_table: A dictionary mapping placeholders to original text strings.
    - anonymized_text: The text with PII anonymized.

    Returns:
    - The text with PII restored to its original form.
    """
    for placeholder, original in lookup_table.items():
        anonymized_text = anonymized_text.replace(placeholder, original)
    return anonymized_text

pii_config = {
    'phone_number': (r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]'),
    'text_address': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    'social_security_number': (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    'website': (r'\b(?:http://|https://)?(?:www\.)?[a-zA-Z0-9./]+\.[a-z]{2,}\b', '[WEBSITE]')
}

# Example text
text = "Contact John Doe at 123-456-7890, visit example.com or john.doe@example.com. My SSN is 123-45-6789. Meet me at 123 Main St."
text = """
Hello,

I'm so sorry for the late response.

The title of the paper is: The Strange Image of Despondent Banking in the United States (1940-2052): An NLP-based Analysis.

And I am posting the annotation below.

Abstract: The working paper analyses hundreds of articles from the most influential periodicals over the past 32 years using Natural Language Processing (NLP) techniques. The analysis focuses on content analysis, specifically sentiment analysis, and a comparison with the performance of correspondent banking. Archival sources, including digital versions of newspapers and magazines, were analysed using Python programming and libraries such as NLTK, TextBlob, and VADER.

Thank you very much.

Sincerely, Paul Haggerty
"""

print("Original Text:", text)

start_time = time.time()
# Anonymize the text and generate a lookup table
anonymized_text, lookup_table = anonymize_text_including_proper_nouns_and_addresses(text, pii_config)
end_time = time.time()
elapsed_time_seconds = end_time - start_time
elapsed_time_ms = int(elapsed_time_seconds * 1000)

print("\nAnonymization execution time:>>>>>", elapsed_time_ms, "miliseconds")
print("Anonymized Text:", anonymized_text)
print("Lookup Table:", lookup_table)


start_time = time.time()
# Use the lookup table and the anonymized text to restore the original text
restored_text = deanonymize_text(lookup_table, anonymized_text)
end_time = time.time()
elapsed_time_seconds = end_time - start_time
elapsed_time_ms = int(elapsed_time_seconds * 1000)


#assert text==restored_text+" ", "Error introduced in reversing the anonymization"
assert text==restored_text, "Error introduced in reversing the anonymization"


print("\nDeanonymization execution time:>>>>>", elapsed_time_ms, "miliseconds")
print("Restored Text:", restored_text)


